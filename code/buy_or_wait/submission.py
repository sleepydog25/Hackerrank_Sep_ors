"""CSV release writer and read-back validator. No extraction or network calls."""
import csv
from decimal import Decimal
from pathlib import Path
from .evidence_integration import forecast_dataset_evidence
from .load import parse
from .models import Payment
from .recommendation import Candidate, select_candidate, status
from .plan_validation import validate_candidate
from datetime import date

OUTPUT_COLUMNS = ('request_id', 'amount_safe_to_pay', 'affordability_status',
                  'recommended_payment_method', 'payment_plan', 'earliest_date_for_full_payment',
                  'spending_changes_needed', 'decision_explanation')
STATUSES = {'affordable_now', 'affordable_with_plan', 'affordable_later', 'not_affordable'}
METHODS = {'full_payment', 'partial_payment', 'installments', 'wait', 'not_recommended'}


def money(value):
    return format(value, 'f')


def baseline_for(data, request):
    # Use frozen Phase 3A normalization, with no unvalidated extraction batches.
    return forecast_dataset_evidence(data, request, ()).forecast


def output_row(data, request, baseline=None):
    baseline = baseline if baseline is not None else baseline_for(data, request)
    profile = data.profiles[request.user_id]
    candidate = select_candidate(profile, request, baseline, data.options_by_request[request.request_id])
    safe = baseline.amount_safe_to_pay
    if not safe.is_finite() or not Decimal(0) <= safe <= request.requested_amount:
        raise ValueError('baseline safe amount out of bounds')
    method = candidate.method if candidate else 'not_recommended'
    if candidate:
        explanation = (f'{profile.home_currency} {money(request.requested_amount)} via {method}; '
                       f'payments finish {candidate.payments[-1].date}; '
                       f'minimum {money(profile.minimum_balance_to_keep)} protected over 90 days.')
    else:
        explanation = (f'{profile.home_currency} {money(request.requested_amount)}: no eligible plan certified '
                       f'by {request.desired_completion_date} while protecting minimum '
                       f'{money(profile.minimum_balance_to_keep)} over 90 days.')
    if baseline.issues:
        explanation += ' Unresolved evidence excluded; structured-data forecast only.'
    return dict(zip(OUTPUT_COLUMNS, (request.request_id, money(safe), status(candidate), method,
                '|'.join(f'{p.date}:{money(p.amount)}' for p in candidate.payments) if candidate else 'none',
                str(baseline.earliest_date_for_full_payment or ''), 'none', explanation)))


def write_output(data, path):
    rows = [output_row(data, q) for q in data.selected_requests]
    with Path(path).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    return rows


def validate_output(data, path, expected_count=250):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != OUTPUT_COLUMNS:
            raise ValueError('invalid output schema/order')
        rows = list(reader)
    requests = {q.request_id: q for q in data.selected_requests}
    ids = [r['request_id'] for r in rows]
    if (len(rows) != expected_count or len(ids) != len(set(ids)) or set(ids) != set(requests)):
        raise ValueError('invalid request coverage/count')
    for row in rows:
        if set(row) != set(OUTPUT_COLUMNS) or any(v is None for v in row.values()):
            raise ValueError('malformed CSV row')
        q = requests[row['request_id']]
        profile = data.profiles[q.user_id]
        baseline = baseline_for(data, q)
        safe = parse(row['amount_safe_to_pay'], Decimal)
        if not Decimal(0) <= safe <= q.requested_amount or safe != baseline.amount_safe_to_pay:
            raise ValueError('safe amount inconsistent with baseline')
        earliest = parse(row['earliest_date_for_full_payment'], date) if row['earliest_date_for_full_payment'] else None
        if earliest != baseline.earliest_date_for_full_payment:
            raise ValueError('earliest date inconsistent with baseline')
        if row['affordability_status'] not in STATUSES or row['recommended_payment_method'] not in METHODS:
            raise ValueError('invalid enum')
        if row['spending_changes_needed'] != 'none':
            raise ValueError('spending changes disabled')
        if not row['decision_explanation'].strip():
            raise ValueError('empty explanation')
        method = row['recommended_payment_method']
        options = data.options_by_request[q.request_id]
        if method == 'not_recommended':
            if row['payment_plan'] != 'none' or row['affordability_status'] != 'not_affordable':
                raise ValueError('invalid fallback')
            if select_candidate(profile, q, baseline, options) is not None:
                raise ValueError('fallback hides valid candidate')
            continue
        payments = []
        for entry in row['payment_plan'].split('|'):
            day, amount = entry.split(':')
            payments.append(Payment(parse(day, date), parse(amount, Decimal)))
        option_ids = [o.payment_option_id for o in options if o.payment_method == 'installments'] if method == 'installments' else ['']
        valid = [Candidate(method, tuple(payments), profile.home_currency, oid) for oid in option_ids
                 if not validate_candidate(Candidate(method, tuple(payments), profile.home_currency, oid),
                                           profile, q, baseline, options)]
        if not valid or row['affordability_status'] != status(valid[0]):
            raise ValueError(f'{q.request_id}: invalid payment plan/status')
        if row['affordability_status'] == 'affordable_now' and earliest != q.request_date:
            raise ValueError('affordable_now date mismatch')
        best = select_candidate(profile, q, baseline, options)
        if best not in valid:
            raise ValueError('plan violates deterministic ranking')
    return rows
