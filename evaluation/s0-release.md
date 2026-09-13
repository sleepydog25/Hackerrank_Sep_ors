# Emergency deterministic submission release

Starting checkpoint: `12ba13b`, branch `feat/message-extraction`.
Frozen financial baseline `b04f7ad` and Phase 3A `7fc459e` are reused unchanged.

The new orchestration builds full, wait, partial and exact supplied installment
plans, independently validates cumulative payments across the entire baseline
ledger, applies the official deterministic ranking and writes the official CSV.
No external model inference or cache reads occur in the final run.

Validation: 230 unit tests pass (210 existing plus 20 focused submission tests).
The complete deterministic pipeline produces 250 unique evaluation rows with
exact column order. Read-back validation checks coverage, finite Decimal bounds,
baseline dates, method/status contracts, chronology, full combined-plan safety,
offer schedules and fees, preferences, deadline and ranking. Spending changes
are disabled and any supplied change is rejected. Dataset diff and whitespace
checks pass.

The release builder inspects ZIP manifest/CRC, scans content for common credential
formats, excludes dataset/cache/credentials/log, and runs the archived code in a
temporary directory to prove byte-identical output before replacing artifacts.
Archives use fixed timestamps and sorted members for reproducibility.

## Post-implementation sample metrics

25 solved samples evaluated only after implementation; no request-specific or
user-specific policy and no tuning to individual samples.

| Field | Exact matches |
|---|---:|
| Safe amount | 2 / 25 |
| Affordability status | 10 / 25 |
| Recommended method | 10 / 25 |
| Payment plan (dates and Decimal amounts) | 10 / 25 |
| Earliest full-payment date | 15 / 25 |
| Spending changes | 22 / 25 |

These are accuracy limitations, not claims of hidden-test performance. Financial
policies remain frozen. Unvalidated message/image extraction is disabled;
unresolved evidence can make capacity provisional. Unknown cash amounts/FX
prevent a certified plan. Optional spending changes are omitted because the
frozen engine does not expose a verified current-obligation scenario adapter,
especially for variable-category budgets and explicit/inferred replacements.
The baseline safe amount is always calculated before any optional change.

Installment maximum duration had no existing recommendation implementation.
S0 conservatively counts all supplied periods, including the first, against
`max_installment_months * 30` days. It never adjusts a supplied schedule.

Reproduce in the checkout:
`powershell -ExecutionPolicy Bypass -File scripts/finalize-submission.ps1`

Portable reproduction: `python code/finalize_submission.py --dataset dataset`.
Submit root `output.csv`, root `code.zip`, and the separately preserved root
`log.txt` as the chat transcript. Usage in the archive is tied to the output hash
and reports zero model calls/tokens/cost for this final strategy.
