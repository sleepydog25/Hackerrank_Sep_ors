"""Repeatable read-only dataset, grouping, completeness, and ledger audit."""
import json
import subprocess
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from buy_or_wait.load import load_dataset
from buy_or_wait.forecast import forecast_request
from buy_or_wait.policy import DEFAULT_POLICY
from buy_or_wait.recurrence import series_description

ROOT=Path(__file__).resolve().parents[2]


def run():
    subprocess.run(['git','diff','--exit-code','HEAD','--','dataset'],cwd=ROOT,check=True)
    assert not subprocess.check_output(['git','status','--porcelain','--','dataset'],cwd=ROOT).strip()
    data=load_dataset(ROOT/'dataset','sample_requests.csv')
    complete=[]
    ledger_count=0
    for request in data.selected_requests:
        result=forecast_request(data,request)
        balance=result.opening_balance
        for row in result.ledger:
            balance+=row.inflow-row.outflow
            assert balance==row.balance
            ledger_count+=1
        if result.complete:
            complete.append(dict(request=request.request_id,
                                 user_messages=len(data.messages_by_user.get(request.user_id,())),
                                 user_images=len(data.images_by_user.get(request.user_id,())),
                                 overlap_offsets=[n for n in result.reconciliation_notes if 'budget offset' in n]))
    groups=defaultdict(set)
    for event in data.events.values():
        if event.status=='settled' and event.category not in DEFAULT_POLICY.variable_categories:
            groups[(event.user_id,event.category,event.direction,event.currency,
                    series_description(event.description,True))].add(series_description(event.description,False))
    pending=Counter(event.description for event in data.events.values() if event.status=='pending'
                    and event.direction=='debit' and event.category in DEFAULT_POLICY.variable_categories)
    evaluation=load_dataset(ROOT/'dataset','requests.csv')
    for request in evaluation.selected_requests:
        result=forecast_request(evaluation,request)
        assert Decimal(0)<=result.amount_safe_to_pay<=request.requested_amount
    assert not (ROOT/'output.csv').exists()
    summary=dict(dataset_unchanged=True,final_output_exists=False,complete_samples=complete,
                 pending_variable_descriptions=dict(pending),
                 fixed_history_groups_merged_by_period_normalization=sum(len(v)>1 for v in groups.values()),
                 sample_ledger_checkpoints_verified=ledger_count,
                 evaluation_requests_smoke_tested=len(evaluation.selected_requests))
    (ROOT/'evaluation/phase2_5-audit.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':run()
