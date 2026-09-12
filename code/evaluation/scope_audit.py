"""Dataset-wide profile/event semantics inventory; no predictions or label input."""
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
from statistics import median
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from buy_or_wait.load import load_dataset
from buy_or_wait.policy import DEFAULT_POLICY

ROOT=Path(__file__).resolve().parents[2]


def inventory(data, users):
    profiles=[p for p in data.profiles.values() if p.user_id in users]
    events=[e for e in data.events.values() if e.user_id in users and e.direction=='debit']
    fields={'protect':'expense_categories_to_protect','reduce':'expense_categories_user_is_willing_to_reduce',
            'stop':'expense_categories_user_is_willing_to_stop','priorities':'financial_priorities'}
    distributions={name:dict(sorted(Counter(c for p in profiles for c in getattr(p,field)).items())) for name,field in fields.items()}
    overlaps={}
    for left,right in [('protect','reduce'),('protect','stop'),('reduce','stop')]:
        pairs=[getattr(p,fields[left]) & getattr(p,fields[right]) for p in profiles]
        overlaps[left+'_'+right]={'profiles':sum(bool(x) for x in pairs),'categories':dict(sorted(Counter(c for x in pairs for c in x).items()))}
    categories={}
    for category in sorted({e.category for e in events}):
        rows=[e for e in events if e.category==category]
        categories[category]={'debit_events':len(rows),'variable_estimator':category in DEFAULT_POLICY.variable_categories,
                             'flexibility':dict(sorted(Counter(e.flexibility for e in rows).items())),
                             'statuses':dict(sorted(Counter(e.status for e in rows).items()))}
    minimums={}
    for currency in sorted({e.currency for e in events}):
        rows=[e for e in events if e.currency==currency]
        amounts=[e.minimum_allowed_amount for e in rows if e.minimum_allowed_amount is not None]
        ratios=[e.minimum_allowed_amount/e.amount for e in rows if e.minimum_allowed_amount is not None and e.amount]
        minimums[currency]={'rows':len(rows),'missing':sum(e.minimum_allowed_amount is None for e in rows),
                           'zero':sum(a==0 for a in amounts),'positive':sum(a>0 for a in amounts),
                           'min':str(min(amounts)) if amounts else None,'median':str(median(amounts)) if amounts else None,
                           'max':str(max(amounts)) if amounts else None,
                           'median_fraction_of_event':str(median(ratios)) if ratios else None}
    return {'users':len(profiles),'debit_events':len(events),'profile_categories':distributions,
            'overlaps':overlaps,'categories':categories,'minimum_allowed_amount_by_currency':minimums,
            'minimum_by_flexibility':{f:dict(Counter('missing' if e.minimum_allowed_amount is None else 'zero' if e.minimum_allowed_amount==0 else 'positive' for e in events if e.flexibility==f)) for f in sorted({e.flexibility for e in events})}}


def run():
    data=load_dataset(ROOT/'dataset','requests.csv')
    payload={'all_profiles':inventory(data,set(data.profiles)),
             'evaluation_users':inventory(data,{q.user_id for q in data.selected_requests})}
    (ROOT/'evaluation/phase2_6-scope.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    lines=['# Dataset-wide expense-scope inventory','',
           'Counts are users or debit event rows, not currency totals. Both all supplied profiles and the evaluation-user subset are in the JSON. No image/message extraction or solved labels are used.','']
    for cohort,report in payload.items():
        lines += [f'## {cohort}: {report["users"]} users, {report["debit_events"]} debit events','',
                  '| Category | Protected users | Reduce users | Stop users | Debit events | Variable estimator | Event flexibility counts |',
                  '|---|---:|---:|---:|---:|---|---|']
        all_categories=set(report['categories'])|set().union(*(set(v) for k,v in report['profile_categories'].items() if k!='priorities'))
        for c in sorted(all_categories):
            event=report['categories'].get(c,{})
            values=[str(report['profile_categories'][k].get(c,0)) for k in ('protect','reduce','stop')]
            lines.append('| '+' | '.join([c]+values+[str(event.get('debit_events',0)),str(event.get('variable_estimator',False)),str(event.get('flexibility',{}))])+' |')
        lines += ['', 'Profile overlaps: '+str(report['overlaps']), '',
                  '| Currency | Min field missing | Zero | Positive | Observed min / median / max | Median minimum/event ratio |',
                  '|---|---:|---:|---:|---|---:|']
        for c,r in report['minimum_allowed_amount_by_currency'].items():
            lines.append(f"| {c} | {r['missing']} | {r['zero']} | {r['positive']} | {r['min']} / {r['median']} / {r['max']} | {r['median_fraction_of_event']} |")
        lines += ['', 'Minimum-field presence by flexibility: '+str(report['minimum_by_flexibility']),'']
    lines+=['## Field-to-engine mapping','',
            '- `category`, event type, amount, dates, direction, status and lifecycle links drive recurrence/reconciliation.',
            '- Profile protection, willingness-to-reduce/stop, priorities, event flexibility and minimum_allowed_amount are loaded and retained, but do not automatically lower baseline reserves.',
            '- This is intentional for optional changes: willingness is permission to consider a plan, not proof spending already stopped. Minimum amounts are potential reduction bounds, not replacement baseline amounts.',
            '- Protection must veto future optional reductions even when willingness sets overlap. No such plan layer exists yet.',
            '- Variable category membership is a modeling policy, not a claim every event is protected. Fixed recurring discretionary services also remain baseline expected spending.',
            '- No scope change is independently justified by the contract. Adopted scope-rule impact is 0/250 amounts, dates and safety classifications; actual before/after replay is in the Phase 2.6 results.']
    (ROOT/'evaluation/phase2_6-scope.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for name,r in payload.items():
        print(name,r['users'],'users;',r['debit_events'],'debits; overlaps',r['overlaps'])


if __name__=='__main__':run()
