"""Read-only presentation of model assumptions and ledger checkpoints."""
from .models import ForecastResult


def summary(result: ForecastResult) -> str:
    explicit_income = sum(f.amount for f in result.cash_flows if f.direction == 'credit' and not f.inferred)
    pending = sum(f.amount for f in result.cash_flows if f.reason.startswith('pending'))
    minimum_row = min(result.ledger, key=lambda r: r.balance)
    return (f'{result.request_id}: {"COMPLETE STRUCTURED BASELINE" if result.complete else "PROVISIONAL / UNRESOLVED EVIDENCE"}\n'
            f'Horizon: {result.start} through {result.end} inclusive\n'
            f'Opening={result.opening_balance}; required minimum={result.minimum_balance}; '
            f'low-water={result.low_water_mark} on {minimum_row.date} ({minimum_row.source})\n'
            f'Pending reserved={pending}; explicit future income={explicit_income}; baseline safe={result.baseline_safe}\n'
            f'amount_safe_to_pay={result.amount_safe_to_pay}; earliest_date_for_full_payment={result.earliest_date_for_full_payment}\n'
            + '\n'.join(f'UNRESOLVED: {x}' for x in result.issues))


def render(result: ForecastResult, full=False) -> str:
    lines = [summary(result), '\nInferred recurring series:']
    for s in result.series:
        lines.append(f'{s.series_id}: {s.amount} {s.currency} {s.cadence}; anchor={s.anchor}; '
                     f'{s.reason}; evidence={",".join(s.event_ids)}')
    lines.extend(['\nReconciliation:', *result.reconciliation_notes,
                  '\ndate | source | inflow | outflow | balance | minimum | provenance'])
    for row in result.ledger:
        if full or row.source != 'close':
            lines.append(f'{row.date} | {row.source} | {row.inflow} | {row.outflow} | '
                         f'{row.balance} | {row.minimum} | {row.provenance}')
    return '\n'.join(lines)+'\n'
