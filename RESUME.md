# Runtime checkpoint

## Current phase / branch
Phase 3B - Message Evidence Extraction; feat/message-extraction.

## Last completed checkpoint
B: Responses adapter, strict parsing/failure handling, transactional SQLite cache, per-attempt usage accounting, bounded retries, restart recovery and 192 passing offline tests. No external calls.

## Last known good commit
Phase 3B B: 29d9b4a; A: 4424afe. Provider follow-up is the commit containing this RESUME version, titled feat: support configured OpenRouter extraction. This is a B adapter follow-up, not completion of C/D. Frozen checkpoint: 7fc459e (Phase 3A D); b04f7ad (financial baseline).

## Last passing test command
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
198 tests; Python 3.12.14, standard library only. The resumed C preparation added cohort-selection and integration tests; no baseline changes.

## Frozen dependencies
Phase 2.x deterministic financial policies and Phase 3A validation/reconciliation/completeness. Only demonstrated integration defects may change these. No baseline tuning, image/VLM, plans/ranking, final output.csv, dataset changes or solved-output-driven prompting.

## Extraction/cache state
Schema/prompt/extractor: message-1. Configured run: openrouter / openai/gpt-4.1-mini, pinned OpenAI upstream with fallbacks disabled. User supplied an OpenRouter credential, retained only in ignored Windows-user-encrypted cache/openrouter-key.dpapi; the launcher injects it into the child environment. Non-secret run settings: cache/message-config.json. SQLite integrity was verified OK; zero cache rows and zero usage attempts before first live run. No existing entries invalidated by provider selection. Explicit content/context and version hashes remain unchanged; provider is already a cache-key component.

## Corpus
215 messages, 215 users and message-bearing requests (198 evaluation + 17 samples); 39 linked / 176 unlinked. All messages precede requests, no empty texts or exact/normalized duplicates. 127-330 characters. Keyword topics are evaluation-only; English/Indonesian require semantic extraction.

## Files currently being changed
Provider adapter follow-up plus preserved C preparation: message_results.py, message_extract.py cohort fix, message integration tests, result/usage artifacts. All existing interrupted work preserved. C/D not complete.

## Exact next action
Checkpoint C: run scripts/message-run.ps1 extract --limit 3, inspect extraction/schema/usage only, then normal full batch (cached successes skipped). Run unchanged batch again and prove zero calls/tokens/cost. Run scripts/message-run.ps1 results for extraction and 250-request diagnostics before inspecting sample-label diagnostics. Then C commit and D read-only review/hardening/freeze. Never refresh all entries merely after restart.

## Reproduction commands
.\.venv\Scripts\python.exe code/evaluation/message_audit.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/evidence_inventory.py
.\.venv\Scripts\python.exe code/evaluation/message_extract.py
.\.venv\Scripts\python.exe code/evaluation/message_extract.py --cache-only
git diff --check
git diff --exit-code HEAD -- dataset

## Known limitations
No extraction accuracy measured yet. Unlinked targets, ambiguous currency/date, percent-only amounts, incomplete context remain unresolved. Image timing/publisher identity are still unknown. Exact quote grounding does not prove semantic truth. Future model outputs must pass Phase 3A reconciliation.

## Checkpoint protocol
Update RESUME, run tests, diff check, verify dataset unchanged, stage explicit paths only, inspect staged diff, commit. Keep log.txt append-only and ignored. Never git add .; preserve interrupted changes.
