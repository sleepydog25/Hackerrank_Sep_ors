"""Restartable incremental real batch. No solved output columns enter extraction."""
import argparse
import json
import sys
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code'))
from buy_or_wait.load import load_dataset
from buy_or_wait.message_extraction import build_input
from buy_or_wait.message_cache import ExtractionStore
from buy_or_wait.message_provider import ModelConfig,OpenAIMessageProvider
from buy_or_wait.message_usage import summarize

def tasks(data):
    for q in sorted(data.requests.values(),key=lambda q:q.request_id):
        for m in sorted(data.messages_by_user.get(q.user_id,()),key=lambda m:(m.sent_at,m.message_id)):
            if m.request_id not in (None,q.request_id) or m.sent_at.date()>q.request_date:continue
            yield q,m,build_input(m,q,data.profiles[q.user_id],data.events_by_user.get(q.user_id,()))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-only',action='store_true')
    parser.add_argument('--refresh',action='store_true',help='Deliberately spend calls again for selected messages')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--message-id',action='append',default=[])
    parser.add_argument('--release-interrupted',help='Exact cache key whose unknown provider attempt was reviewed; may incur another call')
    args=parser.parse_args()
    if args.cache_only and args.refresh:parser.error('--refresh cannot be used with --cache-only')
    try:config=ModelConfig.from_env()
    except (ValueError,ArithmeticError):
        print('CONFIGURATION_MISSING_OR_INVALID: set MESSAGE_PROVIDER=openai and MESSAGE_MODEL; no external calls made.')
        return 2
    if not args.cache_only and not config.api_key:
        print('CONFIGURATION_MISSING: set OPENAI_API_KEY locally; do not paste it into chat. No external calls made.')
        return 2
    store=ExtractionStore(ROOT/'cache/messages.sqlite');provider=OpenAIMessageProvider(config)
    run_id=str(uuid.uuid4());results=[]
    try:
        if args.release_interrupted:store.release_interrupted(args.release_interrupted)
        for filename in ('requests.csv','sample_requests.csv'):
            data=load_dataset(ROOT/'dataset',filename)  # loader discards solved columns
            for q,m,t in tasks(data):
                if args.message_id and m.message_id not in args.message_id:continue
                if args.limit is not None and len(results)>=args.limit:break
                r=store.extract(t,config,provider,run_id,refresh=args.refresh,cache_only=args.cache_only)
                results.append(dict(request_id=q.request_id,message_id=m.message_id,status=r.status,key=r.key,
                                    cache_hit=r.cache_hit,error=r.error))
                print(m.message_id,r.status,'cache' if r.cache_hit else 'miss',flush=True)
        payload=dict(run_id=run_id,results=results,run_usage=summarize(store.entries(run_id)),
                     development_usage=summarize(store.entries()))
        # Operational report is ignored; committed sanitized report generated separately.
        target=ROOT/'cache/message-last-run.json';temp=target.with_suffix('.tmp')
        temp.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8');temp.replace(target)
        print(json.dumps(payload['run_usage'],indent=2))
        return 0 if all(r['status'].endswith('SUCCESS') for r in results) else 2
    finally:store.close()

if __name__=='__main__':raise SystemExit(main())
