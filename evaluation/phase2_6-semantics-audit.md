# Phase 2.6 specification semantics — Checkpoint A

Written before any Phase 2.6 production behavior change. Authority: `problem_statement.md`, then `AGENTS.md`. Samples are diagnostics, not policy definitions. Phase 2.5 already exists in user commit `226adac`; restart checkpoint `a586391` preserves it.

## A. Which dates comprise the 90-day forecast?

**Evidence.** Statement line 59 defines request date as the date of evaluation. Lines 182–186 say “for the next 90 days” and “throughout the 90-day forecast.” Lines 99 and 188 place the immediate payment today. Lines 113 and 189 constrain full payment to the forecast period. No sentence supplies an inclusive/exclusive endpoint or a formula such as D+89. AGENTS adds no endpoint definition.

**Implementation.** `ForecastPolicy.horizon_days=90`, projection through D+90, `range(horizon_days+1)` in `simulate`: 91 calendar-date closes plus event/opening checkpoints. Candidate payments include the endpoint. Settled historical cash is already in opening balance.

**Agreement.** Ambiguous contract, not a proven off-by-one. [D,D+89] counts today among 90 dates; [D,D+90] covers the next 90 dates plus today's checkpoint. Both are linguistically plausible. The Phase 2 documentation explicitly chose the latter conservatively; it did not establish an organizer-specified endpoint. Any later wording presenting 91 dates as exact specification would be unsupported.

**Decision.** Retain [D,D+90], debit → credit → daily-close candidate. Keep day89 evaluation-only. The improved sample score does not justify removing a known endpoint obligation. Same-day ordering is another conservative operational choice, not an explicit intraday timestamp in the data.

**Confidence.** High that endpoint is unspecified; moderate that this conservative convention is the intended evaluator convention. There is no proof of a boundary bug. Record the request_09 boundary signal without selecting by score.

## B. Which expenses belong in baseline reserves?

**Evidence.** Statement line 99 requires payment “before optional spending changes” while covering protected expenses. The 90-Day Safety Check (182–189) explicitly includes “recurring income and expenses” and “confirmed future payments”; it does not limit recurring expenses to protected categories. Line 161 limits changes to recurring flexible expenses. Line 25 requires essentials and minimum balance throughout the forecast. AGENTS §6.2 restricts modifications to non-protected flexible events in permitted categories; §6.3 requires supported recurrence and conservative variable essentials. Neither authority says to replace baseline amounts automatically with `minimum_allowed_amount`.

**Field/algorithm mapping.** Loader retains profile protect/reduce/stop sets, priorities, event flexibility and minimum amount. Reconciliation includes active pending/scheduled debits and excludes cancelled/failed/noncash states. Recurrence uses category, description, direction, currency, amount, type, settlement history and cadence. Profiles do not automatically reduce those forecasts. All supported fixed/variable series retain estimated original amounts. The variable estimator's groceries/transport/dining set is a modeling choice; it is not an automatic protected-category classification.

**Agreement.** Baseline spending unchanged by optional permissions agrees with the contract. The narrower proposal “mandatory + protected + flexible minimums” would implement unrequested reductions or stops and conflict with the explicit before-changes requirement. It is not supported. Numerical inference of what spending will recur remains uncertain; semantics alone do not prove all observed spending recurs.

**Decision, by domain concept:**

| Concept | Baseline rule | Later optional-plan rule |
|---|---|---|
| Active known debit, including debt/rent/other obligations | Reserve once according to lifecycle and dates, regardless of category permission | Cannot remove an obligation merely because its category is stoppable |
| Protected essential category | Keep known/supported spending | Protection vetoes reduction/stop |
| Flexible recurring expense | Keep full supported baseline estimate | May consider a permitted change only in a separate validated plan |
| Reducible expense with a minimum | Do not replace original estimate with minimum | Minimum is a proposed reduction floor; confirm evidence and eligibility |
| Stoppable category | Willingness is not actual cancellation | Eligible recurring flexible event may be considered for stop |
| Protect and reduce/stop overlap | Keep baseline spending | Protection takes precedence |
| Historical discretionary purchase | No replay and no unsupported recurrence | A one-off purchase is not a stoppable recurring commitment |
| Supported discretionary subscription/category | Remains expected baseline spending | Savings require explicit separate change action |
| Financial priorities | Not a numerical discount or income source | May guide later choices within contract ranking |

**Confidence.** High that optional reductions must not affect baseline amount/date; moderate about the statistical recurrence estimate. No expense-scope production change is justified. Dataset-wide field distributions are generated in `phase2_6-scope.md/json`, including both all users and the 250 evaluation users. Preserve the known estimator limitations instead of defining groceries/dining as always protected or always removable.

## C. What makes an earliest full-payment date safe?

**Evidence.** Statement line 189: “the first date the full amount passes the safety check without optional spending changes.” Lines 182–186 require minimum balance throughout the 90-day forecast, not only at purchase time. Line 163 makes capacity independent of payment-method preferences. Lines 113 and 146 distinguish a capacity date within the horizon from the separate completion deadline condition applied to eligible plans.

**Implementation.** `simulate` checks the entire baseline prefix and uses the suffix minimum at each daily-close candidate. A payment at T reduces every later balance through the original request-anchored endpoint. It does not slide a new 90-day window from T. It returns no date if the baseline already breaches the minimum. Future salary counts only from its settlement date; a later credit cannot repair a previous breach.

**Agreement/decision.** Retain this algorithm. Instantaneous cash is insufficient; a later essential bill matters. The specification supplies one request-level forecast, not a new window for every possible payment date. Earliest capacity may be after the desired completion deadline, although a selected plan must obey its separate deadline rule. No preferences, reductions or hypothetical new salary may make the baseline date safe.

**request_13 diagnostic.** On May 15 a payment can fit the immediate balance, but paying 941.60 leaves only 913.04 at the June 5 checkpoint, below the required 1,300 by 386.96. Thus May 15 is unsafe under the current expense forecast and the authoritative continuing-safety rule. The sample discrepancy is expense-model uncertainty, not permission to check only payment-day cash.

**Confidence.** High for continuing safety and no optional changes; moderate for the documented fixed endpoint convention inherited from A. Preserve the mismatch.

## Checkpoint A conclusion and exact next action

No production semantic change is justified by these three questions. Checkpoint B should add synthetic boundary, profile-permission/minimum and future-payment safety tests, retaining production behavior. Then reproduce all six cases and all 250 requests against the accepted Phase 2.5 code. Do not start another estimator search or chase residuals.
