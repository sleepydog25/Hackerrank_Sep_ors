"""Interchangeable, request-anchored expense estimators. No sample labels."""
from datetime import timedelta
from decimal import Decimal, ROUND_CEILING
from statistics import median


def rank(values, fraction):
    ordered = sorted(values)
    n = int((len(ordered)*fraction).to_integral_value(rounding=ROUND_CEILING))
    return ordered[max(0,n-1)]


def estimate(daily, start, policy):
    dates=sorted(daily)
    values=[daily[d] for d in dates]
    gap=Decimal(str(median([(b-a).days for a,b in zip(dates,dates[1:])])))
    # From first observed purchase to request-exclusive window: never pretend
    # unobserved time before the first record was confirmed zero spending.
    exposure=Decimal((start-dates[0]).days)
    observed=sum(values)/exposure
    method=policy.variable_estimator
    cadence='daily'
    if method in {'p75_daily','cadence'}:
        amount=rank(values,policy.variable_quantile)
        rate=amount/gap
        if method=='cadence': cadence='interval'
    elif method=='mean_daily': rate=observed
    elif method=='trimmed_daily':
        count=int(len(values)*policy.trim_fraction)
        ordered=sorted(values)
        trimmed=ordered[count:len(values)-count] if count else ordered
        rate=(sum(trimmed)/len(trimmed))*len(values)/exposure
    elif method=='median_daily': rate=Decimal(str(median(values)))/gap
    elif method=='weekly_p75':
        # Complete, request-anchored seven-day windows, including empty weeks.
        weeks=int(exposure)//7
        totals=[sum(v for d,v in daily.items() if start-timedelta(days=7*(n+1)) <= d < start-timedelta(days=7*n)) for n in range(weeks)]
        rate=rank(totals,policy.variable_quantile)/Decimal(7) if weeks else observed
    else: raise ValueError(f'unknown variable estimator {method}')
    amount=(amount if cadence=='interval' else rate).quantize(policy.cent,rounding=ROUND_CEILING)
    return amount,cadence,int(gap),f'{method}; observed={observed} per calendar day; modeled={rate}; exposure={exposure} days; n={len(values)}'
