# Runtime checkpoint

## Current phase
Phase 3A — Evidence Contract & Reconciliation Foundation. Starting point verified.

## Current branch
feat/evidence-contract

## Last known good commit
`b04f7ad` completed Phase 2.6. 84 tests verified passing; initial tree clean.

## Last completed checkpoint
Phase 3A restart state. A schema, B validation/reconciliation, C fixture integration/inventory, D adversarial review remain.

## Last passing test command
`.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

## Last passing test count
84. Windows Python 3.12.14, standard-library unittest; no PATH changes needed.

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
RESUME.md only; deterministic core frozen after Phase 2.6.

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
Commit restart state; implement Checkpoint A typed evidence schema, provenance and tests, then commit before reconciliation. New request is Phase 3A only: no model extractor. Keep candidate, validation and normalized amendment distinct. Scope and certainty must govern interpretation; confidence never authorizes money.

## Do-not-do list
Do not optimize plans, integrate LLM/VLM, generate output.csv, change dataset, chase request_21, introduce overrides, or begin another estimator search. Stage explicit paths only. Keep log.txt ignored and append-only. Preserve existing commits.
