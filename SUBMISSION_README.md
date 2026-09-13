# Buy or Wait? — deterministic submission

Requires Python 3.12 or newer; standard library only. No installation, API key,
network access, or model cache is required.

Place the organizer-provided `dataset/` alongside `code/`, then run:

```text
python code/main.py --dataset dataset --output output.csv
python code/main.py --dataset dataset --output output.csv --validate-only
```

The first command writes exactly 250 evaluation rows and validates them. Each
request is an independent financial scenario. All money uses Decimal and the
user's home currency; fixed supplied FX rates are used by settlement date.

To regenerate the usage report and reproducible archive, run:

```text
python code/finalize_submission.py --dataset dataset
```

In the development checkout, `scripts/finalize-submission.ps1` also requires
the separately preserved `log.txt`. The archive intentionally excludes the log.
The release command stages and validates output, scans and inspects the ZIP,
executes the archived solution against the supplied dataset, and requires
byte-identical predictions before replacing root artifacts.

The frozen 90-day financial engine handles normalization, cash-state
reconciliation, supported recurrence, essential spending, pending reserves and
baseline capacity. The new recommendation layer constructs full, wait, partial,
and supplied installment candidates. A separate validator checks the entire
combined payment schedule against every financial checkpoint, including events
after the final payment. Payments occur after daily cash events. Deterministic
ranking follows deadline, no changes, total cost, earlier start, fewer payments,
and option identifier.

Installment duration is conservatively counted as `number_of_payments *
payment_frequency_days`, including the first payment period, with 30 days per
permitted month. No earlier planner interpretation existed. Supplied dates and
amounts are never adjusted. Financing fees count toward total payment cost.

S0 limitations: optional spending changes and all unvalidated message/image
extraction are disabled. No experimental cache is read. Missing cash amounts or
FX rates prevent certification of a plan. The baseline capacity fields retain
the frozen structured-data calculation; unresolved evidence is disclosed in
explanations and may affect accuracy. Expense changes are rejected rather than
applied to the frozen baseline without a verified scenario adapter.

`evaluation/usage_report.md` describes only the run that generated `output.csv`:
zero model calls, tokens and cost. `evaluation/s0-release.md` records validation
and limitations. Development experiments are not final-run inference.

For a ledger: `python code/main.py --request REQUEST_ID --full`.
In the development checkout, run tests with
`python -m unittest discover -s tests -v`.
