# Runtime checkpoint

## Current phase
Phase 3A — Evidence Contract & Reconciliation Foundation. Checkpoint C complete.

## Current branch
feat/evidence-contract

## Last known good commit
`1774f76` B; `be3cb00` A; restart `d77b78f`; frozen baseline `b04f7ad`.

## Last completed checkpoint
C: fixture-driven request integration/completeness and evidence inventory complete. 126 tests pass. All 250 evaluation requests run; 50 complete, 200 evidence-provisional. 198 have messages, 11 images, 9 both. Empty adapter changes 0/250 numeric outputs or completeness. Phase 2.6 baseline comparison unchanged.

## Last passing test command
`.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

## Last passing test count
126. Windows Python 3.12.14, standard-library unittest; no PATH changes needed.

## Accepted decisions
- Calendar-day mean variable spending, provisionally; confirmed payroll bridge.
- [D,D+90] conservative endpoint; debit before credit; candidate at daily close.
- Full payment must preserve all remaining forecast balances; prefix baseline must also be safe.
- Keep baseline recurring spending; protect/reduce/stop/minimum fields never cause automatic optional changes.
- Unsupported freelance income excluded.

## Rejected decisions
- Automatic future freelance income; disabling all variable spending.
- Sample-fitted statistical thresholds, identifiers, amounts or category discounts.

## Current unresolved questions
- Endpoint wording is ambiguous: retain [D,D+90]; day89 remains evaluation-only.
- Baseline includes supported recurring expenses; permissions/minimums do not automatically reduce spending.
- Earliest payment must preserve the remaining original forecast, not just payment-day cash.
- Statistical expense-model residuals remain intentional; do not fit them.

## Files currently being changed
forecast.py/reconcile.py typed evidence seams; evidence_integration.py; tests/test_evidence_integration.py; code/evaluation/evidence_inventory.py; inventory md/json; docs/evidence-contract.md; RESUME.md.

## Reproduction commands
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/experiments.py
.\.venv\Scripts\python.exe code/evaluation/audit.py
.\.venv\Scripts\python.exe code/evaluation/scope_audit.py
.\.venv\Scripts\python.exe code/evaluation/semantics.py
.\.venv\Scripts\python.exe code/evaluation/evidence_inventory.py
git diff --check
git diff --exit-code HEAD -- dataset
```

## Exact next action
Commit C with explicit paths, then D adversarial review: read-only first pass, fix confirmed P0/P1/P2 issues, add regression tests, rerun inventory and baseline comparison, update handoff and commit final freeze. No model extraction, no baseline tuning.

## Do-not-do list
Do not optimize plans, integrate LLM/VLM, generate output.csv, change dataset, chase request_21, introduce overrides, or begin another estimator search. Stage explicit paths only. Keep log.txt ignored and append-only. Preserve existing commits.
