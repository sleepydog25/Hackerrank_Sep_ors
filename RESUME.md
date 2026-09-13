# Runtime checkpoint

## Current phase / branch
Phase 3B - Message Evidence Extraction; feat/message-extraction.

## Last completed checkpoint
B: Responses adapter, strict parsing/failure handling, transactional SQLite cache, per-attempt usage accounting, bounded retries, restart recovery and 192 passing offline tests. No external calls.

## Last known good commit
Phase 3B B is the commit containing this RESUME version, titled feat: add cached message model extraction. Resolve with git log -1 --format=%H -- RESUME.md after commit. A: 4424afe. Previous frozen checkpoint: 7fc459e (Phase 3A D); b04f7ad (financial baseline).

## Last passing test command
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
192 tests; Python 3.12.14, standard library only.

## Frozen dependencies
Phase 2.x deterministic financial policies and Phase 3A validation/reconciliation/completeness. Only demonstrated integration defects may change these. No baseline tuning, image/VLM, plans/ranking, final output.csv, dataset changes or solved-output-driven prompting.

## Extraction/cache state
Schema/prompt/extractor: message-1. Provider adapter: openai Responses; exact model must be configured. No real provider calls or real extraction cache yet. No API credentials or model configured in current environment; user has been asked to configure locally. No secrets printed. SQLite stores attempts before dispatch, and output/usage atomically; cached unresolved and successful facts persist. Unknown interrupted calls require explicit review/release.

## Corpus
215 messages, 215 users and message-bearing requests (198 evaluation + 17 samples); 39 linked / 176 unlinked. All messages precede requests, no empty texts or exact/normalized duplicates. 127-330 characters. Keyword topics are evaluation-only; English/Indonesian require semantic extraction.

## Files currently being changed
None after B commit. Before commit: message_extraction.py, message_provider.py, message_cache.py, message_usage.py, message_extract.py, message contract/cache/provider tests, docs/message-extraction.md and RESUME.md.

## Exact next action
Checkpoint C: controlled real batch using MESSAGE_MODEL, MESSAGE_PROVIDER=openai and locally configured OPENAI_API_KEY. First verify B is committed. Run message_extract.py twice; prove unchanged rerun has zero calls/tokens/cost. Build/run aggregate and 250-request integration diagnostics before sample-label comparisons. D remains read-only review then confirmed fixes and final freeze. Do not mark C/D or Phase 3B complete without real execution. Missing credentials permit offline work but block real batch verification.

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
