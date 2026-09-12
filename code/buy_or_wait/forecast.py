"""Baseline ledger and capacity. Incomplete evidence is always surfaced."""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_FLOOR
from .fx import RateBook, MissingRate
from .models import (FinancialProfile, FinancialEvent, FinanceRequest, CashFlow,
                     ForecastResult, LedgerRow, Message, ImageReference)
from .policy import DEFAULT_POLICY, ForecastPolicy
from .reconcile import reconcile, salary_event
from .recurrence import infer_series, project_dates, normalize


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
            for e in reconciled.obligations:
                if e.direction != s.direction or e.currency != s.currency or e.category != s.category:
                    continue
                same_series = (normalize(e.description) == s.description
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

    flows.sort(key=lambda f: (f.date, 0 if f.direction == 'debit' else 1, f.source))
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
        for f in by_day[day]:
            inflow = f.amount if f.direction == 'credit' else Decimal(0)
            outflow = f.amount if f.direction == 'debit' else Decimal(0)
            balance += inflow - outflow
            provenance = f'{f.reason}; {"inferred" if f.inferred else "explicit"}; {f.original_amount} {f.original_currency} x {f.rate} @ {f.rate_date}'
            ledger.append(LedgerRow(day, f.source, inflow, outflow, balance,
                                    profile.minimum_balance_to_keep, provenance))
        ledger.append(LedgerRow(day, 'close', Decimal(0), Decimal(0), balance,
                                profile.minimum_balance_to_keep, 'candidate payment occurs after this checkpoint'))
        closes.append(len(ledger)-1)
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
    return ForecastResult(request.request_id, start, end, profile.current_available_balance,
                          profile.minimum_balance_to_keep, tuple(flows), series, tuple(ledger),
                          low, baseline_safe, safe, earliest, tuple(dict.fromkeys(issues)), tuple(notes))


def forecast_request(dataset, request: FinanceRequest) -> ForecastResult:
    result = forecast(dataset.profiles[request.user_id], request,
                      dataset.events_by_user.get(request.user_id, ()), RateBook(dataset.rates),
                      dataset.messages_by_user.get(request.user_id, ()),
                      dataset.images_by_user.get(request.user_id, ()))
    return result
