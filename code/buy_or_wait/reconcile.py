"""Reconcile cash states without replaying the opening snapshot."""
from dataclasses import dataclass
from datetime import date
from .models import FinancialEvent
from .policy import NONRECURRING_WORDS


def salary_event(e: FinancialEvent) -> bool:
    text = e.description.casefold()
    return (e.direction == 'credit' and e.event_type == 'income' and e.category == 'salary'
            and any(w in text for w in ('salary', 'payroll'))
            and not any(w in text for w in NONRECURRING_WORDS))


@dataclass(frozen=True)
class Reconciliation:
    history: tuple[FinancialEvent, ...]
    obligations: tuple[FinancialEvent, ...]
    notes: tuple[str, ...]


def reconcile(events: tuple[FinancialEvent, ...], start: date) -> Reconciliation:
    if len({e.event_id for e in events}) != len(events):
        raise ValueError('duplicate event IDs in forecast context')
    events = tuple(sorted(events, key=lambda e: (e.event_date, e.event_id)))
    history, future, notes = [], [], []
    # Exact duplicate IDs are a loader error. A link alone never removes cash.
    by_id = {e.event_id: e for e in events}
    superseded = set()
    for e in events:
        parent = by_id.get(e.linked_event_id)
        # Explicit settled replacement of an authorization. Do not collapse a
        # disputed second charge, reimbursement, sale, or unrelated linked debit.
        if (parent and parent.status == 'pending' and e.status == 'settled'
                and parent.direction == e.direction == 'debit'
                and 'authorization' in parent.description.casefold()
                and e.amount == parent.amount and e.currency == parent.currency):
            superseded.add(parent.event_id)
    for e in events:
        if e.event_id in superseded:
            notes.append(f'{e.event_id}: authorization superseded by linked settled debit')
        elif e.status in {'cancelled', 'failed', 'unrealized'} or e.direction == 'non_cash':
            notes.append(f'{e.event_id}: excluded {e.status}; no cash from this record')
        elif e.status == 'settled' and e.settlement_date <= start:
            history.append(e)
        elif e.status == 'pending' and e.direction == 'credit':
            notes.append(f'{e.event_id}: pending credit excluded, settlement date is not confirmation')
        elif e.direction == 'debit':
            future.append(e)
        elif e.status == 'settled' or (e.status == 'scheduled' and salary_event(e)):
            future.append(e)
        else:
            notes.append(f'{e.event_id}: unconfirmed non-salary credit excluded')
    return Reconciliation(tuple(history), tuple(future), tuple(notes))
