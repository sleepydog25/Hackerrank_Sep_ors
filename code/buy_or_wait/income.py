"""Evidence states and conservative, independently selectable income inference."""
from dataclasses import dataclass
from enum import StrEnum
from datetime import timedelta
from decimal import Decimal
from collections import defaultdict
from .models import RecurringSeries
from .policy import ENDED_INCOME_WORDS, NONRECURRING_WORDS
from .reconcile import salary_event
from .recurrence import series_description


def payroll_source(description):
    """Retain informative source words; generic payroll labels identify no employer."""
    generic={'salary','payroll','credit','next','confirmed','first','prorated','monthly',
             'regular','employer','payment','pay','job','partial','month'}
    return frozenset(series_description(description,True).split())-generic


class EvidenceStrength(StrEnum):
    CONFIRMED='CONFIRMED'
    SUPPORTED_RECURRING='SUPPORTED_RECURRING'
    INSUFFICIENT='INSUFFICIENT'
    TERMINATED='TERMINATED'
    ONE_OFF='ONE_OFF'


@dataclass(frozen=True)
class IncomeEvidence:
    source: str
    state: EvidenceStrength
    reason: str


def supplement(history, future, existing, start, policy):
    additions=[]
    evidence=[]
    credits=[e for e in history if e.direction=='credit' and e.amount is not None
             and start-timedelta(days=policy.history_days) <= e.settlement_date < start]
    for e in credits:
        if any(w in e.description.casefold() for w in ENDED_INCOME_WORDS):
            state,reason=EvidenceStrength.TERMINATED,'explicit final payroll'
        elif any(w in e.description.casefold() for w in NONRECURRING_WORDS):
            state,reason=EvidenceStrength.ONE_OFF,'nonrecurring component'
        elif any(e.event_id in s.event_ids for s in existing):
            state,reason=EvidenceStrength.SUPPORTED_RECURRING,'cadence-supported history'
        else: state,reason=EvidenceStrength.INSUFFICIENT,'no accepted recurring series'
        evidence.append(IncomeEvidence(e.event_id,state,reason))
    confirmed=[e for e in future if e.status=='scheduled' and salary_event(e) and e.amount is not None]
    evidence.extend(IncomeEvidence(e.event_id,EvidenceStrength.CONFIRMED,'scheduled salary; dated credit only') for e in confirmed)
    if policy.income_policy=='legacy':return additions,evidence
    currencies={e.currency for e in credits+confirmed}
    for currency in sorted(currencies):
        if any(s.direction=='credit' and s.currency==currency for s in existing):continue
        payroll=sorted([e for e in credits if e.currency==currency and salary_event(e)],key=lambda e:e.settlement_date)
        upcoming=[e for e in confirmed if e.currency==currency]
        ended=any(e.currency==currency and any(w in e.description.casefold() for w in ENDED_INCOME_WORDS) for e in credits)
        if ended:continue
        if len(upcoming)==1 and payroll:
            last,next_pay=payroll[-1],upcoming[0]
            source,next_source=payroll_source(last.description),payroll_source(next_pay.description)
            # Similar amount/cadence cannot bridge two explicitly different jobs.
            if source and next_source and source!=next_source:continue
            months=(next_pay.settlement_date.year-last.settlement_date.year)*12+next_pay.settlement_date.month-last.settlement_date.month
            same_day=abs(next_pay.settlement_date.day-last.settlement_date.day)<=policy.monthly_day_tolerance
            # A prorated first pay may differ. Otherwise require stable amount.
            prorated='prorat' in last.description.casefold() or 'first salary' in last.description.casefold()
            stable=min(last.amount,next_pay.amount)>0 and max(last.amount,next_pay.amount)/min(last.amount,next_pay.amount)<=policy.amount_stability_ratio
            if months==1 and same_day and (prorated or stable):
                amount=next_pay.amount if prorated else min(last.amount,next_pay.amount)
                s=RecurringSeries('income:confirmed-bridge:'+currency,'salary','confirmed payroll bridge','credit',currency,amount,'monthly',next_pay.settlement_date,None,(last.event_id,next_pay.event_id),'SUPPORTED_RECURRING: historical payroll plus next confirmed monthly salary')
                additions.append(s)
                evidence.append(IncomeEvidence(s.series_id,EvidenceStrength.SUPPORTED_RECURRING,s.reason))
                continue
        if policy.income_policy in {'two_payrolls','freelance'} and len(payroll)>=2:
            a,b=payroll[-2:]
            if (policy.experimental_payroll_gap_min <= (b.settlement_date-a.settlement_date).days <= policy.experimental_payroll_gap_max
                    and a.amount==b.amount and (start-b.settlement_date).days<=policy.experimental_income_recent_days
                    and payroll_source(a.description)==payroll_source(b.description)):
                s=RecurringSeries('income:two-payrolls:'+currency,'salary','two payrolls','credit',currency,min(a.amount,b.amount),'monthly',b.settlement_date,None,(a.event_id,b.event_id),'SUPPORTED_RECURRING: two equal monthly payrolls')
                additions.append(s)
                evidence.append(IncomeEvidence(s.series_id,EvidenceStrength.SUPPORTED_RECURRING,s.reason))
                continue
        if policy.income_policy=='freelance':
            rows=[e for e in credits if e.currency==currency and e.category=='salary'
                  and any(w in e.description.casefold() for w in ('freelance','contract','invoice','retainer','project','consulting'))
                  and not any(w in e.description.casefold() for w in NONRECURRING_WORDS)]
            monthly=defaultdict(Decimal)
            for e in rows: monthly[(e.settlement_date.year,e.settlement_date.month)]+=e.amount
            keys=sorted(monthly)
            ordinal=[y*12+m for y,m in keys]
            if len(keys)>=policy.minimum_observations and all(b-a==1 for a,b in zip(ordinal,ordinal[1:])) and (start-max(e.settlement_date for e in rows)).days<=policy.experimental_income_recent_days:
                # Budget only the minimum completed-month receipts, at month end.
                import calendar
                y,m=keys[-1]
                from datetime import date
                s=RecurringSeries('income:freelance:'+currency,'salary','contract income','credit',currency,min(monthly.values()),'monthly',date(y,m,calendar.monthrange(y,m)[1]),None,tuple(e.event_id for e in rows),'SUPPORTED_RECURRING candidate: minimum monthly contract receipts, month-end availability')
                additions.append(s)
                evidence.append(IncomeEvidence(s.series_id,EvidenceStrength.SUPPORTED_RECURRING,s.reason))
    return additions,evidence
