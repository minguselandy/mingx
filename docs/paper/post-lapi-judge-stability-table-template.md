# POST-LAPI Judge Weak-Evidence Stability Table Template

Status: POST-3-CONFIG table template
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This template is for a later owner-approved POST-3 run-pilot result. It is not a
result table yet and must not be filled with live pilot values until the later
run-pilot goal is executed and reviewed.

## Result Table

| Condition | n judgments | parse success rate | duplicate agreement | order-swap agreement | rubric paraphrase agreement | confidence bucket stability | position bias rate | uncertain rate | parse failed rate | cost per judgment | latency per judgment | claim gate status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| original_order | pending | pending | pending | n/a | pending | pending | n/a | pending | pending | pending | pending | configuration only |
| order_swapped | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | configuration only |
| duplicate_judging | pending | pending | pending | n/a | pending | pending | n/a | pending | pending | pending | pending | configuration only |
| rubric_paraphrase | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | configuration only |

## Claim Boundary Columns

| Field | Required value |
| --- | --- |
| allowed claim | `model_adjudicated_weak_evidence` or `operational_diagnostic_evidence` only |
| denied claim | human gold; measurement validation; judge validation; paper-grade evidence; selector superiority |
| live API needed | yes for later owner-approved run-pilot execution only; no for this config package |
| human labels needed | no |
| paper section target | Appendix weak-evidence stability table |
| expected artifact location | `artifacts/experiments/post_lapi_judge_stability/` |
| raw API responses stored | false |
| claim level | `operational_utility_only/no_claim_upgrade` |
| Route 5 locked | true |
| Route 8 locked | true |

## Use Rule

Use this table only for stability diagnostics over model-adjudicated weak
evidence. Passing stability gates may support a weak operational diagnostic
claim, not human/external gold validation, measurement validation, judge
validation, paper-grade evidence, selector superiority, Route 5 unlock, or
Route 8 unlock.
