"""Independent contract and checkpoint validation; never constructs candidates."""
from datetime import timedelta
from decimal import Decimal


def validate_candidate(candidate, profile, request, baseline, options):
    errors = []
    payments = candidate.payments
    method = candidate.method
    if baseline.request_id != request.request_id or profile.user_id != request.user_id:
        return ('context mismatch',)
    if candidate.currency != profile.home_currency:
        errors.append('currency mismatch')
    # S0 deliberately supports no expense modification. Reject all attempted
    # changes, including otherwise legal ones, rather than validate a scenario
    # against an unchanged baseline or guess recurring-event identities.
    if candidate.changes:
        errors.append('spending changes disabled in deterministic release')
    accepted = 'full_payment' if method == 'wait' else method
    if method not in {'full_payment', 'wait', 'partial_payment', 'installments'}:
        errors.append('unknown method')
    if accepted not in profile.payment_methods_user_will_consider:
        errors.append('method not accepted')
    if not payments:
        return (*errors, 'empty plan')
    if any(not isinstance(p.amount, Decimal) or not p.amount.is_finite() or p.amount < 0 for p in payments):
        return (*errors, 'invalid payment amount')
    dates = [p.date for p in payments]
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        errors.append('dates not strictly chronological')
    if any(d < request.request_date or d > baseline.end or d > request.desired_completion_date for d in dates):
        errors.append('payment outside deadline or forecast')
    total = sum((p.amount for p in payments), Decimal(0))
    if method != 'installments':
        if total != request.requested_amount:
            errors.append('incorrect requested total')
        if candidate.option_id:
            errors.append('unexpected option identifier')
    if method == 'full_payment' and (len(payments) != 1 or dates[0] != request.request_date):
        errors.append('invalid full payment')
    earliest = baseline.earliest_date_for_full_payment
    if method == 'wait' and (len(payments) != 1 or dates[0] != earliest or dates[0] <= request.request_date):
        errors.append('invalid wait date')
    if method == 'partial_payment':
        safe = baseline.amount_safe_to_pay
        if (not request.allows_partial_payment or not Decimal(0) < safe < request.requested_amount
                or len(payments) != 2 or earliest is None
                or dates != [request.request_date, earliest]
                or payments[0].amount != safe or payments[-1].amount != request.requested_amount-safe):
            errors.append('invalid partial contract')
    if method == 'installments':
        matches = [o for o in options if o.payment_option_id == candidate.option_id
                   and o.request_id == request.request_id and o.payment_method == 'installments']
        if len(matches) != 1:
            errors.append('unknown installment option')
        else:
            option = matches[0]
            frequency = option.payment_frequency_days
            if frequency is None or frequency <= 0 or option.number_of_payments < 2:
                errors.append('invalid installment option')
            else:
                if (len(payments) != option.number_of_payments
                        or any(p.amount != option.payment_amount or p.date != option.first_payment_date + timedelta(days=n*frequency)
                               for n, p in enumerate(payments))
                        or total != option.total_payable_amount
                        or total != request.requested_amount + option.financing_fee):
                    errors.append('installment does not exactly match offer')
                # No prior planner interpreted this field. Conservatively count
                # all payment periods, including the first, in 30-day months.
                maximum = profile.max_installment_months
                if maximum is None or option.number_of_payments*frequency > maximum*30:
                    errors.append('installment duration exceeds preference')
    if errors:
        return tuple(errors)
    # Unknown cash amounts/rates cannot certify a positive payment. The baseline
    # capacity fields remain the frozen calculation; no missing value is filled.
    if any('missing amount' in issue or 'missing FX' in issue for issue in baseline.issues):
        return ('unresolved cash amount or exchange rate',)
    # Replay cumulative payments against EVERY baseline checkpoint. Payments
    # occur after daily close, exactly as in the frozen default timing policy.
    paid = Decimal(0)
    due = {p.date: p.amount for p in payments}
    seen = set()
    for row in baseline.ledger:
        if row.balance-paid < profile.minimum_balance_to_keep:
            return ('minimum balance breached before or after a future cash event',)
        if row.source == 'close' and row.date in due:
            paid += due[row.date]
            seen.add(row.date)
            if row.balance-paid < profile.minimum_balance_to_keep:
                return ('minimum balance breached by payment',)
    if seen != set(dates) or paid != total:
        return ('payment not covered by ledger',)
    return ()
