# Runtime checkpoint

## Current phase
Phase 2.6 complete — Forecast Semantics Audit. Checkpoint D is the commit containing this final state.

## Current branch
feat/forecast-semantics

## Last known good commit
Checkpoint C `32f1b05`; B `8c5dfc7`; A `3130e43`; restart `a586391`; accepted Phase 2.5 `226adac`. Final good checkpoint D: resolve with `git log -1 --format=%H -- evaluation/phase2_6-review.md` (cannot embed a commit's own hash inside itself).

## Last completed checkpoint
Checkpoint D: semantics, tests, reproducible results and adversarial review complete. 84 tests pass; 250 requests run without exceptions (50 complete, 200 provisional). 0/250 changes in amount/date/safety. Six-case metrics unchanged: 1/6 amounts, 4/6 dates, normalized MAE 18.8738%. No production changes or unresolved P0/P1/P2 finding.

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
None after final commit. Phase 2.6 files are committed; source dataset, production core, virtualenv and ignored transcript preserved.

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
READY FOR PHASE 3 — Evidence Normalization Layer. Wait for the user to authorize Phase 3; then implement validated, scoped evidence normalization. Do not restart baseline calibration. Reproduce Phase 2.6 with the two scope_audit.py / semantics.py commands above; Git history containing 226adac is required. Intentional residuals: 05 expense budget, 09 endpoint, 13 future expense shortfall, 21 small estimator difference, 25 pre-payroll budget. Details: evaluation/phase2_6-results.md.

## Do-not-do list
Do not optimize plans, integrate LLM/VLM, generate output.csv, change dataset, chase request_21, introduce overrides, or begin another estimator search. Stage explicit paths only. Keep log.txt ignored and append-only. Preserve existing commits.
