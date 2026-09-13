"""Read-only history/usage audit, including offline checks of earlier parser output."""
import json
import sqlite3
import sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code'))
from buy_or_wait.message_extraction import parse_output,SCHEMA_VERSION,PROMPT_VERSION,EXTRACTOR_VERSION
from buy_or_wait.message_usage import summarize
from buy_or_wait.load import load_dataset
from message_extract import tasks

def main():
    db=sqlite3.connect('file:'+str(ROOT/'cache/messages.sqlite').replace('\\','/')+'?mode=ro',uri=True)
    try:
        integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
        groups=defaultdict(Counter);checks=[]
        inputs={m.message_id:t for name in ('requests.csv','sample_requests.csv') for q,m,t in tasks(load_dataset(ROOT/'dataset',name))}
        for key,meta,status,output in db.execute('SELECT key,metadata,status,output FROM cache ORDER BY key'):
            m=json.loads(meta)
            namespace=' | '.join(m[k] for k in ('model','schema_version','prompt_version','extractor_version'))
            groups[namespace][status]+=1
            source=m['source']['source_id']
            # Offline regression only; never promotes an older entry into a current cache hit.
            if output and source in inputs and m['schema_version']==SCHEMA_VERSION and m['prompt_version']==PROMPT_VERSION:
                try:
                    parse_output(output,inputs[source]);result='PARSES_NOT_FINANCIALLY_VALIDATED'
                except (ValueError,TypeError,KeyError):result='REJECTED_BY_CURRENT_PARSER'
                checks.append(dict(source_id=source,model=m['model'],original_extractor=m['extractor_version'],result=result))
        records=[json.loads(r[0]) for r in db.execute('SELECT record FROM usage')]
        unknown=[dict(key=k,source_id=json.loads(r)['source']['source_id'])
                 for k,r in db.execute("SELECT key,record FROM usage WHERE state='IN_FLIGHT'")]
        report=dict(integrity=integrity,current_versions=dict(schema=SCHEMA_VERSION,prompt=PROMPT_VERSION,extractor=EXTRACTOR_VERSION),
                    namespaces={k:dict(v) for k,v in sorted(groups.items())},in_flight=unknown,
                    offline_parser_checks=checks,usage=summarize(records))
        (ROOT/'evaluation/phase3b-cache-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k!='usage'},indent=2))
        return 0 if integrity=='ok' else 2
    finally:db.close()

if __name__=='__main__':raise SystemExit(main())
