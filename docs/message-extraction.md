# Message extraction, Phase 3B

The extractor interprets a single message into the existing Phase 3A candidates. It never computes money or chooses recommendations. The versioned system instruction and closed JSON schema live in `code/buy_or_wait/message_extraction.py`. Initial schema/prompt/extractor versions are `message-1`. Provenance and fact IDs are attached by application code, not requested from the model. Every returned monetary fact requires an exact supporting message quote; this is a grounding check, not proof of semantic correctness.

The model sees isolated untrusted message text, sent_at, request_date, source category, home currency and at most the directly related structured event. It sees no balances, requested purchase amount, preferences, sample outputs or other messages. Event context is withheld unless its event_date is on/before the message date. Scheduled obligations may have later settlement dates only when that recording-date gate passes. This conservative window and all supplied context enter the cache identity. Unlinked messages do not acquire guessed targets or verified publisher identities.

Home currency is context, not permission to infer an ambiguous dollar symbol. Relative dates without explicit unambiguous ISO context remain unresolved in v1. Percent-only amendments are unresolved; a model must not compute a replacement amount. Net/gross, next/ongoing, hypothetical/confirmed, pending/settled, and valuation/sale remain distinct. English and Indonesian are present in this corpus; no production keyword rules are used.

The thin response envelope is `{outcome, facts, reasons}`. FACTS requires one to eight facts and no unresolved reasons. NO_FACT requires no facts/reasons and becomes an explicit NON_FINANCIAL candidate, avoiding Phase 3A's empty-batch ambiguity. UNRESOLVED requires machine-readable reasons and produces a disputed marker plus a non-exhaustive batch. It may preserve independent candidates but cannot mark the source complete. Invalid output is a failure, never NO_FACT. Every result still passes Phase 3A validation/reconciliation.

Offline fixtures cover 21 financial situations and ten instruction-style attacks. They test deterministic construction/parsing, not model accuracy or immunity to semantic hallucinations. The model has no tools, and message content cannot replace system instructions, schema or trusted source metadata.

The provider adapter will use the Responses API `text.format` JSON schema and local strict validation; see the [official structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs). Refusals/truncation and unknown usage must be handled separately from valid structured output. No live call is allowed until Checkpoint B is committed.

Reproduce Checkpoint A:
```powershell
.\.venv\Scripts\python.exe code/evaluation/message_audit.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
