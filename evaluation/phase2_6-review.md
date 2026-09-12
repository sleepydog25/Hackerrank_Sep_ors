# Phase 2.6 adversarial review

Reviewed `a586391..32f1b05` read-only before making final documentation fixes. Also checked that `226adac..HEAD -- code/buy_or_wait` is empty. Production financial behavior has not changed in Phase 2.6.

## Findings and disposition

| Priority | Finding | Evidence | Resolution |
|---|---|---|---|
| P0 | None confirmed | No changed money kernel or dataset writes | No action |
| P1 | None confirmed | Full safety-window semantics and independent replay agree | No action |
| P2 | Restart handoff could suggest redoing already committed work | Checkpoint C RESUME.md, “Exact next action,” still begins with commit C; older docs/financial-core.md “Before Phase 3” asks for renewed calibration | Final RESUME points to completed checkpoints and evidence normalization. Core docs and README now identify Phase 2.6 as latest; historical reports remain historical. |
| P3 | Evaluation reproducer requires Git history including 226adac | code/evaluation/semantics.py:16 and archive call | Documented dependency; appropriate for repository checkpoint recovery, not the eventual standalone solver package |

No confirmed production P0/P1/P2 defect arose from the three-question audit. No financially justified behavior was changed for sample score. Remaining estimator/unknown-source limitations are intentional model uncertainty, not hidden fixes deferred past this milestone.

## Financial and isolation checks

- **Boundary:** D+89 and D+90 expenses count, D+91 does not; full payment at D+90 is tested. Retained 91 closes are explicitly a conservative convention, not a falsely quoted specification formula.
- **Safety window:** earliest date independently replayed on all 91 dates for each of six complete cases, under both immutable old and current cores (1,092 candidate replays). A later essential debit can invalidate instant purchasing capacity. Later salary cannot repair an earlier breach. No rolling T+90 window was introduced.
- **Ordering and Decimal:** debit before credit before candidate; intraday breach checks retained. Production amounts/rates use Decimal and cent-floor capacity. Existing 200 synthetic direct/replay scenarios and 132 policy-case checks remain passing.
- **Expense scope:** protected/unprotected categories, reduce/stop permission, permission overlaps and flexible minimum amounts have explicit synthetic tests. None causes an automatic baseline reduction. No pending or recurring cash item was removed in this phase.
- **Future information:** recurrence history remains request-exclusive; scheduled salary is supplied future evidence, not a replay of future settled history into an estimator. Pending/unconfirmed credits, freelance extrapolation, and future-dated messages are not new income. Image/message facts remain unresolved. Financial-event dates are transaction dates, not a supplied ingestion timestamp; do not invent an availability timestamp from them.
- **Identity and sample isolation:** request/user identifiers still perform necessary loading, joins, ownership validation, evidence association, and trace identity. They do not select numerical policies. No solved ID/amount override exists in production; expected outputs are read only by evaluation. Synthetic identifiers are not solved cases.
- **Reproduction:** old and new cores run in separate processes. The old core comes from the participant's own accepted Git tree; only `code/buy_or_wait` is extracted to a temporary directory and cleaned up. All 250 before/after comparisons are recorded; no regression is concealed.
- **Dataset integrity:** working and staged dataset changes absent; no final output.csv. All intended artifacts are tracked, while virtualenv, caches, log and temporary ledgers remain ignored. Ordinary final diff/status must be empty after checkpoint D.
- **Tests:** 14 added tests describe boundary/expense/payment invariants, not expected sample labels. Full suite: 84 passing. The 250-request smoke test has 50 complete structured contexts and 200 explicitly provisional contexts.

## Final decision

**READY FOR PHASE 3 — Evidence Normalization Layer.** Horizon ambiguity is documented; baseline expense and earliest-date semantics are resolved as far as the contract allows. No concrete unresolved semantic defect blocks evidence normalization. This does not authorize payment-plan optimization, another baseline-fitting phase, external model calls in Phase 2.6, or treating unresolved forecasts as final recommendations.

Reproduce with the commands in RESUME.md and phase2_6-results.md. The final checkpoint containing this review is discoverable with `git log -1 --format=%H -- evaluation/phase2_6-review.md`; this avoids a self-referential commit hash inside the commit itself.
