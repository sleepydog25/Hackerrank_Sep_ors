"""Deterministic gates for untrusted candidates; no cash arithmetic."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from .evidence import (EvidenceCandidate, EvidenceSource, EvidenceDecision, ValidatedEvidenceFact,
                       FactType as F, Certainty as C, Scope as S, AmountMeaning as M,
                       ValidationStatus as V, Reason as R)
from .models import FinanceRequest, FinancialEvent
from .load import CURRENCIES


@dataclass(frozen=True)
class EvidenceContext:
    request: FinanceRequest
    events: tuple[FinancialEvent, ...]
    sources: tuple[EvidenceSource, ...]


def validate(c: EvidenceCandidate, context: EvidenceContext) -> EvidenceDecision:
    def result(status,reason):
        return EvidenceDecision(c,status,reason,ValidatedEvidenceFact(c) if status==V.ACCEPTED else None)
    q=context.request
    if (c.source not in context.sources or c.source.user_id!=q.user_id
            or c.source.request_id not in (None,q.request_id)):
        return result(V.UNRESOLVED,R.SOURCE_MISMATCH)
    if not c.fact_id or not c.original_label:return result(V.UNRESOLVED,R.INSUFFICIENT_CONTEXT)
    if type(c.explicit_amendment) is not bool:return result(V.UNRESOLVED,R.INSUFFICIENT_CONTEXT)
    time=c.source.observed_at
    if time is None:return result(V.UNRESOLVED,R.MISSING_SOURCE_TIME)
    if not isinstance(time,datetime) or time.tzinfo is None:return result(V.UNRESOLVED,R.INVALID_DATES)
    if time.date()>q.request_date:return result(V.UNRESOLVED,R.FUTURE_EVIDENCE)
    event=next((e for e in context.events if e.event_id==c.source.related_event_id),None)
    if c.source.related_event_id and (event is None or event.user_id!=q.user_id):
        return result(V.UNRESOLVED,R.SOURCE_EVENT_MISMATCH)
    if not isinstance(c.fact_type,F) or not isinstance(c.certainty,C) or not isinstance(c.scope,S) or not isinstance(c.amount_meaning,M):
        return result(V.UNRESOLVED,R.INSUFFICIENT_CONTEXT)
    if c.confidence is not None and (not isinstance(c.confidence,Decimal) or not c.confidence.is_finite() or not 0<=c.confidence<=1):
        return result(V.UNRESOLVED,R.INSUFFICIENT_CONTEXT)
    if c.certainty==C.HYPOTHETICAL:return result(V.REJECTED,R.HYPOTHETICAL_NOT_ACTIONABLE)
    if c.certainty==C.CONDITIONAL:return result(V.REJECTED,R.CONDITIONAL_NOT_ACTIONABLE)
    if c.certainty==C.DISPUTED:return result(V.UNRESOLVED,R.CONFLICTING_EVIDENCE)
    if c.fact_type==F.INVESTMENT_VALUE:return result(V.REJECTED,R.VALUATION_NOT_CASH)
    if c.fact_type==F.NON_FINANCIAL:return result(V.REJECTED,R.NON_FINANCIAL)
    if c.amount_meaning in (M.GROSS_PAY,M.SUBTOTAL,M.TAX,M.ACCOUNT_BALANCE):return result(V.REJECTED,R.CONTEXT_ONLY)
    if c.certainty==C.PENDING or c.fact_type==F.PENDING_PAYOUT:return result(V.REJECTED,R.PENDING_NOT_CASH)
    if c.certainty==C.CANCELLED and c.fact_type!=F.CANCELLATION:
        return result(V.UNRESOLVED,R.CONFLICTING_EVIDENCE)
    dates=(c.effective_date,c.payment_date,c.due_date,c.period_start,c.period_end)
    if any(d is not None and type(d) is not date for d in dates):return result(V.UNRESOLVED,R.INVALID_DATES)
    if c.period_start and c.period_end and c.period_end<c.period_start:return result(V.UNRESOLVED,R.INVALID_DATES)
    if c.scope in (S.ONGOING,S.FROM_DATE,S.UNTIL_DATE) and not c.effective_date:
        return result(V.UNRESOLVED,R.INVALID_DATES)
    if c.scope==S.UNTIL_DATE and (not c.period_end or c.period_end<c.effective_date):
        return result(V.UNRESOLVED,R.INVALID_DATES)
    if c.scope in (S.ONGOING,S.FROM_DATE,S.UNTIL_DATE) and c.fact_type not in (F.SALARY,F.RENT,F.EMPLOYMENT_ENDED):
        return result(V.UNRESOLVED,R.UNSUPPORTED_SCOPE)
    if c.fact_type==F.EMPLOYMENT_ENDED and c.scope not in (S.ONGOING,S.FROM_DATE):
        return result(V.UNRESOLVED,R.UNSUPPORTED_SCOPE)
    if c.fact_type==F.RESCHEDULE and c.scope not in (S.EVENT_SPECIFIC,S.NEXT_OCCURRENCE_ONLY):
        return result(V.UNRESOLVED,R.UNSUPPORTED_SCOPE)
    if c.fact_type in (F.CANCELLATION,F.RESCHEDULE,F.EMPLOYMENT_ENDED,F.FINAL_PAYROLL,F.SALARY,F.RENT,F.PAYMENT_RECEIVED) and event is None:
        return result(V.UNRESOLVED,R.MISSING_LINK)
    if c.fact_type in (F.SALARY,F.FINAL_PAYROLL,F.EMPLOYMENT_ENDED) and (event.category!='salary' or event.direction!='credit'):
        return result(V.UNRESOLVED,R.SOURCE_EVENT_MISMATCH)
    if c.fact_type in (F.EXPENSE,F.RENT) and event and event.direction!='debit':
        return result(V.UNRESOLVED,R.SOURCE_EVENT_MISMATCH)
    if c.fact_type==F.RENT and event.category!='rent':return result(V.UNRESOLVED,R.SOURCE_EVENT_MISMATCH)
    if event and c.fact_type in (F.REFUND,F.REIMBURSEMENT,F.INVESTMENT_SALE,F.INVOICE_APPROVED):
        # A lifecycle association is not permission to turn payroll or a
        # valuation record into a different kind of cash transaction.
        compatible={F.REFUND:{'refund'},F.REIMBURSEMENT:{'refund','income'},
                    F.INVESTMENT_SALE:{'investment_sale'},F.INVOICE_APPROVED:{'income'}}
        if (event.direction!='credit' or event.event_type not in compatible[c.fact_type]
                or event.category=='salary'):
            return result(V.UNRESOLVED,R.SOURCE_EVENT_MISMATCH)
    if c.fact_type in (F.CANCELLATION,F.EMPLOYMENT_ENDED):
        if not c.effective_date:return result(V.UNRESOLVED,R.INVALID_DATES)
        if c.fact_type==F.CANCELLATION and (event.status=='settled' or c.scope not in (S.EVENT_SPECIFIC,S.NEXT_OCCURRENCE_ONLY)):
            return result(V.UNRESOLVED,R.UNSUPPORTED_SCOPE)
        if c.fact_type==F.CANCELLATION and c.effective_date>event.settlement_date:
            return result(V.UNRESOLVED,R.INVALID_DATES)
        return result(V.ACCEPTED,R.VALIDATED)
    if c.payment_date is None:return result(V.UNRESOLVED,R.INVALID_DATES)
    if event is None and c.payment_date<q.request_date and c.certainty!=C.SETTLED:
        return result(V.UNRESOLVED,R.UNCONFIRMED_SETTLEMENT)
    if c.certainty==C.SETTLED and c.payment_date>q.request_date:
        return result(V.UNRESOLVED,R.INVALID_DATES)
    if event and event.status=='pending' and event.direction=='credit' and c.certainty!=C.SETTLED and c.fact_type!=F.RESCHEDULE:
        return result(V.UNRESOLVED,R.UNCONFIRMED_SETTLEMENT)
    if c.effective_date and c.payment_date<c.effective_date:return result(V.UNRESOLVED,R.INVALID_DATES)
    if c.fact_type==F.RESCHEDULE:
        if event.status not in ('pending','scheduled'):return result(V.UNRESOLVED,R.UNSUPPORTED_SCOPE)
        return result(V.ACCEPTED,R.VALIDATED)
    if c.amount is None:return result(V.UNRESOLVED,R.MISSING_AMOUNT)
    if not isinstance(c.amount,Decimal) or not c.amount.is_finite() or c.amount<=0:
        return result(V.UNRESOLVED,R.INVALID_AMOUNT)
    if c.currency is None:return result(V.UNRESOLVED,R.MISSING_CURRENCY)
    if c.currency not in CURRENCIES:return result(V.UNRESOLVED,R.INVALID_CURRENCY)
    if event and c.currency!=event.currency:return result(V.UNRESOLVED,R.SOURCE_EVENT_MISMATCH)
    allowed={F.SALARY:{M.NET_PAY},F.FINAL_PAYROLL:{M.NET_PAY},F.EXPENSE:{M.BALANCE_DUE,M.TOTAL},
             F.RENT:{M.BALANCE_DUE,M.TOTAL},F.PAYMENT_RECEIVED:{M.AMOUNT_RECEIVED,M.AMOUNT_PAID},
             F.REFUND:{M.AMOUNT_RECEIVED},F.REIMBURSEMENT:{M.AMOUNT_RECEIVED},
             F.INVESTMENT_SALE:{M.SALE_PROCEEDS},F.INVOICE_APPROVED:{M.INVOICE_AMOUNT}}
    if c.amount_meaning not in allowed.get(c.fact_type,set()):return result(V.UNRESOLVED,R.AMBIGUOUS_AMOUNT_MEANING)
    if c.fact_type in (F.EXPENSE,F.RENT) and c.amount_meaning==M.TOTAL and event and event.amount is None:
        # A total does not establish the outstanding balance of a partially paid bill.
        return result(V.UNRESOLVED,R.AMBIGUOUS_AMOUNT_MEANING)
    if event is None and (not c.obligation_key or not c.category or c.scope!=S.ONE_OFF):
        return result(V.UNRESOLVED,R.INSUFFICIENT_CONTEXT)
    return result(V.ACCEPTED,R.VALIDATED)
