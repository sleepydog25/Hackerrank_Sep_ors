# Runtime checkpoint

## Current phase
Phase 2.6 — Forecast Semantics Audit; accepted Phase 2.5 verified.

## Current branch
main; next create `feat/forecast-semantics`.

## Last known good commit
`226adac` (user's existing complete Phase 2.5 commit). Do not duplicate/amend it.

## Last completed checkpoint
Phase 2.5 acceptance: clean tree, 70 tests pass, dataset unchanged. This commit adds restart state only.

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
- Is the horizon [D,D+89] or [D,D+90]?
- Which expenses belong in baseline reserves, versus optional spending-change plans?
- What remaining interval must stay safe for earliest full payment?

## Files currently being changed
Only RESUME.md. Phase 2.5 is already fully tracked in 226adac.

## Reproduction commands
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/experiments.py
.\.venv\Scripts\python.exe code/evaluation/audit.py
git diff --check
git diff --exit-code HEAD -- dataset
```

## Exact next action
Commit this restart checkpoint, create `feat/forecast-semantics`, write and commit Checkpoint A semantics audit before any production changes. Read the Phase 2.5 reports for quantitative context. Checkpoints B (justified rules/tests), C (results), D (adversarial review) remain.

## Do-not-do list
Do not optimize plans, integrate LLM/VLM, generate output.csv, change dataset, chase request_21, introduce overrides, or begin another estimator search. Stage explicit paths only. Keep log.txt ignored and append-only. Preserve existing commits.
