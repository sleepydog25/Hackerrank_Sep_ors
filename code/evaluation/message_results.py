"""Cache-only diagnostics. Labels are read last, only after real extraction exists."""
import json
import argparse
import sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code'))
from buy_or_wait.load import load_dataset
from buy_or_wait.forecast import forecast_request
from buy_or_wait.evidence_integration import forecast_dataset_evidence
from buy_or_wait.message_cache import ExtractionStore,ExtractionResult,SUCCESS,identity
from buy_or_wait.message_provider import ModelConfig
from buy_or_wait.message_usage import summarize
from buy_or_wait.message_extraction import parse_output,canonical,digest
from message_extract import tasks

def evaluate(data,extractions):
    requests=[];counts=Counter();decisions=Counter();reasons=Counter()
    for q in sorted(data.selected_requests,key=lambda q:q.request_id):
        selected=extractions.get(q.request_id,[])
        batches=[r.batch for _,r in selected if r.batch is not None]
        before=forecast_request(data,q)
        after=forecast_dataset_evidence(data,q,batches)
        f=after.forecast
        amount=f.amount_safe_to_pay!=before.amount_safe_to_pay
        earliest=f.earliest_date_for_full_payment!=before.earliest_date_for_full_payment
        safety=f.baseline_safe!=before.baseline_safe
        if (amount or earliest or safety) and not after.normalized.amendments:
            raise AssertionError('financial change without accepted evidence amendment')
        ids={m.message_id for m,r in selected}
        message_unresolved=any(issue.split(':',1)[0].split(' -> ',1)[0] in ids for issue in after.source_issues)
        images=any(i.request_id in (None,q.request_id) for i in data.images_by_user.get(q.user_id,()))
        for key,value in [('complete_before',before.complete),('complete_after',f.complete),
                          ('provisional_before',not before.complete),('provisional_after',not f.complete),
                          ('financially_changed',amount or earliest or safety),('safe_changed',amount),
                          ('earliest_changed',earliest),('baseline_safety_changed',safety),
                          ('unresolved_messages',message_unresolved),('unresolved_both',message_unresolved and images),
                          ('unresolved_images_only',bool(f.issues) and all(issue.startswith('image_') for issue in f.issues))]:counts[key]+=int(value)
        details=[]
        for d in after.normalized.decisions:
            decisions[d.status.value]+=1
            if d.status.value=='UNRESOLVED':reasons[d.reason.value]+=1
            c=d.candidate
            details.append(dict(message_id=c.source.source_id,fact_id=c.fact_id,type=c.fact_type.value,
                                certainty=c.certainty.value,scope=c.scope.value,amount_meaning=c.amount_meaning.value,
                                amount=str(c.amount) if c.amount is not None else None,currency=c.currency,
                                payment_date=str(c.payment_date) if c.payment_date else None,status=d.status.value,reason=d.reason.value))
        requests.append(dict(request_id=q.request_id,cohort='message+image' if ids and images else 'message_only' if ids else 'image_only' if images else 'structured_only',
                             complete=f.complete,baseline_amount_safe_to_pay=str(before.amount_safe_to_pay),
                             baseline_earliest_date=str(before.earliest_date_for_full_payment) if before.earliest_date_for_full_payment else '',
                             amount_safe_to_pay=str(f.amount_safe_to_pay),
                             earliest_date_for_full_payment=str(f.earliest_date_for_full_payment) if f.earliest_date_for_full_payment else '',
                             issues=list(f.issues),candidates=details,
                             amendments=[dict(fact_id=a.fact_id,source_id=a.source.source_id,
                                              before=a.before.event_id if a.before else None,after=a.after.event_id if a.after else None)
                                         for a in after.normalized.amendments]))
    return dict(summary=dict(counts),validation=dict(decisions),unresolved_reasons=dict(reasons),requests=requests)

def write_artifacts(payload,usage):
    directory=ROOT/'evaluation'
    for name,value in [('phase3b-message-results',payload),('phase3b-usage',usage)]:
        (directory/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    lines=['# Phase 3B message diagnostics','',f"Run status: **{payload['run_status']}**.",'',
           'Cache-only report; no model calls, no fake real-message facts. Missing extraction is not a no-fact result.', '',
           '## Extraction','', '```json',json.dumps({k:v for k,v in payload['extraction'].items() if k!='messages'},indent=2),'```','',
           '## Evaluation request integration','', '```json',json.dumps(payload['evaluation']['summary'],indent=2),'```','',
           'Validation: '+str(payload['evaluation']['validation']),
           'Remaining reasons: '+str(payload['evaluation']['unresolved_reasons']),'',
           '## Samples and manual review','']
    if payload['run_status']!='REAL_BATCH_AVAILABLE':
        lines+=['Deferred: the real batch is not available. Unchanged baselines here do not establish extraction quality or real cache-hit coverage. No solved expected outputs were inspected for this report.']
    else:
        lines+=['Sample details are evaluation-only in JSON. Manual-review candidates are selected by distinct type/certainty/scope combinations and multi-fact messages, not financial mismatch.', '',
                '| Message | Type | Certainty | Scope | Decision | Reason |','|---|---|---|---|---|---|']
        seen=set();n=0
        for r in payload['evaluation']['requests']:
            for c in r['candidates']:
                key=(c['type'],c['certainty'],c['scope'])
                if key in seen or n>=20:continue
                seen.add(key);n+=1
                lines.append('| '+' | '.join(c[k] for k in ('message_id','type','certainty','scope','status','reason'))+' |')
        lines+=['','This table is a review queue. Actual source-level assessments are in phase3b-manual-review.md.']
        if payload.get('samples'):
            lines+=['','### Solved samples (diagnostic only)','',
                    '| Request | Cohort | Complete | Safe | Difference | Earliest | Expected earliest |',
                    '|---|---|---|---:|---:|---|---|']
            for r in payload['samples']['requests']:
                lines.append('| '+' | '.join(str(r[k]) for k in ('request_id','cohort','complete','amount_safe_to_pay',
                              'amount_difference','earliest_date_for_full_payment','expected_earliest_date_for_full_payment'))+' |')
    (directory/'phase3b-message-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (directory/'phase3b-usage.md').write_text('# Phase 3B development application usage\n\nNot Codex usage; not the final submission run. Unknown provider usage/cost remains null.\n\n```json\n'+json.dumps(usage,indent=2)+'\n```\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-samples',action='store_true',help='Publish extraction and evaluation metrics without reading labels')
    parser.add_argument('--artifact',type=Path,help='Replay sanitized committed extraction outputs without credentials or operational cache')
    args=parser.parse_args()
    artifact=json.loads(args.artifact.read_text(encoding='utf-8')) if args.artifact else None
    if artifact:
        config=ModelConfig(artifact['model'],provider=artifact['provider'],max_output_tokens=artifact['max_output_tokens'],
                           upstream=artifact.get('upstream','OpenAI'),reasoning_enabled=artifact.get('reasoning_enabled'))
        replay={r['key']:r for r in artifact['extractions']}
        if len(replay)!=len(artifact['extractions']):raise ValueError('duplicate snapshot keys')
    else:
        try:config=ModelConfig.from_env()
        except (ValueError,ArithmeticError):config=None
    store=ExtractionStore(ROOT/'cache/messages.sqlite')
    try:
        datasets={name:load_dataset(ROOT/'dataset',name) for name in ('requests.csv','sample_requests.csv')}
        extracted={};status=Counter();types=Counter();certainty=Counter();scope=Counter();meaning=Counter();ambiguity=Counter();per_message=[];snapshot=[]
        for name,data in datasets.items():
            groups={}
            for q,m,t in tasks(data):
                if artifact:
                    metadata=identity(t,config);key=digest(metadata);saved=replay.get(key)
                    if saved is None or saved['metadata']!=metadata:raise ValueError('snapshot version/content/context mismatch')
                    batch=parse_output(canonical(saved['output']),t) if saved['status'] in SUCCESS else None
                    r=ExtractionResult(key,saved['status'],batch,True,saved['error'])
                else:
                    r=store.extract(t,config,None,'report',cache_only=True) if config else ExtractionResult('','NOT_RUN',None,False,'CONFIGURATION_MISSING')
                if config and not artifact:
                    saved=store.db.execute('SELECT metadata,status,output,error FROM cache WHERE key=?',(r.key,)).fetchone()
                    if saved:snapshot.append(dict(key=r.key,metadata=json.loads(saved[0]),status=saved[1],output=json.loads(saved[2]) if saved[2] else None,error=saved[3]))
                    else:snapshot.append(dict(key=r.key,metadata=identity(t,config),status=r.status,output=None,error=r.error))
                groups.setdefault(q.request_id,[]).append((m,r));status[r.status]+=1
                facts=tuple(c for c in r.batch.candidates if c.fact_id.startswith('message-fact:')) if r.batch else ()
                markers=tuple(c for c in r.batch.candidates if c.fact_id.startswith('message-state:')) if r.batch else ()
                types.update(c.fact_type.value for c in facts);certainty.update(c.certainty.value for c in facts)
                scope.update(c.scope.value for c in facts);meaning.update(c.amount_meaning.value for c in facts)
                per_message.append(dict(message_id=m.message_id,status=r.status,facts=len(facts),error=r.error))
                for reason in ('AMBIGUOUS_DATE','AMBIGUOUS_CURRENCY','UNRESOLVED_TARGET'):
                    ambiguity[reason]+=any(reason in c.original_label for c in markers)
            extracted[name]=groups
        # Extraction summaries first, then evaluation finances; labels only last.
        extraction=dict(messages_total=len(per_message),statuses=dict(status),successful_parse=sum(v for k,v in status.items() if k in SUCCESS),
                        no_fact=status['NON_ACTIONABLE_SUCCESS'],facts_by_type=dict(types),facts_by_certainty=dict(certainty),
                        facts_by_scope=dict(scope),facts_by_amount_meaning=dict(meaning),ambiguity=dict(ambiguity),
                        multi_fact_messages=sum(r['facts']>1 for r in per_message),messages=per_message)
        evaluation=evaluate(datasets['requests.csv'],extracted['requests.csv'])
        available=all(r['status'] not in ('NOT_RUN','INTERRUPTED_ATTEMPT','RETRYABLE_FAILURE') for r in per_message)
        payload=dict(run_status='REAL_BATCH_AVAILABLE' if available else 'BLOCKED_OR_INCOMPLETE',extraction=extraction,evaluation=evaluation,samples=None)
        if available and not args.skip_samples:
            import csv
            from decimal import Decimal
            samples=evaluate(datasets['sample_requests.csv'],extracted['sample_requests.csv'])
            with (ROOT/'dataset/sample_requests.csv').open(encoding='utf-8-sig',newline='') as f:
                labels={r['request_id']:r for r in csv.DictReader(f)}
            for row in samples['requests']:
                expected=labels[row['request_id']]
                row['expected_amount_safe_to_pay']=expected['amount_safe_to_pay']
                row['amount_difference']=str(Decimal(row['amount_safe_to_pay'])-Decimal(expected['amount_safe_to_pay']))
                row['expected_earliest_date_for_full_payment']=expected['earliest_date_for_full_payment']
            payload['samples']=samples
        usage=artifact['usage'] if artifact else summarize(store.entries())
        if config and not artifact:
            sanitized=dict(provider=config.provider,model=config.model,max_output_tokens=config.max_output_tokens,
                           upstream=config.upstream,reasoning_enabled=config.reasoning_enabled,
                           extractions=snapshot,usage=usage)
            (ROOT/'evaluation/phase3b-extractions.json').write_text(json.dumps(sanitized,indent=2)+'\n',encoding='utf-8')
        write_artifacts(payload,usage)
        print(json.dumps(dict(run_status=payload['run_status'],extraction_status=dict(status),evaluation=evaluation['summary'],usage=usage),indent=2))
        return 0 if available else 2
    finally:store.close()

if __name__=='__main__':raise SystemExit(main())
