"""Compare baseline fields only; expected labels are confined to evaluation."""
import argparse
import csv
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from buy_or_wait.load import load_dataset
from buy_or_wait.forecast import forecast_request
from buy_or_wait.diagnostics import summary, render


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument('--dataset', type=Path, default=root/'dataset')
    parser.add_argument('--save', action='store_true', help='write phase2-summary.md and ignored full ledgers')
    args = parser.parse_args()
    data = load_dataset(args.dataset, 'sample_requests.csv')
    with (args.dataset/'sample_requests.csv').open(encoding='utf-8-sig', newline='') as stream:
        expected = {r['request_id']: (Decimal(r['amount_safe_to_pay']), r['earliest_date_for_full_payment']) for r in csv.DictReader(stream)}
    lines = ['# Phase 2 sample baseline diagnostics', '',
             'No recommendation selection, evidence extraction, or final output.csv. '
             'Only complete structured cases are scored. Provisional numbers are not validated capacity.', '',
             '| Request | Evidence | Safe today | Expected | Earliest full | Expected | Likely mismatch cause |',
             '|---|---|---:|---:|---|---|---|']
    counts = Counter()
    details = []
    ledger_dir = root/'evaluation'/'phase2-ledgers'
    if args.save:
        ledger_dir.mkdir(parents=True, exist_ok=True)
    for q in data.selected_requests:
        r = forecast_request(data,q)
        amount, day = expected[q.request_id]
        actual_day = r.earliest_date_for_full_payment.isoformat() if r.earliest_date_for_full_payment else ''
        amount_match = r.amount_safe_to_pay == amount
        date_match = actual_day == day
        counts['total'] += 1
        if r.complete:
            counts['complete'] += 1
            counts['amount_matches'] += amount_match
            counts['date_matches'] += date_match
            counts['both_match'] += amount_match and date_match
            cause = 'match' if amount_match and date_match else 'recurrence / variable-spending estimator; boundary timing uncalibrated'
        else:
            counts['unresolved'] += 1
            cause = 'FX' if any('missing FX' in x for x in r.issues) else 'unresolved evidence'
        lines.append(f'| {q.request_id} | {"complete" if r.complete else "unresolved"} | '
                     f'{r.amount_safe_to_pay} | {amount} | {actual_day or "—"} | {day or "—"} | {cause} |')
        details.extend(['', '```text', summary(r),
                        'Series: '+ '; '.join(f'{s.category} {s.amount} {s.currency}/{s.cadence}' for s in r.series),
                        '```'])
        if args.save:
            # IDs are validated dataset identifiers, but filenames still need a path guard.
            name = ''.join(c for c in q.request_id if c.isalnum() or c in '_-')
            (ledger_dir/f'{name}.txt').write_text(render(r,full=True),encoding='utf-8')
    lines.extend(['', f'Counts: {dict(counts)}', '',
                  'Likely-cause labels are hypotheses, not isolated causal diagnoses. '
                  'No policy thresholds were tuned to sample labels. Full traces include the exact low-water checkpoint, '
                  'series, explicit income, and reservations. Resolve evidence before attributing provisional mismatches.'])
    lines.extend(details)
    report='\n'.join(lines)+'\n'
    if args.save:
        (root/'evaluation'/'phase2-summary.md').write_text(report,encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
