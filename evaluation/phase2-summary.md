# Phase 2 sample baseline diagnostics

No recommendation selection, evidence extraction, or final output.csv. Only complete structured cases are scored. Provisional numbers are not validated capacity.

| Request | Evidence | Safe today | Expected | Earliest full | Expected | Likely mismatch cause |
|---|---|---:|---:|---|---|---|
| request_01 | complete | 4642.55 | 25256 | — | 2024-03-03 | recurrence / variable-spending estimator; boundary timing uncalibrated |
| request_02 | unresolved | 15875832.33 | 17229139.2 | 2025-10-15 | 2025-09-15 | unresolved evidence |
| request_03 | unresolved | 832382.23 | 873000 | 2019-11-15 | 2019-11-15 | unresolved evidence |
| request_04 | unresolved | 8289097.63 | 8401800 | 2024-06-15 | 2024-06-15 | unresolved evidence |
| request_05 | complete | 0.00 | 737 | — | — | recurrence / variable-spending estimator; boundary timing uncalibrated |
| request_06 | unresolved | 0.00 | 603.3 | — | 2026-01-15 | unresolved evidence |
| request_07 | unresolved | 0.00 | 87170.56 | — | 2024-10-23 | unresolved evidence |
| request_08 | unresolved | 0.00 | 284.57 | — | 2025-04-15 | unresolved evidence |
| request_09 | complete | 0.00 | 166.61 | — | 2026-07-04 | recurrence / variable-spending estimator; boundary timing uncalibrated |
| request_10 | unresolved | 0.00 | 12700 | — | — | unresolved evidence |
| request_11 | unresolved | 8135067.67 | 12510645 | 2025-07-15 | 2025-07-15 | unresolved evidence |
| request_12 | unresolved | 53549.58 | 65164 | — | 2026-04-05 | unresolved evidence |
| request_13 | complete | 200.85 | 433.4 | — | 2024-05-15 | recurrence / variable-spending estimator; boundary timing uncalibrated |
| request_14 | unresolved | 0.00 | 597.74 | — | — | unresolved evidence |
| request_15 | unresolved | 0.00 | 83.05 | — | — | unresolved evidence |
| request_16 | unresolved | 122500 | 122500 | 2023-08-12 | 2023-08-12 | unresolved evidence |
| request_17 | unresolved | 234898.43 | 243849.58 | 2026-05-15 | 2026-03-15 | unresolved evidence |
| request_18 | unresolved | 471.97 | 462 | 2026-09-15 | 2026-09-15 | unresolved evidence |
| request_19 | unresolved | 12394.78 | 28820 | 2024-10-15 | 2024-09-15 | unresolved evidence |
| request_20 | unresolved | 8306.63 | 5400 | — | — | unresolved evidence |
| request_21 | complete | 1535.26 | 1543.35 | 2026-04-15 | 2026-04-15 | recurrence / variable-spending estimator; boundary timing uncalibrated |
| request_22 | unresolved | 425.17 | 475.46 | 2025-02-15 | 2025-01-15 | unresolved evidence |
| request_23 | unresolved | 4171.49 | 9152 | — | 2025-07-15 | unresolved evidence |
| request_24 | unresolved | 9900.62 | 13420 | — | — | unresolved evidence |
| request_25 | complete | 0.00 | 1425000 | — | — | recurrence / variable-spending estimator; boundary timing uncalibrated |

Counts: {'total': 25, 'complete': 6, 'amount_matches': 0, 'date_matches': 3, 'both_match': 0, 'unresolved': 19}

Likely-cause labels are hypotheses, not isolated causal diagnoses. No policy thresholds were tuned to sample labels. Full traces include the exact low-water checkpoint, series, explicit income, and reservations. Resolve evidence before attributing provisional mismatches.

```text
request_01: COMPLETE STRUCTURED BASELINE
Horizon: 2024-03-03 through 2024-06-01 inclusive
Opening=58481.1; required minimum=18000; low-water=22642.55 on 2024-06-01 (series:transport|*|debit|ZAR)
Pending reserved=567.6; explicit future income=23320; baseline safe=True
amount_safe_to_pay=4642.55; earliest_date_for_full_payment=None

Series: debt_repayment 3487 ZAR/monthly; delivery_membership 306.9 ZAR/monthly; dining 86.70 ZAR/daily; education 1821.6 ZAR/monthly; groceries 128.44 ZAR/daily; music_subscription 235.4 ZAR/monthly; rent 5148 ZAR/monthly; transport 71.86 ZAR/daily; utilities 1541.75 ZAR/monthly
```

```text
request_02: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2025-08-05 through 2025-11-03 inclusive
Opening=60383889.2; required minimum=29158400; low-water=45034232.33 on 2025-08-15 (series:transport|*|debit|IDR)
Pending reserved=1651100; explicit future income=0; baseline safe=True
amount_safe_to_pay=15875832.33; earliest_date_for_full_payment=2025-10-15
UNRESOLVED: unresolved message message_01: extraction not implemented
Series: cloud_storage 369550 IDR/monthly; dining 55554.52 IDR/daily; education 3040000 IDR/monthly; entertainment 1352563.79 IDR/monthly; groceries 219247.55 IDR/daily; healthcare 1594883.08 IDR/monthly; housing 3534000 IDR/monthly; insurance 1132400 IDR/monthly; salary 33345000 IDR/monthly; transport 94953.39 IDR/daily; utilities 2141849.94 IDR/monthly
```

```text
request_03: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2019-09-03 through 2019-12-02 inclusive
Opening=5810300; required minimum=2668700; low-water=3501082.23 on 2019-09-15 (series:transport|*|debit|IDR)
Pending reserved=95000; explicit future income=0; baseline safe=True
amount_safe_to_pay=832382.23; earliest_date_for_full_payment=2019-11-15
UNRESOLVED: unresolved message message_02: extraction not implemented
UNRESOLVED: unresolved image image_01: extraction not implemented
UNRESOLVED: missing amount event_253: never substituted with zero
Series: cloud_storage 20900 IDR/monthly; dining 8152.00 IDR/daily; groceries 22157.89 IDR/daily; rent 1140000 IDR/monthly; salary 4365000 IDR/monthly; shopping 180395.29 IDR/monthly; streaming 117800 IDR/monthly; transport 5058.74 IDR/daily; utilities 295330.29 IDR/monthly
```

```text
request_04: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2024-06-04 through 2024-09-02 inclusive
Opening=52206950; required minimum=30686600; low-water=38975697.63 on 2024-06-15 (series:transport|*|debit|IDR)
Pending reserved=0; explicit future income=0; baseline safe=True
amount_safe_to_pay=8289097.63; earliest_date_for_full_payment=2024-06-15
UNRESOLVED: unresolved message message_03: extraction not implemented
Series: delivery_membership 377150 IDR/monthly; dining 147689.94 IDR/daily; entertainment 1484369.68 IDR/monthly; groceries 242611.19 IDR/daily; gym 1027900 IDR/monthly; music_subscription 332500 IDR/monthly; rent 12293000 IDR/monthly; salary 38190000 IDR/monthly; transport 133692.98 IDR/daily; utilities 2017103.37 IDR/monthly
```

```text
request_05: COMPLETE STRUCTURED BASELINE
Horizon: 2025-11-06 through 2026-02-04 inclusive
Opening=46475.1; required minimum=13100; low-water=6573.01 on 2026-02-04 (series:transport|*|debit|ZAR)
Pending reserved=0; explicit future income=0; baseline safe=False
amount_safe_to_pay=0.00; earliest_date_for_full_payment=None

Series: cloud_storage 113.3 ZAR/monthly; debt_repayment 968 ZAR/monthly; family_support 840.4 ZAR/monthly; groceries 115.33 ZAR/daily; healthcare 722.37 ZAR/monthly; rent 4972 ZAR/monthly; shopping 420.31 ZAR/monthly; transport 34.69 ZAR/daily; utilities 713.71 ZAR/monthly
```

```text
request_06: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2026-01-03 through 2026-04-03 inclusive
Opening=1942.4; required minimum=800; low-water=-1335.48 on 2026-04-03 (series:transport|*|debit|EUR)
Pending reserved=0; explicit future income=0; baseline safe=False
amount_safe_to_pay=0.00; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_04: extraction not implemented
Series: cloud_storage 5 EUR/monthly; dining 7.61 EUR/daily; entertainment 38.33 EUR/monthly; groceries 5.14 EUR/daily; insurance 26 EUR/monthly; rent 254.1 EUR/monthly; shopping 41.44 EUR/monthly; streaming 19 EUR/monthly; transport 5.90 EUR/daily; utilities 58.34 EUR/monthly
```

```text
request_07: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2024-09-05 through 2024-12-04 inclusive
Opening=218945.56; required minimum=93000; low-water=-50852.85 on 2024-12-04 (series:transport|*|debit|INR)
Pending reserved=0; explicit future income=0; baseline safe=False
amount_safe_to_pay=0.00; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_05: extraction not implemented
Series: debt_repayment 15650 INR/monthly; dining 309.24 INR/daily; groceries 565.28 INR/daily; music_subscription 1005 INR/monthly; rent 34200 INR/monthly; transport 175.76 INR/daily; utilities 7219.31 INR/monthly
```

```text
request_08: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2025-02-07 through 2025-05-08 inclusive
Opening=1536.57; required minimum=800; low-water=-2912.34 on 2025-05-08 (series:transport|*|debit|EUR)
Pending reserved=0; explicit future income=0; baseline safe=False
amount_safe_to_pay=0.00; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_06: extraction not implemented
Series: debt_repayment 177 EUR/monthly; delivery_membership 24 EUR/monthly; dining 4.01 EUR/daily; education 89 EUR/monthly; groceries 9.86 EUR/daily; music_subscription 14 EUR/monthly; rent 467.5 EUR/monthly; transport 5.94 EUR/daily; utilities 80.9 EUR/monthly
```

```text
request_09: COMPLETE STRUCTURED BASELINE
Horizon: 2026-07-04 through 2026-10-02 inclusive
Opening=2231.1; required minimum=600; low-water=510.84 on 2026-10-02 (series:transport|*|debit|EUR)
Pending reserved=0; explicit future income=0; baseline safe=False
amount_safe_to_pay=0.00; earliest_date_for_full_payment=None

Series: cloud_storage 5 EUR/monthly; dining 1.57 EUR/daily; groceries 5.11 EUR/daily; rent 211.2 EUR/monthly; shopping 28.32 EUR/monthly; streaming 20 EUR/monthly; transport 1.30 EUR/daily; utilities 66.84 EUR/monthly
```

```text
request_10: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2024-12-06 through 2025-03-06 inclusive
Opening=750155; required minimum=225400; low-water=139117.56 on 2025-03-06 (series:transport|*|debit|INR)
Pending reserved=0; explicit future income=0; baseline safe=False
amount_safe_to_pay=0.00; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_07: extraction not implemented
Series: delivery_membership 1895 INR/monthly; dining 687.23 INR/daily; entertainment 4883.78 INR/monthly; groceries 1718.22 INR/daily; gym 4860 INR/monthly; music_subscription 2800 INR/monthly; rent 69100 INR/monthly; transport 969.36 INR/daily; utilities 17771.13 INR/monthly
```

```text
request_11: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2025-05-03 through 2025-08-01 inclusive
Opening=63531795; required minimum=34140600; low-water=42275667.67 on 2025-07-15 (series:transport|*|debit|IDR)
Pending reserved=0; explicit future income=0; baseline safe=True
amount_safe_to_pay=8135067.67; earliest_date_for_full_payment=2025-07-15
UNRESOLVED: unresolved message message_08: extraction not implemented
Series: cloud_storage 168150 IDR/monthly; dining 71601.69 IDR/daily; education 2544100 IDR/monthly; entertainment 1674887.61 IDR/monthly; groceries 161429.17 IDR/daily; healthcare 3118089.32 IDR/monthly; housing 2954500 IDR/monthly; insurance 1881000 IDR/monthly; salary 23256000 IDR/monthly; transport 87879.75 IDR/daily; utilities 2891149.67 IDR/monthly
```

```text
request_12: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2026-04-05 through 2026-07-04 inclusive
Opening=193089.89; required minimum=43200; low-water=96749.58 on 2026-07-04 (series:transport|*|debit|ZAR)
Pending reserved=0; explicit future income=0; baseline safe=True
amount_safe_to_pay=53549.58; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_09: extraction not implemented
Series: cloud_storage 447.7 ZAR/monthly; dining 116.77 ZAR/daily; groceries 244.80 ZAR/daily; rent 11792 ZAR/monthly; shopping 1267.67 ZAR/monthly; streaming 1504.8 ZAR/monthly; transport 79.96 ZAR/daily; utilities 3708.19 ZAR/monthly
```

```text
request_13: COMPLETE STRUCTURED BASELINE
Horizon: 2024-03-07 through 2024-06-05 inclusive
Opening=2789.52; required minimum=1300; low-water=1500.85 on 2024-05-15 (series:transport|*|debit|EUR)
Pending reserved=0; explicit future income=1343.54; baseline safe=True
amount_safe_to_pay=200.85; earliest_date_for_full_payment=None

Series: delivery_membership 21 EUR/monthly; dining 5.04 EUR/daily; entertainment 33.83 EUR/monthly; groceries 16.37 EUR/daily; gym 61 EUR/monthly; music_subscription 29 EUR/monthly; rent 622.6 EUR/monthly; salary 1343.54 EUR/monthly; transport 7.21 EUR/daily; utilities 146.33 EUR/monthly
```

```text
request_14: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2025-08-04 through 2025-11-02 inclusive
Opening=3931.74; required minimum=2200; low-water=-2321.23 on 2025-11-02 (series:transport|*|debit|EUR)
Pending reserved=0; explicit future income=0; baseline safe=False
amount_safe_to_pay=0.00; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_10: extraction not implemented
Series: cloud_storage 14 EUR/monthly; debt_repayment 350 EUR/monthly; family_support 226 EUR/monthly; groceries 17.38 EUR/daily; healthcare 92.65 EUR/monthly; rent 688.6 EUR/monthly; shopping 140.39 EUR/monthly; transport 4.00 EUR/daily; utilities 153.69 EUR/monthly
```

```text
request_15: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2026-01-06 through 2026-04-06 inclusive
Opening=1770.05; required minimum=1200; low-water=-2297.37 on 2026-04-06 (series:transport|*|debit|EUR)
Pending reserved=0; explicit future income=0; baseline safe=False
amount_safe_to_pay=0.00; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_11: extraction not implemented
Series: debt_repayment 84 EUR/monthly; delivery_membership 27 EUR/monthly; dining 3.23 EUR/daily; education 159 EUR/monthly; groceries 9.72 EUR/daily; music_subscription 11 EUR/monthly; rent 435.6 EUR/monthly; transport 5.25 EUR/daily; utilities 87.14 EUR/monthly
```

```text
request_16: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2023-08-12 through 2023-11-10 inclusive
Opening=362370; required minimum=122400; low-water=352659.32 on 2023-09-15 (series:transport|*|debit|INR)
Pending reserved=0; explicit future income=0; baseline safe=True
amount_safe_to_pay=122500; earliest_date_for_full_payment=2023-08-12
UNRESOLVED: unresolved message message_12: extraction not implemented
UNRESOLVED: unresolved image image_02: extraction not implemented
UNRESOLVED: missing amount event_1442: never substituted with zero
Series: cloud_storage 1055 INR/monthly; debt_repayment 17750 INR/monthly; dining 421.79 INR/daily; groceries 1185.80 INR/daily; rent 57100 INR/monthly; salary 173000 INR/monthly; shopping 10178.56 INR/monthly; streaming 3510 INR/monthly; transport 723.96 INR/daily; utilities 11512.87 INR/monthly
```

```text
request_17: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2026-03-01 through 2026-05-30 inclusive
Opening=550379.58; required minimum=166100; low-water=400998.43 on 2026-03-15 (series:transport|*|debit|INR)
Pending reserved=0; explicit future income=206000; baseline safe=True
amount_safe_to_pay=234898.43; earliest_date_for_full_payment=2026-05-15
UNRESOLVED: unresolved image image_03: extraction not implemented
UNRESOLVED: missing amount event_1545: never substituted with zero
Series: debt_repayment 30200 INR/monthly; delivery_membership 1675 INR/monthly; dining 477.78 INR/daily; education 13660 INR/monthly; groceries 1490.29 INR/daily; music_subscription 2055 INR/monthly; rent 49600 INR/monthly; salary 206000 INR/monthly; transport 848.13 INR/daily; utilities 9948.15 INR/monthly
```

```text
request_18: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2026-07-07 through 2026-10-05 inclusive
Opening=2486; required minimum=1400; low-water=1871.97 on 2026-07-15 (series:transport|*|debit|EUR)
Pending reserved=0; explicit future income=0; baseline safe=True
amount_safe_to_pay=471.97; earliest_date_for_full_payment=2026-09-15
UNRESOLVED: unresolved message message_13: extraction not implemented
Series: dining 7.28 EUR/daily; groceries 10.65 EUR/daily; healthcare 162.41 EUR/monthly; housing 167 EUR/monthly; insurance 68 EUR/monthly; salary 2310 EUR/monthly; streaming 68 EUR/monthly; transport 3.62 EUR/daily; utilities 121.67 EUR/monthly
```

```text
request_19: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2024-09-04 through 2024-12-03 inclusive
Opening=199545; required minimum=92800; low-water=105194.78 on 2024-09-15 (series:transport|*|debit|INR)
Pending reserved=0; explicit future income=0; baseline safe=True
amount_safe_to_pay=12394.78; earliest_date_for_full_payment=2024-10-15
UNRESOLVED: unresolved image image_04: extraction not implemented
UNRESOLVED: missing amount event_1700: never substituted with zero
Series: cloud_storage 395 INR/monthly; debt_repayment 11850 INR/monthly; family_support 12650 INR/monthly; groceries 772.32 INR/daily; healthcare 8946.09 INR/monthly; rent 36100 INR/monthly; salary 131000 INR/monthly; shopping 6069.58 INR/monthly; transport 245.21 INR/daily; utilities 6129.19 INR/monthly
```

```text
request_20: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2026-02-07 through 2026-05-08 inclusive
Opening=102609.05; required minimum=64500; low-water=72806.63 on 2026-02-15 (series:transport|*|debit|INR)
Pending reserved=4470; explicit future income=0; baseline safe=True
amount_safe_to_pay=8306.63; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_14: extraction not implemented
UNRESOLVED: unresolved image image_05: extraction not implemented
UNRESOLVED: missing amount event_1786: never substituted with zero
Series: cloud_storage 365 INR/monthly; dining 181.15 INR/daily; education 8740 INR/monthly; entertainment 2279.67 INR/monthly; groceries 410.42 INR/daily; healthcare 6654.33 INR/monthly; housing 7950 INR/monthly; insurance 3290 INR/monthly; salary 108000 INR/monthly; transport 218.81 INR/daily; utilities 7977.68 INR/monthly
```

```text
request_21: COMPLETE STRUCTURED BASELINE
Horizon: 2026-04-03 through 2026-07-02 inclusive
Opening=3911.35; required minimum=1800; low-water=3335.26 on 2026-04-15 (series:transport|*|debit|USD)
Pending reserved=53; explicit future income=2256; baseline safe=True
amount_safe_to_pay=1535.26; earliest_date_for_full_payment=2026-04-15

Series: cloud_storage 11 USD/monthly; dining 4.66 USD/daily; groceries 9.57 USD/daily; rent 718.8 USD/monthly; salary 2256 USD/monthly; shopping 126.38 USD/monthly; streaming 47 USD/monthly; transport 2.28 USD/daily; utilities 124.08 USD/monthly
```

```text
request_22: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2024-12-05 through 2025-03-05 inclusive
Opening=1132.46; required minimum=500; low-water=925.17 on 2024-12-15 (series:transport|*|debit|EUR)
Pending reserved=43; explicit future income=0; baseline safe=True
amount_safe_to_pay=425.17; earliest_date_for_full_payment=2025-02-15
UNRESOLVED: unresolved message message_15: extraction not implemented
Series: delivery_membership 5 EUR/monthly; dining 1.32 EUR/daily; entertainment 22.03 EUR/monthly; groceries 3.91 EUR/daily; gym 17 EUR/monthly; music_subscription 6 EUR/monthly; rent 178.2 EUR/monthly; salary 616 EUR/monthly; transport 2.20 EUR/daily; utilities 32.53 EUR/monthly
```

```text
request_23: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2025-05-07 through 2025-08-05 inclusive
Opening=51957.9; required minimum=27000; low-water=31171.49 on 2025-05-15 (series:transport|*|debit|ZAR)
Pending reserved=1553.2; explicit future income=0; baseline safe=True
amount_safe_to_pay=4171.49; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_16: extraction not implemented
Series: cloud_storage 295.9 ZAR/monthly; debt_repayment 5852 ZAR/monthly; family_support 4270.2 ZAR/monthly; groceries 283.02 ZAR/daily; healthcare 1377.89 ZAR/monthly; rent 15312 ZAR/monthly; salary 45760 ZAR/monthly; shopping 1389.39 ZAR/monthly; transport 69.20 ZAR/daily; utilities 2877.85 ZAR/monthly
```

```text
request_24: PROVISIONAL / UNRESOLVED EVIDENCE
Horizon: 2026-01-04 through 2026-04-04 inclusive
Opening=85045; required minimum=51000; low-water=60900.62 on 2026-01-15 (series:transport|*|debit|INR)
Pending reserved=0; explicit future income=0; baseline safe=True
amount_safe_to_pay=9900.62; earliest_date_for_full_payment=None
UNRESOLVED: unresolved message message_17: extraction not implemented
Series: cloud_storage 355 INR/monthly; dining 305.39 INR/daily; entertainment 1916.16 INR/monthly; groceries 243.92 INR/daily; insurance 2510 INR/monthly; rent 18600 INR/monthly; salary 61000 INR/monthly; shopping 2564 INR/monthly; streaming 1200 INR/monthly; transport 307.25 INR/daily; utilities 3490.5 INR/monthly
```

```text
request_25: COMPLETE STRUCTURED BASELINE
Horizon: 2024-03-06 through 2024-06-04 inclusive
Opening=32063050; required minimum=23379100; low-water=23113981.00 on 2024-03-15 (series:transport|*|debit|IDR)
Pending reserved=0; explicit future income=28499994.00; baseline safe=False
amount_safe_to_pay=0.00; earliest_date_for_full_payment=None

Series: cloud_storage 126350 IDR/monthly; dining 161862.39 IDR/daily; entertainment 499510.22 IDR/monthly; groceries 138856.92 IDR/daily; insurance 904400 IDR/monthly; rent 6954000 IDR/monthly; salary 1800 USD/monthly; shopping 1170271.29 IDR/monthly; streaming 573800 IDR/monthly; transport 132600.30 IDR/daily; utilities 1341541.39 IDR/monthly
```
