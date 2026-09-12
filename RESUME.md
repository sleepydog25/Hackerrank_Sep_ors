# Runtime checkpoint

## Current phase
Phase 2.6 — Forecast Semantics Audit; Checkpoint A complete.

## Current branch
feat/forecast-semantics

## Last known good commit
`a586391` restart checkpoint; accepted production baseline `226adac`. This file's next commit is Checkpoint A.

## Last completed checkpoint
Checkpoint A: semantics report and dataset-wide scope inventory complete, 70 tests pass, dataset unchanged. No production change.

## Last passing test command
`.\.venv\Scripts\python.exe -m unittest discover -s tests -q`

## Last passing test count
70. Windows Python 3.12.14, standard-library unittest; no PATH changes needed.

## Accepted decisions
- Calendar-day mean variable spending, provisionally; confirmed payroll bridge.
- Debit before credit; candidate at daily close unless the specification disproves it.
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
RESUME.md; evaluation/phase2_6-semantics-audit.md; code/evaluation/scope_audit.py; evaluation/phase2_6-scope.md/json.

## Reproduction commands
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/experiments.py
.\.venv\Scripts\python.exe code/evaluation/audit.py
.\.venv\Scripts\python.exe code/evaluation/scope_audit.py
git diff --check
git diff --exit-code HEAD -- dataset
```

## Exact next action
Commit Checkpoint A. Then add boundary, profile/minimum and future-payment semantic tests for Checkpoint B; no production behavior change is justified. C: reproduce metrics and 250-request impact. D: adversarial review and final checkpoint.

## Do-not-do list
Do not optimize plans, integrate LLM/VLM, generate output.csv, change dataset, chase request_21, introduce overrides, or begin another estimator search. Stage explicit paths only. Keep log.txt ignored and append-only. Preserve existing commits.
