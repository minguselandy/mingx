# POST-LAPI Reprojection Witness Table Template

Status: POST-5-CONFIG table template
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This template is for a later owner-approved POST-5 run-pilot result. It is not a
result table yet and must not be filled with live or controlled replay values
until the later run-pilot goal is executed and reviewed.

## Witness Table

| Case class | n cases | repair rate | label change rate | abstain to support rate | unsupported to supported rate | cost delta | latency delta | position sensitivity rate | claim gate status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `sufficient_dropped` | pending | pending | pending | pending | pending | pending | pending | pending | configuration only |
| `insufficient_and_answered` | pending | pending | pending | pending | pending | pending | pending | pending | configuration only |
| high `missing_evidence_type` confidence | pending | pending | pending | pending | pending | pending | pending | pending | configuration only |
| replay artifact complete | pending | pending | pending | pending | pending | pending | pending | pending | configuration only |

## Required Controlled Fields

| Field | Required value |
| --- | --- |
| `downstream_prompt_hash` | fixed across before/after comparison |
| `model_snapshot` | fixed across before/after comparison |
| `endpoint` | fixed across before/after comparison |
| `thinking_mode` | fixed across before/after comparison |
| `decoding_policy` | fixed across before/after comparison |
| `token_budget_accounting` | fixed accounting method with budget delta recorded |
| `selected_evidence_before_hash` | present |
| `restored_evidence_hash` | present |
| `context_diff_hash` | present |
| `before_output_hash` | present |
| `after_output_hash` | present |
| `judge_prompt_hash` | present |
| `claim_ledger_entry` | present and claim-upgrade false |

## Claim Boundary Columns

| Field | Required value |
| --- | --- |
| allowed claim | `operational_reprojection_witness`; `omitted_evidence_operational_diagnostic`; `replayable_artifact_evidence` |
| denied claim | validated repair; truth correction guarantee; metric bridge support; selector superiority |
| live API needed | yes only for later owner-approved run-pilot execution; no for this config package |
| controlled replay call needed | yes only for later owner-approved run-pilot execution; no for this config package |
| human labels needed | no |
| paper section target | Appendix reprojection witness repair table |
| expected artifact location | `artifacts/experiments/post_lapi_reprojection_witness/` |
| raw API responses stored | false |
| claim level | `operational_utility_only/no_claim_upgrade` |
| Route 5 locked | true |
| Route 8 locked | true |

## Use Rule

Use this table only for operational witness diagnostics over replayable
artifacts. Passing later pilot gates may support operational reprojection
witness evidence, not validated repair, truth correction guarantees, metric
bridge support, selector superiority, Route 5 unlock, or Route 8 unlock.
