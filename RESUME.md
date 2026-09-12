# Runtime checkpoint

## Current phase
Phase 2.6 — Forecast Semantics Audit; Checkpoint C complete.

## Current branch
feat/forecast-semantics

## Last known good commit
`8c5dfc7` Checkpoint B; A `3130e43`; restart `a586391`; accepted baseline `226adac`.

## Last completed checkpoint
Checkpoint C: metrics and dataset-wide impact reproduced against isolated code from 226adac. 84 tests pass; 250 requests run without exceptions (50 complete, 200 provisional). 0/250 changes in amount/date/safety. Six-case metrics unchanged: 1/6 amounts, 4/6 dates, normalized MAE 18.8738%.

## Last passing test command
`.\.venv\Scripts\python.exe -m unittest discover -s tests -q`

## Last passing test count
84. Windows Python 3.12.14, standard-library unittest; no PATH changes needed.

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
RESUME.md; code/evaluation/semantics.py; evaluation/phase2_6-results.md and phase2_6-details.json. Production unchanged.

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
Commit Checkpoint C; exact next action: adversarial review (read-only first pass), then fix confirmed P0/P1/P2 findings, rerun tests/diagnostics, and commit D. Preserve five amount residuals; do not chase labels.

## Do-not-do list
Do not optimize plans, integrate LLM/VLM, generate output.csv, change dataset, chase request_21, introduce overrides, or begin another estimator search. Stage explicit paths only. Keep log.txt ignored and append-only. Preserve existing commits.
