# Runtime checkpoint

## Current phase / branch
Phase 3B - Message Evidence Extraction; feat/message-extraction.

## Last completed checkpoint
C: real-message batch and 250-request integration evaluated. 215 actual calls, 186 parsed (157 facts, 17 unresolved, 12 no-fact), 29 parse failures; zero provider failures/retries. Immediate unchanged rerun: 215 cache hits, zero calls/tokens/cost (evaluation/phase3b-cache-proof.json).

## Last known good commit
C is the commit containing this RESUME, titled test: evaluate real message extraction. B follow-up c751d23; B 29d9b4a; A 4424afe; frozen Phase 3A 7fc459e.

## Last passing test command
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
198 tests; Python 3.12.14, standard library only. The resumed C preparation added cohort-selection and integration tests; no baseline changes.

## Frozen dependencies
Phase 2.x deterministic financial policies and Phase 3A validation/reconciliation/completeness. Only demonstrated integration defects may change these. No baseline tuning, image/VLM, plans/ranking, final output.csv, dataset changes or solved-output-driven prompting.

## Extraction/cache state
Schema/prompt/extractor: message-1. Configured run: openrouter / openai/gpt-4.1-mini, pinned OpenAI upstream with fallbacks disabled. User supplied an OpenRouter credential, retained only in ignored Windows-user-encrypted cache/openrouter-key.dpapi; the launcher injects it into the child environment. Non-secret run settings: cache/message-config.json. SQLite integrity was verified OK; zero cache rows and zero usage attempts before first live run. No existing entries invalidated by provider selection. Explicit content/context and version hashes remain unchanged; provider is already a cache-key component.

## Corpus
215 messages, 215 users and message-bearing requests (198 evaluation + 17 samples); 39 linked / 176 unlinked. All messages precede requests, no empty texts or exact/normalized duplicates. 127-330 characters. Keyword topics are evaluation-only; English/Indonesian require semantic extraction.

## Current checkpoint / persisted progress
C complete; D remains. Cache integrity checked and all 215 message-1 entries retained. Actual usage: 198785 input + 25507 output = 224292 tokens, USD 0.1203252 estimated and provider-reported. No unknown calls. 250-request smoke passes: 50 -> 90 complete, 200 -> 160 provisional; zero numerical changes. Completeness improvements are not an accuracy claim: manual review found a false NO_FACT termination and other semantic defects.

## Files currently being changed
None after this C commit. C includes the previously untracked message_results.py required by the B-follow-up tests. Preserve ignored cache and DPAPI credential.

## Exact next action
D: read-only review of full Phase 3B diff, record findings, then address source-grounded false NO_FACT termination, incorrect date/type/amount-meaning extraction and parse diagnostics. No baseline or sample-driven tuning. Any prompt change requires version bump and advance invalidation/cost notice; do not repeat message-1 extraction unchanged. Then synthetic/real adversarial smoke, full tests, cached reproduction, final D freeze.

## Reproduction commands
.\.venv\Scripts\python.exe code/evaluation/message_audit.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/evidence_inventory.py
.\.venv\Scripts\python.exe code/evaluation/message_extract.py
.\.venv\Scripts\python.exe code/evaluation/message_extract.py --cache-only
git diff --check
git diff --exit-code HEAD -- dataset

## Known limitations
Qualitative review in evaluation/phase3b-manual-review.md found a material false NO_FACT termination; D must fix before readiness. Unlinked targets, ambiguous currency/date, percent-only amounts, incomplete context remain unresolved. Image timing/publisher identity are still unknown. Exact quote grounding does not prove semantic truth. Future model outputs must pass Phase 3A reconciliation.

## Checkpoint protocol
Update RESUME, run tests, diff check, verify dataset unchanged, stage explicit paths only, inspect staged diff, commit. Keep log.txt append-only and ignored. Never git add .; preserve interrupted changes.
