"""Metadata/topic diagnostics only. No interpretation or solved-output access."""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code'))
from buy_or_wait.load import load_dataset

TOPICS={
    'salary_payroll':('salary','payroll','gaji','penggajian'),
    'salary_change':('increas','reduc','temporary','naik','berubah'),
    'salary_delay':('delay','revised date','replaces the payroll date','tertunda'),
    'final_payroll':('final salary','final payroll','last salary'),
    'employment_ended':('contract has ended','employment','off-season','ended'),
    'bonus_commission':('bonus','commission','komisi'),
    'freelance_gig':('freelance','gig','shift','payout','quickcrew'),
    'refund':('refund','pengembalian'), 'reimbursement':('reimbursement','reimburse'),
    'invoice':('invoice','faktur'), 'rent':('rent','lease','sewa'),
    'duplicate_dispute':('duplicate','disput','duplikat'),
    'failed_retry':('failed','retry','gagal'), 'investment':('investment','portfolio','sale proceeds','investasi'),
    'internal_transfer':('transfer between','internal transfer','two accounts')}

def main():
    data=load_dataset(ROOT/'dataset')
    samples=load_dataset(ROOT/'dataset','sample_requests.csv')
    requests={q.request_id:q for q in (*data.requests.values(),*samples.requests.values())}
    messages=sorted((m for rows in data.messages_by_user.values() for m in rows),key=lambda m:m.message_id)
    per_request=Counter(); timing=Counter(); topics=Counter(); sources=Counter()
    duplicates={kind:defaultdict(list) for kind in ('exact','normalized')}
    rows=[]
    for m in messages:
        applicable=[q for q in requests.values() if q.user_id==m.user_id and m.request_id in (None,q.request_id)]
        for q in applicable:
            per_request[q.request_id]+=1
            timing['before' if m.sent_at.date()<q.request_date else 'on' if m.sent_at.date()==q.request_date else 'after']+=1
        text=m.message_text.casefold()
        buckets=[k for k,words in TOPICS.items() if any(w in text for w in words)] or ['unknown']
        topics.update(buckets); sources[m.source_type]+=1
        duplicates['exact'][m.message_text].append(m.message_id)
        duplicates['normalized'][re.sub(r'\W+',' ',text).strip()].append(m.message_id)
        risk=any(w in text for w in ('ignore previous','ignore all','system:','expected answer','mark this','output json','pretend'))
        rows.append(dict(message_id=m.message_id,length=len(m.message_text),topics=buckets,
                         instruction_like=risk,linked=bool(m.related_event_id),request_count=len(applicable)))
    lengths=sorted(r['length'] for r in rows)
    summary=dict(messages=len(messages),requests=len(per_request),users=len({m.user_id for m in messages}),
                 source_types=dict(sorted(sources.items())),linked=sum(r['linked'] for r in rows),
                 unlinked=sum(not r['linked'] for r in rows),request_relative_timing=dict(timing),
                 empty=sum(not m.message_text.strip() for m in messages),near_empty=sum(len(m.message_text.strip())<10 for m in messages),
                 duplicate_groups={k:[ids for ids in groups.values() if len(ids)>1] for k,groups in duplicates.items()},
                 length_characters={k:lengths[int((len(lengths)-1)*p)] for k,p in [('min',0),('p25',.25),('median',.5),('p75',.75),('max',1)]},
                 topics=dict(sorted(topics.items())),instruction_like=sum(r['instruction_like'] for r in rows),
                 messages_per_request_distribution=dict(sorted(Counter(per_request.values()).items())))
    payload=dict(summary=summary,messages=rows,messages_per_request=dict(sorted(per_request.items())))
    (ROOT/'evaluation/phase3b-message-audit.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    lines=['# Phase 3B message corpus audit','',
           'Deterministic metadata and overlapping keyword diagnostics only; no production keyword rules, financial interpretation, or solved-label access. Timing counts message/request pairs, including user-level messages. Near-empty means fewer than 10 stripped characters. Duplicate normalization casefolds and collapses punctuation/whitespace; it does not remove numbers or references.', '',
           '| Metric | Value |','|---|---|']
    lines += [f'| {k} | {v} |' for k,v in summary.items()]
    lines += ['','English and Indonesian appear in the inspected corpus. Keyword coverage is exploratory and incomplete across languages. Instruction-like matches are risk signals, not proof of malicious content; synthetic attacks remain required even if none are detected.', '',
              'Reproduce: `.\\.venv\\Scripts\\python.exe code/evaluation/message_audit.py`.']
    (ROOT/'evaluation/phase3b-message-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
