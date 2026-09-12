"""Reproduce Phase 2.6 against immutable Phase 2.5 code in isolated processes."""
import csv
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from decimal import Decimal as D
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[2]
BASELINE_COMMIT='226adac'  # Evaluation provenance, never imported by production.


def worker(package):
    sys.path.insert(0,str(package))
    from buy_or_wait.load import load_dataset
    from buy_or_wait.forecast import forecast_request
    output={}
    for filename in ('sample_requests.csv','requests.csv'):
        data=load_dataset(ROOT/'dataset',filename)
        records=[]
        for q in data.selected_requests:
            r=forecast_request(data,q)
            binding=min(r.ledger,key=lambda row:row.balance)
            record=dict(request=q.request_id,requested=str(q.requested_amount),home_currency=data.profiles[q.user_id].home_currency,
                        safe=str(r.amount_safe_to_pay),earliest=str(r.earliest_date_for_full_payment) if r.earliest_date_for_full_payment else '',
                        low=str(r.low_water_mark),binding_date=str(binding.date),baseline_safe=r.baseline_safe,
                        complete=r.complete,issues=list(r.issues),opening=str(r.opening_balance),minimum=str(r.minimum_balance))
            if filename=='sample_requests.csv' and r.complete:
                # Independent event replay at every candidate, no expected date used.
                capacities={}
                for n,row in enumerate(r.ledger):
                    if row.source!='close':continue
                    balance=r.opening_balance
                    low=balance
                    for k,x in enumerate(r.ledger):
                        balance+=x.inflow-x.outflow
                        if k==n:balance-=q.requested_amount
                        low=min(low,balance)
                    capacities[str(row.date)]={'full_payment_minimum':str(low),'safe':low>=r.minimum_balance}
                first=next((day for day,x in capacities.items() if x['safe']), '')
                assert first==record['earliest'],(q.request_id,first,record['earliest'])
                record['full_payment_replay_by_date']=capacities
            records.append(record)
        output[filename]=records
    return output


def snapshot(package):
    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(package)],
                          cwd=ROOT,capture_output=True,text=True,check=True)
    return json.loads(result.stdout)


def run():
    # Only the participant's own accepted core is extracted, never organizer files.
    archive=subprocess.check_output(['git','archive','--format=zip',BASELINE_COMMIT,'code/buy_or_wait'],cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix='forecast-semantics-') as temporary:
        with zipfile.ZipFile(io.BytesIO(archive)) as source:
            source.extractall(temporary)
        before=snapshot(Path(temporary)/'code')
    after=snapshot(ROOT/'code')
    with (ROOT/'dataset/sample_requests.csv').open(encoding='utf-8-sig',newline='') as f:
        labels={row['request_id']:row for row in csv.DictReader(f)}
    samples=[]
    for r in after['sample_requests.csv']:
        if not r['complete']:continue
        expected=labels[r['request']]
        error=D(r['safe'])-D(expected['amount_safe_to_pay'])
        samples.append({**r,'expected':expected['amount_safe_to_pay'],'expected_date':expected['earliest_date_for_full_payment'],
                        'error':str(error),'absolute_error':str(abs(error)),'normalized_error':str(abs(error)/D(r['requested']))})
    from experiments import metrics
    historical=json.loads((ROOT/'evaluation/phase2_5-details.json').read_text(encoding='utf-8'))
    old_samples=[{**r,'expected':labels[r['request']]['amount_safe_to_pay'],
                  'expected_date':labels[r['request']]['earliest_date_for_full_payment']}
                 for r in before['sample_requests.csv'] if r['complete']]
    assert metrics(old_samples)==historical['policies']['selected']['metrics']
    combined_metrics={'phase2':historical['policies']['phase2']['metrics'],
                      'phase2_5':metrics(old_samples),'phase2_6':metrics(samples)}
    earlier={r['request']:r for r in before['requests.csv']}
    changes=[]
    for r in after['requests.csv']:
        old=earlier[r['request']]
        changes.append({'request':r['request'],'safe_before':old['safe'],'safe_after':r['safe'],
                        'safe_delta':str(D(r['safe'])-D(old['safe'])),
                        'date_before':old['earliest'],'date_after':r['earliest'],
                        'baseline_safe_before':old['baseline_safe'],'baseline_safe_after':r['baseline_safe'],
                        'complete':r['complete']})
    deltas=[D(r['safe_delta']) for r in changes]
    impact=dict(requests=len(changes),safe_changed=sum(d!=0 for d in deltas),increased=sum(d>0 for d in deltas),decreased=sum(d<0 for d in deltas),
                median_change=str(median(deltas)),median_changed_only=str(median([d for d in deltas if d])) if any(deltas) else None,
                earliest_changed=sum(r['date_before']!=r['date_after'] for r in changes),
                baseline_safety_changed=sum(r['baseline_safe_before']!=r['baseline_safe_after'] for r in changes),
                complete=sum(r['complete'] for r in changes))
    payload={'baseline_commit':BASELINE_COMMIT,'metrics':combined_metrics,'sample_cases':samples,
             'evaluation_impact':impact,'evaluation_requests':changes,
             'expense_scope_change':'none justified; no automatic reductions or category removal'}
    (ROOT/'evaluation/phase2_6-details.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    lines=['# Phase 2.6 results','',
           'Production semantics retained after contract audit. Old core is executed from immutable Git commit `226adac` in an isolated temporary directory; current core executes in a separate process. No expected sample fields enter either core. All temporary extracted files are removed automatically.', '',
           '| Phase | Amount exact | MAE (mixed currency) | Median AE | Normalized MAE | Date exact | False present/absent | Baseline safety agreement |',
           '|---|---:|---:|---:|---:|---:|---|---:|']
    for name,m in combined_metrics.items():
        lines.append(f"| {name} | {m['exact']}/6 | {D(m['mae']):.2f} | {D(m['median_ae']):.2f} | {D(m['normalized_mae']):.4%} | {m['date_exact']}/6 | {m['false_present']}/{m['false_absent']} | {m['baseline_safe_agreement']}/6 |")
    lines += ['', 'Both present predicted dates agree exactly (zero day-distance); two expected dates remain absent. Safety agreement is derivable here because all six expected safe amounts are positive.', '',
              '| Case | Predicted | Expected | Absolute error | Normalized error | Earliest / expected | Binding date | Low | Baseline safe |',
              '|---|---:|---:|---:|---:|---|---|---:|---|']
    for r in samples:
        lines.append(f"| {r['request']} | {r['safe']} | {r['expected']} | {r['absolute_error']} | {D(r['normalized_error']):.4%} | {r['earliest'] or 'none'} / {r['expected_date'] or 'none'} | {r['binding_date']} | {r['low']} | {r['baseline_safe']} |")
    lines += ['', '## Dataset-wide impact', '',
              f"Executed {impact['requests']} evaluation requests without exceptions. Amount changes: {impact['safe_changed']} ({impact['increased']} increases, {impact['decreased']} decreases); median change {impact['median_change']}. Earliest-date changes: {impact['earliest_changed']}; baseline safety changes: {impact['baseline_safety_changed']}. {impact['complete']} have complete structured evidence; all others remain provisional, not actionable predictions.", '',
              'No expense-scope change was adopted, so no category contributes an adopted-rule delta. Field distributions and ignored-for-baseline permission/minimum fields are in phase2_6-scope.md/json. All 250 before/after comparisons are retained in the details JSON.', '',
              '## Preserved causal residuals', '',
              '- 01: supported payroll bridge already resolves the amount and date.',
              '- 05: binding low 7,791.50 against minimum 13,100. Expected 737 requires 6,045.50 additional capacity. Fixed expenses 26,250.27 plus groceries 9,647.82 and transport 2,785.51 cannot be cut automatically based on scope semantics.',
              '- 09: day-90 rent 211.20 plus variable reserve 7.34 causes the endpoint breach. Day89 alternative matches with mean spending; keep the safer production endpoint because wording remains ambiguous.',
              '- 13: today residual 52.65; full payment on May 15 leaves a June 5 minimum of 913.04, short of 1,300 by 386.96. Future-safety semantics require preserving that shortfall, not checking cash only on May 15.',
              '- 21: 12.58 residual preserved. No independent expense rule supports adding that amount.',
              '- 25: required extra pre-payroll capacity 1,266,488; category reserves are groceries 1,219,499.80, transport 1,211,954.70, dining 1,478,110.60. None may be removed solely to fit. Later FX payroll contributes zero at the binding checkpoint.', '',
              'Full additive low-water components and nonadditive removal sensitivities remain in phase2_5-details.json. The Phase 2.6 details additionally independently replay full payment on every forecast date for all six complete cases in both old and current cores.', '',
              '## Reproduce', '', '```powershell',
              '.\\.venv\\Scripts\\python.exe code/evaluation/scope_audit.py',
              '.\\.venv\\Scripts\\python.exe code/evaluation/semantics.py',
              '.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v',
              'git diff --check','git diff --exit-code HEAD -- dataset','```', '',
              'The semantic audit found no necessary production policy change. The final review and readiness decision are in phase2_6-review.md and RESUME.md. Phase 3 means evidence normalization, not payment-plan optimization.']
    (ROOT/'evaluation/phase2_6-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'metrics':combined_metrics,'impact':impact},indent=2))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        print(json.dumps(worker(Path(sys.argv[2]))))
    else:run()
