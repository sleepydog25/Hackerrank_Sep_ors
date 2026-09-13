"""Post-implementation sample metrics, never imported by the prediction path."""
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from buy_or_wait.load import load_dataset
from buy_or_wait.submission import output_row, OUTPUT_COLUMNS


def main():
    root = Path(__file__).resolve().parents[2]
    data = load_dataset(root/'dataset','sample_requests.csv')
    predictions = {q.request_id:output_row(data,q) for q in data.selected_requests}
    with (root/'dataset'/'sample_requests.csv').open(encoding='utf-8-sig',newline='') as stream:
        samples = list(csv.DictReader(stream))
    def canonical_plan(value):
        if value == 'none': return ()
        return tuple((day,Decimal(amount)) for day,amount in (item.split(':') for item in value.split('|')))
    exact = {}
    for field in OUTPUT_COLUMNS[1:-1]:
        transform = Decimal if field == 'amount_safe_to_pay' else canonical_plan if field == 'payment_plan' else str
        exact[field] = sum(transform(predictions[s['request_id']][field]) == transform(s[field]) for s in samples)
    report = {'strategy':'deterministic S0; post-implementation evaluation; no sample tuning',
              'sample_count':len(samples),'exact_matches':exact}
    target = root/'evaluation'/'s0-sample-metrics.json'
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
