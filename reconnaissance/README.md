# Phase 1: repository and dataset reconnaissance

Inspected on 2026-09-12. This report describes supplied data and proposes engineering work; it is not a prediction engine. No dataset files were modified. Sample IDs below identify review evidence only and must never become branches or lookup labels in production logic.

## A. What we learned

### Repository state

- Read the complete root `AGENTS.md`, `problem_statement.md`, and `README.md`.
- The checkout is on `main`; no nested `AGENTS.md` was found.
- `code/main.py`, `code/evaluation/main.py`, and `code/evaluation/usage_report.md` are empty placeholders. There is no implemented solver, dependency manifest, or test suite.
- Added `.gitignore` with the mandated `log.txt` exclusion and append-only session/turn logging using `tool=Codex`.
- `python` is not on this machine's PATH. The bundled Python runtime successfully runs the reconnaissance audit; portable Python setup remains an implementation task.
- Final predictions belong at repository-root `output.csv`. `dataset/output.csv` is a read-only template, clarified by the README.
- Predictions must use only participant-facing dataset inputs. No organizer-only logic or labels were inspected or used.

### Data inventory and complete schemas

CSV numeric/date/boolean fields are text on disk. Parse IDs as strings, amounts and rates as `Decimal`, dates explicitly, `true`/`false` explicitly, and pipe-delimited preferences as sets. Preserve missing values separately from zero and from the output literal `none`.

| File | Rows | Grain / key |
|---|---:|---|
| financial_profiles.csv | 275 | One profile per `user_id` |
| financial_events.csv | 25,342 | One financial record per `event_id`; not necessarily one independent cash flow |
| exchange_rates.csv | 134 | `(rate_date, from_currency, to_currency)` |
| requests.csv | 250 | One evaluation request per `request_id` |
| sample_requests.csv | 25 | One solved example per `request_id` |
| request_payment_options.csv | 790 | One offer per `payment_option_id` |
| messages.csv | 215 | One message per `message_id` |
| images.csv | 16 | One image mapping per `image_id` |
| output.csv | 250 | Evaluation request ID plus seven blank prediction fields |

**financial_profiles.csv**

```text
user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months
```

**financial_events.csv**

```text
event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount
```

**exchange_rates.csv**

```text
rate_date,from_currency,to_currency,rate
```

**requests.csv**

```text
request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text
```

**sample_requests.csv**: the same eight request fields followed by:

```text
amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

**request_payment_options.csv**

```text
payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount
```

**messages.csv**

```text
message_id,user_id,request_id,related_event_id,sent_at,source_type,message_text
```

**images.csv**

```text
image_id,user_id,request_id,related_event_id
```

**output.csv**

```text
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

Evaluation request types: purchase 28, travel 28, education 28, family_transfer 28, debt_repayment 28, investment 28, housing 28, emergency_expense 27, other 27. Evaluation request dates span 2023-01-20 through 2026-09-04; samples span 2019-09-03 through 2026-07-07. Forecast from each request's date, never from today's date.

### Joins and boundaries

| Starting table | Join | Relationship and caution |
|---|---|---|
| requests or sample_requests | `user_id = financial_profiles.user_id` | Many requests to one profile in the general design; this dataset has one request per user |
| request/profile | `user_id = financial_events.user_id` | One user to many events; distinguish historical evidence from future cash flows |
| request | `request_id = request_payment_options.request_id` | One request to 2–4 offers |
| request | messages with matching `user_id` and either blank or matching `request_id` | Include user-level notices; do not drop rows with blank request IDs |
| messages/images | `related_event_id = financial_events.event_id` | Direct event evidence when populated; validate same user |
| event | `linked_event_id = earlier financial_events.event_id` | Lifecycle edge, not an instruction to discard the row |
| images | `dataset/media/images/<image_id>.png` | Metadata contains no extracted text or amount |
| foreign event | `(settlement_date, currency, home_currency)` to rates | Multiply by the supplied directional rate, retaining source rate/date |
| output template | `request_id = requests.request_id` | Exactly evaluation IDs, in template order |

Do not combine all tables into one flat join: messages × events × offers can multiply cash-flow rows. Build indexed per-user/per-request contexts. Keep solved output columns out of the prediction context, including LLM prompts.

The audit found no duplicate primary/composite keys or broken user/request/event references in the checks implemented. All 16 linked PNGs exist, and all 16 blank event amounts have image mappings. Every supplied foreign event with a settlement date has its exact directional rate. All 790 offers satisfy `payment_amount * number_of_payments = total_payable_amount = requested_amount + financing_fee` using decimal arithmetic. These are structural checks, not proof of financial feasibility.

### Nullable fields

| Table | Blank fields and counts | Interpretation |
|---|---|---|
| profiles | willing_to_reduce 39; willing_to_stop 62 | No permission for that action, not unrestricted permission |
| profiles | max_installment_months 119 | User does not consider installments |
| events | amount 16 | Must resolve image; never zero-fill |
| events | settlement_date 10 | Non-cash unrealized valuations |
| events | linked_event_id 25,284 | No explicit lifecycle link; 58 links are present |
| events | minimum_allowed_amount 22,435 | Not applicable to many events; do not infer permission to reduce to zero |
| messages | request_id 87 | User-level evidence |
| messages | related_event_id 176 | No direct one-row match; semantic linkage may be required |
| options | payment_frequency_days 275 | Single full-payment offers; no interval needed |
| samples | earliest_date_for_full_payment 7 | All seven not-affordable examples |
| output | all seven output fields, 250 each | Blank template, not missing input evidence |

All other inspected fields have no empty cells. `sent_at` uses UTC timestamps, unlike the date-only financial fields.

### Events, recurrence, currencies, and preferences

| Event type | Count |
|---|---:|
| expense | 20,525 |
| subscription | 2,488 |
| income | 1,696 |
| debt_payment | 567 |
| investment_purchase | 29 |
| refund | 22 |
| investment_valuation | 10 |
| investment_sale | 5 |

| Status | Count | Treatment |
|---|---:|---|
| settled | 25,148 | Cash settled; past cash is already represented by the opening balance, while history informs recurrence |
| pending | 71 | Reserve debits; exclude credits until settlement is confirmed |
| scheduled | 70 | Include known obligations and confirmed salary on settlement dates; validate evidence and avoid duplicate forecasts |
| cancelled | 22 | No cash from cancelled attempt; inspect any replacement |
| failed | 21 | Failed attempt is not cash; a still-outstanding bill or scheduled retry can remain payable |
| unrealized | 10 | Non-cash, never spendable |

Directions: debit 23,609; credit 1,723; non_cash 10. Flexibility: fixed 21,138; reducible 2,682; stoppable 1,297; reducible_or_stoppable 225. Flexibility alone does not authorize a change: recurrence, category permission, protection, and any minimum must also pass.

The 22 observed categories are cloud_storage, debt_repayment, delivery_membership, dining, education, entertainment, family_support, groceries, gym, healthcare, housing, insurance, investment, music_subscription, rent, salary, shopping, streaming, transport, utilities, windfall, and work_expense.

**There are no recurrence flags, interval fields, merchant IDs, or recurring-series IDs in financial_events.** Examples include monthly salary/rent/subscriptions and purchases at repeated day intervals with varying descriptions and amounts. Category-only aggregation would mix base salary with commissions, ordinary groceries with a bulk purchase, and rent with arrears. Description-only grouping would split grocery/transport history across merchants. Infer fixed obligations by stable series and cadence; model essential variable categories separately. A single receipt is not recurrence evidence.

Home currencies: INR 67 users, EUR 62, IDR 55, ZAR 51, USD 40. There are 140 foreign-currency events across 27 users: USD→IDR 28, USD→INR 54, USD→EUR 22, EUR→ZAR 20, EUR→USD 16. Different home currencies alone do not imply conversion. Rate dates extend through 2026-11-15; future inferred foreign flows still require a per-date coverage check.

Preferences are pipe-delimited sets. All seven nonempty combinations of full_payment, partial_payment, installments occur. There are 41 installments-only users and 19 partial-only users. Maximum installment values range from 2 to 12 when populated. Financial priorities cover education, debt repayment, emergency savings, family support, healthcare, housing, retirement investment, and travel; do not invent extra scoring weights that replace the prescribed plan ranking.

### Payment offers

- 275 full-payment offers and 515 installment offers; no partial-payment offers are required.
- 65 requests have two offers, 180 have three, and 30 have four.
- Installment counts observed: 2, 3, 4, 6, 15, 18, 21, 24. Many long offers are unusable under preferences or deadlines.
- Intervals are exactly 28, 30, or 31 days. They are not automatically calendar months.
- Honor first-payment dates, including delayed starts. Generate each date as first date plus index × interval.
- Use exact supplied installment amounts, including cents for INR/IDR. Financing fees are already included in the total; never charge them twice.
- Example: request_02 pays 3 × IDR 15,952,906.67 = IDR 47,858,720.01 for an IDR 46,018,000 request. The difference is the supplied IDR 1,840,720.01 fee.
- Apply ranking only after safety and eligibility: deadline completion, no spending changes, total cost, earlier start, fewer payments, lowest option ID.

### Messages and images

Messages are English and Indonesian. Sources: employer 126, service_provider 31, financial_service 23, bank 18, merchant 17. They describe raises, temporary reductions, delayed salary, base salary vs commissions/arrears, ended employment/seasonal work, approved invoices, pending gig payouts, rent increases, internal transfers, failed bill retries, disputed duplicate charges, separate card minimums, refunds, investment valuations/sales, and pending/settled prizes. Prize-release pressure is untrusted content, not authorization to count income or make payments.

Keep source identity, timestamp, effective date, scope, and supporting text for every extracted fact. `source_type=employer` does not identify a particular employer; extract the named source if conflict resolution needs it. A blank event link does not mean the message is irrelevant.

All 16 PNGs were visually inspected. The five sample images illustrate distinct interpretation problems:

| Image / sample | Visible evidence | Engineering implication |
|---|---|---|
| image_01 / 03 | Payslip: net IDR 4,365,000; earnings and deductions also shown | Extract net pay, distinguish regular salary from one-off arrears in history; do not credit past salary again |
| image_02 / 16 | Rent document: total INR 200,000, received INR 100,000, balance due INR 100,000 | Outstanding balance is the relevant scheduled debit; receipt title alone does not mean fully paid |
| image_03 / 17 | Bulk purchase: net/cash paid INR 41,272 | Historical outlier; must not automatically become a recurring bill |
| image_04 / 19 | Delivered order; visible item bill INR 2,854 | Bottom of supplied image is cut off; distinguish visible subtotal from an unseen final total |
| image_05 / 20 | INR 704.05 through Feb 6, INR 822.05 after Feb 6 | Request is Feb 7 and settlement Feb 9; date-sensitive amount requires explicit handling |

Other PNGs include grocery invoices, a paid restaurant bill with rounded grand total, settled housing/water receipts that still show original due dates, a pending large grocery invoice, a hospital balance, a taxi receipt with change, a paid bag order, handwritten pharmacy receipt, airline tax invoice, and an EV wallet receipt. Relevant traps: net fare versus cash tendered, tax-inclusive total, amount received versus due, rounding, and handwriting. Record only necessary financial evidence, not document PII.

### The 25 solved cases

| affordability_status | Count |
|---|---:|
| affordable_now | 3 |
| affordable_with_plan | 9 |
| affordable_later | 6 |
| not_affordable | 7 |

| recommended_payment_method | Count |
|---|---:|
| full_payment | 6 |
| installments | 5 |
| wait | 6 |
| not_recommended | 7 |
| partial_payment | 1 |

Evidence categories: messages only 14; images only 2; both 3; neither 6. Thus 17 have relevant messages, 5 have images, and 19 have at least one form. Currency conversion: 1 yes, 24 no. Recurring expense history: 25 yes, 0 no. Spending changes: 3 yes, 22 no; one stop-only, one reduce-only, one stop plus reduce.

“Evidence matters” here means relevant supplied facts must be considered, including confirmations/exclusions. It does not claim removing every message would change the final label. Establishing causal label/amount changes requires a later with/without-evidence forecast comparison. All images fill missing financial facts; settled historical images need not create a new future debit. Recurrence is required for all 25 safety assessments, even where the recommendation might remain unchanged without it.

In this table, N=affordable_now, P=affordable_with_plan, L=affordable_later, X=not_affordable; M=messages, I=images. IDs are the suffixes of `request_XX`.

| Sample | Status | Method | Evidence | FX | Recurring expenses | Changes | Main review point |
|---|---|---|---|---|---|---|---|
| 01 | N | full_payment | — | No | Yes | none | Linked reversals/authorization; pending fuel |
| 02 | P | installments | M | No | Yes | none | Salary raise; preferences; delayed fee-bearing offer |
| 03 | L | wait | M+I | No | Yes | none | Net salary image; one-off arrears; long offers rejected |
| 04 | L | wait | M | No | Yes | none | Unconfirmed bonus; school fee; full-only preference |
| 05 | X | not_recommended | — | No | Yes | none | Failed debit; no safe eligible option |
| 06 | P | full_payment | M | No | Yes | stop | Temporary lower salary; stop event_476 |
| 07 | P | installments | M | No | Yes | none | Salary delay to 23rd; installments-only |
| 08 | L | wait | M | No | Yes | none | Unpaid-leave salary notice versus history |
| 09 | N | full_payment | — | No | Yes | none | Immediate full payment is cheapest eligible plan |
| 10 | X | not_recommended | M | No | Yes | none | Pending gig payout excluded |
| 11 | P | full_payment | M | No | Yes | reduce | Base salary vs commissions; event_989→665950 |
| 12 | P | installments | M | No | Yes | none | Seasonal work ended; full payment financially possible but excluded by preferences |
| 13 | L | wait | — | No | Yes | none | Confirmed salary; full-only preference |
| 14 | X | not_recommended | M | No | Yes | none | Return from leave; childcare notice; partial-only |
| 15 | X | not_recommended | M | No | Yes | none | First salary; partial-only while request forbids partial |
| 16 | N | full_payment | M+I | No | Yes | none | 12% rent increase plus separate outstanding balance |
| 17 | P | installments | I | No | Yes | none | Bulk grocery receipt; reimbursement; installments-only |
| 18 | L | wait | M | No | Yes | none | Internal transfer does not establish income |
| 19 | P | partial_payment | I | No | Yes | none | 28820 now + 10840 on Sep 15; cheaper than installments |
| 20 | X | not_recommended | M+I | No | Yes | none | Pending refund excluded; telecom late amount and pending order |
| 21 | P | full_payment | — | No | Yes | stop+reduce | Stop event_1815 and event_1816→23.50; ignore valuation |
| 22 | P | installments | M | No | Yes | none | Unrealized portfolio; pending debit; installments-only |
| 23 | L | wait | M | No | Yes | none | Prize processing is not available cash |
| 24 | X | not_recommended | M | No | Yes | none | Settled prize is one-off; scheduled insurance |
| 25 | X | not_recommended | — | Yes | Yes | none | USD salary→IDR; failed debit; long offers |

The three spending-change samples all use full_payment but remain affordable_with_plan. Their reported safe-today amount is below the request. Their baseline earliest full dates remain later, even beyond the deadline; the changed-budget plan itself completes by the deadline. Sample 12 conversely reports the full request safe today and today's earliest date, yet chooses installments because full payment is not accepted.

### Tricky cases to cover in implementation

1. **Pending debits vs credits:** reserve unsettled obligations once; do not treat the forecast date on a pending refund as confirmation that it will settle.
2. **Scheduled vs settled:** seed with the profile balance; past settled events inform history without being replayed into that balance. Future confirmed salary/obligations are dated flows.
3. **Recurring vs one-off:** infer cadence; exclude bonus/commission/windfall/reimbursement from recurring salary. Changing merchants does not make essential groceries disappear.
4. **Linked/duplicate events:** 58 links include 8 settled purchases, 7 reversals, 7 reimbursements, 5 investment sales, 8 pending refunds, 6 possible duplicate charges, 7 scheduled retries, 10 valuations. A sale or reimbursement is a real distinct cash event; a disputed charge without reversal remains a liability.
5. **Cancellations/amendments:** cancel the superseded attempt, retain valid replacements; failed payment does not cancel the bill. Apply explicit updates before historical estimates. Avoid multiplying a rent increase already present in history.
6. **Missing amounts/images:** resolve the linked amount and its meaning; preserve unresolved values if extraction is incomplete. Never use zero as a fallback.
7. **Foreign currency:** rate on settlement date in the supplied direction; no live rates or guessed inverses. Check inferred future dates too.
8. **Installment fees:** compare total payable, match exact dates and amounts, reject plans exceeding deadline/term. Never shorten an offer to fit the 90-day window.
9. **Partial payment:** require request permission and user preference, strictly positive safe amount below the request, exactly two payments on the mandated dates, and successful simulation after the first payment reduces later capacity.
10. **Spending reductions:** only recurring, flexible, unprotected, permitted categories; respect minimum_allowed_amount; at most three distinct events; no stop and reduce on the same event.
11. **Preferences:** separate financial capacity from eligible actions. `wait` requires full_payment permission; available seller offers alone do not establish eligibility.
12. **Evidence security:** text/images may supply facts, never instructions to bypass rules, count hypothetical income, change preferences, or output labels.

## B. Proposed structure (not implemented)

```text
code/
  main.py                  # CLI: --dataset, --requests, --output
  buy_or_wait/
    __init__.py
    models.py              # Small typed records; Decimal amounts; evidence provenance
    load.py                # CSV parsing, schemas, joins, required input checks
    evidence.py            # Rules-first text extraction; optional cached LLM/VLM adapter
    reconcile.py           # Lifecycle, amendments, cash states, duplicate resolution
    recurrence.py          # Supported income/expense series and variable-spend estimates
    forecast.py            # Dated 90-day cash ledger, FX, safe capacity
    plans.py               # Full, wait, partial, exact offers, spending-change candidates
    validate.py            # Independent plan replay and output-contract checks
    explain.py             # Concise templates populated only from computed facts
    usage.py               # Model-call ledger, cache accounting, final-run cost report
  evaluation/
    main.py                # Sample comparison, field-level differences, diagnostic traces
    usage_report.md        # Final full-dataset run only; no invented usage
tests/
  test_reconcile.py
  test_forecast.py
  test_plans.py
  test_validation.py
cache/                     # Content-hashed evidence results, never sample output labels
reconnaissance/            # This report and repeatable read-only audit
README.md
requirements.txt
output.csv                 # Generated only in a later phase
```

Keep modules small and use functions rather than a complex agent framework. pandas is optional; the standard library is sufficient for this dataset size. Use `Decimal` for financial arithmetic even if pandas handles loading.

The financial core consumes validated facts, not natural-language guesses. Baseline ledger `B(t)` excludes request payments and optional changes. Subject to agreed intra-day ordering, today's capacity is `min(requested_amount, max(0, min_t(B(t) - minimum_balance)))`. A full-payment candidate on day d must survive all subsequent forecast checkpoints, and the original baseline must itself be safe before d. Every multi-payment candidate is replayed on the same ledger. Baseline safe amount and earliest full date remain unchanged when evaluating optional spending adjustments.

LLM/VLM scope is extraction only: amount candidates with labels, currency, dates, status, recurring/one-off assertions, source identity, and evidence references. Extract percentages as facts and calculate their effect in Python. Never ask the model to calculate balances, affordability, schedules, rankings, or expected sample outputs.

Cache by evidence content hash, relevant event context, schema/prompt version, and model identifier. Share extracted facts across requests when context permits. Try explicit text rules first; use a small model for unsupported message phrasing and VLM only where image extraction is needed. Record calls, retries, input/output tokens, model/provider, cache hits, and cost assumptions. Keep development usage separate from the final run; report warm-cache behavior honestly with provenance. Package `evaluation/usage_report.md` at the ZIP's required path, regardless of the working-tree `code/` prefix.

## C. Implementation phases

1. **Reconnaissance — complete.** Inventory, joins, sample matrix, image review, assumptions. No solver or predictions.
2. **Typed inputs and evidence.** Strict loader; raw-to-normalized facts; content-addressed extraction cache; image/multilingual evidence review. Check missing amounts, temporal scope, and provenance before financial arithmetic.
3. **Financial reconstruction and baseline forecast.** Cash-state/lifecycle rules, recurrence, essential spending estimator, dated FX, 90-day ledger. Test with synthetic edge cases and explain sample mismatches in a ledger.
4. **Plan generation and validation.** Eligibility, exact offers, partial payment, spending changes, deterministic ranking, independent balance replay. Generate explanations from verified facts.
5. **Sample evaluation and targeted correction.** Compare all seven output fields on all 25 samples; diagnose general rule discrepancies without ID-specific logic. Add tests for unseen combinations such as a failed debit with retry and an unresolved duplicate charge.
6. **Full run and submission packaging.** Predict exactly 250 rows, validate root output, record final-run usage/costs, document setup, package code and evaluation report, preserve transcript. No model-price estimates should be invented; verify pricing when an actual provider/model is selected.

## D. Assumptions to resolve with samples and explicit rules

| Question | Evidence / proposed treatment |
|---|---|
| Variable essential spending estimator | The rules say conservative but specify no lookback, percentile, buffer, or aggregation period. Compare a small set of interpretable policies against sample amounts and ledger minima; report residual mismatches rather than tuning per request. |
| Forecast boundaries and intra-day ordering | Define whether day 90 is included and how salary, bills, and request payments on the same date are ordered. Use a fixed request-anchored horizon unless the specification clarifies a rolling horizon; do not silently gain affordability near the horizon end. |
| Opening balance and pending holds | Treat profile balance as the opening snapshot and reserve pending debits exactly once. Confirm numerical reconciliation with samples 01/02/20; history must not be added to the balance again. |
| Temporary salary changes | Sample 08 history has regular EUR 1,422.85 followed by EUR 782.57, while the message explicitly calls the next salary reduced to EUR 1,422.85. Prefer the explicit next-pay fact, but test whether later cycles are supported; do not apply another percentage cut. Sample 06 supports EUR 1,037.52 for the affected upcoming cycle. |
| Salary components | Sample 11 history shows IDR 23,256,000 base plus variable commissions, while its message states confirmed base IDR 38,760,000. The explicit message should win under the contract; reconcile the sample's July 15 baseline date before assuming a different rule. |
| Salary delay duration | Sample 07's latest settlement and next-pay notice point to the 23rd; the solved earliest full date is October 23. Investigate whether the revised day is ongoing, rather than assuming it applies only once. |
| New childcare obligation | Sample 14's message announces recurring childcare without an amount. No education-category event was found for that sample. Resolve against other relevant event descriptions; if no amount exists, flag incomplete evidence instead of inventing an expense. |
| Missing/cropped image total | Sample 19's image visibly shows item bill INR 2,854 but crops the remainder. Treat this as a visible amount candidate, not proof that no extra charges exist. Sample reconciliation must document any subtotal-as-total assumption. |
| Late fees | Sample 20's image implies INR 822.05 after the due date rather than INR 704.05. Use applicable dated charges, and diagnose any mismatch explicitly. |
| Existing vs amended rent | Sample 16 history shows INR 57,100 monthly; message adds 12% for the next payment, and image adds INR 100,000 outstanding balance. Keep the arrears separate from recurring rent and apply the amendment once. |
| Recurring-series action IDs | Samples 06, 11, 21 reference recent historical event IDs. Use a deterministic representative event for future series changes, likely the latest settled eligible row; compare all samples before finalizing. Do not refund the historical payment. |
| Reduction amount search | Samples 11 and 21 reduce exactly to minimum_allowed_amount. Minimum-based candidates are a simple starting point; the specification allows other valid new amounts, so do not assume only minima are legal. |
| Installment maximum in months | Offers use day intervals, profiles use months. Define duration vs installment-count interpretation. The 25 samples do not fully distinguish all 28/30/31-day boundary cases. |
| Deadline vs status | The spec defines not_affordable partly by the forecast period but requires plans to finish by deadline. None of the seven not-affordable samples has a populated full-payment date, so they do not settle the case where full payment is safe only after deadline. Never recommend a late plan; keep this mapping explicit. |
| Lowest option ID | IDs have numeric suffixes with varying length. Clarify numeric versus lexicographic ordering if a real final tie occurs; samples do not establish it. |
| Approved invoices and one-off arrears | Evaluation messages include approved invoice payments and one-time payroll adjustments. Determine whether each is settled, scheduled-confirmed, or merely pending; never project uncertain income or repeat a one-off component. |

These are investigation items for the next phases, not requests for the beginner to invent financial policy. The engineer should test and document them using public inputs/samples, with the written contract taking precedence where conflicts remain.

## Reproducing the structural audit

From repository root with Python 3 available:

```text
python reconnaissance/audit.py
python reconnaissance/audit.py --save
```

The first prints the inventory; the second saves `reconnaissance/inventory.json`. It reads only dataset CSVs and checks image existence. Visual image interpretations and message semantics in this report were reviewed separately. It does not forecast, predict, call a model, edit dataset files, or validate sample financial answers.
