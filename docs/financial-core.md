# Phase 2 financial core

Implemented scope: typed CSV inputs, indexed joins, cash-state reconciliation, supplied-rate FX, recurrence v1, a baseline cash ledger, safe amount today, earliest full-payment capacity, and diagnostics. No recommendation, ranking, spending-change plan, external model/API, or final output writer is implemented.

## Reproducible execution

Target Python 3.12 or newer. Tested on Windows with Python **3.12.14**. No third-party packages are needed; `requirements.txt` intentionally has no dependencies. pytest was not installed in the available interpreter, so tests use the standard library's `unittest` runner. No network install is necessary.

From repository root in PowerShell:

```powershell
.\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/main.py --requests sample_requests.csv --request request_21
.\.venv\Scripts\python.exe code/evaluation/main.py --save
```

The bootstrap discovers the bundled interpreter on this machine, or an installed `python` command, and creates `.venv` without pip. It accepts an explicit interpreter elsewhere:

```powershell
.\scripts\bootstrap.ps1 -PythonExecutable 'C:\path\to\python.exe'
```

No PATH modification or virtualenv activation is required. On other platforms, use `python3 -m venv --without-pip .venv`, followed by `.venv/bin/python` with the same arguments. The code locates default dataset paths relative to the source file, not the current working directory. `--dataset` accepts another directory with the challenge schemas; `--requests` selects samples or evaluation requests. The diagnostic ID is a CLI parameter, never a rule in the solver.

## Module ownership

| File | Responsibility |
|---|---|
| code/buy_or_wait/models.py | Immutable domain models, cash flows, recurring series, ledger, result |
| code/buy_or_wait/load.py | Strict schema/type/key/join checks and indexes; excludes sample labels |
| code/buy_or_wait/policy.py | Central v1 recurrence thresholds and horizon |
| code/buy_or_wait/reconcile.py | Cash-state and linked-authorization rules |
| code/buy_or_wait/fx.py | Exact settlement-date/directional conversion |
| code/buy_or_wait/recurrence.py | Conservative dated history-to-series inference |
| code/buy_or_wait/forecast.py | Project flows, resolve explicit/inferred overlap, ledger and capacity |
| code/buy_or_wait/diagnostics.py | Human-readable summaries, reasons, and full ledger |
| code/main.py | Single-request diagnostic CLI |
| code/evaluation/main.py | Isolated sample expectations and comparisons |

The loader reads both request input sets for foreign-key validation, but creates `FinanceRequest` only from its eight input columns. Neither the solver nor its models contain solved labels. No flat join multiplies cash-flow records. No source dataset is written.

## Financial policies chosen

### Horizon, snapshot, and ordering

- The horizon is **request date (day 0) through request date + 90 days, inclusive**: an opening checkpoint and 91 daily closes. This resolves an unspecified endpoint conservatively; it is not a rolling 90-day horizon for every candidate.
- Profile balance is the opening snapshot. Settled flows dated on/before request date are already in that snapshot. They inform recurrence but are never replayed. Future-dated supplied settled flows and scheduled obligations are applied on their supplied settlement dates.
- Pending debits are reserved on day 0, once, including a hold with a later settlement date. Its FX valuation still uses that settlement date. The reserve is not deducted a second time. Overdue scheduled debits are reserved on day 0 too.
- Within a day: **debits, then credits, then candidate purchase**. IDs provide a stable tie-break. Every event checkpoint is checked, so a same-day credit cannot erase an earlier essential-expense breach.
- A candidate payment occurs at daily close. Therefore today's capacity uses the minimum of all checkpoints at/after today's close, provided the entire baseline (including earlier day-0 checkpoints) is safe. If a salary settles today, it can fund a purchase after settlement. This is why the opening or pre-credit low-water mark alone is not always the correct capacity formula.
- Capacity is `min(requested_amount, max(0, suffix_minimum - minimum_balance))`, rounded **down** to cents before capping. Cents are supported even for INR/IDR. FX products are retained at Decimal precision; no rounding up makes a payment appear safe.
- If the baseline itself violates the minimum at any checkpoint, safe amount is zero and no safe full-payment date exists under that forecast. `baseline_safe=False` distinguishes this from a valid zero discretionary capacity.
- Earliest full-payment date scans daily-close suffix minima across the fixed horizon. It is independent of payment preferences and the desired completion date. The written field definition and spending-change samples support recording a baseline date after the deadline; any eventual selected plan must separately satisfy the deadline. No affordability status is inferred in this phase.

### Cash state, links, and confirmation

- Pending credits never enter available cash, even if they have a forecast settlement date or salary-like description.
- A scheduled regular salary is a confirmed future credit. Scheduled non-salary credits (bonus, commission, refund, etc.) are excluded in v1. Supported recurring salary is inferred from settled history and marked inferred, not falsely described as explicitly confirmed.
- Failed, cancelled, and unrealized rows are not replayed. A separately supplied retry remains payable. Cancelling a transaction does not automatically cancel the whole recurring service.
- Links alone do not deduplicate records. Settled reimbursements/sales can be distinct cash events. A disputed duplicate debit remains reserved without a reversal.
- A pending authorization is superseded only when a linked settled debit has the same direction, amount, and currency and the parent describes an authorization. More complex matching requires later evidence reconciliation; no generic link-based removal exists.
- Explicit future entries replace matching inferred occurrences for the same monthly cycle or interval date. Exact normalized description or a lifecycle link identifies the series. A generic confirmed salary replaces the month's inferred payroll only when there is one same-currency income series; ambiguous multiple jobs are not silently merged.
- Routine variable-category budgeting is independent of unmatched one-off pending charges. This can be conservative; the pending event itself is only reserved once. A later evidence layer should distinguish an authorization for the ordinary category purchase from an additional obligation.

### Recurrence v1

All constants are in `ForecastPolicy`. They were chosen for interpretability, not fitted to sample outputs.

- Use up to 180 days of settled history and at least three distinct observation dates.
- Group stable obligations by category, normalized description, direction, and currency. Group groceries, transport, and dining across merchant descriptions. Dining remains in the unchanged baseline; omission would imply an unauthorized spending cut.
- Recognize consecutive calendar-month observations with day variation up to three days, including month-end schedules. Recognize regular day intervals up to 35 days with up to two days' deviation.
- For recurring debit amounts, use the greater of latest amount and the nearest-rank 75th percentile. Keep flexible recurring spending in the baseline; do not apply optional reductions.
- For regular salary, require salary/payroll semantics and stable cadence. Use the minimum of the last three amounts and reject a recent max/min ratio above 1.25 or a last observation more than 1.5 expected cycles old. Explicit final-payroll history stops old salary inference for that currency; the lack of employer identifiers means this is conservative for multi-job households.
- Bonus, commission, arrears, reimbursement, windfall, internal transfer, and investment valuation/sale proceeds do not establish recurring salary. A rent paid by transfer is still an expense, not an internal transfer.
- Variable-category reserve = nearest-rank P75 daily purchase total divided by median observed spacing, rounded up to cents and charged daily. This captures an upper-typical amount while avoiding a single bulk outlier setting every future purchase size. Reserving daily avoids assuming essential spending can wait until payday. This is an interpretable heuristic, not a guaranteed bound on spending; validation against samples shows it needs revision.
- Rejected recurring income and stable-series groups are noted in the trace. Irregular freelance receipts are not assumed to recur, and a single first salary plus one scheduled paycheck does not invent subsequent payrolls.

### FX and incomplete evidence

- Convert original currency to home currency using the exact directional rate on the settlement date. Inferred foreign flows use their projected settlement dates. No inversion, interpolation, nearest-date fallback, or live lookup exists.
- Cash-flow provenance includes original amount, currency, conversion date, and exact rate. A missing rate is a named issue, not a zero-rate fallback.
- Missing amounts remain `None`. The trace lists every missing amount and every relevant unprocessed message/image. Known structured flows still produce a **provisional** ledger, useful for debugging. Omitted unknown flows can make provisional capacity optimistic; it must never be treated as an actionable complete result.
- `ForecastResult.complete` is false whenever those issues exist. This means evidence completeness, not financial correctness. A complete result is still subject to the documented v1 modeling assumptions.
- Future messages beyond the request date are not considered available evidence. Raw message text is not interpreted in this phase. No manually inspected image amount is copied into the engine.

## Diagnostics and observed sample results

`code/evaluation/main.py --save` regenerates `evaluation/phase2-summary.md` and full per-request ledgers in `evaluation/phase2-ledgers/` (ignored because they are reproducible). The report includes all 25 rows, baseline amounts/dates, expected values, evidence gaps, and low-water summaries. The diagnostic writer never creates `output.csv`.

Six samples have no unresolved message/image facts: 01, 05, 09, 13, 21, 25. Nineteen are provisional. On the six complete structured baselines, the current policy matches **0/6 safe amounts**, **3/6 earliest dates**, and **0/6 pairs** exactly. The matching dates include two absent dates. This is not a claim of prediction quality: it is a measured starting point for the next phase.

| Sample | Likely cause, supported by the ledger |
|---|---|
| 01 | Income recurrence: only a prorated first salary and one confirmed future salary are supplied. V1 includes the confirmed credit once but lacks three observations to infer later monthly salaries. Recurring rent is included. |
| 05 | Essential-spend estimator/horizon: final payroll prevents future income inference; daily reserves and recurring obligations bring the v1 balance below the minimum. |
| 09 | Income recurrence: irregular freelance/contract receipts are excluded from recurring salary. No confirmed future invoice is supplied. Whether a conservative recurring freelance allowance is intended needs resolution. |
| 13 | Variable spending and timing: confirmed/inferred salary is present without double counting, but daily category reserves and upper-typical bills delay capacity relative to the sample. |
| 21 | Variable spending/timing: USD 1,535.26 versus USD 1,543.35 (USD 8.09 lower); earliest date matches. No optional stop/reduce was applied. |
| 25 | Essential-spend timing: day-0-through-payday daily reservations breach the minimum before payroll. Dated USD→IDR rates resolve successfully; no FX fallback is involved. |

These are likely causes, not quantified causal decompositions. No repeated threshold tuning was performed. The first diagnostic run did reveal an implementation bug—an overly broad “transfer” exclusion omitted rent paid by transfer—which was fixed with a synthetic regression test. That correctness fix was not sample-ID logic.

## Before Phase 3

1. Establish supported recurrence for first-pay and variable freelance income, and improve expense grouping without merging separate obligations.
2. Revisit the daily P75 expense estimator and same-day/horizon assumptions using explicit ledger differences, not arbitrary per-case constants.
3. Add validated fact overrides with scope/effective date for messages and images; require evidence completeness before plan selection. Resolve pending-variable overlap and multi-job termination scope.
4. Only then add payment plans, preferences, deadline validation, ranking, and independent plan replay. Keep raw sample expectations in evaluation only.

No external model calls were made by the engine. The final-run usage report remains untouched because this phase did not produce a final full-dataset prediction run.
