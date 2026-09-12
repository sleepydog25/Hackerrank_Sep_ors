# Phase 2.6 results

Production semantics retained after contract audit. Old core is executed from immutable Git commit `226adac` in an isolated temporary directory; current core executes in a separate process. No expected sample fields enter either core. All temporary extracted files are removed automatically.

| Phase | Amount exact | MAE (mixed currency) | Median AE | Normalized MAE | Date exact | False present/absent | Baseline safety agreement |
|---|---:|---:|---:|---:|---:|---|---:|
| phase2 | 0/6 | 241126.28 | 484.78 | 35.6572% | 3/6 | 0/3 | 3/6 |
| phase2_5 | 1/6 | 211242.81 | 109.63 | 18.8738% | 4/6 | 0/2 | 4/6 |
| phase2_6 | 1/6 | 211242.81 | 109.63 | 18.8738% | 4/6 | 0/2 | 4/6 |

Both present predicted dates agree exactly (zero day-distance); two expected dates remain absent. Safety agreement is derivable here because all six expected safe amounts are positive.

| Case | Predicted | Expected | Absolute error | Normalized error | Earliest / expected | Binding date | Low | Baseline safe |
|---|---:|---:|---:|---:|---|---|---:|---|
| request_01 | 25256 | 25256 | 0 | 0.0000% | 2024-03-03 / 2024-03-03 | 2024-03-15 | 47125.90 | True |
| request_05 | 0.00 | 737 | 737.00 | 4.7585% | none / none | 2026-02-04 | 7791.50 | False |
| request_09 | 0.00 | 166.61 | 166.61 | 100.0000% | none / 2026-07-04 | 2026-10-02 | 569.08 | False |
| request_13 | 380.75 | 433.4 | 52.65 | 5.5915% | none / 2024-05-15 | 2024-05-15 | 1680.75 | True |
| request_21 | 1555.93 | 1543.35 | 12.58 | 0.7990% | 2026-04-15 / 2026-04-15 | 2026-04-15 | 3355.93 | True |
| request_25 | 158512.00 | 1425000 | 1266488.00 | 2.0935% | none / none | 2024-03-15 | 23537612.00 | True |

## Dataset-wide impact

Executed 250 evaluation requests without exceptions. Amount changes: 0 (0 increases, 0 decreases); median change 0.00. Earliest-date changes: 0; baseline safety changes: 0. 50 have complete structured evidence; all others remain provisional, not actionable predictions.

No expense-scope change was adopted, so no category contributes an adopted-rule delta. Field distributions and ignored-for-baseline permission/minimum fields are in phase2_6-scope.md/json. All 250 before/after comparisons are retained in the details JSON.

## Preserved causal residuals

- 01: supported payroll bridge already resolves the amount and date.
- 05: binding low 7,791.50 against minimum 13,100. Expected 737 requires 6,045.50 additional capacity. Fixed expenses 26,250.27 plus groceries 9,647.82 and transport 2,785.51 cannot be cut automatically based on scope semantics.
- 09: day-90 rent 211.20 plus variable reserve 7.34 causes the endpoint breach. Day89 alternative matches with mean spending; keep the safer production endpoint because wording remains ambiguous.
- 13: today residual 52.65; full payment on May 15 leaves a June 5 minimum of 913.04, short of 1,300 by 386.96. Future-safety semantics require preserving that shortfall, not checking cash only on May 15.
- 21: 12.58 residual preserved. No independent expense rule supports adding that amount.
- 25: required extra pre-payroll capacity 1,266,488; category reserves are groceries 1,219,499.80, transport 1,211,954.70, dining 1,478,110.60. None may be removed solely to fit. Later FX payroll contributes zero at the binding checkpoint.

Full additive low-water components and nonadditive removal sensitivities remain in phase2_5-details.json. The Phase 2.6 details additionally independently replay full payment on every forecast date for all six complete cases in both old and current cores.

## Reproduce

```powershell
.\.venv\Scripts\python.exe code/evaluation/scope_audit.py
.\.venv\Scripts\python.exe code/evaluation/semantics.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
git diff --exit-code HEAD -- dataset
```

The semantic audit found no necessary production policy change. The final review and readiness decision are in phase2_6-review.md and RESUME.md. Phase 3 means evidence normalization, not payment-plan optimization.
