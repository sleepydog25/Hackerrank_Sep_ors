"""Untrusted typed extraction contract. Parsing never authorizes cash."""
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
import json


class SourceType(StrEnum):
    MESSAGE = 'MESSAGE'
    IMAGE = 'IMAGE'


class FactType(StrEnum):
    SALARY = 'SALARY'  # amount/change distinguished by scope and amendment flag
    EXPENSE = 'EXPENSE'  # includes outstanding invoice balance
    RENT = 'RENT'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED'
    REFUND = 'REFUND'
    REIMBURSEMENT = 'REIMBURSEMENT'
    INVESTMENT_VALUE = 'INVESTMENT_VALUE'
    INVESTMENT_SALE = 'INVESTMENT_SALE'
    INVOICE_APPROVED = 'INVOICE_APPROVED'
    PENDING_PAYOUT = 'PENDING_PAYOUT'
    RESCHEDULE = 'RESCHEDULE'  # delay is a later payment date
    CANCELLATION = 'CANCELLATION'
    EMPLOYMENT_ENDED = 'EMPLOYMENT_ENDED'
    FINAL_PAYROLL = 'FINAL_PAYROLL'
    NON_FINANCIAL = 'NON_FINANCIAL'


class Certainty(StrEnum):
    CONFIRMED = 'CONFIRMED'
    SETTLED = 'SETTLED'
    PENDING = 'PENDING'
    HYPOTHETICAL = 'HYPOTHETICAL'
    CONDITIONAL = 'CONDITIONAL'
    DISPUTED = 'DISPUTED'
    CANCELLED = 'CANCELLED'


class Scope(StrEnum):
    EVENT_SPECIFIC = 'EVENT_SPECIFIC'
    NEXT_OCCURRENCE_ONLY = 'NEXT_OCCURRENCE_ONLY'
    ONGOING = 'ONGOING'
    UNTIL_DATE = 'UNTIL_DATE'
    FROM_DATE = 'FROM_DATE'
    ONE_OFF = 'ONE_OFF'


class AmountMeaning(StrEnum):
    NET_PAY = 'net_pay'
    GROSS_PAY = 'gross_pay'
    SUBTOTAL = 'subtotal'
    TAX = 'tax'
    TOTAL = 'total'
    AMOUNT_PAID = 'amount_paid'
    AMOUNT_RECEIVED = 'amount_received'
    BALANCE_DUE = 'balance_due'
    LATE_FEE = 'late_fee'
    ACCOUNT_BALANCE = 'account_balance'
    INVOICE_AMOUNT = 'invoice_amount'
    VALUATION = 'valuation'
    SALE_PROCEEDS = 'sale_proceeds'
    UNKNOWN = 'unknown'


class ValidationStatus(StrEnum):
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'
    UNRESOLVED = 'UNRESOLVED'


class Reason(StrEnum):
    VALIDATED = 'VALIDATED'
    APPLIED = 'APPLIED'
    COMPATIBLE = 'COMPATIBLE'
    SUPERSEDED = 'SUPERSEDED'
    HYPOTHETICAL_NOT_ACTIONABLE = 'HYPOTHETICAL_NOT_ACTIONABLE'
    CONDITIONAL_NOT_ACTIONABLE = 'CONDITIONAL_NOT_ACTIONABLE'
    PENDING_NOT_CASH = 'PENDING_NOT_CASH'
    VALUATION_NOT_CASH = 'VALUATION_NOT_CASH'
    NON_FINANCIAL = 'NON_FINANCIAL'
    MISSING_AMOUNT = 'MISSING_AMOUNT'
    INVALID_AMOUNT = 'INVALID_AMOUNT'
    MISSING_CURRENCY = 'MISSING_CURRENCY'
    INVALID_CURRENCY = 'INVALID_CURRENCY'
    AMBIGUOUS_AMOUNT_MEANING = 'AMBIGUOUS_AMOUNT_MEANING'
    SOURCE_MISMATCH = 'SOURCE_MISMATCH'
    SOURCE_EVENT_MISMATCH = 'SOURCE_EVENT_MISMATCH'
    MISSING_SOURCE_TIME = 'MISSING_SOURCE_TIME'
    FUTURE_EVIDENCE = 'FUTURE_EVIDENCE'
    INVALID_DATES = 'INVALID_DATES'
    UNSUPPORTED_SCOPE = 'UNSUPPORTED_SCOPE'
    CONFLICTING_EVIDENCE = 'CONFLICTING_EVIDENCE'
    MISSING_LINK = 'MISSING_LINK'
    PAST_CASH_IN_SNAPSHOT = 'PAST_CASH_IN_SNAPSHOT'
    INSUFFICIENT_CONTEXT = 'INSUFFICIENT_CONTEXT'
    UNCONFIRMED_SETTLEMENT = 'UNCONFIRMED_SETTLEMENT'
    SOURCE_NOT_EXHAUSTED = 'SOURCE_NOT_EXHAUSTED'
    NO_CANDIDATES = 'NO_CANDIDATES'
    CONTEXT_ONLY = 'CONTEXT_ONLY'


@dataclass(frozen=True)
class EvidenceSource:
    source_type: SourceType
    source_id: str
    user_id: str
    request_id: str | None = None
    related_event_id: str | None = None
    observed_at: datetime | None = None
    publisher_id: str | None = None  # trusted source identity, not source category


@dataclass(frozen=True)
class EvidenceCandidate:
    fact_id: str
    source: EvidenceSource
    fact_type: FactType
    certainty: Certainty
    scope: Scope
    amount_meaning: AmountMeaning
    original_label: str
    amount: Decimal | None = None
    currency: str | None = None
    effective_date: date | None = None
    payment_date: date | None = None
    due_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    confidence: Decimal | None = None  # diagnostic only; no financial threshold
    explicit_amendment: bool = False
    category: str | None = None
    obligation_key: str | None = None  # stable external transaction reference for new cash


@dataclass(frozen=True)
class ValidatedEvidenceFact:
    candidate: EvidenceCandidate


@dataclass(frozen=True)
class EvidenceDecision:
    candidate: EvidenceCandidate
    status: ValidationStatus
    reason: Reason
    fact: ValidatedEvidenceFact | None = None


@dataclass(frozen=True)
class EvidenceBatch:
    source: EvidenceSource
    candidates: tuple[EvidenceCandidate, ...]
    exhaustive: bool = False  # extractor must explicitly account for whole source


def to_json(candidate: EvidenceCandidate) -> str:
    def encode(value):
        if isinstance(value, Decimal):return str(value)
        if isinstance(value, (date, datetime)):return value.isoformat()
        raise TypeError(type(value).__name__)
    return json.dumps(asdict(candidate),default=encode,sort_keys=True)


def from_json(text: str) -> EvidenceCandidate:
    """Strict transport parser. Money must be strings, never JSON float numbers."""
    def unique_fields(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('duplicate JSON field: '+key)
            result[key]=value
        return result
    raw=json.loads(text,object_pairs_hook=unique_fields)
    if not isinstance(raw,dict) or set(raw)-{f.name for f in fields(EvidenceCandidate)}:
        raise ValueError('invalid candidate fields')
    source=raw.pop('source')
    source['source_type']=SourceType(source['source_type'])
    if source.get('observed_at'):
        source['observed_at']=datetime.fromisoformat(source['observed_at'])
    raw['source']=EvidenceSource(**source)
    for name,kind in [('fact_type',FactType),('certainty',Certainty),('scope',Scope),('amount_meaning',AmountMeaning)]:
        raw[name]=kind(raw[name])
    for name in ('amount','confidence'):
        if raw.get(name) is not None:
            if not isinstance(raw[name],str):raise ValueError('Decimal fields require strings')
            raw[name]=Decimal(raw[name])
    for name in ('effective_date','payment_date','due_date','period_start','period_end'):
        if raw.get(name) is not None:
            value=raw[name]
            parsed=date.fromisoformat(value)
            if parsed.isoformat()!=value:raise ValueError('dates require YYYY-MM-DD')
            raw[name]=parsed
    if 'explicit_amendment' in raw and type(raw['explicit_amendment']) is not bool:
        raise ValueError('explicit_amendment requires boolean')
    return EvidenceCandidate(**raw)
