# Runtime checkpoint

## Current phase
Phase 3A — Evidence Contract & Reconciliation Foundation. Checkpoint B complete.

## Current branch
feat/evidence-contract

## Last known good commit
`be3cb00` A; restart `d77b78f`; frozen baseline `b04f7ad`.

## Last completed checkpoint
B: deterministic validation, typed normalized state, exact-target replacement, conflict handling and provenance complete. 112 tests pass; all 84 frozen baseline tests unchanged. Integration has not been added yet.

## Last passing test command
`.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

## Last passing test count
112. Windows Python 3.12.14, standard-library unittest; no PATH changes needed.

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
RESUME.md; evidence.py; evidence_validation.py; evidence_state.py; evidence_reconciliation.py; docs/evidence-contract.md; tests/test_evidence_reconciliation.py.

## Reproduction commands
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/experiments.py
.\.venv\Scripts\python.exe code/evaluation/audit.py
.\.venv\Scripts\python.exe code/evaluation/scope_audit.py
.\.venv\Scripts\python.exe code/evaluation/semantics.py
git diff --check
git diff --exit-code HEAD -- dataset
```

## Exact next action
Commit B. Implement C fixture-driven forecast adapter: retain original recurrence evidence, apply normalized event/series amendments without duplicate occurrences, carry explicit credit confirmation, preserve provenance/completeness. Then dataset inventory and frozen-baseline smoke. No real evidence extraction. D adversarial review follows.

## Do-not-do list
Do not optimize plans, integrate LLM/VLM, generate output.csv, change dataset, chase request_21, introduce overrides, or begin another estimator search. Stage explicit paths only. Keep log.txt ignored and append-only. Preserve existing commits.
