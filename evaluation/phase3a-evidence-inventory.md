# Phase 3A evidence inventory

Metadata only: no message interpretation, OCR, model calls, or solved-label access. Counts include request-specific and user-level evidence available by the request date. Images have no observed timestamp in the CSV and remain unresolved until observation context is established.

| Cohort | Requests | Messages | Images | Both | Linked evidence | Complete | Provisional | Provisional solely uninterpreted evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| requests.csv | 250 | 198 | 11 | 9 | 41 | 50 | 200 | 200 |
| sample_requests.csv | 25 | 17 | 5 | 3 | 7 | 6 | 19 | 19 |

“Solely uninterpreted” includes missing structured amounts whose events have mapped evidence, and excludes missing rates/other issues. It does not claim future extraction will successfully resolve those sources.

| All supplied rows (samples + evaluation) | Count |
|---|---:|
| message_rows | 215 |
| image_rows | 16 |
| mapped_message_rows | 39 |
| mapped_image_rows | 16 |
| missing_amount_events | 16 |
| missing_amount_events_with_evidence | 16 |
| message_source_types | {'bank': 18, 'employer': 126, 'financial_service': 23, 'merchant': 17, 'service_provider': 31} |
| image_source_types | {'IMAGE': 16} |

All 250 evaluation requests and 25 samples pass the empty-evidence-adapter comparison for safe amount, earliest date, baseline safety and completeness. Structured-complete requests retain their financial outputs. Raw evidence has not been converted into fixtures for these real requests.

Synthetic end-to-end tests cover ongoing/next-pay salary, reschedule, final payroll, refund/reimbursement, approved invoice, investment sale/value, outstanding invoice, hypothetical income, ambiguous image, cancellation and provenance.

```powershell
.\.venv\Scripts\python.exe code/evaluation/evidence_inventory.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe code/evaluation/semantics.py
```
