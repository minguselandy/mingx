# Operational Evaluation and Weak-Evidence Diagnostics

Status: LAPI-8 paper-facing section draft
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This section is the paper-facing integration point for the completed
live-API-only LAPI package. The manuscript stance is live-API-only,
audit-first, claim-gated, and formal V-information anchor only. Current
experiments do not estimate a fixed-target bridge, do not provide
teacher-forced NLL, and do not unlock stronger metric claims.

Current experiments do not estimate a fixed-target bridge.

Live-API outputs remain operational diagnostics or candidate evidence only.

The section name is intentional: operational evaluation and weak-evidence
diagnostics, not validation.

## Allowed Evaluation Story

The paper can state that the live-API package records operational diagnostics
or candidate evidence only. It can describe replayable artifacts, backend
capability witnesses, judge manifests, sufficiency/reprojection witnesses,
operational replay plans, and extraction-risk ledgers as audit surfaces for the
context-projection pipeline.

The formal V-information objective remains the mathematical anchor for the
paper. The live-API evidence package does not measure that objective directly
and does not certify a V-information proxy. The bridge from operational utility
or generated output-token confidence to formal V-information remains blocked
unless a future fixed-target logloss or predictive-family bridge is separately
reviewed and accepted.

## Completed LAPI Package Mapping

| package | paper-facing role | claim boundary |
|---|---|---|
| LAPI-1 live API capability contract | Records the approved DashScope-compatible capability surface and denied backend claims. | Generated output-token logprobs are answer-side confidence diagnostics only. |
| LAPI-2 ProjectionBundleV1 | Provides a normalized artifact envelope with claim ledgers and raw-response exclusion. | Artifact completeness can support replayability, not validation. |
| LAPI-3 backend bridge audit witness | Records that fixed-target teacher-forced NLL and fixed-target continuation scoring are unsupported. | Fail-closed bridge audit only. |
| LAPI-4 LLM judge weak-evidence harness | Defines weak model-adjudicated candidate evidence with stability gates. | Model-adjudicated evidence only, not human labels or kappa. |
| LAPI-5 sufficiency abstention and reprojection protocol | Defines offline sufficiency, abstention, and reprojection diagnostics. | Candidate operational diagnostics only. |
| LAPI-6 operational replay expansion plan | Prepares matched-budget replay configs for future controlled runs. | No replay run was executed by that package. |
| LAPI-7 extraction quality audit framework | Defines model-adjudicated extraction-risk records for the `M* -> M` bottleneck. | Extraction-risk diagnostics only; human sentinel audit is future optional. |

## Hard Replay Versus Weak Evidence

Hard replay evidence is separated from weak model-adjudicated evidence.

Hard replay evidence means records with fixed candidate pools, matched budgets,
stable materialization, and replay-compatible operational metrics. Existing
Route 2 HotpotQA replay/comparison records may be discussed only as scoped
operational replay under matched budgets because bridge attempts failed closed.

Weak model-adjudicated evidence means LLM judge labels, silver labels,
extraction-risk labels, sufficiency labels, and uncertainty buckets. These
outputs can prioritize review and expose failure modes, but they cannot replace
human/external gold labels, human-human agreement, fixed-target scoring, or a
fresh metric bridge.

## Claim Flags For The Section

| claim flag | value |
|---|---|
| claim status | `operational_utility_only/no_claim_upgrade` |
| teacher-forced NLL support: false | false |
| fixed-target continuation scoring support: false | false |
| current experiments estimate fixed-target bridge | false |
| metric bridge support | false |
| measurement validation | false |
| calibrated_proxy_supported | false |
| vinfo_proxy_supported | false |
| paper evidence | false |
| selector superiority | false |
| global selector superiority | false |
| Route 5 locked: true | true |
| Route 8 locked: true | true |
| Route 5 unlock | false |
| Route 8 unlock | false |

## Safe Manuscript Paragraph

The live-API-only evaluation section reports operational evaluation and
weak-evidence diagnostics. The formal V-information objective remains the
paper's anchor, but the current live-API backend does not expose fixed-target
teacher-forced NLL or fixed-target continuation scoring. Route 2 replay supplies
scoped operational evidence under matched budgets, while judge, sufficiency,
silver-label, and extraction-audit outputs remain weak-source candidate
diagnostics. The resulting claim level is
`operational_utility_only/no_claim_upgrade`: not measurement validation, not
metric bridge support, not calibrated proxy support, not V-information proxy
support, not paper evidence, not selector superiority, and no Route 5 or Route
8 unlock.
