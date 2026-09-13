"""Generate and validate deterministic output.csv; optionally inspect a ledger."""
import argparse
from pathlib import Path
from buy_or_wait.load import load_dataset
from buy_or_wait.forecast import forecast_request
from buy_or_wait.diagnostics import render
from buy_or_wait.submission import write_output, validate_output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path(__file__).resolve().parents[1]/'dataset')
    parser.add_argument('--requests', choices=['requests.csv', 'sample_requests.csv'], default='requests.csv')
    parser.add_argument('--request', help='request ID for diagnostic ledger')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'output.csv')
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--full', action='store_true', help='include quiet daily closes')
    args = parser.parse_args()
    data = load_dataset(args.dataset, args.requests)
    if args.request is None:
        if not args.validate_only:
            write_output(data, args.output)
        rows = validate_output(data, args.output, 250 if args.requests == 'requests.csv' else len(data.selected_requests))
        print(f'Validated {len(rows)} deterministic predictions: {args.output}')
        return
    selected = {q.request_id: q for q in data.selected_requests}
    if args.request not in selected:
        parser.error('request ID not in selected request file')
    print(render(forecast_request(data, selected[args.request]), args.full))


if __name__ == '__main__':
    main()
