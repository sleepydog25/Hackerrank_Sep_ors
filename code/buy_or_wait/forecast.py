"""Baseline ledger and capacity. Incomplete evidence is always surfaced."""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_FLOOR
from .fx import RateBook, MissingRate
from .models import (FinancialProfile, FinancialEvent, FinanceRequest, CashFlow,
                     ForecastResult, LedgerRow, Message, ImageReference)
from .policy import DEFAULT_POLICY, ForecastPolicy
from .reconcile import reconcile, salary_event
from .recurrence import infer_series, project_dates, normalize, series_description
from .income import supplement


def forecast(profile: FinancialProfile, request: FinanceRequest,
             events: tuple[FinancialEvent, ...], rates: RateBook,
             messages: tuple[Message, ...] = (), images: tuple[ImageReference, ...] = (),
             policy: ForecastPolicy = DEFAULT_POLICY) -> ForecastResult:
    if request.user_id != profile.user_id or any(e.user_id != profile.user_id for e in events):
        raise ValueError('forecast context contains another user')
    start, end = request.request_date, request.request_date + timedelta(days=policy.horizon_days)
    issues = []
    for m in messages:
        if m.user_id == profile.user_id and m.request_id in {None, request.request_id} and m.sent_at.date() <= start:
            issues.append(f'unresolved message {m.message_id}: extraction not implemented')
    for i in images:
        if i.user_id == profile.user_id and i.request_id in {None, request.request_id}:
            issues.append(f'unresolved image {i.image_id}: extraction not implemented')
    for e in events:
        if e.amount is None:
            issues.append(f'missing amount {e.event_id}: never substituted with zero')
    reconciled = reconcile(events, start)
    flows = []
    notes = list(reconciled.notes)
    series = infer_series(reconciled.history, start, policy, notes)
    added,income_evidence=supplement(reconciled.history,reconciled.obligations,series,start,policy)
    series=series+tuple(added)
    notes.extend(f'{e.source}: {e.state}: {e.reason}' for e in income_evidence)

    def add(day, amount, direction, source, reason, inferred, currency, rate_date):
        try:
            converted, rate = rates.convert(amount, currency, profile.home_currency, rate_date)
        except MissingRate as exc:
            issues.append(f'{source}: {exc}')
            return
        flows.append(CashFlow(day, converted, direction, source, reason, inferred,
                              amount, currency, rate_date, rate))

    for e in reconciled.obligations:
        if e.amount is None:
            continue
        # Pending funds are unavailable immediately, not deducted again on settlement.
        day = start if e.status == 'pending' else max(start, e.settlement_date)
        if day <= end:
            add(day, e.amount, e.direction, e.event_id,
                'pending reservation (once)' if e.status == 'pending' else f'{e.status} cash event',
                False, e.currency, e.settlement_date)

    for s in series:
        for day in project_dates(s, start, end):
            matches = []
            # Request-exclusive inference must not reintroduce an occurrence
            # already paid today and included in the opening snapshot.
            represented=reconciled.obligations+tuple(e for e in reconciled.history if e.settlement_date==start)
            # A category accrual is not a discrete linked transaction. Its
            # overlap is handled once, by the budget-substitution policy below.
            if s.description=='*':represented=()
            for e in represented:
                if e.direction != s.direction or e.currency != s.currency or e.category != s.category:
                    continue
                same_series = (series_description(e.description,policy.robust_grouping) == s.description
                               or e.linked_event_id in s.event_ids
                               or (salary_event(e) and s.direction == 'credit'
                                   and sum(x.direction == 'credit' and x.currency == s.currency for x in series) == 1))
                same_cycle = (e.settlement_date.year, e.settlement_date.month) == (day.year, day.month) if s.cadence == 'monthly' else e.settlement_date == day
                if same_series and same_cycle:
                    matches.append(e)
            if matches:
                notes.append(f'{s.series_id} {day}: inferred occurrence replaced by '+','.join(e.event_id for e in matches))
                continue
            add(day, s.amount, s.direction, s.series_id, s.reason, True, s.currency, day)

    if policy.pending_overlap:
        flows=resolve_overlap(flows,events,series,start,notes,policy)
    ledger,low,baseline_safe,safe,earliest=simulate(profile,request,flows,policy)
    return ForecastResult(request.request_id, start, end, profile.current_available_balance,
                          profile.minimum_balance_to_keep, tuple(sorted(flows,key=lambda f:(f.date,0 if f.direction=='debit' else 1,f.source))), series, tuple(ledger),
                          low, baseline_safe, safe, earliest, tuple(dict.fromkeys(issues)), tuple(notes))


def resolve_overlap(flows,events,series,start,notes,policy):
    """Only strong identity and near-term timing justify replacing a budget slice."""
    from dataclasses import replace
    output=list(flows)
    by_id={e.event_id:e for e in events}
    for hold in sorted(events,key=lambda e:e.event_id):
        if hold.status!='pending' or hold.direction!='debit' or hold.amount is None:continue
        # A settled replacement can have removed this hold during reconciliation.
        # Such a hold must not also remove an inferred category budget.
        if not any(f.source==hold.event_id and f.reason.startswith('pending') for f in output):continue
        for s in series:
            if s.description!='*' or s.currency!=hold.currency or s.category!=hold.category:continue
            rows=[by_id[id] for id in s.event_ids]
            # Category alone, generic "fuel authorization", or similar amount
            # does not establish identity. Require exact prior description/link.
            identity=hold.linked_event_id in s.event_ids or normalize(hold.description) in {normalize(e.description) for e in rows}
            gaps=sorted((b.settlement_date-a.settlement_date).days for a,b in zip(rows,rows[1:]) if b.settlement_date>a.settlement_date)
            if not gaps:continue
            gap=gaps[len(gaps)//2]
            typical=sorted(e.amount for e in rows)[len(rows)//2]
            if not identity or not 0 <= (hold.settlement_date-start).days <= gap or not typical*policy.overlap_amount_min_ratio <= hold.amount <= typical*policy.overlap_amount_max_ratio:continue
            remaining=hold.amount
            for n,f in enumerate(output):
                if f.source!=s.series_id or not start <= f.date < start+timedelta(days=gap):continue
                reduction=min(remaining,f.original_amount)
                output[n]=replace(f,original_amount=f.original_amount-reduction,amount=f.amount-reduction*f.rate,
                                  reason=f.reason+f'; occurrence overlap {hold.event_id}')
                remaining-=reduction
                if remaining==0:break
            notes.append(f'{hold.event_id}: matched variable occurrence; budget offset {hold.amount-remaining} {hold.currency}; reservation retained')
    return output


def simulate(profile,request,flows,policy=DEFAULT_POLICY):
    """Pure ledger/capacity kernel also used by evaluation ablations."""
    start=request.request_date
    flows=sorted(flows,key=lambda f:(f.date,0 if f.direction=='debit' else 1,f.source))
    ledger = [LedgerRow(start, 'opening', Decimal(0), Decimal(0), profile.current_available_balance,
                        profile.minimum_balance_to_keep, 'opening snapshot; historical settled cash not replayed')]
    by_day = defaultdict(list)
    for f in flows:
        by_day[f.date].append(f)
    balance = profile.current_available_balance
    # Checkpoints include every event and every daily close, including quiet days.
    closes = []
    for offset in range(policy.horizon_days + 1):
        day = start + timedelta(days=offset)
        candidate_index=None
        for f in by_day[day]:
            if policy.candidate_timing=='before_credit' and f.direction=='credit' and candidate_index is None:
                ledger.append(LedgerRow(day,'candidate',Decimal(0),Decimal(0),balance,profile.minimum_balance_to_keep,'candidate before salary'))
                candidate_index=len(ledger)-1
            inflow = f.amount if f.direction == 'credit' else Decimal(0)
            outflow = f.amount if f.direction == 'debit' else Decimal(0)
            balance += inflow - outflow
            provenance = f'{f.reason}; {"inferred" if f.inferred else "explicit"}; {f.original_amount} {f.original_currency} x {f.rate} @ {f.rate_date}'
            ledger.append(LedgerRow(day, f.source, inflow, outflow, balance,
                                    profile.minimum_balance_to_keep, provenance))
        ledger.append(LedgerRow(day, 'close', Decimal(0), Decimal(0), balance,
                                profile.minimum_balance_to_keep, 'candidate payment occurs after this checkpoint'))
        closes.append(candidate_index if candidate_index is not None else len(ledger)-1)
    low = min(row.balance for row in ledger)
    baseline_safe = low >= profile.minimum_balance_to_keep
    # Payment on a date occurs after daily debits/credits. Prefix must already be
    # safe, and every checkpoint from payment onward must retain the reserve.
    suffix_min = [Decimal(0)] * len(ledger)
    running = ledger[-1].balance
    for n in range(len(ledger)-1, -1, -1):
        running = min(running, ledger[n].balance)
        suffix_min[n] = running
    today_capacity = max(Decimal(0), suffix_min[closes[0]] - profile.minimum_balance_to_keep) if baseline_safe else Decimal(0)
    safe = min(request.requested_amount, today_capacity.quantize(policy.cent, rounding=ROUND_FLOOR))
    earliest = None
    if baseline_safe:
        for checkpoint in closes:
            if suffix_min[checkpoint] - profile.minimum_balance_to_keep >= request.requested_amount:
                earliest = ledger[checkpoint].date
                break
    return ledger,low,baseline_safe,safe,earliest


def forecast_request(dataset, request: FinanceRequest) -> ForecastResult:
    result = forecast(dataset.profiles[request.user_id], request,
                      dataset.events_by_user.get(request.user_id, ()), RateBook(dataset.rates),
                      dataset.messages_by_user.get(request.user_id, ()),
                      dataset.images_by_user.get(request.user_id, ()))
    return result
