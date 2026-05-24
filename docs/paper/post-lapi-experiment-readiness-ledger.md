# POST-LAPI Experiment Readiness Ledger

Status: POST-2 experiment-readiness package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This ledger records readiness for the post-LAPI paper tables. It is not an
experiment log. It does not execute live API calls, model judging, replay
pilots, controlled reprojection, human labeling, or extraction audits.

## Readiness Summary

| Package | Current status | Evidence source | Next required step | Allowed claim | Denied claim boundary | Live API needed | Human labels needed | Expected artifact location |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Backend capability / claim boundary | Ready for paper table | `docs/api/live-api-capability-contract.md`; `docs/paper/live-api-experiment-boundaries.md` | None | fail-closed bridge audit | No fixed-target NLL support, teacher-forced scoring support, metric bridge support, Route 5 unlock, or Route 8 unlock | No | No | `docs/api/live-api-capability-contract.md` |
| Artifact replay integrity | Ready for appendix table | `docs/experiments/POST-LAPI-artifact-replay-integrity-audit.md`; `artifacts/audits/post_lapi_replay_integrity/summary.json` | None | replayable artifact evidence | No scientific validation, measurement validation, paper-grade evidence, metric bridge support, or selector superiority | No | No | `artifacts/audits/post_lapi_replay_integrity/` |
| Matched-budget operational replay | Existing Route 2 evidence ready; expansion not yet run | `docs/experiments/P67R-route2-operational-evidence-package.md`; `configs/post_lapi/operational_replay_expansion_config.yaml` | POST-6 configuration before any owner-approved expansion | scoped operational improvement under matched budgets | No selector superiority, global selector superiority, metric bridge support, measurement validation, or V-information verification | Conditional future run only | No | `artifacts/experiments/post_lapi_operational_replay_expansion/` |
| Judge weak-evidence stability | Not ready as result table; ready as planned table template | `configs/post_lapi/judge_stability_pilot_config.yaml`; `docs/experiments/llm-judge-weak-evidence-protocol.md` | POST-3 configuration and dry-run validation | model-adjudicated weak evidence | No human/external gold validation, measurement validation, paper-grade evidence, or selector superiority | Future owner-approved pilot only | No | `artifacts/experiments/post_lapi_judge_stability/` |
| Sufficiency / abstention regimes | Not ready as result table; ready as planned table template | `configs/post_lapi/sufficiency_abstention_config.yaml`; `docs/experiments/sufficiency-abstention-reprojection-protocol.md` | POST-4 configuration and dry-run validation | sufficiency / abstention diagnostic | No truth validation, human-calibrated abstention, measurement validation, or paper-grade evidence | Future owner-approved pilot only | No | `artifacts/experiments/post_lapi_sufficiency_abstention/` |
| Reprojection witness repair | Not ready as result table; ready as planned table template | `configs/post_lapi/reprojection_witness_config.yaml`; `docs/experiments/reprojection-witness-pilot-v12.md`; `docs/experiments/P59-reprojection-replay-integration-plan.md` | POST-5 configuration and dry-run validation | replayable artifact evidence | No validated repair, truth correction guarantee, metric bridge support, or selector superiority | Future owner-approved controlled replay only | No | `artifacts/experiments/post_lapi_reprojection_witness/` |

## Appendix Readiness

| Appendix | Current status | Evidence source | Next required step | Allowed claim | Denied claim boundary | Live API needed | Human labels needed | Expected artifact location |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EPF-FINAL candidate package | Ready with candidate-only ceiling | `docs/experiments/EPF-final-live-api-silver-label-candidate-package.md`; `artifacts/experiments/epf_final/final_epf_manifest.json` | None for current package | candidate operational evidence | No human/external gold validation, measurement validation, paper-grade evidence, metric bridge support, Route 5 unlock, or Route 8 unlock | No | No | `artifacts/experiments/epf_final/` |
| Denied claims / claim ledger | Ready | `docs/paper/v12-evidence-ledger.md`; `configs/post_lapi/post_lapi_global_claim_contract.yaml` | None | fail-closed bridge audit | Denied claims remain false and route locks remain active | No | No | `docs/paper/post-lapi-experiment-readiness-ledger.md` |
| Optional extraction quality audit | Not ready as result table; optional configuration pending | `configs/post_lapi/extraction_quality_audit_config.yaml`; `docs/experiments/extraction-quality-audit-protocol.md` | POST-7 configuration only unless owner approves a later audit | candidate operational evidence | No human-validated extraction measurement, measurement validation, theorem transfer to M*, or end-to-end validation | No for configuration | No for configuration | `artifacts/experiments/post_lapi_extraction_quality_audit/` |
| Related work gap matrix | Ready as a planning appendix | `docs/paper/post-lapi-table-plan.md`; `docs/paper/v12-evidence-ledger.md` | None | fail-closed bridge audit | No selector superiority, global selector superiority, or paper-grade evidence | No | No | `docs/paper/post-lapi-table-plan.md` |
| Live API capability matrix | Ready as a boundary appendix | `docs/api/live-api-capability-contract.md`; backend capability reports | None | fail-closed bridge audit | No fixed-target NLL support, teacher-forced scoring support, metric bridge support, Route 5 unlock, or Route 8 unlock | No | No | `docs/api/live-api-capability-contract.md` |

## Sequencing

1. POST-3 should configure judge weak-evidence stability before any judging run.
2. POST-4 should configure sufficiency / abstention before any pilot run.
3. POST-5 should configure reprojection witness controlled replay before any
   controlled replay call.
4. POST-6 should configure matched-budget operational replay expansion before
   any dataset-scale expansion.
5. POST-7 is optional and should stay an extraction-risk audit configuration
   unless the owner explicitly approves a later audit run.

## Boundary Ledger

| Boundary | POST-2 value |
| --- | --- |
| Live API calls run | no |
| New experiments run | no |
| New model judging run | no |
| New silver labels created | no |
| Raw API responses stored | no |
| Claim level | `operational_utility_only/no_claim_upgrade` |
| Claim upgrade introduced | no |
| Route 5 locked | yes |
| Route 8 locked | yes |

The readiness state is therefore paper-table planning and experiment sequencing
only. Rows that require POST-3 through POST-7 are not results and must not be
presented as completed evidence until their own goal conditions pass.
