"""Normalized evidence output; consumed by the financial engine, never a balance."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from .evidence import EvidenceDecision, EvidenceSource, Scope
from .models import FinancialEvent


class SeriesAction(StrEnum):
    AMOUNT = 'AMOUNT'
    SKIP_OCCURRENCE = 'SKIP_OCCURRENCE'
    END = 'END'


@dataclass(frozen=True)
class SeriesAmendment:
    target: FinancialEvent
    action: SeriesAction
    effective_date: date
    end_date: date | None
    amount: Decimal | None
    fact_id: str
    source_id: str


@dataclass(frozen=True)
class FinancialAmendment:
    fact_id: str
    source: EvidenceSource
    original_label: str
    before: FinancialEvent | None
    after: FinancialEvent | None


@dataclass(frozen=True)
class NormalizedEvidenceState:
    original_events: tuple[FinancialEvent, ...]
    events: tuple[FinancialEvent, ...]
    decisions: tuple[EvidenceDecision, ...]
    amendments: tuple[FinancialAmendment, ...]
    series_amendments: tuple[SeriesAmendment, ...]
    confirmed_credit_ids: frozenset[str]
