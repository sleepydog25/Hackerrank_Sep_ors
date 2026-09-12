# Runtime checkpoint

## Current phase
Phase 2.6 — Forecast Semantics Audit; Checkpoint B complete.

## Current branch
feat/forecast-semantics

## Last known good commit
`3130e43` Checkpoint A; restart `a586391`; accepted production baseline `226adac`.

## Last completed checkpoint
Checkpoint B: no production behavior change justified. Added 14 semantic tests; 84 tests pass. All 132 Phase 2.5 case-policy direct/replay checks pass. Dataset unchanged.

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
RESUME.md and tests/test_semantics.py; production unchanged.

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
Commit Checkpoint B test coverage. Next C: add reproducible six-case metrics and all-250 comparison against immutable Phase 2.5 commit, then adversarial review for D. Existing five amount residuals are preserved.

## Do-not-do list
Do not optimize plans, integrate LLM/VLM, generate output.csv, change dataset, chase request_21, introduce overrides, or begin another estimator search. Stage explicit paths only. Keep log.txt ignored and append-only. Preserve existing commits.
