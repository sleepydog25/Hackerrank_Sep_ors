# Runtime checkpoint

## EMERGENCY SUBMISSION BASELINE

S0 replaces the earlier roadmap priority. Deterministic release implemented from
`12ba13b` without changing frozen financial or Phase 3A policies. Exact known-good
release commit: `70859c23b12b2e887fdfad94ecbdcb588a027d0d`
(`feat: package deterministic emergency submission`). Its committed output and
archive are always available as the S0 fallback.

Reproduce: `powershell -ExecutionPolicy Bypass -File scripts/finalize-submission.ps1`
(or `.\.venv\Scripts\python.exe code/finalize_submission.py --require-log`).

Root `output.csv` has 250 validated rows; root `code.zip` opens, contains
`evaluation/usage_report.md`, passes secret/manifest checks, and reproduces output
byte-for-byte when extracted. Root `log.txt` remains separate and ignored.
230 tests pass. Dataset unchanged. Final inference calls/tokens/cost are zero.
Usage is tied to output SHA-256
`62a1801f90d4a20b569aea475a23f8b3712bd5d0f28fba502245cf5b7f4a89db`.

Full/partial/wait/supplied installments are independently validated and ranked.
Spending changes are disabled conservatively; no unvalidated model evidence or
historical cache is used. Baseline capacity may remain provisional where evidence
is missing. Missing cash amount/FX prevents plan certification. See
`evaluation/s0-release.md` and `SUBMISSION_README.md` for limitations and the
conservative installment-duration rule. Sample exact matches (25): safe amount 2,
status/method/plan 10 each, earliest date 15, spending changes 22. No sample tuning.

The older checkpoint notes below are retained as development history, not the
current release instructions. Always preserve this passing release before any
optional bounded Gemini qualification. No Nemotron/Nex retries or paid fallback.

## Current checkpoint / branch
Phase 3B D hardening checkpoint, NOT final freeze; feat/message-extraction. NOT READY for Phase 3C.

## Last completed checkpoint
C 93ef28f: full message-1 extraction, cache reproduction and 250-request integration. D read-only review and offline fixes are persisted, but reliable final-version extraction remains blocked by free-model semantic errors.

## Last known good commit
C 93ef28f; B follow-up c751d23; B 29d9b4a; A 4424afe. The latest hardening checkpoint is the commit containing this RESUME, titled fix: checkpoint message hardening and free-model findings. Verify its hash with git log. Frozen Phase 3A 7fc459e and financial baseline b04f7ad are unchanged.

## Last passing test command
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
210 tests pass; Python 3.12.14, standard library only. All 250 requests execute with zero frozen-baseline changes. Dataset and whitespace checks pass.

## Provider/model and versions
Configured provider openrouter; model nvidia/nemotron-3-super-120b-a12b:free; upstream nvidia; reasoning disabled; no fallback; zero-price ceiling. The user explicitly requested a free model after paid-model HTTP 402. Do not switch back to paid inference automatically.
Schema version message-2; prompt version message-3; extractor version message-4. Descriptions/coverage rules and strict currency/amount-meaning contradictions were versioned. Model output remains candidates only.

## Cache location/state
Ignored cache/messages.sqlite, SQLite integrity ok; all earlier namespaces retained. Ignored cache/message-config.json holds non-secret settings. Ignored cache/openrouter-key.dpapi holds user-bound encrypted credentials, injected only into a child environment. Never print or commit credentials.
The complete C namespace still has 215 entries and proved 215 cache hits, zero calls/tokens/cost on immediate unchanged rerun. New model/versions are separate: no final-version corpus entries yet. The last parser change invalidated the three free real-message entries; no further calls were made. Offline replay demonstrates the bad gross-pay/receipt output is rejected without changing or promoting its original cache entry.
One paid-model dispatch was interrupted: message_146, key 6f295a14ce81385739aeb42c72a1290189b640563c2669316b11668556d144f2. Preserve IN_FLIGHT/unknown usage; do not silently release or replay. No active process remains.

## Message extraction progress
Corpus 215 (198 evaluation + 17 samples), 39 linked / 176 unlinked. C: 157 FACTS, 17 unresolved, 12 no-fact, 29 parse failures; 186 parsed. Original C complete count 50 to 90 is not an accuracy claim: manual review found false no-fact termination. Paid prompt-2 extracted 33 corpus messages before account failure. Free-model assessment made 12 synthetic calls across two free models and three real-message calls; real semantic errors stopped the free corpus batch. Current exact-version report is intentionally incomplete: 50 evaluation requests complete, 200 provisional, zero numerical changes.

## Actual external-call count / usage
311 journaled external dispatches/intents: 310 completed attempts and one interrupted unknown. By model: GPT-4.1-mini 296, NVIDIA free 11, Nex free 4. No retries. Known input 268637, output 38261, total 306898 tokens. Known reported and estimated cost USD 0.1492180. 41 attempts have unknown token/cost fields, so all-attempt totals remain unknown. Free success responses report zero cost. Development inference is separate from Codex and final-submission usage.

## Files currently being changed
None after this hardening checkpoint. Preserve all code, reports, ignored operational cache and log.txt. No dataset, baseline or Phase 3A source edits.

## Known failures / limitations
P1 extraction-quality blocker: tested free models confuse financial type, scope, currency and amount meaning. Narrow synthetic smoke pass flags are not semantic certification. Strict guards reject demonstrated contradictions but cannot prove model truth or coverage. Paid configuration returned HTTP 402; user now requires free inference. Unlinked targets, unknown dates/currencies, percentage-only amendments and all image evidence remain unresolved. No final output.csv or payment optimization exists.

## Exact next action
Continue only unfinished D. Inspect evaluation/phase3b-review.md, phase3b-manual-review.md and cache audit. Strengthen message-level semantic validation/evaluation and approve a reliable free extractor with a bounded source-level smoke before any full batch. Do not chase random outputs or solved labels. Then extract only missing valid-version entries, prove unchanged zero-call reproduction, run all 250 and freeze D. NOT READY for Phase 3C until that defect is resolved.

## Reproduction commands (offline, no new model calls)
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/message_cache_audit.py
.\.venv\Scripts\python.exe code/evaluation/message_results.py --artifact evaluation/phase3b-extractions.json --skip-samples
.\.venv\Scripts\python.exe code/evaluation/evidence_inventory.py
.\.venv\Scripts\python.exe code/evaluation/semantics.py
git diff --check
git diff --exit-code HEAD -- dataset
Artifact report exits nonzero intentionally because extraction is incomplete. Full command history and model/version results: evaluation/phase3b-handoff.md. Do not run an unchanged-looking live command under a changed model/version expecting old-namespace hits.

## Checkpoint protocol
Update RESUME, run tests, diff check, verify dataset unchanged, stage explicit paths, inspect staged diff, commit. Never git add .; never commit log.txt, secrets or operational cache. Do not repeat earlier checkpoints or change financial policy.
