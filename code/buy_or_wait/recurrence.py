"""Small, inspectable recurrence rules; no fitted labels or inferred windfalls."""
import calendar
import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING
from statistics import median
from .models import FinancialEvent, RecurringSeries
from .policy import DEFAULT_POLICY, NONRECURRING_WORDS, ENDED_INCOME_WORDS, ForecastPolicy
from .reconcile import salary_event
from .spending import estimate


def normalize(text: str) -> str:
    return ' '.join(re.findall(r'[a-z0-9]+', text.casefold()))


def series_description(text: str, robust: bool) -> str:
    if robust:
        # Strip billing period tokens, never account numbers or vendor identities.
        text=re.sub(r'\b\d{4}-\d{2}(?:-\d{2})?\b','',text)
        text=re.sub(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b','',text,flags=re.I)
    return normalize(text)


def quantile(values, fraction: Decimal) -> Decimal:
    """Nearest-rank quantile, retaining Decimal arithmetic."""
    ordered = sorted(values)
    rank = int((Decimal(len(ordered)) * fraction).to_integral_value(rounding=ROUND_CEILING))
    return ordered[max(0, rank - 1)]


def monthly_date(anchor: date, offset: int) -> date:
    month = anchor.year * 12 + anchor.month - 1 + offset
    year, zero_month = divmod(month, 12)
    last = calendar.monthrange(year, zero_month + 1)[1]
    is_month_end = anchor.day == calendar.monthrange(anchor.year, anchor.month)[1]
    return date(year, zero_month + 1, last if is_month_end else min(anchor.day, last))


def infer_series(history: tuple[FinancialEvent, ...], start: date,
                 policy: ForecastPolicy = DEFAULT_POLICY, notes: list[str] | None = None) -> tuple[RecurringSeries, ...]:
    notes = notes if notes is not None else []
    groups = defaultdict(list)
    for e in history:
        if (e.amount is None or e.status != 'settled' or e.direction == 'non_cash'
                or not start - timedelta(days=policy.history_days) <= e.settlement_date < start):
            continue
        if any(w in e.description.casefold() for w in NONRECURRING_WORDS):
            continue
        if e.direction == 'credit' and not salary_event(e):
            notes.append(f'{e.event_id}: not recurring income; no regular salary evidence')
            continue
        if e.direction == 'debit' and e.event_type not in {'expense', 'subscription', 'debt_payment'}:
            continue
        variable = e.direction == 'debit' and e.category in policy.variable_categories
        key = (e.category, '*' if variable else series_description(e.description,policy.robust_grouping), e.direction, e.currency)
        groups[key].append(e)
    series = []
    for key, rows in sorted(groups.items()):
        rows.sort(key=lambda e: (e.settlement_date, e.event_id))
        category, description, direction, currency = key
        # Aggregate transactions on a day before estimating category cadence.
        daily = defaultdict(Decimal)
        for e in rows:
            daily[e.settlement_date] += e.amount
        dates = sorted(daily)
        if len(dates) < policy.minimum_observations:
            notes.append(f'{key}: recurrence rejected; fewer than {policy.minimum_observations} observed dates')
            continue
        amounts = list(daily.values())
        gaps = [(b-a).days for a, b in zip(dates, dates[1:])]
        interval = int(median(gaps))
        months = [d.year * 12 + d.month for d in dates]
        month_steps = [b-a for a, b in zip(months, months[1:])]
        month_end = all(d.day == calendar.monthrange(d.year, d.month)[1] for d in dates)
        monthly = (all(step == 1 for step in month_steps)
                   and (month_end or max(d.day for d in dates)-min(d.day for d in dates) <= policy.monthly_day_tolerance))
        variable = description == '*'
        if variable:
            if interval <= 0 or interval > policy.maximum_interval_days:
                continue
            # Robust upper-typical transaction amount spread over observed cadence.
            # Daily reservation avoids assuming groceries can wait until payday.
            amount,cadence,interval,reason=estimate(daily,start,policy)
            if cadence=='daily':interval=1
        else:
            if monthly:
                cadence, interval = 'monthly', None
            elif (0 < interval <= policy.maximum_interval_days
                  and all(abs(g-interval) <= policy.interval_tolerance_days for g in gaps)):
                cadence = 'interval'
            else:
                notes.append(f'{key}: recurrence rejected; irregular cadence')
                continue
            if direction == 'credit':
                endings = [e for e in history if e.direction == 'credit' and e.currency == currency
                           and any(word in e.description.casefold() for word in ENDED_INCOME_WORDS)
                           and e.settlement_date >= dates[-1]]
                if endings:
                    notes.append(f'{key}: no future salary inferred; explicit final payroll in history')
                    continue
                recent = amounts[-policy.minimum_observations:]
                if min(recent) == 0 or max(recent) / min(recent) > policy.amount_stability_ratio:
                    notes.append(f'{key}: recurring income rejected; unstable recent amounts')
                    continue
                expected_gap = Decimal(31 if monthly else interval)
                if Decimal((start-dates[-1]).days) > expected_gap * policy.stale_income_cycles:
                    notes.append(f'{key}: recurring income rejected; stale history')
                    continue
                amount = min(recent)
                reason = f'regular salary: minimum of last {len(recent)} amounts; stable cadence'
            else:
                amount = max(amounts[-1], quantile(amounts, policy.variable_quantile))
                reason = 'recurring debit: max(latest amount, P75 history); no optional reductions'
        series.append(RecurringSeries('series:'+'|'.join(key), category, description, direction,
                                      currency, amount, cadence, dates[-1], interval,
                                      tuple(e.event_id for e in rows), reason))
    return tuple(series)


def project_dates(series: RecurringSeries, start: date, end: date):
    if series.cadence == 'daily':
        day = start
        while day <= end:
            yield day
            day += timedelta(days=1)
    elif series.cadence == 'monthly':
        offset = 1
        day = monthly_date(series.anchor, offset)
        while day <= end:
            if day >= start:
                yield day
            offset += 1
            day = monthly_date(series.anchor, offset)
    else:
        day = series.anchor + timedelta(days=series.interval_days)
        while day <= end:
            if day >= start:
                yield day
            day += timedelta(days=series.interval_days)
