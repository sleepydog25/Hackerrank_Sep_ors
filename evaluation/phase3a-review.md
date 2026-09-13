# Phase 3A adversarial review and final handoff

The first pass inspected the committed A/B/C diff without editing code. C (`cda4e05`) passed 126 tests. The resumed run preserved its implementation and inventory; only Checkpoint D remained. No baseline estimator experiment was repeated.

## Confirmed findings and fixes

No P0 found. All confirmed P1/P2 findings below are fixed and regression-tested in `tests/test_evidence_review.py`. Locations refer to functions to remain stable as line numbers change.

| Priority | C behavior / trigger | D correction |
|---|---|---|
| P1 | `forecast.forecast`: historical ongoing rent amendment changed projections but left an explicit upcoming bill at the old amount | Apply scoped amount to explicit and inferred occurrences, once each, retaining dates/identity/FX/provenance. Synthetic three-payment rent total is 450 rather than 400. |
| P1 | Series rules attached to different historical event IDs could choose different amounts for one series by iteration order | `evidence_scope.bind_series_amendments` binds original history and atomically reverts conflicting facts; all remain UNRESOLVED. A separately amended next-pay value cannot be overwritten either. |
| P1 | Single-payroll-series fallback could attach final-pay evidence for a different named employer | Named payroll sources must agree; ambiguous/unsupported binding reverts the fact. Other employer's inferred continuation survives. |
| P1 | `evidence_validation.validate` allowed event/next-only termination or inappropriate reschedule scope | Termination requires ongoing/from-date scope; reschedule requires event/next scope. Explicit confirmed final pay remains separate from inferred continuation. |
| P1 | Cancellation always won against a conflicting explicit settlement | `reconcile_evidence` keeps contradictions unresolved unless known-source explicit precedence resolves them. No blanket cancellation of settled cash. |
| P1 | Unlinked confirmed-but-unsettled past invoice could become day-zero cash | Require settlement for past unlinked income; no addition to opening cash. |
| P2 | Refund/sale/invoice semantic labels could target an unrelated payroll/lifecycle row | Financial type, direction and salary-category compatibility validated before amendment. |
| P2 | Any normalized state suppressed missing-amount issues for pre-existing cancelled records | Exemption now requires an actual accepted cancellation; empty adapter preserves completeness. |
| P2 | Truthy string `exhaustive='false'` could certify coverage | Non-boolean coverage values fail explicitly. |
| P2 | JSON duplicate amount keys silently used the last value; due date absent from conflict signature | Duplicate keys rejected; due-date differences participate in conflict detection. |

Additional invariant regressions cover until-date limits, pending debit reservation once, gross pay rejected despite high confidence, and historical receipt clarification causing neither cash replay nor unsupported recurrence. Existing tests already cover source/user/request ownership, pending credits, valuation, hypothetical/conditional facts, currency and amount validation, delay identity, cancellation scope, invoice balance ambiguity, provenance, and full-payment capacity/replay invariants.

## Final architecture

`evidence.py` defines sources, candidate facts, amount meanings, certainty, temporal scope, decisions, batches and strict Decimal/date transport. `evidence_validation.py` validates context and semantics; ACCEPTED means eligible for reconciliation, not available cash. `evidence_reconciliation.py` produces immutable event replacements and scoped directives. `evidence_scope.py` rejects ambiguous recurring bindings and conflicts. `evidence_integration.py` computes source completeness and calls the existing forecast through its typed state interface. `evidence_state.py` carries before/after records and source/fact provenance. The financial engine alone computes balances, FX, low-water marks and capacity.

Compatible facts coalesce; explicit cancellation overrides a prior schedule; a newer explicit amendment supersedes only with the same known publisher. Unknown publisher, tied timestamps, incompatible source facts and unsupported scope remain provisional. Unlinked one-off cash requires a stable obligation reference, explicit date/currency/category and unconditional confirmation; pending CSV credits remain excluded without settlement. Full historical settlement is opening-snapshot evidence, never replayed cash. Confidence and source prose never control arithmetic.

The full contract and machine-readable reason enums are in `docs/evidence-contract.md` and `code/buy_or_wait/evidence.py`. Rejected non-actionable facts can resolve a source; unresolved facts, partial source coverage, missing required amounts/rates and ambiguous scope keep `complete=False`. Numeric provisional forecasts are diagnostics only.

## Checkpoints and validation

| Checkpoint | Commit | Tests |
|---|---|---:|
| A: contract | `be3cb00` | 92 |
| B: validation/reconciliation | `1774f76` | 112 |
| C: integration/inventory | `cda4e05` | 126 |
| D: review/freeze | Commit containing this report; `git log -1 --format=%H -- evaluation/phase3a-review.md` | 143 |

The phase adds 59 tests to the frozen 84-test baseline, including 17 D regression tests. All 143 pass. No solved sample identifiers or expected numerical outputs appear in evidence production code. All prior synthetic financial invariants remain passing. No policy constants changed.

Metadata inventory: 250 evaluation requests, 198 with messages, 11 images, 9 both, 41 linked; 50 complete and 200 provisional solely due to uninterpreted evidence/evidence-backed missing amounts. Samples: 25 requests, 17 with messages, 5 images, 3 both; 6 complete and 19 provisional. There are 215 message rows and 16 image rows overall; 39 messages and all 16 images map events. All 16 missing event amounts have evidence. Details and source distributions are in `phase3a-evidence-inventory.md/json`.

All 275 requests pass empty-adapter regression for amount, earliest date, baseline safety and completeness. The isolated historical comparison across 250 evaluation requests reports **0 safe-amount changes, 0 earliest-date changes, 0 baseline-safety changes**, with 50 complete. Phase 2.6 sample metrics are unchanged (amount 1/6 exact, earliest 4/6 exact); no fit-oriented adjustment was made.

## Exact reproduction and checkpoint commands

Executed from repository root using the existing Windows Python 3.12.14 environment:

```powershell
git status --short
git log --oneline -10
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe code/evaluation/evidence_inventory.py
.\.venv\Scripts\python.exe code/evaluation/semantics.py
git diff --check
git diff --exit-code HEAD -- dataset
git diff --exit-code b04f7ad -- dataset
git ls-files --others --exclude-standard -- dataset
git diff --stat
git add README.md RESUME.md code/buy_or_wait/evidence.py code/buy_or_wait/evidence_integration.py code/buy_or_wait/evidence_reconciliation.py code/buy_or_wait/evidence_validation.py code/buy_or_wait/evidence_scope.py code/buy_or_wait/forecast.py docs/evidence-contract.md tests/test_evidence_review.py evaluation/phase3a-review.md
git diff --cached --check
git diff --cached --stat
git diff --cached
git commit -m "fix: harden evidence reconciliation and freeze Phase 3A"
git status --short
git diff --stat
```

Checkpoint D stages only these explicit paths. `RESUME.md` is updated before testing/staging. Dataset checks against HEAD and the frozen baseline return no differences; no new dataset files. After commit, status and working-tree diff are empty. Root `output.csv` is absent. `log.txt` remains ignored and append-only. No external AI, credentials, network calls, OCR or plan optimizer was added.

## Deliberately deferred limitations

- Real messages/images remain uninterpreted; synthetic candidates do not substitute for real extraction.
- Image observation time is absent from metadata. Generic employer/bank source categories cannot establish publisher identity for supersession.
- Complex bill tiers, partial-paid arithmetic without explicit outstanding balance, cross-currency amendments and unsupported recurring targets remain unresolved. The schema preserves amount/date meanings for later work.
- Cross-target overlapping amendments have no guessed precedence; the affected facts are rolled back and provisional. An extractor cannot declare a request safe simply because it produced valid JSON.
- Baseline statistical residuals and endpoint uncertainty are retained from Phase 2.6.

**READY FOR PHASE 3B — Message Evidence Extraction.** No remaining confirmed architectural blocker in this boundary. The exact next action, after user authorization, is a message-only candidate/batch adapter with trusted metadata, unresolved outcomes, caching and usage accounting. Keep validation, reconciliation and finance deterministic; do not begin VLM extraction or payment-plan optimization.
