# Phase 3B message diagnostics

Run status: **BLOCKED_OR_INCOMPLETE**.

Cache-only report; no model calls, no fake real-message facts. Missing extraction is not a no-fact result.

## Extraction

```json
{
  "messages_total": 215,
  "statuses": {
    "NOT_RUN": 215
  },
  "successful_parse": 0,
  "no_fact": 0,
  "facts_by_type": {},
  "facts_by_certainty": {},
  "facts_by_scope": {},
  "facts_by_amount_meaning": {},
  "ambiguity": {
    "AMBIGUOUS_DATE": 0,
    "AMBIGUOUS_CURRENCY": 0,
    "UNRESOLVED_TARGET": 0
  },
  "multi_fact_messages": 0
}
```

## Evaluation request integration

```json
{
  "complete_before": 50,
  "complete_after": 50,
  "provisional_before": 200,
  "provisional_after": 200,
  "financially_changed": 0,
  "safe_changed": 0,
  "earliest_changed": 0,
  "baseline_safety_changed": 0,
  "unresolved_messages": 198,
  "unresolved_both": 9,
  "unresolved_images_only": 0
}
```

Validation: {}
Remaining reasons: {}

## Samples and manual review

Deferred: the real batch is not available. Unchanged baselines here do not establish extraction quality or real cache-hit coverage. No solved expected outputs were inspected for this report.
