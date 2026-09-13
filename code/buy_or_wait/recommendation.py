"""Deterministic candidate construction and ranking over the frozen forecast."""
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from .models import Payment


@dataclass(frozen=True)
class Candidate:
    method: str
    payments: tuple[Payment, ...]
    currency: str
    option_id: str = ''
    changes: tuple[str, ...] = ()


def candidates(profile, request, baseline, options):
    """Construct possibilities; independent validation decides eligibility."""
    currency = profile.home_currency
    yield Candidate('full_payment', (Payment(request.request_date, request.requested_amount),), currency)
    earliest = baseline.earliest_date_for_full_payment
    safe = baseline.amount_safe_to_pay
    if earliest is not None and earliest > request.request_date:
        yield Candidate('wait', (Payment(earliest, request.requested_amount),), currency)
        if Decimal(0) < safe < request.requested_amount:
            yield Candidate('partial_payment', (Payment(request.request_date, safe),
                            Payment(earliest, request.requested_amount-safe)), currency)
    for option in options:
        if option.payment_method != 'installments':
            continue
        payments = tuple(Payment(option.first_payment_date + timedelta(days=n*option.payment_frequency_days),
                                 option.payment_amount) for n in range(option.number_of_payments))
        yield Candidate('installments', payments, currency, option.payment_option_id)


def rank(candidate, request):
    return (candidate.payments[-1].date > request.desired_completion_date,
            bool(candidate.changes), sum(p.amount for p in candidate.payments),
            candidate.payments[0].date, len(candidate.payments), candidate.option_id)


def select_candidate(profile, request, baseline, options):
    from .plan_validation import validate_candidate
    valid = [c for c in candidates(profile, request, baseline, options)
             if not validate_candidate(c, profile, request, baseline, options)]
    return min(valid, key=lambda c: rank(c, request)) if valid else None


def status(candidate):
    if candidate is None:
        return 'not_affordable'
    if candidate.changes or candidate.method in {'partial_payment', 'installments'}:
        return 'affordable_with_plan'
    return 'affordable_later' if candidate.method == 'wait' else 'affordable_now'
