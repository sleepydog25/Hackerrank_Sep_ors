# Phase 3B message corpus audit

Deterministic metadata and overlapping keyword diagnostics only; no production keyword rules, financial interpretation, or solved-label access. Timing counts message/request pairs, including user-level messages. Near-empty means fewer than 10 stripped characters. Duplicate normalization casefolds and collapses punctuation/whitespace; it does not remove numbers or references.

| Metric | Value |
|---|---|
| messages | 215 |
| requests | 215 |
| users | 215 |
| source_types | {'bank': 18, 'employer': 126, 'financial_service': 23, 'merchant': 17, 'service_provider': 31} |
| linked | 39 |
| unlinked | 176 |
| request_relative_timing | {'before': 215} |
| empty | 0 |
| near_empty | 0 |
| duplicate_groups | {'exact': [], 'normalized': []} |
| length_characters | {'min': 127, 'p25': 230, 'median': 254, 'p75': 276, 'max': 330} |
| topics | {'bonus_commission': 17, 'duplicate_dispute': 5, 'employment_ended': 13, 'failed_retry': 4, 'freelance_gig': 31, 'internal_transfer': 5, 'investment': 10, 'invoice': 15, 'refund': 14, 'reimbursement': 2, 'rent': 31, 'salary_change': 46, 'salary_delay': 10, 'salary_payroll': 127, 'unknown': 19} |
| instruction_like | 0 |
| messages_per_request_distribution | {1: 215} |

English and Indonesian appear in the inspected corpus. Keyword coverage is exploratory and incomplete across languages. Instruction-like matches are risk signals, not proof of malicious content; synthetic attacks remain required even if none are detected.

Reproduce: `.\.venv\Scripts\python.exe code/evaluation/message_audit.py`.
