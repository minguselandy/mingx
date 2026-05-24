# POST-LAPI Sufficiency / Abstention Table Template

Status: POST-4-CONFIG table template
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This template is for a later owner-approved POST-4 run-pilot result. It is not a
result table yet and must not be filled with live pilot values until the later
run-pilot goal is executed and reviewed.

## Regime Table

| Regime | n cases | support rate | insufficient rate | contradict rate | uncertain rate | parse failed rate | abstain rate | abstain when insufficient rate | unsafe answer rate | missing evidence type distribution | cost per case | latency per case | claim gate status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| `sufficient_kept` | pending | pending | pending | pending | pending | pending | pending | n/a | pending | pending | pending | pending | configuration only |
| `sufficient_dropped` | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | configuration only |
| `insufficient_and_answered` | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | configuration only |
| `insufficient_and_abstained` | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | configuration only |

## Required Row Fields

| Field | Required value |
| --- | --- |
| allowed labels | `support`; `insufficient`; `contradict`; `uncertain`; `parse_failed` |
| additional fields | `abstain_recommended`; `missing_evidence_type`; `confidence_bucket`; `prompt_hash`; `model_snapshot`; `endpoint`; `raw_response_stored=false` |
| allowed claim | `sufficiency_abstention_diagnostic`; `model_adjudicated_weak_evidence`; `operational_utility_only` |
| denied claim | truth validation; human-calibrated abstention; measurement validation; paper-grade evidence |
| live API needed | yes for later owner-approved run-pilot execution only; no for this config package |
| human labels needed | no |
| paper section target | Appendix sufficiency and abstention regime table |
| expected artifact location | `artifacts/experiments/post_lapi_sufficiency_abstention/` |
| raw API responses stored | false |
| claim level | `operational_utility_only/no_claim_upgrade` |
| Route 5 locked | true |
| Route 8 locked | true |

## Use Rule

Use this table only for sufficiency / abstention diagnostics over candidate
operational evidence. Passing later pilot gates may support operational
sufficiency-abstention diagnostics, not truth validation, human-calibrated
abstention, measurement validation, paper-grade evidence, Route 5 unlock, or
Route 8 unlock.
