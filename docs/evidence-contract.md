# Evidence contract — Phase 3A

Interpretation can be probabilistic. Money cannot.

`EvidenceCandidate` is an untrusted typed extraction, not financial authorization. A future extractor targets the JSON format produced by `to_json`; decimal fields are strings and dates have distinct ISO meanings. `from_json` validates transport shape without treating a successful parse as accepted cash. Negative/zero/nonfinite values can reach semantic validation and cannot bypass it by parsing successfully.

`EvidenceSource` carries MESSAGE/IMAGE identity, user/request/event associations, observed timestamp and an optional trusted publisher identity. Message source categories such as bank/employer are not unique publisher identifiers. Unknown image timing/currency stays unknown. Candidate `original_label` preserves the extracted semantic label; it is never interpreted as an instruction.

Fact types distinguish salary, expense/rent, receipt, refund/reimbursement, approved invoice, pending payout, investment value/sale, cancellation, reschedule, employment ended and final payroll. Salary amount versus ongoing change uses scope plus explicit-amendment metadata, not separate enums for every wording. Amount meaning distinguishes net/gross pay, invoice total/balance/paid, tax, subtotal, late fee, valuation, sale proceeds and account balance. Scope distinguishes one event/next occurrence from ongoing/from/until/one-off applicability. Effective, payment, due and period dates are separate; date-dependent bill tiers can be represented as scoped candidates and may remain unresolved if the applicable tier is unknown.

`EvidenceDecision` is ACCEPTED, REJECTED or UNRESOLVED with a machine-readable reason. Only validation can wrap a candidate in `ValidatedEvidenceFact`; later reconciliation can still find conflicts. Confidence is diagnostic and never authorizes cash. `EvidenceBatch.exhaustive` tracks whether a source has been fully accounted for; one accepted number does not establish that a cropped image has been resolved.

Checkpoint A provides only schema/transport/tests. Checkpoint B must implement validation and deterministic normalized amendments, and Checkpoint C connects those amendments through a typed forecast interface. No external extractor, prompt, credential, API or model usage is part of Phase 3A. No sample label belongs in production.
