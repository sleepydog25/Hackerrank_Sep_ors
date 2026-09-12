"""Read-only dataset inventory. Does not generate financial predictions."""
import csv
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = {p.stem: list(csv.DictReader(p.open(encoding='utf-8-sig', newline='')))
          for p in sorted((ROOT / 'dataset').glob('*.csv'))}
profiles = {r['user_id']: r for r in TABLES['financial_profiles']}
events = {r['event_id']: r for r in TABLES['financial_events']}
requests = {r['request_id']: r for t in ('requests', 'sample_requests') for r in TABLES[t]}
report = {'tables': {}, 'integrity_errors': [], 'samples': []}
for name, rows in TABLES.items():
    report['tables'][name] = {'rows': len(rows), 'columns': list(rows[0]),
        'nulls': {c: sum(r[c] == '' for r in rows) for c in rows[0] if any(r[c] == '' for r in rows)}}
    key = {'exchange_rates': 'rate_date', 'financial_profiles': 'user_id', 'financial_events': 'event_id',
           'messages': 'message_id', 'images': 'image_id', 'request_payment_options': 'payment_option_id'}.get(name, 'request_id')
    keys = [(r['rate_date'], r['from_currency'], r['to_currency']) if name == 'exchange_rates' else r[key] for r in rows]
    if len(keys) != len(set(keys)):
        report['integrity_errors'].append(f'{name}: duplicate keys')
    for r in rows:
        if r.get('user_id') and r['user_id'] not in profiles:
            report['integrity_errors'].append(f'{name}: unknown user')
        if r.get('request_id'):
            q = requests.get(r['request_id'])
            if not q or (r.get('user_id') and q['user_id'] != r['user_id']):
                report['integrity_errors'].append(f'{name}: invalid request join')
        for c in ('related_event_id', 'linked_event_id'):
            if r.get(c):
                e = events.get(r[c])
                if not e or e['user_id'] != r['user_id']:
                    report['integrity_errors'].append(f'{name}: invalid event join')
rates = {(r['rate_date'], r['from_currency'], r['to_currency']) for r in TABLES['exchange_rates']}
foreign = [e for e in events.values() if e['currency'] != profiles[e['user_id']]['home_currency']]
report['foreign'] = {'events': len(foreign), 'users': len({e['user_id'] for e in foreign}),
    'pairs': dict(Counter(e['currency']+'->'+profiles[e['user_id']]['home_currency'] for e in foreign)),
    'missing_rates': [e['event_id'] for e in foreign if e['settlement_date'] and (e['settlement_date'], e['currency'], profiles[e['user_id']]['home_currency']) not in rates]}
report['images_missing'] = [r['image_id'] for r in TABLES['images'] if not (ROOT/'dataset/media/images'/f"{r['image_id']}.png").is_file()]
report['blank_amounts_without_image'] = [e['event_id'] for e in events.values() if not e['amount'] and not any(i['related_event_id'] == e['event_id'] for i in TABLES['images'])]
report['option_counts'] = dict(Counter(Counter(r['request_id'] for r in TABLES['request_payment_options']).values()))
report['option_money_errors'] = [r['payment_option_id'] for r in TABLES['request_payment_options'] if Decimal(r['payment_amount'])*int(r['number_of_payments']) != Decimal(r['total_payable_amount']) or Decimal(r['total_payable_amount']) != Decimal(requests[r['request_id']]['requested_amount'])+Decimal(r['financing_fee'])]
report['dates'] = {t: {c: [min(r[c] for r in TABLES[t] if r[c]), max(r[c] for r in TABLES[t] if r[c])] for c in cols} for t, cols in {'requests':['request_date','desired_completion_date'], 'sample_requests':['request_date'], 'financial_events':['event_date','settlement_date'], 'exchange_rates':['rate_date']}.items()}
for q in TABLES['sample_requests']:
    uid = q['user_id']
    es = [e for e in events.values() if e['user_id'] == uid]
    ms = [m for m in TABLES['messages'] if m['user_id'] == uid and m['request_id'] in ('', q['request_id'])]
    ims = [i for i in TABLES['images'] if i['user_id'] == uid]
    report['samples'].append({'request':q['request_id'], 'status':q['affordability_status'], 'method':q['recommended_payment_method'],
      'messages':[m['message_id'] for m in ms], 'images':[i['image_id'] for i in ims], 'fx':any(e in foreign for e in es),
      'recurring_expense_history':any(n >= 3 for n in Counter((e['category'], e['description']) for e in es if e['direction']=='debit' and e['status']=='settled').values()),
      'changes':q['spending_changes_needed']})
report['sample_counts'] = {c: dict(Counter(r[c] for r in TABLES['sample_requests'])) for c in ['affordability_status','recommended_payment_method']}
report['sample_evidence_counts'] = dict(Counter('both' if r['messages'] and r['images'] else 'messages_only' if r['messages'] else 'images_only' if r['images'] else 'neither' for r in report['samples']))
report['event_values'] = {c: dict(Counter(e[c] for e in events.values())) for c in ['event_type','category','direction','status','flexibility','currency']}
report['request_user_counts'] = {t: len({r['user_id'] for r in TABLES[t]}) for t in ['requests','sample_requests']}
report['sample_evaluation_overlap'] = sorted({r['request_id'] for r in TABLES['requests']} & {r['request_id'] for r in TABLES['sample_requests']})
report['template_matches_requests'] = [r['request_id'] for r in TABLES['output']] == [r['request_id'] for r in TABLES['requests']]
if '--save' in sys.argv:
    (Path(__file__).resolve().parent / 'inventory.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
else:
    print(json.dumps(report, indent=2))
