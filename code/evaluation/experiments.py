"""Controlled evaluation-only ablations; expectations never enter the engine."""
import csv
import json
import sys
from dataclasses import replace
from datetime import date
from decimal import Decimal as D
from pathlib import Path
from statistics import median
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from buy_or_wait.load import load_dataset
from buy_or_wait.forecast import forecast,simulate
from buy_or_wait.fx import RateBook
from buy_or_wait.policy import ForecastPolicy,DEFAULT_POLICY
from buy_or_wait.diagnostics import render

ROOT=Path(__file__).resolve().parents[2]


def replay_capacity(result,requested,timing='after_credit'):
    """Independent cent binary search with explicit payment subtraction."""
    rows=result.ledger
    candidate=next(i for i,r in enumerate(rows) if r.source==('candidate' if timing=='before_credit' and any(x.source=='candidate' and x.date==result.start for x in rows) else 'close'))
    def safe(cents):
        balance=result.opening_balance
        for i,r in enumerate(rows):
            balance+=r.inflow-r.outflow
            if i==candidate:balance-=D(cents)/100
            if balance<result.minimum_balance:return False
        return True
    if not safe(0):return D(0)
    lo,hi=0,int(requested*100)
    while lo<hi:
        mid=(lo+hi+1)//2
        if safe(mid):lo=mid
        else:hi=mid-1
    return D(lo)/100


def metrics(records):
    errors=[abs(D(r['safe'])-D(r['expected'])) for r in records]
    normalized=[e/D(r['requested']) for e,r in zip(errors,records)]
    distances=[abs((date.fromisoformat(r['earliest'])-date.fromisoformat(r['expected_date'])).days) for r in records if r['earliest'] and r['expected_date']]
    return dict(exact=sum(e.quantize(D('.01'))==0 for e in errors),mae=str(sum(errors)/len(errors)),
                median_ae=str(median(errors)),normalized_mae=str(sum(normalized)/len(normalized)),
                date_exact=sum(r['earliest']==r['expected_date'] for r in records),
                date_distances=distances,false_present=sum(bool(r['earliest']) and not r['expected_date'] for r in records),
                false_absent=sum(not r['earliest'] and bool(r['expected_date']) for r in records),
                baseline_safe_agreement=sum(r['baseline_safe'] for r in records))


def run():
    data=load_dataset(ROOT/'dataset','sample_requests.csv')
    with (ROOT/'dataset/sample_requests.csv').open(encoding='utf-8-sig',newline='') as f:
        expected={r['request_id']:r for r in csv.DictReader(f)}
    legacy=ForecastPolicy()
    def compute(q,p):
        return forecast(data.profiles[q.user_id],q,data.events_by_user[q.user_id],RateBook(data.rates),
                        data.messages_by_user.get(q.user_id,()),data.images_by_user.get(q.user_id,()),p)
    cases=[q for q in data.selected_requests if compute(q,legacy).complete]
    methods=['p75_daily','mean_daily','trimmed_daily','median_daily','weekly_p75','cadence']
    policies={'phase2':legacy}
    policies.update({m:replace(legacy,variable_estimator=m) for m in methods[1:]})
    policies.update({p:replace(legacy,income_policy=p) for p in ['confirmed_bridge','two_payrolls','freelance']})
    policies.update({'combined_'+m:replace(legacy,income_policy='confirmed_bridge',variable_estimator=m) for m in methods})
    policies.update({'day89':replace(legacy,horizon_days=89),'before_salary':replace(legacy,candidate_timing='before_credit'),
                     'overlap':replace(legacy,pending_overlap=True),'grouping':replace(legacy,robust_grouping=True)})
    policies['selected']=DEFAULT_POLICY
    policies['selected_day89']=replace(DEFAULT_POLICY,horizon_days=89)
    policies['selected_before_salary']=replace(DEFAULT_POLICY,candidate_timing='before_credit')
    all_records={}
    results={}
    for name,p in policies.items():
        records=[]
        for q in cases:
            r=compute(q,p)
            assert replay_capacity(r,q.requested_amount,p.candidate_timing)==r.amount_safe_to_pay,(name,q.request_id)
            totals={}
            for s in r.series:
                if s.description=='*':
                    totals[s.category]={'projection':str(sum(f.amount for f in r.cash_flows if f.source==s.series_id)),
                                         'rate_evidence':s.reason,'amount':str(s.amount),'cadence':s.cadence}
            ex=expected[q.request_id]
            records.append(dict(request=q.request_id,requested=str(q.requested_amount),safe=str(r.amount_safe_to_pay),
                  expected=ex['amount_safe_to_pay'],error=str(r.amount_safe_to_pay-D(ex['amount_safe_to_pay'])),
                  earliest=r.earliest_date_for_full_payment.isoformat() if r.earliest_date_for_full_payment else '',
                  expected_date=ex['earliest_date_for_full_payment'],low=str(r.low_water_mark),baseline_safe=r.baseline_safe,
                  spending=totals))
            results[(name,q.request_id)]=r
        all_records[name]={'metrics':metrics(records),'cases':records}
    # Independent one-factor removal of modeled components; effects need not add
    # because the binding low-water date and requested-amount cap can move.
    decomposition={}
    for model_name,q in [(name,q) for name in ('phase2','selected') for q in cases]:
        r=results[(model_name,q.request_id)]
        active_policy=policies[model_name]
        profile=data.profiles[q.user_id]
        def category(f):
            if f.source.startswith('series:'):return f.source.split('|')[0].split(':',1)[1]
            e=data.events.get(f.source)
            return e.category if e else 'salary'
        masks={c:lambda f,c=c:f.inferred and f.direction=='debit' and category(f)==c for c in ['groceries','transport','dining']}
        masks.update({'all_variable':lambda f:f.inferred and category(f) in legacy.variable_categories and f.direction=='debit',
                      'fixed':lambda f:f.inferred and category(f) not in legacy.variable_categories and f.direction=='debit',
                      'inferred_income':lambda f:f.inferred and f.direction=='credit',
                      'pending':lambda f:f.reason.startswith('pending')})
        impacts={}
        for label,remove in masks.items():
            ledger,low,safe,capacity,earliest=simulate(profile,q,[f for f in r.cash_flows if not remove(f)],active_policy)
            impacts[label]={'safe_delta':str(capacity-r.amount_safe_to_pay),'low_delta':str(low-r.low_water_mark),
                            'earliest':str(earliest) if earliest else ''}
        # FX audit: retained exact rate products and rate provenance, no made-up
        # common exchange rate or meaningless USD/IDR unit substitution.
        impacts['fx']=[{'source':f.source,'original':str(f.original_amount),'rate':str(f.rate),'date':str(f.rate_date),'home':str(f.amount)} for f in r.cash_flows if f.original_currency!=profile.home_currency]
        low_index=min(range(len(r.ledger)),key=lambda n:r.ledger[n].balance)
        binding=r.ledger[low_index]
        components={}
        flow_map={f.source+'@'+str(f.date):f for f in r.cash_flows}
        for row in r.ledger[:low_index+1]:
            f=flow_map.get(row.source+'@'+str(row.date))
            if not f:continue
            group='inferred_income' if f.direction=='credit' and f.inferred else 'confirmed_income' if f.direction=='credit' else 'pending' if f.reason.startswith('pending') else category(f) if category(f) in legacy.variable_categories and f.inferred else 'fixed_and_other'
            components[group]=components.get(group,D(0))+row.inflow-row.outflow
        assert profile.current_available_balance+sum(components.values())==binding.balance
        key=q.request_id if model_name=='phase2' else q.request_id+':selected'
        decomposition[key]={'binding_date':str(binding.date),'opening':str(profile.current_available_balance),
                                     'minimum':str(profile.minimum_balance_to_keep),'binding_components':{k:str(v) for k,v in components.items()},'ablations':impacts}
    snapshot=json.loads((ROOT/'evaluation/phase2_5-before.json').read_text(encoding='utf-8'))
    # Saved Phase 2 numbers are evaluation assertions, never solver inputs.
    for record in all_records['phase2']['cases']:
        previous=snapshot[record['request']]
        assert D(previous['safe'])==D(record['safe'])
        assert ('' if previous['earliest'] in ('None',None) else previous['earliest'])==record['earliest']
        assert D(previous['low'])==D(record['low'])
    payload={'policies':all_records,'decomposition':decomposition}
    (ROOT/'evaluation/phase2_5-details.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    lines=['# Phase 2.5 controlled experiments','',
           'All six structured cases; one-factor changes from Phase 2 unless named combined. Every capacity passes independent cent-level binary-search/replay. '
           'MAE mixes home-currency units and is descriptive only; normalized MAE is the comparable aggregate.', '',
           '| Policy | Amount exact | MAE (mixed units) | Median AE | Normalized MAE | Date exact | False present/absent | Baseline safe |',
           '|---|---:|---:|---:|---:|---:|---|---:|']
    for name,record in all_records.items():
        m=record['metrics']
        lines.append(f"| {name} | {m['exact']}/6 | {D(m['mae']):.2f} | {D(m['median_ae']):.2f} | {D(m['normalized_mae']):.4%} | {m['date_exact']}/6 | {m['false_present']}/{m['false_absent']} | {m['baseline_safe_agreement']}/6 |")
    lines+=['','All expected safe amounts are positive, so baseline safety is derivably true for these six. '
            'Date distances when both dates exist, every per-policy per-case error, low-water mark, variable-category projection, and historical rate are in phase2_5-details.json.',
            '', '## Safe amount sensitivity by case', '',
            '| Case | Before | Expected | No groceries Δ | No transport Δ | No dining Δ | No variable Δ | No fixed Δ | No inferred income Δ | No pending Δ |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for q in cases:
        r=results[('phase2',q.request_id)]
        ab=decomposition[q.request_id]['ablations']
        lines.append('| '+ ' | '.join([q.request_id,str(r.amount_safe_to_pay),expected[q.request_id]['amount_safe_to_pay']]+[ab[x]['safe_delta'] for x in ['groceries','transport','dining','all_variable','fixed','inferred_income','pending']])+' |')
    lines+=['','These are controlled counterfactual sensitivities, not additive allocations of error. The JSON also provides an exact additive opening + inflows − outflows reconciliation at each original binding checkpoint. Capped expected amounts imply bounds, not an exact target low-water mark.', '',
            '## Per-case policy effects', '', '| Policy | '+' | '.join(q.request_id for q in cases)+' |', '|---|'+'---:|'*len(cases)]
    for name,record in all_records.items():
        lines.append('| '+name+' | '+' | '.join(r['safe'] for r in record['cases'])+' |')
    lines+=['','## Selected policy residuals','','| Case | Selected | Expected | Error | Earliest / expected |','|---|---:|---:|---:|---|']
    for r in all_records['selected']['cases']:
        lines.append(f"| {r['request']} | {r['safe']} | {r['expected']} | {r['error']} | {r['earliest'] or 'none'} / {r['expected_date'] or 'none'} |")
    lines+=['','## Selected low-water reconciliation','',
            'All component values below are signed home-currency amounts through the binding event, not 90-day totals. Opening plus components equals the low-water mark exactly.', '',
            '| Case / binding date | Opening | Minimum | Fixed/other | Groceries | Transport | Dining | Pending | Confirmed income | Inferred income | Low |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for q in cases:
        d=decomposition[q.request_id+':selected']
        c=d['binding_components']
        values=[c.get(k,'0') for k in ['fixed_and_other','groceries','transport','dining','pending','confirmed_income','inferred_income']]
        lines.append('| '+' | '.join([q.request_id+' / '+d['binding_date'],d['opening'],d['minimum']]+values+[str(results[('selected',q.request_id)].low_water_mark)])+' |')
    notes=ROOT/'evaluation/phase2_5-findings.md'
    if notes.exists():lines+=['',notes.read_text(encoding='utf-8')]
    (ROOT/'evaluation/phase2_5-experiments.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for q in cases:
        (ROOT/'evaluation/phase2_5-ledgers').mkdir(exist_ok=True)
        (ROOT/'evaluation/phase2_5-ledgers'/f'{q.request_id}-before.txt').write_text(render(results[('phase2',q.request_id)],True),encoding='utf-8')
        (ROOT/'evaluation/phase2_5-ledgers'/f'{q.request_id}-after.txt').write_text(render(results[('selected',q.request_id)],True),encoding='utf-8')
    print('\n'.join(lines[:29]))


if __name__=='__main__':run()
