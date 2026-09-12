# Phase 2.5 execution record

Run from repository root in PowerShell, using the existing Python 3.12.14 virtualenv. No dependency installation, activation, PATH change, model call, or live data access was required.

Exact reproducible validation commands executed (some repeated during regression fixes):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/experiments.py
.\.venv\Scripts\python.exe code/evaluation/audit.py
.\.venv\Scripts\python.exe code/main.py --requests sample_requests.csv --request request_21 --full
git diff --check
git diff --exit-code HEAD -- dataset
git status --short
git diff --stat
```

Pre-change verification reproduced all six safe amounts, earliest dates and low-water marks in `phase2_5-before.json`, which agree with the historical Phase 2 summary. All 43 original tests passed before policy changes. Each complete legacy ledger was inspected and its rows arithmetically reconciled. The resumed run first inspected `git diff`, preserved the existing changes, and reran those tests before extending coverage.

The experiment command now asserts that reproduction on every run and checks **132 case-policy pairs** (22 configurations × six cases) against an independent cent-level binary-search payment replay. It regenerates complete before/after ledgers under `evaluation/phase2_5-ledgers/` (ignored, reproducible), raw comparisons in `phase2_5-details.json`, and the report. Human findings are maintained in `phase2_5-findings.md` and included in the generated report.

Final suite: **70 tests pass**, comprising the retained 43 tests and 27 new financial-behavior tests. One invariant test checks 100 deterministic synthetic ledgers under both candidate orderings, including baseline breaches, future obligations, inflows, and requested-amount caps. No synthetic test uses sample identifiers or expected outputs. The first regression run caught an incorrectly constructed authorization fixture; it was corrected to exercise actual authorization reconciliation. The final run passes without skips.

The read-only audit verifies **9,274 sample ledger checkpoints** across all 25 samples, confirms all six complete users have zero mapped messages/images, inventories pending variable charges and grouping effects, and smoke-tests **250 evaluation requests**. `git diff --exit-code HEAD -- dataset` and a clean dataset status confirm tracked and untracked dataset state is unchanged. No root `output.csv` exists. `log.txt` is append-only and ignored. The final full-dataset model usage report is not relabeled as complete: no final prediction run or external AI calls occurred.

`git diff --check` passes. Ordinary `git diff --stat` lists modifications to tracked files only; newly created modules, tests and reports remain untracked until the user stages them. The final handoff reports both, without staging or reverting user work.
