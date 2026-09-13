# Phase 3B adversarial review

Read-only first pass: full changes from frozen 7fc459e through C 93ef28f, including every production message module, evaluation adapter, launcher and offline tests. Findings below were recorded before D edits. No baseline or Phase 3A source change was identified as necessary.

| Priority | Finding | Location | Required action |
|---|---|---|---|
| P1 | A termination without a monetary amount was emitted as NO_FACT, exhausting a financially relevant source | message_extraction.SYSTEM_INSTRUCTION; manual review message_103 | Explicit nonmonetary financial coverage, English/Indonesian synthetic and live regression; version prompt |
| P2 | Invoice approval/settlement dates mapped to received payment/due date; unspecified salary promoted to net pay | same instruction; manual review | Define existing enum/date meanings explicitly; never infer net from salary; synthetic and live checks |
| P2 | Invalid results lose the local rejection reason, preventing root-cause analysis of 29 failures | message_cache.ExtractionStore.extract | Persist bounded allowlisted error detail and response hash/size, never raw error text or credentials |
| P2 | Global --refresh is accepted without explicit selection, making accidental paid re-extraction easy | evaluation/message_extract.main | Require explicit message selection for refresh |
| P3 | Development usage status counts combine cache hits with calls | message_usage.summarize | Label separate call/cache status counts; totals already correctly exclude cache hits |
| P3 | Report review queue is not actual manual review; prior C artifacts retained no full DTO replay | message_results | Link actual semantic review, preserve sanitized exact outputs separately for offline reproducibility |

Verified boundaries: source ownership is attached by application code; model output cannot supply provenance. Payload contains no balances, purchase amount, solved output or financial decision. Direct context has message/request cutoff gates, including later settlement exclusion. One-message inputs have no later-message ordering channel. JSON shape/duplicate keys/Decimal/date validation is closed and bounded. Pending/hypothetical/valuation/gross candidates cannot authorize cash through Phase 3A. Supported scopes, employer matching, cancellation/reschedule identities and duplicate amendments retain the frozen deterministic tests. Cache identity includes content/context, source, actual prompt/schema hashes and all three versions plus provider/model; in-flight intent precedes dispatch, retries are journaled, and cached replays incur zero usage. User-bound credential and operational cache are ignored. No request-specific branch or expected-output access exists in production.

No P0 found. Source-level model errors are probabilistic risks, not permission to tune baseline policy or fabricate missing fields. D must address the confirmed findings and retain unresolved evidence when context remains insufficient.

## Hardening performed and remaining blocker

Prompt message-2 fixed the inspected Indonesian termination omission, retained pending commission beside salary and improved payment-date extraction in the paid-model subset. Source-level verification is in the manual review. The batch then encountered HTTP 402; it was interrupted with one explicitly unknown attempt retained. A new P2 finding was that generic HTTP errors did not retain status and a batch could continue through account failures. HTTP status is now recorded without response bodies, and the batch stops on a provider failure or unknown in-flight attempt. A synthetic regression proves only one call is dispatched on an account error.

The user explicitly requested a free model. Live catalog metadata selected pinned NVIDIA Nemotron, then a bounded Nex-N2.5-Pro smoke. Neither initial free-model smoke preserved financial types reliably. Schema message-2 adds field-local enum/date definitions; prompt message-3 explicitly separates legitimate statements from adjacent instructions. This improved NVIDIA's high-level types, but ancillary meanings/scopes remain unreliable. Three real free-model messages were checked, then the corpus batch was stopped on observed semantic errors.

Extractor message-2 rejects direct quoted currency contradictions; message-3 rejects nonmonetary lifecycle facts mislabeled with context-only amount meanings. Message-4 additionally rejects gross-pay labels on non-payroll facts. These are general cross-field contradictions: without rejection, Phase 3A could discard a material fact as context and incorrectly exhaust its source. Regression tests and offline re-parsing prove the received-payment/gross-pay output is now rejected. No financial baseline/Phase 3A source was changed.

Global refresh now requires explicit message IDs. Call and cache-hit status counts are separate, with per-model usage totals. Cache-only inspection recognizes in-flight unknowns. Exact default-route cache identities remain unchanged; explicit upstream/reasoning choices enter new identities. All earlier cache namespaces remain intact.

**Remaining P1 extraction blocker:** the configured free model still produced unsupported currency/meaning/scope and incorrect financial types on real messages. A syntactically valid result is not reliable extraction. The synthetic smoke's `passed` fields cover only the stated checks; they are not comprehensive semantic accuracy or financial safety certification. Do not use its 4/4 narrow checks to approve corpus execution. No further calls were made to chase better random outputs.

**NOT READY FOR PHASE 3C.** D hardening is checkpointed, not a completed final freeze. Full extraction and semantic review under the final contract remain required. Existing C results and later experimental results must not be silently promoted across versions.
