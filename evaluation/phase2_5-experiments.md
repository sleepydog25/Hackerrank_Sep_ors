# Phase 2.5 controlled experiments

All six structured cases; one-factor changes from Phase 2 unless named combined. Every capacity passes independent cent-level binary-search/replay. MAE mixes home-currency units and is descriptive only; normalized MAE is the comparable aggregate.

| Policy | Amount exact | MAE (mixed units) | Median AE | Normalized MAE | Date exact | False present/absent | Baseline safe |
|---|---:|---:|---:|---:|---:|---|---:|
| phase2 | 0/6 | 241126.28 | 484.78 | 35.6572% | 3/6 | 0/3 | 3/6 |
| mean_daily | 0/6 | 214286.32 | 451.80 | 30.9244% | 3/6 | 0/3 | 4/6 |
| trimmed_daily | 0/6 | 216043.79 | 451.80 | 30.8965% | 3/6 | 0/3 | 4/6 |
| median_daily | 0/6 | 213206.42 | 451.80 | 29.2426% | 3/6 | 0/3 | 4/6 |
| weekly_p75 | 0/6 | 241957.96 | 585.20 | 43.8283% | 3/6 | 0/3 | 1/6 |
| cadence | 0/6 | 241028.64 | 484.15 | 35.4772% | 2/6 | 0/3 | 3/6 |
| confirmed_bridge | 1/6 | 237690.71 | 199.58 | 22.0542% | 4/6 | 0/2 | 3/6 |
| two_payrolls | 1/6 | 237690.71 | 199.58 | 22.0542% | 4/6 | 0/2 | 3/6 |
| freelance | 2/6 | 237662.94 | 120.32 | 5.3875% | 5/6 | 0/1 | 4/6 |
| combined_p75_daily | 1/6 | 237690.71 | 199.58 | 22.0542% | 4/6 | 0/2 | 3/6 |
| combined_mean_daily | 1/6 | 211242.81 | 109.63 | 18.8738% | 4/6 | 0/2 | 4/6 |
| combined_trimmed_daily | 1/6 | 213008.77 | 109.63 | 18.8794% | 4/6 | 0/2 | 4/6 |
| combined_median_daily | 1/6 | 210390.56 | 94.60 | 18.0933% | 4/6 | 0/2 | 4/6 |
| combined_weekly_p75 | 1/6 | 237748.62 | 300.00 | 27.1617% | 4/6 | 0/2 | 2/6 |
| combined_cadence | 1/6 | 237694.33 | 198.96 | 22.2751% | 3/6 | 0/2 | 3/6 |
| day89 | 0/6 | 241056.78 | 484.78 | 22.4614% | 3/6 | 0/3 | 4/6 |
| before_salary | 0/6 | 241126.28 | 484.78 | 35.6572% | 2/6 | 0/3 | 3/6 |
| overlap | 0/6 | 241126.28 | 484.78 | 35.6572% | 3/6 | 0/3 | 3/6 |
| grouping | 0/6 | 241126.28 | 484.78 | 35.6572% | 3/6 | 0/3 | 3/6 |
| selected | 1/6 | 211242.81 | 109.63 | 18.8738% | 4/6 | 0/2 | 4/6 |
| selected_day89 | 2/6 | 211215.04 | 32.62 | 2.2071% | 5/6 | 0/1 | 5/6 |
| selected_before_salary | 1/6 | 211242.81 | 109.63 | 18.8738% | 3/6 | 0/2 | 4/6 |

All expected safe amounts are positive, so baseline safety is derivably true for these six. Date distances when both dates exist, every per-policy per-case error, low-water mark, variable-category projection, and historical rate are in phase2_5-details.json.

## Safe amount sensitivity by case

| Case | Before | Expected | No groceries Δ | No transport Δ | No dining Δ | No variable Δ | No fixed Δ | No inferred income Δ | No pending Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| request_01 | 4642.55 | 25256 | 11688.04 | 6539.26 | 7889.70 | 20613.45 | 20613.45 | 0.00 | 567.60 |
| request_05 | 0.00 | 737 | 3968.04 | 0.00 | 0.00 | 7124.83 | 15488.00 | 0.00 | 0.00 |
| request_09 | 0.00 | 166.61 | 166.61 | 29.14 | 53.71 | 166.61 | 166.61 | 0.00 | 0.00 |
| request_13 | 200.85 | 433.4 | 740.75 | 504.70 | 352.80 | 740.75 | 740.75 | -200.85 | 0.00 |
| request_21 | 1535.26 | 1543.35 | 39.14 | 29.64 | 39.14 | 39.14 | 39.14 | -1535.26 | 39.14 |
| request_25 | 0.00 | 1425000 | 1123450.20 | 1060884.00 | 1353504.90 | 4068077.10 | 4350753.90 | 0.00 | 0.00 |

These are controlled counterfactual sensitivities, not additive allocations of error. The JSON also provides an exact additive opening + inflows − outflows reconciliation at each original binding checkpoint. Capped expected amounts imply bounds, not an exact target low-water mark.

## Per-case policy effects

| Policy | request_01 | request_05 | request_09 | request_13 | request_21 | request_25 |
|---|---:|---:|---:|---:|---:|---:|
| phase2 | 4642.55 | 0.00 | 0.00 | 200.85 | 1535.26 | 0.00 |
| mean_daily | 6994.90 | 0.00 | 0.00 | 380.75 | 1555.93 | 158512.00 |
| trimmed_daily | 7045.86 | 0.00 | 0.00 | 380.75 | 1556.19 | 147916.50 |
| median_daily | 8360.81 | 0.00 | 0.00 | 436.05 | 1565.94 | 163585.50 |
| weekly_p75 | 0.00 | 0.00 | 0.00 | 0.00 | 1388.62 | 0.00 |
| cadence | 5250.09 | 0.00 | 0.00 | 202.10 | 1574.4 | 0.00 |
| confirmed_bridge | 25256 | 0.00 | 0.00 | 200.85 | 1535.26 | 0.00 |
| two_payrolls | 25256 | 0.00 | 0.00 | 200.85 | 1535.26 | 0.00 |
| freelance | 25256 | 0.00 | 166.61 | 200.85 | 1535.26 | 0.00 |
| combined_p75_daily | 25256 | 0.00 | 0.00 | 200.85 | 1535.26 | 0.00 |
| combined_mean_daily | 25256 | 0.00 | 0.00 | 380.75 | 1555.93 | 158512.00 |
| combined_trimmed_daily | 25256 | 0.00 | 0.00 | 380.75 | 1556.19 | 147916.50 |
| combined_median_daily | 25256 | 0.00 | 0.00 | 436.05 | 1565.94 | 163585.50 |
| combined_weekly_p75 | 25256 | 0.00 | 0.00 | 0.00 | 1388.62 | 0.00 |
| combined_cadence | 25256 | 0.00 | 0.00 | 202.10 | 1574.4 | 0.00 |
| day89 | 4929.55 | 0.00 | 130.02 | 200.85 | 1535.26 | 0.00 |
| before_salary | 4642.55 | 0.00 | 0.00 | 200.85 | 1535.26 | 0.00 |
| overlap | 4642.55 | 0.00 | 0.00 | 200.85 | 1535.26 | 0.00 |
| grouping | 4642.55 | 0.00 | 0.00 | 200.85 | 1535.26 | 0.00 |
| selected | 25256 | 0.00 | 0.00 | 380.75 | 1555.93 | 158512.00 |
| selected_day89 | 25256 | 0.00 | 166.61 | 380.75 | 1555.93 | 158512.00 |
| selected_before_salary | 25256 | 0.00 | 0.00 | 380.75 | 1555.93 | 158512.00 |

## Selected policy residuals

| Case | Selected | Expected | Error | Earliest / expected |
|---|---:|---:|---:|---|
| request_01 | 25256 | 25256 | 0 | 2024-03-03 / 2024-03-03 |
| request_05 | 0.00 | 737 | -737.00 | none / none |
| request_09 | 0.00 | 166.61 | -166.61 | none / 2026-07-04 |
| request_13 | 380.75 | 433.4 | -52.65 | none / 2024-05-15 |
| request_21 | 1555.93 | 1543.35 | 12.58 | 2026-04-15 / 2026-04-15 |
| request_25 | 158512.00 | 1425000 | -1266488.00 | none / none |

## Selected low-water reconciliation

All component values below are signed home-currency amounts through the binding event, not 90-day totals. Opening plus components equals the low-water mark exactly.

| Case / binding date | Opening | Minimum | Fixed/other | Groceries | Transport | Dining | Pending | Confirmed income | Inferred income | Low |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| request_01 / 2024-03-15 | 58481.1 | 18000 | -7392.65 | -1499.42 | -843.57 | -1051.96 | -567.6 | 0 | 0 | 47125.90 |
| request_05 / 2026-02-04 | 46475.1 | 13100 | -26250.27 | -9647.82 | -2785.51 | 0 | 0 | 0 | 0 | 7791.50 |
| request_09 / 2026-10-02 | 2231.1 | 600 | -994.08 | -413.14 | -112.84 | -141.96 | 0 | 0 | 0 | 569.08 |
| request_13 / 2024-05-15 | 2789.52 | 1300 | -1972.35 | -1024.80 | -464.10 | -334.60 | 0 | 1343.54 | 1343.54 | 1680.75 |
| request_21 / 2026-04-15 | 3911.35 | 1800 | -308.46 | -110.63 | -27.43 | -55.90 | -53 | 0 | 0 | 3355.93 |
| request_25 / 2024-03-15 | 32063050 | 23379100 | -4615872.90 | -1219499.80 | -1211954.70 | -1478110.60 | 0 | 0 | 0 | 23537612.00 |

## Decision and financial interpretation

Select **calendar-day mean spending + confirmed payroll bridge**. Keep the existing 180-day lookback, three historical spending dates, day-90 inclusion, debit-before-credit ordering, and candidate at daily close. No parameter was numerically fitted. `ForecastPolicy()` reproduces the previous model for controlled experiments; `DEFAULT_POLICY` selects the calibrated model. Production code has no sample identifiers or expected outputs.

The prior spending calculation combines an upper purchase quantile with median transaction spacing. It can systematically exceed the observed cash spending rate even when no evidence supports a higher future budget. The selected estimator divides all settled category spending in the request-exclusive lookback by calendar days from the first covered purchase to the request. It includes observed high purchases, combines merchants within a variable category, rounds the daily reserve up to cents, and reserves it daily rather than assuming essentials can wait for payday. It does not assume that days before the first available record represent zero spending. This is a conservative timing policy with a transparent expected-spend estimate, **not a guaranteed upper bound**. Missing coverage and structural changes remain limitations.

Retain stable, non-stale three-observation payroll inference. Additionally, one historical payroll plus one explicitly scheduled next payroll supports monthly continuation when calendar cadence and amounts agree (or the historical payment explicitly represents a prorated first salary). The scheduled installment is included exactly once; inferred continuation starts the following month. Incompatible named payroll sources cannot be bridged. Generic descriptions cannot reliably identify employers, so ambiguous multi-job cases remain conservative. Final-payroll evidence blocks continuation; scheduled credits still settle once. Evidence states distinguish CONFIRMED, SUPPORTED_RECURRING, INSUFFICIENT, TERMINATED, and ONE_OFF. No income is accepted merely because a sample expects it.

## Rejected alternatives and failure modes

| Candidate | Reason not selected |
|---|---|
| P75 purchase / median spacing | Overstates aggregate spending in several cases; mixes two statistics that need not describe a coherent spending rate. |
| Trimmed mean | Discards real high spending without evidence it will stop; with sparse histories it often equals the mean. |
| P50 purchase / median spacing | Slightly better aggregate score, but can discard substantial actual spending and still confounds typical amount with typical spacing. Better sample fit alone is insufficient. |
| P75 complete weekly totals | A defensible upper budget, but systematically more restrictive here. Empty weeks are included; partial boundary weeks are excluded. |
| Expected transaction dates | Assumes essentials can wait until their next predicted date; raises capacity simply by shifting spending past a binding paycheck. |
| Two historical payrolls without a confirmed next payment | Weaker evidence than the selected bridge; no additional benefit on these six. Available only as an experiment. |
| Repeated freelance monthly receipts | Best apparent income-policy score, but past projects do not confirm future work or settlement. Do not turn repeated invoices into available future cash. |
| All variable reserves disabled | Measures sensitivity only. It would remove real baseline spending without an authorized change. |
| Earlier same-day candidate | Makes the matching April 15 date become April 16; does not explain amount errors. |
| Excluding day 90 | Explains one case in combination with mean spending, but no global endpoint conclusion follows from six cases. See boundary audit below. |

## Causal explanations for all six cases

The preceding tables and `phase2_5-details.json` separate two different quantities: exact signed cash components at the binding checkpoint, and one-factor counterfactual effects. Counterfactual safe-amount deltas do **not** add because the limiting date and requested-amount cap may change. Expected amounts cannot reveal an organizer's exact spending decomposition; the following residual requirements are arithmetic implications, not invented ground truth.

- **01:** Legacy safe capacity 4,642.55 becomes 6,994.90 from spending estimation alone (+2,352.35). Adding supported payroll alone reaches the requested cap 25,256 (+20,613.45). The selected forecast's actual uncapped capacity is 29,125.90. Removing its inferred continuation lowers safe capacity by 18,261.10. The omitted supported continuation was the dominant error; treating all variable expenses as zero also reaches the cap but has no financial justification. No FX exists; the 567.60 pending obligation is retained.
- **05:** No future payroll is supported after final employment pay. The original low-water mark 6,573.01 becomes 7,791.50 (+1,218.49 from spending estimation), still below the 13,100 minimum. To support the expected 737 under the same binding checkpoint requires 6,045.50 less net outflow. Selected fixed/other expenses total 26,250.27, groceries 9,647.82, and transport 2,785.51. Removing groceries raises safe capacity to 4,339.32; removing all variable spending raises it to 7,124.83. Neither is an allowed baseline correction. No pending/FX contribution or endpoint experiment explains the residual. The discrepancy is budget scope/amount under an ended-income horizon, not hidden pending income.
- **09:** Selected expenses exceed opening discretionary cash by 30.92 at October 2. Groceries 413.14, transport 112.84, dining 141.96, and fixed/other 994.08 account exactly for the 569.08 low, against a 600 minimum. Funding the requested 166.61 would require at least 197.53 additional capacity under this horizon. Crucially, October 2 is day 90 and contains 211.20 rent plus 7.34 daily variable spending. Excluding that day removes 218.54 and produces **the exact amount and date** with mean spending, without invented freelance income. Thus this is an actual horizon/estimator interaction, not solely an income issue. The legacy estimator with day 89 only reaches 130.02. Future freelance income is a second possible explanation, but is unsupported.
- **13:** Mean spending improves safe capacity 200.85 → 380.75 (+179.90), leaving 52.65 less than expected. Through the binding May 15 pre-salary checkpoint, groceries consume 1,024.80, transport 464.10, dining 334.60, and fixed/other obligations 1,972.35, offset by 2,687.08 of prior income. P50 spending would produce 436.05, close but still 2.65 high; fitting between estimators would be arbitrary. At the expected May 15 full-payment date, the subsequent minimum is 1,854.64 on June 5: capacity 554.64 versus a 941.60 request, a **386.96 future shortfall**. Removing transport or dining produces the expected date, but would be a spending reduction and is not applied to baseline. Horizon/order changes do not resolve it.
- **21:** Mean spending changes today's amount 1,535.26 → 1,555.93 (+20.67); expected 1,543.35 lies between them. The selected pre-payroll budget comprises groceries 110.63, transport 27.43, dining 55.90, fixed/other 308.46, and a 53 pending fuel hold. Matching the expected amount would require another 12.58 of pre-payroll outflow. There is no evidence to assign that value to any category. Both forecasts correctly identify April 15; moving the candidate before salary incorrectly shifts this to April 16. Blanket pending/category subtraction would increase an already optimistic amount.
- **25:** Mean spending raises the March 15 pre-payroll low from 23,113,981 to 23,537,612 (+423,631). Because the original baseline breached its minimum, safe amount increases from zero to 158,512. Expected 1,425,000 requires a further 1,266,488 of pre-payroll capacity. The selected ten-day reserves are groceries 1,219,499.80, transport 1,211,954.70, dining 1,478,110.60; fixed/other obligations are 4,615,872.90. Removing any one variable category changes capacity by that category's reserve, but none is an evidenced baseline correction. Three supplied/projected USD payrolls each convert 1,800 × 15,833.33 = 28,499,994 IDR on their settlement dates. The binding point precedes the first credit: FX contributes **zero to the binding balance**, and changing a later rate cannot solve this pre-payroll gap. Day-90/order experiments do not change today's amount.

## Pending-variable overlap audit

Across the supplied structured events there are 15 pending variable-category records: 14 generic fuel authorizations and one grocery invoice with a missing amount. None establishes an exact historical merchant/occurrence identity for a substitutable variable series in the six complete cases. The one-factor overlap experiment therefore changes **zero** complete-case outputs. User-level message/image counts are also zero for each of the six; they have not been incorrectly declared complete while mapped evidence was ignored.

Selected general rule: retain the explicit pending reserve. Substitute only the near-term budget slice when an active hold has an exact historical description or lifecycle link, matches category/currency, settles within one historical median spacing, and lies between half and twice the historical median amount. Offset at most the hold amount and at most the budget in that interval. A generic category match, distant charge, or unusually large purchase remains additional. Multiple holds cannot make a category budget negative. This is an explainable overlap heuristic, not proof that two identical merchant transactions are the same purchase; ambiguous real evidence must remain conservative.

Regression tests exposed and fixed two integration errors in the new overlap path: a reconciled-away authorization could still subtract budget, and generic linked-occurrence suppression could act on daily variable accruals before the overlap pass. Neither affected the six samples. Overlap now requires an active reserved hold; variable budgets have exactly one substitution path. A zero confirmed paycheck also exposed a division-by-zero possibility in bridge stability validation, now guarded. The original Phase 2 cash-capacity kernel reproduced its saved values and showed no arithmetic defect.

## Grouping audit

Fixed obligations retain category + direction + currency + normalized description. Only explicit billing-period tokens (`YYYY-MM[-DD]`, `Month YYYY`) are removed; merchant words and account numbers survive. The full dataset has **zero** fixed-history groups joined by this normalization, so this change does not claim a sample-score gain. Synthetic tests show a date label no longer splits one rent/payroll series and distinct loan accounts remain separate. Variable merchants deliberately share category budgets; modeling them as independent full category budgets would double forecast spending.

Do not merge arbitrary same-category payroll/expenses. The bridge rejects explicitly different named sources. No large fuzzy-matching dependency is added. Remaining limitations: generic employer labels lack identifiers; final-payroll termination is conservatively scoped to currency, possibly suppressing another job; irregular changing descriptions without identifiable dates may still split a genuine fixed series. These require scoped source evidence, not label tuning.

## Boundary and ordering audit

The specification says forecast the next 90 days, but does not explicitly define whether request day is inside that count. Retain the already documented request date through +90 inclusive pending a principled contract clarification. The 89-day experiment is meaningful: combined with mean spending it resolves 09 exactly and raises aggregate matches to 2/6 amounts, 5/6 dates, normalized MAE 2.2071%. This result is recorded rather than hidden; it is insufficient to erase a known day-90 rent from the production safety horizon solely to fit a label. Other residuals remain. Before-salary candidate ordering leaves all six today's amounts unchanged and worsens the matching date for 21. Debits still precede credits; daily-close candidates remain selected.

## Validation and readiness

All 43 original tests are retained. Added tests cover all six estimators, sparse and request-exclusive history, outliers, payroll evidence states and source compatibility, first/prorated pay with confirmation, freelance/one-off exclusion, final payroll, same-day paid obligations, pending overlap, grouping, and boundary behavior. A fixed-seed invariant generates 100 synthetic ledgers under both candidate orderings and independently binary-searches payment replay. The experiment matrix also asserts direct formula = replay for every case/policy combination, and reproduces saved Phase 2 amounts, dates, and low-water marks.

The before/after comparison is **0/6 → 1/6 amount exact**, **3/6 → 4/6 date exact**, **35.6572% → 18.8738% normalized MAE** (about 47% reduction). Median absolute error falls 484.78 → 109.63. Raw MAE mixes currencies and should not drive selection. The final date distances are zero whenever both dates exist; there are zero false-present and two false-absent dates. Baseline safety agreement improves 3/6 → 4/6. This is a measured improvement, not a claim of adequate final prediction quality.

**Recommendation: not ready for payment-plan optimization.** This calibration milestone is complete, but resolve the endpoint interpretation and baseline expense scope/estimation before trusting optimized plans. Evidence extraction infrastructure can later provide scoped facts, but it cannot resolve these six via mapped images/messages because none exist. Do not chase exact labels with arbitrary allowances. Preserve these mismatches as regression diagnostics and obtain a general financial-policy interpretation before Phase 3 ranking.

