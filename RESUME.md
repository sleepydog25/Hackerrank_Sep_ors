# Runtime checkpoint

## Current phase
Phase 3A — Evidence Contract & Reconciliation Foundation. Checkpoint A complete.

## Current branch
feat/evidence-contract

## Last known good commit
`d77b78f` restart; frozen baseline `b04f7ad`.

## Last completed checkpoint
A: typed evidence schema, provenance, certainty/scope/amount labels and strict JSON transport complete. 92 tests pass; dataset unchanged. No reconciliation yet.

## Last passing test command
`.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

## Last passing test count
92. Windows Python 3.12.14, standard-library unittest; no PATH changes needed.

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
RESUME.md; evidence.py; docs/evidence-contract.md; tests/test_evidence.py.

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
Commit A, then implement B deterministic validation and reconciliation. Validate canonical source identity, semantic meaning, certainty, scope and dates; conflict may remain unresolved. Only normalized amendments may feed the frozen financial engine. C fixture integration/inventory and D review remain.

## Do-not-do list
Do not optimize plans, integrate LLM/VLM, generate output.csv, change dataset, chase request_21, introduce overrides, or begin another estimator search. Stage explicit paths only. Keep log.txt ignored and append-only. Preserve existing commits.
