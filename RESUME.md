# Runtime checkpoint

## Current phase
Phase 3A — Evidence Contract & Reconciliation Foundation complete. Checkpoint D final freeze.

## Current branch
`feat/evidence-contract`

## Last known good commit
Checkpoint D is the commit containing this version of RESUME.md, titled `fix: harden evidence reconciliation and freeze Phase 3A`. Resolve its hash with `git log -1 --format=%H -- RESUME.md`; verify its title and tests before trusting it. A document cannot embed its own commit hash.

Prior verified checkpoints: C `cda4e05`, B `1774f76`, A `be3cb00`, restart `d77b78f`. Frozen baseline `b04f7ad` (Phase 2.6), accepted Phase 2.5 `226adac`.

## Last completed checkpoint
D: read-only adversarial first pass, confirmed P1/P2 integration fixes, 17 new regression tests, full 143-test suite, metadata inventory, 250-request frozen-baseline comparison, dataset and diff checks. See `evaluation/phase3a-review.md`.

## Last passing test command
`.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

## Last passing test count
143. Windows Python 3.12.14; standard-library unittest, no PATH changes or external services.

## Final evidence contract
- EvidenceSource -> EvidenceCandidate -> deterministic validation -> ValidatedEvidenceFact -> normalized amendments -> deterministic forecast.
- ACCEPTED / REJECTED / UNRESOLVED and typed reason codes; parsing/confidence never authorize money.
- Exact source ownership/link/date/currency/amount semantics; unknown facts are not repaired.
- Atomic event amendments; scope binding to supported original history; explicit/inferred occurrences share accepted ongoing amounts.
- Compatible facts coalesce; scoped cancellation, known-publisher newer amendments, unresolved contradictions. Conflicting series amendments revert affected facts.
- Provenance retained in decisions, before/after amendments and ledger reasons.
- Complete only with exhaustive source coverage and no unresolved facts, missing amounts/rates or scope issues. Rejected non-actionable evidence can be resolved.

## Frozen financial policies
- Calendar-day mean variable spending; confirmed payroll bridge; unsupported freelance income excluded.
- [D,D+90], debit -> credit -> candidate at daily close.
- Full payment preserves the remaining forecast; unsafe prefix cannot be repaired by later salary.
- No automatic optional spending reductions/stops. No baseline tuning in Phase 3A.

## Reproduction and inventory results
250 evaluation requests: 198 with messages, 11 images, 9 both, 41 with linked evidence; 50 complete / 200 provisional solely from uninterpreted evidence or evidence-backed missing amounts.
25 samples: 17 with messages, 5 images, 3 both; 6 complete / 19 provisional.
All 275 empty-adapter comparisons preserve amount, earliest date, safety and completeness. All 250 frozen-baseline comparisons have zero numeric/date/safety changes. Real evidence remains uninterpreted.

## Files currently being changed
None after the Checkpoint D commit. If interrupted before commit, preserve and inspect the explicit D edits: evidence.py, evidence_validation.py, evidence_reconciliation.py, evidence_integration.py, evidence_scope.py, forecast.py, test_evidence_review.py, README.md, docs/evidence-contract.md, evaluation/phase3a-review.md and this file. Do not repeat A/B/C.

## Exact reproduction commands
From repository root:
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/evidence_inventory.py
.\.venv\Scripts\python.exe code/evaluation/semantics.py
git diff --check
git diff --exit-code HEAD -- dataset
git diff --exit-code b04f7ad -- dataset
git status --short
git diff --stat
```
If the environment is absent, run `.\scripts\bootstrap.ps1` first. The historical comparison requires Git history containing `226adac`; the runtime and tests do not.

## Known limitations
No real message/image extraction yet. Image metadata lacks observation time; source categories are not trusted publisher identity. Complex date-tiered bills, partial payments without explicit outstanding balance, cross-currency amendments, ambiguous recurrence and overlapping cross-target amendments remain unresolved. A provisional forecast's numbers are diagnostic, not a final recommendation. Statistical baseline residuals and the conservative endpoint are intentionally unchanged.

## Exact next action
READY FOR PHASE 3B — Message Evidence Extraction. Wait for user authorization for that phase. Then reread AGENTS.md, problem_statement.md, this file and docs/evidence-contract.md; verify the D commit and rerun the recorded tests. Build a message-only extraction adapter targeting EvidenceCandidate/EvidenceBatch with trusted dataset provenance, explicit unresolved outcomes, caching and usage accounting; keep financial validation/reconciliation deterministic. Do not begin image extraction or payment-plan optimization under Phase 3B without scope authorization.

## Do-not-do list
No external AI in Phase 3A, no final output.csv, no dataset changes, no solved-output leakage or request-specific branches, no estimator tuning, no plan ranking. Never use git add .; stage explicit paths. Keep log.txt ignored and append-only.
