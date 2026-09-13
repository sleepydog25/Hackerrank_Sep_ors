"""Metadata-only evidence inventory and regression; never extract source prose."""
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from buy_or_wait.load import load_dataset
from buy_or_wait.forecast import forecast_request
from buy_or_wait.evidence_integration import dataset_sources, forecast_dataset_evidence
from buy_or_wait.evidence import SourceType

ROOT=Path(__file__).resolve().parents[2]


def run():
    cohorts={}
    for filename in ('requests.csv','sample_requests.csv'):
        data=load_dataset(ROOT/'dataset',filename)
        records=[]
        for q in data.selected_requests:
            sources=[s for s in dataset_sources(data,q) if s.observed_at is None or s.observed_at.date()<=q.request_date]
            events=data.events_by_user.get(q.user_id,())
            missing=[e for e in events if e.amount is None]
            mapped={s.related_event_id for s in sources if s.related_event_id}
            original=forecast_request(data,q)
            empty=forecast_dataset_evidence(data,q,()).forecast
            assert (original.amount_safe_to_pay,original.earliest_date_for_full_payment,original.baseline_safe)==(empty.amount_safe_to_pay,empty.earliest_date_for_full_payment,empty.baseline_safe)
            assert original.complete==empty.complete,(q.request_id,original.issues,empty.issues)
            evidence_only=bool(original.issues) and all(x.startswith(('unresolved message','unresolved image','missing amount')) for x in original.issues) and all(e.event_id in mapped for e in missing)
            records.append(dict(request=q.request_id,messages=sum(s.source_type==SourceType.MESSAGE for s in sources),
                                images=sum(s.source_type==SourceType.IMAGE for s in sources),
                                linked_rows=sum(s.related_event_id is not None for s in sources),
                                missing_amounts=len(missing),missing_amounts_with_evidence=sum(e.event_id in mapped for e in missing),
                                complete=original.complete,provisional_only_uninterpreted_evidence=evidence_only))
        summaries=dict(requests=len(records),with_messages=sum(r['messages']>0 for r in records),with_images=sum(r['images']>0 for r in records),
                       with_both=sum(r['messages']>0 and r['images']>0 for r in records),with_related_event_id=sum(r['linked_rows']>0 for r in records),
                       structured_complete=sum(r['complete'] for r in records),provisional=sum(not r['complete'] for r in records),
                       provisional_only_uninterpreted_evidence=sum(r['provisional_only_uninterpreted_evidence'] for r in records),
                       empty_adapter_numeric_changes=0)
        cohorts[filename]={'summary':summaries,'requests':records}
    data=load_dataset(ROOT/'dataset','requests.csv')
    messages=[m for rows in data.messages_by_user.values() for m in rows]
    images=[i for rows in data.images_by_user.values() for i in rows]
    mapped_ids={x.related_event_id for x in messages+images if x.related_event_id}
    missing=[e for e in data.events.values() if e.amount is None]
    global_counts=dict(message_rows=len(messages),image_rows=len(images),
                       mapped_message_rows=sum(m.related_event_id in data.events for m in messages),
                       mapped_image_rows=sum(i.related_event_id in data.events for i in images),
                       missing_amount_events=len(missing),missing_amount_events_with_evidence=sum(e.event_id in mapped_ids for e in missing),
                       message_source_types=dict(sorted(Counter(m.source_type for m in messages).items())),
                       image_source_types={'IMAGE':len(images)})
    payload={'metadata_only':True,'all_supplied_evidence':global_counts,'cohorts':cohorts}
    (ROOT/'evaluation/phase3a-evidence-inventory.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    lines=['# Phase 3A evidence inventory','',
           'Metadata only: no message interpretation, OCR, model calls, or solved-label access. Counts include request-specific and user-level evidence available by the request date. Images have no observed timestamp in the CSV and remain unresolved until observation context is established.', '',
           '| Cohort | Requests | Messages | Images | Both | Linked evidence | Complete | Provisional | Provisional solely uninterpreted evidence |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,cohort in cohorts.items():
        r=cohort['summary']
        lines.append('| '+' | '.join([name]+[str(r[k]) for k in ('requests','with_messages','with_images','with_both','with_related_event_id','structured_complete','provisional','provisional_only_uninterpreted_evidence')])+' |')
    lines+=['','“Solely uninterpreted” includes missing structured amounts whose events have mapped evidence, and excludes missing rates/other issues. It does not claim future extraction will successfully resolve those sources.', '',
            '| All supplied rows (samples + evaluation) | Count |','|---|---:|']
    for k,v in global_counts.items():lines.append(f'| {k} | {v} |')
    lines+=['','All 250 evaluation requests and 25 samples pass the empty-evidence-adapter comparison for safe amount, earliest date, baseline safety and completeness. Structured-complete requests retain their financial outputs. Raw evidence has not been converted into fixtures for these real requests.', '',
            'Synthetic end-to-end tests cover ongoing/next-pay salary, reschedule, final payroll, refund/reimbursement, approved invoice, investment sale/value, outstanding invoice, hypothetical income, ambiguous image, cancellation and provenance.', '',
            '```powershell','.\\.venv\\Scripts\\python.exe code/evaluation/evidence_inventory.py',
            '.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v',
            '.\\.venv\\Scripts\\python.exe code/evaluation/semantics.py','```']
    (ROOT/'evaluation/phase3a-evidence-inventory.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'global':global_counts,'cohorts':{k:v['summary'] for k,v in cohorts.items()}},indent=2))


if __name__=='__main__':run()
