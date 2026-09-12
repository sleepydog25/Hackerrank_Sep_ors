"""Immutable input and output records; money is Decimal, never float."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class FinancialProfile:
    user_id: str
    home_currency: str
    current_available_balance: Decimal
    minimum_balance_to_keep: Decimal
    financial_priorities: frozenset[str]
    expense_categories_to_protect: frozenset[str]
    expense_categories_user_is_willing_to_reduce: frozenset[str]
    expense_categories_user_is_willing_to_stop: frozenset[str]
    payment_methods_user_will_consider: frozenset[str]
    max_installment_months: int | None


@dataclass(frozen=True)
class FinancialEvent:
    event_id: str
    user_id: str
    event_type: str
    description: str
    category: str
    direction: str
    amount: Decimal | None
    currency: str
    event_date: date
    settlement_date: date | None
    status: str
    linked_event_id: str | None
    flexibility: str
    minimum_allowed_amount: Decimal | None


@dataclass(frozen=True)
class FinanceRequest:
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: Decimal
    desired_completion_date: date
    allows_partial_payment: bool
    request_text: str


@dataclass(frozen=True)
class PaymentOption:
    payment_option_id: str
    request_id: str
    payment_method: str
    payment_amount: Decimal
    number_of_payments: int
    first_payment_date: date
    payment_frequency_days: int | None
    financing_fee: Decimal
    total_payable_amount: Decimal


@dataclass(frozen=True)
class ExchangeRate:
    rate_date: date
    from_currency: str
    to_currency: str
    rate: Decimal


@dataclass(frozen=True)
class Message:
    message_id: str
    user_id: str
    request_id: str | None
    related_event_id: str | None
    sent_at: datetime
    source_type: str
    message_text: str


@dataclass(frozen=True)
class ImageReference:
    image_id: str
    user_id: str
    request_id: str | None
    related_event_id: str | None


@dataclass(frozen=True)
class Payment:
    date: date
    amount: Decimal


@dataclass(frozen=True)
class CashFlow:
    date: date
    amount: Decimal
    direction: str
    source: str
    reason: str
    inferred: bool
    original_amount: Decimal
    original_currency: str
    rate_date: date
    rate: Decimal


@dataclass(frozen=True)
class RecurringSeries:
    series_id: str
    category: str
    description: str
    direction: str
    currency: str
    amount: Decimal
    cadence: str
    anchor: date
    interval_days: int | None
    event_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class LedgerRow:
    date: date
    source: str
    inflow: Decimal
    outflow: Decimal
    balance: Decimal
    minimum: Decimal
    provenance: str


@dataclass(frozen=True)
class ForecastResult:
    request_id: str
    start: date
    end: date
    opening_balance: Decimal
    minimum_balance: Decimal
    cash_flows: tuple[CashFlow, ...]
    series: tuple[RecurringSeries, ...]
    ledger: tuple[LedgerRow, ...]
    low_water_mark: Decimal
    baseline_safe: bool
    amount_safe_to_pay: Decimal
    earliest_date_for_full_payment: date | None
    issues: tuple[str, ...]
    reconciliation_notes: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.issues
