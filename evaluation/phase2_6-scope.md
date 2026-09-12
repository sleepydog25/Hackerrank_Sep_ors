# Dataset-wide expense-scope inventory

Counts are users or debit event rows, not currency totals. Both all supplied profiles and the evaluation-user subset are in the JSON. No image/message extraction or solved labels are used.

## all_profiles: 275 users, 23609 debit events

| Category | Protected users | Reduce users | Stop users | Debit events | Variable estimator | Event flexibility counts |
|---|---:|---:|---:|---:|---|---|
| cloud_storage | 0 | 0 | 109 | 833 | False | {'fixed': 286, 'stoppable': 547} |
| debt_repayment | 56 | 0 | 0 | 553 | False | {'fixed': 553} |
| delivery_membership | 0 | 0 | 41 | 351 | False | {'fixed': 146, 'stoppable': 205} |
| dining | 0 | 153 | 0 | 3479 | True | {'fixed': 1554, 'reducible': 1925} |
| education | 60 | 0 | 0 | 306 | False | {'fixed': 306} |
| entertainment | 0 | 44 | 0 | 521 | False | {'fixed': 301, 'reducible': 220} |
| family_support | 25 | 0 | 0 | 125 | False | {'fixed': 125} |
| groceries | 166 | 0 | 0 | 5812 | True | {'fixed': 5812} |
| gym | 0 | 14 | 12 | 170 | False | {'fixed': 60, 'reducible': 50, 'reducible_or_stoppable': 20, 'stoppable': 40} |
| healthcare | 44 | 0 | 0 | 356 | False | {'fixed': 356} |
| housing | 43 | 0 | 0 | 246 | False | {'fixed': 246} |
| insurance | 46 | 0 | 0 | 456 | False | {'fixed': 456} |
| investment | 0 | 0 | 0 | 29 | False | {'fixed': 29} |
| music_subscription | 0 | 0 | 58 | 451 | False | {'fixed': 161, 'stoppable': 290} |
| rent | 232 | 0 | 0 | 1355 | False | {'fixed': 1355} |
| shopping | 0 | 72 | 0 | 798 | False | {'fixed': 438, 'reducible': 360} |
| streaming | 0 | 66 | 84 | 683 | False | {'fixed': 136, 'reducible': 127, 'reducible_or_stoppable': 205, 'stoppable': 215} |
| transport | 109 | 0 | 0 | 5626 | True | {'fixed': 5626} |
| utilities | 105 | 0 | 0 | 1452 | False | {'fixed': 1452} |
| work_expense | 0 | 0 | 0 | 7 | False | {'fixed': 7} |

Profile overlaps: {'protect_reduce': {'profiles': 0, 'categories': {}}, 'protect_stop': {'profiles': 0, 'categories': {}}, 'reduce_stop': {'profiles': 45, 'categories': {'gym': 4, 'streaming': 41}}}

| Currency | Min field missing | Zero | Positive | Observed min / median / max | Median minimum/event ratio |
|---|---:|---:|---:|---|---:|
| EUR | 4614 | 0 | 586 | 9.5 / 25.25 / 51.6 | 0.5 |
| IDR | 4121 | 0 | 534 | 58900 / 501600 / 810350 | 0.5 |
| INR | 5364 | 0 | 740 | 530 / 2105 / 4796 | 0.4969798531913913535326344688 |
| USD | 3033 | 0 | 441 | 8 / 32 / 64.5 | 0.5 |
| ZAR | 3570 | 0 | 606 | 161.04 / 545.6 / 1197.9 | 0.4843366975905156375039338540 |

Minimum-field presence by flexibility: {'fixed': {'missing': 19405}, 'reducible': {'positive': 2682}, 'reducible_or_stoppable': {'positive': 225}, 'stoppable': {'missing': 1297}}

## evaluation_users: 250 users, 21479 debit events

| Category | Protected users | Reduce users | Stop users | Debit events | Variable estimator | Event flexibility counts |
|---|---:|---:|---:|---:|---|---|
| cloud_storage | 0 | 0 | 99 | 757 | False | {'fixed': 260, 'stoppable': 497} |
| debt_repayment | 51 | 0 | 0 | 502 | False | {'fixed': 502} |
| delivery_membership | 0 | 0 | 36 | 311 | False | {'fixed': 131, 'stoppable': 180} |
| dining | 0 | 141 | 0 | 3201 | True | {'fixed': 1425, 'reducible': 1776} |
| education | 53 | 0 | 0 | 270 | False | {'fixed': 270} |
| entertainment | 0 | 39 | 0 | 471 | False | {'fixed': 276, 'reducible': 195} |
| family_support | 21 | 0 | 0 | 105 | False | {'fixed': 105} |
| groceries | 149 | 0 | 0 | 5264 | True | {'fixed': 5264} |
| gym | 0 | 12 | 11 | 150 | False | {'fixed': 55, 'reducible': 40, 'reducible_or_stoppable': 20, 'stoppable': 35} |
| healthcare | 39 | 0 | 0 | 314 | False | {'fixed': 314} |
| housing | 39 | 0 | 0 | 223 | False | {'fixed': 223} |
| insurance | 43 | 0 | 0 | 419 | False | {'fixed': 419} |
| investment | 0 | 0 | 0 | 25 | False | {'fixed': 25} |
| music_subscription | 0 | 0 | 51 | 406 | False | {'fixed': 151, 'stoppable': 255} |
| rent | 211 | 0 | 0 | 1232 | False | {'fixed': 1232} |
| shopping | 0 | 65 | 0 | 729 | False | {'fixed': 404, 'reducible': 325} |
| streaming | 0 | 62 | 78 | 637 | False | {'fixed': 120, 'reducible': 127, 'reducible_or_stoppable': 185, 'stoppable': 205} |
| transport | 101 | 0 | 0 | 5137 | True | {'fixed': 5137} |
| utilities | 96 | 0 | 0 | 1320 | False | {'fixed': 1320} |
| work_expense | 0 | 0 | 0 | 6 | False | {'fixed': 6} |

Profile overlaps: {'protect_reduce': {'profiles': 0, 'categories': {}}, 'protect_stop': {'profiles': 0, 'categories': {}}, 'reduce_stop': {'profiles': 41, 'categories': {'gym': 4, 'streaming': 37}}}

| Currency | Min field missing | Zero | Positive | Observed min / median / max | Median minimum/event ratio |
|---|---:|---:|---:|---|---:|
| EUR | 3962 | 0 | 532 | 9.5 / 25 / 51.6 | 0.5 |
| IDR | 3728 | 0 | 500 | 148200 / 501600 / 810350 | 0.5 |
| INR | 4840 | 0 | 645 | 530 / 2105 / 4796 | 0.4977347987729313532291814802 |
| USD | 2988 | 0 | 422 | 8 / 32 / 64.5 | 0.5 |
| ZAR | 3293 | 0 | 569 | 193.6 / 545.6 / 1197.9 | 0.4895181734701085463578497932 |

Minimum-field presence by flexibility: {'fixed': {'missing': 17639}, 'reducible': {'positive': 2463}, 'reducible_or_stoppable': {'positive': 205}, 'stoppable': {'missing': 1172}}

## Field-to-engine mapping

- `category`, event type, amount, dates, direction, status and lifecycle links drive recurrence/reconciliation.
- Profile protection, willingness-to-reduce/stop, priorities, event flexibility and minimum_allowed_amount are loaded and retained, but do not automatically lower baseline reserves.
- This is intentional for optional changes: willingness is permission to consider a plan, not proof spending already stopped. Minimum amounts are potential reduction bounds, not replacement baseline amounts.
- Protection must veto future optional reductions even when willingness sets overlap. No such plan layer exists yet.
- Variable category membership is a modeling policy, not a claim every event is protected. Fixed recurring discretionary services also remain baseline expected spending.
- No scope change is independently justified by the contract. Adopted scope-rule impact is 0/250 amounts, dates and safety classifications; actual before/after replay is in the Phase 2.6 results.
