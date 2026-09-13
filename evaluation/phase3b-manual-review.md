# Message semantic review

Selection: first distinct type/certainty/scope combinations in persisted extraction order, plus a parse failure. Selection uses message semantics, never financial label mismatch. Source text was read directly, without images. This is a qualitative review, not a measured accuracy score.

## Initial message-1 extraction

| Message | Source meaning | Extracted interpretation | Assessment |
|---|---|---|---|
| message_75 | Prize already credited; no repeat promised | One-off received payment, no amount/date | Correct one-off direction; settlement certainty understated. Missing context must remain unresolved. |
| message_77 | Temporary reduced next pay | Next-only salary, no date | Correct scope; net-pay label not explicit, amendment flag omitted. |
| message_78 | Base pay and unapproved commission | Ongoing salary only | Incomplete coverage of pending commission; net pay not established. |
| message_79 | Portfolio value increased | Unresolved, no amount | Safe, but a noncash valuation fact could resolve this without inventing an amount. |
| message_80 | First pay confirmed for explicit date | One-off salary with effective date only | Payment date semantics lost; net/gross remains unspecified. |
| message_82 | Base salary plus pending commission | Parse failure | Provisional; invalid output was discarded, so the original local rejection reason cannot be reconstructed. |
| message_83 | Invoice approved, settlement expected | Payment received with due date | Wrong fact/date/amount-paid semantics; deterministic validation prevents cash. |
| message_86 | Charged wallet, image has amount; future salary credit | Expense without amount and salary with due date | Two facts retained, but salary payment date missing. Image remains unresolved. |
| message_89 | Monthly pay increase from explicit date | Salary FROM_DATE, explicit amendment | Scope/change captured; net-pay assertion unsupported by wording alone. |
| message_92 | Indonesian: investment sale already credited | One-off sale, no amount/date | Correct sale versus valuation; settlement certainty understated. |
| message_93 | Indonesian: invoice approved, settlement expected | Invoice approved without payment date | Fact type correct; explicit settlement date omitted. |
| message_96 | Approved invoice with other invoices awaiting approval | Pending payout | Conservative but loses approval distinction; no settled cash authorized. |
| message_103 | Indonesian: seasonal contract ended, no renewal | NO_FACT | **Incorrect and material:** employment termination is financial evidence without an amount. Could incorrectly exhaust a source. |
| message_108 | Investment sale settled; linked history available | Linked sale with context amount/date | Context supplied the amount; must remain historical snapshot evidence, never new cash. |
| message_109 | Invoice payment approved but not received | Pending payment received | Pending certainty prevents availability, but fact type is misleading. |
| message_112 | Regular next salary and separate one-off arrears | Two salary facts, different scopes | Separation correct; net-pay/paid labels unsupported. Do not sum in the model. |
| message_117 | Employer reimbursement, explicitly not salary | One-off reimbursement | Correct nonrecurrence; missing values/context unresolved. |
| message_123 | Gig payout pending, not withdrawable | Next pending payout | Correct noncash certainty; missing amount must not trigger guessing. |
| message_152 | Refund initiated, not credited | Pending refund | Correct certainty; sent date substituted for effective date without explicit support. |
| message_163 | Indonesian: unsold investment value declined | Investment valuation | Correct noncash type; ongoing scope/date unnecessarily inferred. |
| message_165 | Indonesian: revised salary settlement date | Salary with explicit amendment/date | New date captured, but RESCHEDULE is the clearer contract type. |
| message_166 | Seasonal contract ended | Employment ended, missing date | Material fact retained; unknown date/target correctly needs reconciliation context. |

No sample financial output motivated these findings. The source-level defects justify clearer general contract instructions in checkpoint D. The frozen financial engine must not compensate for them.

Per-candidate validator reasons, accepted amendment identities and final complete/provisional states for all reviewed sources are recorded in phase3b-message-results.json. No manual reading is injected into production facts.
