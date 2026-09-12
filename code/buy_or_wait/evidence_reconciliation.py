"""Validate, resolve conflicts and normalize records without forecasting balances."""
from collections import defaultdict
from dataclasses import replace
from hashlib import sha256
from .evidence import (FactType as F, Scope as S, Certainty as C, AmountMeaning as M,
                       ValidationStatus as V, Reason as R, EvidenceDecision)
from .evidence_validation import validate, EvidenceContext
from .evidence_state import NormalizedEvidenceState, FinancialAmendment, SeriesAmendment, SeriesAction as A
from .models import FinancialEvent


def reconcile_evidence(candidates, context: EvidenceContext) -> NormalizedEvidenceState:
    candidates=tuple(candidates)
    if len({c.fact_id for c in candidates})!=len(candidates):raise ValueError('duplicate evidence fact IDs')
    decisions={c.fact_id:validate(c,context) for c in candidates}
    groups=defaultdict(list)
    for c in candidates:
        if decisions[c.fact_id].status==V.ACCEPTED:
            groups[c.source.related_event_id or ('new',c.obligation_key)].append(c)
    events={e.event_id:e for e in context.events}
    amendments=[]; rules=[]; confirmed=set()
    def decide(c,status,reason):
        old=decisions[c.fact_id]
        decisions[c.fact_id]=replace(old,status=status,reason=reason,fact=old.fact if status==V.ACCEPTED else None)
    for key,rows in sorted(groups.items(),key=lambda pair:str(pair[0])):
        # Atomic per target. Contradictory partial interpretations never partly apply.
        def signature(c):
            return (c.fact_type,c.certainty,c.scope,c.amount_meaning,c.amount,c.currency,
                    c.effective_date,c.payment_date,c.period_start,c.period_end,c.category)
        rows.sort(key=lambda c:(c.source.observed_at,c.fact_id))
        chosen=rows[-1]
        if len({signature(c) for c in rows})>1:
            cancellations=[c for c in rows if c.fact_type==F.CANCELLATION]
            same_publisher=len({c.source.publisher_id for c in rows})==1 and rows[0].source.publisher_id is not None
            if cancellations and all(c.scope in (S.EVENT_SPECIFIC,S.NEXT_OCCURRENCE_ONLY) for c in rows):
                chosen=cancellations[-1]
            elif not (same_publisher and chosen.explicit_amendment and chosen.source.observed_at>max(c.source.observed_at for c in rows[:-1])):
                for c in rows:decide(c,V.UNRESOLVED,R.CONFLICTING_EVIDENCE)
                continue
        for c in rows:
            if c!=chosen:decide(c,V.REJECTED,R.SUPERSEDED if signature(c)!=signature(chosen) else R.COMPATIBLE)
        c=chosen
        target=events.get(c.source.related_event_id)
        day=c.payment_date
        after=None
        if target and target.status=='settled' and target.settlement_date<=context.request.request_date and c.fact_type!=F.EMPLOYMENT_ENDED:
            # A correction may clarify missing historical data, but never replay cash.
            if target.amount is not None:
                if c.fact_type==F.FINAL_PAYROLL:
                    rules.append(SeriesAmendment(target,A.END,day,None,None,c.fact_id,c.source.source_id))
                    amendments.append(FinancialAmendment(c.fact_id,c.source,c.original_label,target,target))
                    decide(c,V.ACCEPTED,R.APPLIED)
                elif c.scope in (S.ONGOING,S.FROM_DATE,S.UNTIL_DATE) and c.fact_type in (F.SALARY,F.RENT):
                    rules.append(SeriesAmendment(target,A.AMOUNT,c.effective_date,c.period_end if c.scope==S.UNTIL_DATE else None,c.amount,c.fact_id,c.source.source_id))
                    amendments.append(FinancialAmendment(c.fact_id,c.source,c.original_label,target,target))
                    decide(c,V.ACCEPTED,R.APPLIED)
                else:decide(c,V.REJECTED,R.PAST_CASH_IN_SNAPSHOT)
                continue
        if c.fact_type==F.EMPLOYMENT_ENDED:
            rules.append(SeriesAmendment(target,A.END,c.effective_date,None,None,c.fact_id,c.source.source_id))
            after=target
        elif c.fact_type==F.CANCELLATION:
            after=replace(target,status='cancelled')
            rules.append(SeriesAmendment(target,A.SKIP_OCCURRENCE,target.settlement_date,None,None,c.fact_id,c.source.source_id))
        elif c.fact_type==F.RESCHEDULE:
            after=replace(target,settlement_date=day)
        elif c.fact_type==F.PAYMENT_RECEIVED and target.direction=='debit':
            if c.amount!=target.amount or day>context.request.request_date or c.certainty!=C.SETTLED:
                decide(c,V.UNRESOLVED,R.INSUFFICIENT_CONTEXT); continue
            after=replace(target,status='settled',settlement_date=day)
            rules.append(SeriesAmendment(target,A.SKIP_OCCURRENCE,target.settlement_date,None,None,c.fact_id,c.source.source_id))
        elif target:
            if target.amount is not None and target.amount!=c.amount and not c.explicit_amendment:
                decide(c,V.UNRESOLVED,R.CONFLICTING_EVIDENCE); continue
            if target.direction=='credit' and c.fact_type in (F.EXPENSE,F.RENT):
                decide(c,V.UNRESOLVED,R.SOURCE_EVENT_MISMATCH); continue
            if target.direction!='credit' and c.fact_type not in (F.EXPENSE,F.RENT):
                decide(c,V.UNRESOLVED,R.SOURCE_EVENT_MISMATCH); continue
            status='settled' if c.certainty==C.SETTLED else target.status
            after=replace(target,amount=c.amount,settlement_date=day,status=status)
            if c.fact_type==F.FINAL_PAYROLL:
                rules.append(SeriesAmendment(target,A.END,day,None,None,c.fact_id,c.source.source_id))
            elif c.scope in (S.ONGOING,S.FROM_DATE,S.UNTIL_DATE):
                rules.append(SeriesAmendment(target,A.AMOUNT,c.effective_date,c.period_end if c.scope==S.UNTIL_DATE else None,c.amount,c.fact_id,c.source.source_id))
        else:
            direction='debit' if c.fact_type==F.EXPENSE else 'credit'
            if any(e.direction==direction and e.currency==c.currency and e.amount==c.amount and e.settlement_date==day for e in context.events):
                decide(c,V.UNRESOLVED,R.MISSING_LINK); continue
            identity=sha256((c.source.user_id+'|'+c.obligation_key).encode()).hexdigest()[:24]
            kind='expense' if direction=='debit' else 'investment_sale' if c.fact_type==F.INVESTMENT_SALE else 'refund' if c.fact_type in (F.REFUND,F.REIMBURSEMENT) else 'income'
            after=FinancialEvent('evidence:'+identity,c.source.user_id,kind,'Evidence '+c.fact_type.value,
                                 c.category,direction,c.amount,c.currency,c.source.observed_at.date(),day,
                                 'settled' if c.certainty==C.SETTLED else 'scheduled',None,'fixed',None)
        if after is not None:
            if after.direction=='credit' and c.certainty in (C.CONFIRMED,C.SETTLED) and c.fact_type not in (F.EMPLOYMENT_ENDED,F.RESCHEDULE):
                confirmed.add(after.event_id)
            events[after.event_id]=after
            amendments.append(FinancialAmendment(c.fact_id,c.source,c.original_label,target,after))
            decide(c,V.ACCEPTED,R.APPLIED)
    return NormalizedEvidenceState(tuple(context.events),tuple(events.values()),tuple(decisions[c.fact_id] for c in sorted(candidates,key=lambda c:c.fact_id)),
                                   tuple(amendments),tuple(rules),frozenset(confirmed))
