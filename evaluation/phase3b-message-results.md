# Phase 3B message diagnostics

Run status: **REAL_BATCH_AVAILABLE**.

Cache-only report; no model calls, no fake real-message facts. Missing extraction is not a no-fact result.

## Extraction

```json
{
  "messages_total": 215,
  "statuses": {
    "SUCCESS": 157,
    "UNRESOLVED_SUCCESS": 17,
    "PERMANENT_PARSE_FAILURE": 29,
    "NON_ACTIONABLE_SUCCESS": 12
  },
  "successful_parse": 186,
  "no_fact": 12,
  "facts_by_type": {
    "PAYMENT_RECEIVED": 26,
    "SALARY": 108,
    "EXPENSE": 1,
    "INVESTMENT_SALE": 3,
    "INVOICE_APPROVED": 3,
    "PENDING_PAYOUT": 7,
    "REIMBURSEMENT": 3,
    "REFUND": 7,
    "INVESTMENT_VALUE": 6,
    "EMPLOYMENT_ENDED": 2,
    "NON_FINANCIAL": 1
  },
  "facts_by_certainty": {
    "CONFIRMED": 146,
    "PENDING": 21
  },
  "facts_by_scope": {
    "ONE_OFF": 79,
    "NEXT_OCCURRENCE_ONLY": 35,
    "ONGOING": 26,
    "EVENT_SPECIFIC": 14,
    "FROM_DATE": 13
  },
  "facts_by_amount_meaning": {
    "amount_received": 4,
    "amount_paid": 39,
    "net_pay": 100,
    "sale_proceeds": 4,
    "invoice_amount": 3,
    "gross_pay": 2,
    "balance_due": 6,
    "valuation": 6,
    "unknown": 3
  },
  "ambiguity": {
    "AMBIGUOUS_DATE": 0,
    "AMBIGUOUS_CURRENCY": 0,
    "UNRESOLVED_TARGET": 8
  },
  "multi_fact_messages": 10
}
```

## Evaluation request integration

```json
{
  "complete_before": 50,
  "complete_after": 90,
  "provisional_before": 200,
  "provisional_after": 160,
  "financially_changed": 0,
  "safe_changed": 0,
  "earliest_changed": 0,
  "baseline_safety_changed": 0,
  "unresolved_messages": 157,
  "unresolved_both": 8,
  "unresolved_images_only": 0
}
```

Validation: {'UNRESOLVED': 140, 'REJECTED': 41}
Remaining reasons: {'INVALID_DATES': 18, 'MISSING_LINK': 99, 'CONFLICTING_EVIDENCE': 16, 'MISSING_AMOUNT': 3, 'SOURCE_EVENT_MISMATCH': 1, 'AMBIGUOUS_AMOUNT_MEANING': 1, 'UNSUPPORTED_SCOPE': 1, 'INSUFFICIENT_CONTEXT': 1}

## Samples and manual review

Sample details are evaluation-only in JSON. Manual-review candidates are selected by distinct type/certainty/scope combinations and multi-fact messages, not financial mismatch.

| Message | Type | Certainty | Scope | Decision | Reason |
|---|---|---|---|---|---|
| message_75 | PAYMENT_RECEIVED | CONFIRMED | ONE_OFF | UNRESOLVED | INVALID_DATES |
| message_77 | SALARY | CONFIRMED | NEXT_OCCURRENCE_ONLY | UNRESOLVED | MISSING_LINK |
| message_78 | SALARY | CONFIRMED | ONGOING | UNRESOLVED | INVALID_DATES |
| message_79 | NON_FINANCIAL | DISPUTED | ONE_OFF | UNRESOLVED | CONFLICTING_EVIDENCE |
| message_80 | SALARY | CONFIRMED | ONE_OFF | UNRESOLVED | MISSING_LINK |
| message_83 | PAYMENT_RECEIVED | CONFIRMED | EVENT_SPECIFIC | UNRESOLVED | MISSING_LINK |
| message_86 | EXPENSE | CONFIRMED | EVENT_SPECIFIC | UNRESOLVED | MISSING_AMOUNT |
| message_89 | SALARY | CONFIRMED | FROM_DATE | UNRESOLVED | MISSING_LINK |
| message_92 | INVESTMENT_SALE | CONFIRMED | ONE_OFF | UNRESOLVED | INVALID_DATES |
| message_93 | INVOICE_APPROVED | CONFIRMED | ONE_OFF | UNRESOLVED | INVALID_DATES |
| message_96 | PENDING_PAYOUT | PENDING | ONE_OFF | REJECTED | PENDING_NOT_CASH |
| message_103 | NON_FINANCIAL | CONFIRMED | ONE_OFF | REJECTED | NON_FINANCIAL |
| message_108 | INVESTMENT_SALE | CONFIRMED | EVENT_SPECIFIC | REJECTED | PAST_CASH_IN_SNAPSHOT |
| message_109 | PAYMENT_RECEIVED | PENDING | ONE_OFF | REJECTED | PENDING_NOT_CASH |
| message_117 | REIMBURSEMENT | CONFIRMED | ONE_OFF | UNRESOLVED | INVALID_DATES |
| message_123 | PENDING_PAYOUT | PENDING | NEXT_OCCURRENCE_ONLY | REJECTED | PENDING_NOT_CASH |
| message_152 | REFUND | PENDING | ONE_OFF | REJECTED | PENDING_NOT_CASH |
| message_163 | INVESTMENT_VALUE | CONFIRMED | ONGOING | REJECTED | VALUATION_NOT_CASH |
| message_165 | SALARY | CONFIRMED | EVENT_SPECIFIC | UNRESOLVED | MISSING_LINK |
| message_166 | EMPLOYMENT_ENDED | CONFIRMED | EVENT_SPECIFIC | UNRESOLVED | UNSUPPORTED_SCOPE |

This table is a review queue, not a claim that manual semantic review has been completed.
