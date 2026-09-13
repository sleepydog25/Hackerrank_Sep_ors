"""Development inference usage only; never Codex or final-submission usage."""
from collections import Counter
from decimal import Decimal

def summarize(records):
    calls=[r for r in records if r['external_call']]
    result=dict(external_attempts=len(calls),cache_hits=sum(r['cache_hit'] for r in records),
                statuses=dict(Counter(r['status'] for r in records)),
                uncertain_attempts=sum(r['status'] in ('IN_FLIGHT','UNKNOWN_PROVIDER_OUTCOME') for r in calls),
                retries=sum(r['attempt']>1 for r in calls),providers=sorted({r['provider'] for r in calls}),
                configured_models=sorted({r['model'] for r in calls}),
                actual_models=sorted({r['actual_model'] for r in calls if r.get('actual_model')}))
    for key in ('input_tokens','output_tokens','total_tokens','cached_input_tokens'):
        known=[r[key] for r in calls if r.get(key) is not None]
        result[key]=sum(known) if len(known)==len(calls) else None
        result['known_'+key]=sum(known)
        result['unknown_'+key+'_attempts']=len(calls)-len(known)
    costs=[Decimal(r['estimated_cost_usd']) for r in calls if r.get('estimated_cost_usd') is not None]
    result['estimated_cost_usd']=str(sum(costs,Decimal(0))) if len(costs)==len(calls) else None
    result['known_estimated_cost_usd']=str(sum(costs,Decimal(0)))
    result['unknown_cost_attempts']=len(calls)-len(costs)
    return result
