# Message extraction, Phase 3B

The extractor interprets a single message into the existing Phase 3A candidates. It never computes money or chooses recommendations. The versioned system instruction and closed JSON schema live in `code/buy_or_wait/message_extraction.py`. Initial schema/prompt/extractor versions are `message-1`. Provenance and fact IDs are attached by application code, not requested from the model. Every returned monetary fact requires an exact supporting message quote; this is a grounding check, not proof of semantic correctness.

The model sees isolated untrusted message text, sent_at, request_date, source category, home currency and at most the directly related structured event. It sees no balances, requested purchase amount, preferences, sample outputs or other messages. Event context is withheld unless its event_date is on/before the message date. Scheduled obligations may have later settlement dates only when that recording-date gate passes. This conservative window and all supplied context enter the cache identity. Unlinked messages do not acquire guessed targets or verified publisher identities.

Home currency is context, not permission to infer an ambiguous dollar symbol. Relative dates without explicit unambiguous ISO context remain unresolved in v1. Percent-only amendments are unresolved; a model must not compute a replacement amount. Net/gross, next/ongoing, hypothetical/confirmed, pending/settled, and valuation/sale remain distinct. English and Indonesian are present in this corpus; no production keyword rules are used.

The thin response envelope is `{outcome, facts, reasons}`. FACTS requires one to eight facts and no unresolved reasons. NO_FACT requires no facts/reasons and becomes an explicit NON_FINANCIAL candidate, avoiding Phase 3A's empty-batch ambiguity. UNRESOLVED requires machine-readable reasons and produces a disputed marker plus a non-exhaustive batch. It may preserve independent candidates but cannot mark the source complete. Invalid output is a failure, never NO_FACT. Every result still passes Phase 3A validation/reconciliation.

Offline fixtures cover 21 financial situations and ten instruction-style attacks. They test deterministic construction/parsing, not model accuracy or immunity to semantic hallucinations. The model has no tools, and message content cannot replace system instructions, schema or trusted source metadata.

The provider adapter uses the Responses API `text.format` JSON schema and local strict validation; see the [official structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs). Refusals/truncation and unknown usage are handled separately from valid structured output. No live call is allowed until Checkpoint B is committed.

Reproduce Checkpoint A:
```powershell
.\.venv\Scripts\python.exe code/evaluation/message_audit.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Provider, cache and usage

Configuration is environment-only: MESSAGE_PROVIDER=openai, MESSAGE_MODEL (required exact identifier), OPENAI_API_KEY (secret), MESSAGE_TIMEOUT (1-60 seconds, default 45), MESSAGE_MAX_ATTEMPTS (1-3, default 2), MESSAGE_MAX_OUTPUT_TOKENS (256-8000, default 3000). There is no implicit model substitution or credential discovery outside the configured environment. Offline tests mock the transport and never spend tokens. No SDK/runtime dependency is added.

SQLite at ignored `cache/messages.sqlite` uses WAL and FULL synchronization. Cache identity hashes raw content, complete supplied context, trusted source associations, provider/model, schema/prompt/extractor versions and their actual content hashes, and output-token limit. Successful facts, no-fact and unresolved interpretations are cached; deterministic parse/provider failures are also retained to avoid repeated charges. Retryable failures permit later retry. Each call intent is persisted before I/O; completion, usage and cache result commit in one transaction. An in-flight crash remains unknown and blocks silent redispatch. Review its exact key before using `--release-interrupted KEY`; a lost provider response cannot honestly be assigned zero tokens/cost. No secret or raw provider error body is stored. Only validated response envelopes (including bounded evidence quotes) are retained; cache hits reparse against current trusted input.

Normal reruns use cache. `--refresh --message-id ID` deliberately refreshes selected entries; never refresh an entire corpus merely for diagnostics. `--cache-only` forbids calls and works without an API key when MESSAGE_MODEL is configured. Ordering is evaluation requests then samples, sorted request ID, sent_at, message ID; messages are independently interpreted with no later-message history. The cache is reusable after process restart. Reports never call providers.

Usage records each attempt separately, including retries, provider/model, versions, source associations, timestamps, provider counts and unknown fields. Cache hits have external_call=false and incremental tokens/cost exactly zero. IN_FLIGHT counts are dispatch intents with uncertain outcomes, not verified completed calls. Optional MESSAGE_INPUT_USD_PER_MILLION, MESSAGE_OUTPUT_USD_PER_MILLION and MESSAGE_CACHED_INPUT_USD_PER_MILLION allow an explicit local Decimal estimate; unknown rates or counts yield unknown cost. Provider-reported costs are unavailable in this adapter. Development application inference remains separate from Codex tokens and the eventual final-run `evaluation/usage_report.md`.

After B is committed and the environment is configured, run:
```powershell
.\.venv\Scripts\python.exe code/evaluation/message_extract.py
.\.venv\Scripts\python.exe code/evaluation/message_extract.py
.\.venv\Scripts\python.exe code/evaluation/message_extract.py --cache-only
```
The first unchanged rerun must report zero external attempts and zero incremental tokens/cost. A preflight missing-configuration exit makes no calls and is not evidence of a completed batch.

## Configured OpenRouter run

The supplied credential selected OpenRouter explicitly; no call uses it at the OpenAI endpoint. `MESSAGE_PROVIDER=openrouter` uses `/api/v1/chat/completions` with strict response_format, temperature 0 and the OpenAI upstream pinned without fallbacks. Model: `openai/gpt-4.1-mini`, chosen for low-cost structured extraction. [OpenRouter documents schema support and prices](https://openrouter.ai/openai/gpt-4.1-mini): USD 0.40/M input, 1.60/M output, 0.10/M cached input. These are explicit local estimates; provider-reported usage.cost is separately retained using Decimal. Changing provider/model changes the existing cache key; no successful entries existed before this configuration.

The optional Windows launcher `scripts/message-run.ps1` reads non-secret run settings from ignored `cache/message-config.json`, decrypts the user-bound DPAPI credential into a child environment, clears it afterwards, and invokes extract/results. The application still reads credentials only from environment. The encrypted local credential is not portable or part of the submission. Normal environment configuration remains supported on every platform.

```powershell
.\scripts\message-run.ps1 extract --limit 3
.\scripts\message-run.ps1 extract
.\scripts\message-run.ps1 extract
.\scripts\message-run.ps1 results
```
