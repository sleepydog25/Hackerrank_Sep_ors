# Runtime checkpoint

## Current phase / branch
Phase 3B - Message Evidence Extraction; feat/message-extraction.

## Last completed checkpoint
A: corpus audit, extraction specification, strict candidate transport and synthetic fixtures. No external calls. 170 tests pass.

## Last known good commit
Phase 3B A is the commit containing this RESUME version, titled feat: define message extraction boundary. Resolve with git log -1 --format=%H -- RESUME.md after commit. Previous frozen checkpoint: 7fc459e (Phase 3A D); b04f7ad (financial baseline).

## Last passing test command
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
170 tests; Python 3.12.14, standard library only.

## Frozen dependencies
Phase 2.x deterministic financial policies and Phase 3A validation/reconciliation/completeness. Only demonstrated integration defects may change these. No baseline tuning, image/VLM, plans/ranking, final output.csv, dataset changes or solved-output-driven prompting.

## Extraction/cache state
Schema/prompt/extractor: message-1. No provider calls or cache yet. No API credentials or model configured in current environment; user has been asked to configure locally. No secrets printed. API adapter can be built/tested offline.

## Corpus
215 messages, 215 users and message-bearing requests (198 evaluation + 17 samples); 39 linked / 176 unlinked. All messages precede requests, no empty texts or exact/normalized duplicates. 127-330 characters. Keyword topics are evaluation-only; English/Indonesian require semantic extraction.

## Files currently being changed
None after A commit. Before commit: message_extraction.py, message_audit.py, test_message_extraction_contract.py, docs/message-extraction.md, phase3b-message-audit.md/json, RESUME.md.

## Exact next action
Checkpoint B: implement Responses provider adapter, strict failure handling, SQLite persistent cache and atomic per-attempt usage accounting, bounded retry and offline tests. Do not make external calls before B commit. Then C real batch (requires local provider/model credentials), diagnostics before sample labels, unchanged-cache rerun. D read-only review, confirmed fixes, final freeze. Do not mark C complete without a real run.

## Reproduction commands
.\.venv\Scripts\python.exe code/evaluation/message_audit.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/evidence_inventory.py
git diff --check
git diff --exit-code HEAD -- dataset

## Known limitations
No extraction accuracy measured yet. Unlinked targets, ambiguous currency/date, percent-only amounts, incomplete context remain unresolved. Image timing/publisher identity are still unknown. Exact quote grounding does not prove semantic truth. Future model outputs must pass Phase 3A reconciliation.

## Checkpoint protocol
Update RESUME, run tests, diff check, verify dataset unchanged, stage explicit paths only, inspect staged diff, commit. Keep log.txt append-only and ignored. Never git add .; preserve interrupted changes.