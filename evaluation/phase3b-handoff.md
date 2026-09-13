# Phase 3B checkpoint handoff

**NOT READY FOR PHASE 3C.** Infrastructure and offline hardening work, but the tested free model is not reliable enough for the full message batch. No image extraction, payment optimization, final output or dataset edits were made.

## Checkpoints and versions

A 4424afe; B 29d9b4a; explicit OpenRouter B follow-up c751d23; C 93ef28f. D is the commit containing this handoff, titled `fix: checkpoint message hardening and free-model findings`; D final freeze remains incomplete. Frozen Phase 3A 7fc459e and baseline b04f7ad remain unchanged.

Current schema message-2, prompt message-3, extractor message-4. Configured OpenRouter model: nvidia/nemotron-3-super-120b-a12b:free, pinned nvidia, reasoning disabled, no fallback, zero-price ceiling. User explicitly requested free inference after paid-model HTTP 402. Paid OpenAI and free Nex experiments remain recorded separately.

## What was actually run

Corpus: 215 messages (198 evaluation, 17 samples); 39 linked, 176 unlinked; English/Indonesian; all before requests; no empty or duplicate texts.

| Run | Result |
|---|---|
| C, GPT-4.1-mini, all versions message-1 | 215 calls; 157 FACTS, 17 unresolved, 12 no-fact, 29 parse failures |
| Immediate unchanged C rerun | 215/215 cache hits; 0 calls, tokens and incremental USD |
| C evaluation integration | 250 execute; complete 50 to 90, provisional 200 to 160; zero numerical changes |
| C validation, evaluation cohort | 0 accepted, 41 rejected, 140 unresolved; missing link dominates |
| C message-relevant samples | 17 cases; 1 exact safe amount, 11 exact earliest dates; no numerical changes, no tuning |
| Paid prompt-2 corpus | 33 parsed, then account errors; stopped; one interrupted attempt retained as unknown |
| Free-model assessment | NVIDIA 8 synthetic + 3 real calls; Nex 4 synthetic calls; no paid fallback |
| Final contract | No compatible completed real cache entries yet; old entries preserved, not relabeled |
| Final offline integration | All 250 execute; 50 complete, 200 provisional; baseline unchanged |

C completeness improvement is **not** validated accuracy: manual review found false NO_FACT termination and other semantic defects. The original C metrics and sample details are preserved in phase3b-checkpoint-c.json. Current phase3b-message-results.json is explicitly incomplete; it does not substitute old-version facts. The last stricter parser invalidated the three free real-message entries, with zero subsequent calls. Offline re-parsing rejects the demonstrated gross-pay/receipt contradiction without re-calling the model.

## Development application usage

| Actual model | External dispatches/intents | Known input | Known output | Known total | Known reported USD |
|---|---:|---:|---:|---:|---:|
| openai/gpt-4.1-mini | 296 | 253841 | 31313 | 285154 | 0.1492180 |
| nvidia/nemotron-3-super-120b-a12b:free | 11 | 10934 | 2096 | 13030 | 0 |
| nex-agi/nex-n2.5-pro:free | 4 | 3862 | 4852 | 8714 | 0 |
| Total | 311 | 268637 | 38261 | 306898 | 0.1492180 |

There are 310 completed external attempts and one interrupted dispatch intent; 41 attempts have unknown token/cost fields. Therefore final all-attempt token and cost totals are **unknown**, not the known subtotals above. No retries occurred. Free success responses report zero cost; an error with unavailable usage is not falsely reported as a known free success. These are application development calls, not Codex tokens or the future final submission run.

## Engineering changes and tests

Closed DTO/schema to Phase 3A candidates; trusted source attachment; temporal context gates; bounded Decimal/date parsing; untrusted text isolation; transactional SQLite cache and usage intent journal; provider/model/upstream/version identity; strict failures; explicit account-error stop; selective refresh; cross-field contradiction guards; cache/history audits and sanitized offline report replay. No model directly changes money. Tests total **210**, all passing, up from 143 frozen Phase 3A tests.

Regression additions cover termination with no amount, unspecified net/gross, distinct due/payment dates, pending secondary facts, malicious currency override, incompatible lifecycle/gross labels, zero-price pinned routing, global-refresh rejection, provider-account-error stop and unknown in-flight cache inspection. See phase3b-review.md for findings and phase3b-manual-review.md for source-level assessments. Free-model narrow smoke checks do not establish full extraction quality.

## Exact reproduction commands

Offline, no credentials or model calls:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/message_cache_audit.py
.\.venv\Scripts\python.exe code/evaluation/message_results.py --artifact evaluation/phase3b-extractions.json --skip-samples
.\.venv\Scripts\python.exe code/evaluation/evidence_inventory.py
.\.venv\Scripts\python.exe code/evaluation/semantics.py
git diff --check
git diff --exit-code HEAD -- dataset
```

The artifact reproduction exits nonzero intentionally because final-version extraction is incomplete. The local cache audit requires the preserved operational cache. It never calls a model. The artifact replay needs no operational cache/credential and reproduces the explicit incomplete state.

Commands actually used for real inference and cached checks, with configuration/version changes documented above:

```powershell
.\scripts\message-run.ps1 extract --limit 3
.\scripts\message-run.ps1 extract
.\scripts\message-run.ps1 extract
.\scripts\message-run.ps1 results --skip-samples
.\scripts\message-run.ps1 results
.\scripts\message-run.ps1 adversarial
.\scripts\message-run.ps1 adversarial --cache-only
.\scripts\message-run.ps1 extract --message-id message_147
```

Do not rerun live commands merely to reproduce reports. Current versions/model intentionally differ from C; a new full run would require new keys. The 215-hit C proof is in phase3b-cache-proof.json, not a claim of current-version coverage. No successful cached extraction was repeated unchanged. Cache audit lists the retained unknown attempt key; do not silently release or replay it.

## Exact next action

Continue D from this checkpoint. Inspect preserved failed free-model source checks and add stronger message-level semantic validation/evaluation before selecting or approving another free extractor. Keep the user's free-model preference; do not switch back to paid inference automatically. Run a bounded synthetic and real-source smoke before any new full batch. Then process only missing valid-version keys, prove an unchanged zero-call rerun, run all 250, complete review and freeze D. Do not proceed to Phase 3C yet.
