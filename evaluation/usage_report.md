# Final submitted run usage

Strategy: deterministic S0, all 250 evaluation requests, frozen 90-day Python forecast
and Phase 3A reconciliation with no probabilistic evidence batches.

| Item | Final run |
|---|---:|
| Model provider / model | None / none |
| Model calls (external) | 0 |
| Cache hits / misses | 0 / 0 |
| Input tokens | 0 |
| Output tokens | 0 |
| Total tokens | 0 |
| Average tokens per request | 0 |
| Estimated total cost (USD) | 0 |
| Estimated cost per request (USD) | 0 |

Unvalidated probabilistic message and image extraction was disabled for the final run.
No historical extraction cache is read, relabeled, or replayed. Unknown cash amounts
or FX rates prevent plan certification; other unprocessed evidence remains explicitly
unresolved. Optional spending changes are disabled. Baseline capacity fields retain
the frozen structured-data calculation and can be provisional where evidence is missing.

This report covers only the application run producing the submitted output, not
development experiments or coding-assistant usage. Historical development usage,
including unknown attempts, remains separately documented and is not charged to this run.

Output SHA-256: `62a1801f90d4a20b569aea475a23f8b3712bd5d0f28fba502245cf5b7f4a89db`

Reproduce: `python code/main.py --dataset dataset --output output.csv`
Release: `python code/finalize_submission.py --dataset dataset`
