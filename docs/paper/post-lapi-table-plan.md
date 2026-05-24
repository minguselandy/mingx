# POST-LAPI Paper Table Plan

Status: POST-2 table readiness package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This plan maps the post-LAPI evidence package into paper tables and appendices.
It is a docs/config readiness package only. It does not run live API calls,
start experiments, create new labels, store raw API responses, unlock Route 5,
unlock Route 8, or upgrade claims.

## Claim Classes

Allowed claim classes:
- operational replay evidence
- candidate operational evidence
- model-adjudicated weak evidence
- sufficiency / abstention diagnostic
- replayable artifact evidence
- fail-closed bridge audit
- scoped operational improvement under matched budgets

Denied claim classes:
- fixed-target NLL support
- teacher-forced scoring support
- metric bridge support
- calibrated_proxy_supported
- vinfo_proxy_supported
- measurement validation
- human/external gold validation
- paper-grade evidence
- selector superiority
- global selector superiority
- Route 5 unlock
- Route 8 unlock

## Required Paper Tables

### 1. Backend Capability / Claim Boundary

| Field | Value |
| --- | --- |
| evidence source | `docs/api/live-api-capability-contract.md`; `docs/paper/live-api-experiment-boundaries.md`; `docs/paper/v12-live-api-operational-paper-claim-table.md` |
| current completion status | Complete boundary documentation available. |
| required next experiment, if any | None. |
| allowed claim | fail-closed bridge audit |
| denied claim | fixed-target NLL support; teacher-forced scoring support; metric bridge support; `calibrated_proxy_supported`; `vinfo_proxy_supported`; Route 5 unlock; Route 8 unlock |
| whether live API is needed | No. |
| whether human labels are needed | No. |
| paper section target | Section 4.9 backend capability and limitations |
| expected artifact location | `docs/api/live-api-capability-contract.md` |

### 2. Artifact Replay Integrity

| Field | Value |
| --- | --- |
| evidence source | `docs/experiments/POST-LAPI-artifact-replay-integrity-audit.md`; `artifacts/audits/post_lapi_replay_integrity/summary.json`; `artifacts/audits/post_lapi_replay_integrity/summary.csv` |
| current completion status | Complete offline audit available from POST-1. |
| required next experiment, if any | None. |
| allowed claim | replayable artifact evidence |
| denied claim | scientific validation; measurement validation; paper-grade evidence; metric bridge support; selector superiority |
| whether live API is needed | No. |
| whether human labels are needed | No. |
| paper section target | Appendix artifact replay and auditability table |
| expected artifact location | `artifacts/audits/post_lapi_replay_integrity/` |

### 3. Matched-Budget Operational Replay

| Field | Value |
| --- | --- |
| evidence source | `docs/experiments/P67R-route2-operational-evidence-package.md`; `artifacts/experiments/route2_operational_evidence_package/claim_ledger.json`; `configs/post_lapi/operational_replay_expansion_config.yaml` |
| current completion status | Existing Route 2 package is available; POST-6 expansion remains configuration/future-run work. |
| required next experiment, if any | POST-6 configuration, then owner-approved matched-budget replay expansion only. |
| allowed claim | scoped operational improvement under matched budgets |
| denied claim | selector superiority; global selector superiority; metric bridge support; measurement validation; V-information verification |
| whether live API is needed | No for existing Route 2 package; conditional for a future owner-approved expansion. |
| whether human labels are needed | No. |
| paper section target | Section 4.8 operational replay and Appendix matched-budget details |
| expected artifact location | `artifacts/experiments/post_lapi_operational_replay_expansion/` |

### 4. Judge Weak-Evidence Stability

| Field | Value |
| --- | --- |
| evidence source | `configs/post_lapi/judge_stability_pilot_config.yaml`; `docs/experiments/llm-judge-weak-evidence-protocol.md`; `docs/experiments/WS4-llm-judge-weak-source-audit.md` |
| current completion status | Configuration stub available; POST-3 configuration and dry-run validation remain pending. |
| required next experiment, if any | POST-3 configuration and dry-run validation; later owner-approved pilot only. |
| allowed claim | model-adjudicated weak evidence |
| denied claim | human/external gold validation; measurement validation; paper-grade evidence; selector superiority |
| whether live API is needed | Yes only for a future owner-approved pilot, not for this package. |
| whether human labels are needed | No. |
| paper section target | Appendix weak-evidence stability table |
| expected artifact location | `artifacts/experiments/post_lapi_judge_stability/` |

### 5. Sufficiency / Abstention Regimes

| Field | Value |
| --- | --- |
| evidence source | `configs/post_lapi/sufficiency_abstention_config.yaml`; `docs/experiments/sufficiency-abstention-reprojection-protocol.md` |
| current completion status | Configuration stub available; POST-4 configuration and dry-run validation remain pending. |
| required next experiment, if any | POST-4 configuration and dry-run validation; later owner-approved pilot only. |
| allowed claim | sufficiency / abstention diagnostic |
| denied claim | truth validation; human-calibrated abstention; measurement validation; paper-grade evidence |
| whether live API is needed | Yes only for a future owner-approved pilot, not for this package. |
| whether human labels are needed | No. |
| paper section target | Appendix sufficiency and abstention regime table |
| expected artifact location | `artifacts/experiments/post_lapi_sufficiency_abstention/` |

### 6. Reprojection Witness Repair

| Field | Value |
| --- | --- |
| evidence source | `configs/post_lapi/reprojection_witness_config.yaml`; `docs/experiments/reprojection-witness-pilot-v12.md`; `docs/experiments/P59-reprojection-replay-integration-plan.md` |
| current completion status | Configuration stub available; POST-5 configuration and dry-run validation remain pending. |
| required next experiment, if any | POST-5 configuration and dry-run validation; later controlled replay only with owner approval. |
| allowed claim | replayable artifact evidence |
| denied claim | validated repair; truth correction guarantee; metric bridge support; selector superiority |
| whether live API is needed | Yes only for a future owner-approved controlled replay, not for this package. |
| whether human labels are needed | No. |
| paper section target | Appendix reprojection witness repair table |
| expected artifact location | `artifacts/experiments/post_lapi_reprojection_witness/` |

## Appendices

### EPF-FINAL Candidate Package

| Field | Value |
| --- | --- |
| evidence source | `docs/experiments/EPF-final-live-api-silver-label-candidate-package.md`; `artifacts/experiments/epf_final/final_epf_manifest.json` |
| current completion status | Complete candidate package available. |
| required next experiment, if any | None for the current candidate package. |
| allowed claim | candidate operational evidence |
| denied claim | human/external gold validation; measurement validation; paper-grade evidence; metric bridge support; Route 5 unlock; Route 8 unlock |
| whether live API is needed | No. |
| whether human labels are needed | No. |
| paper section target | Appendix EPF-FINAL candidate package |
| expected artifact location | `artifacts/experiments/epf_final/` |

### Denied Claims / Claim Ledger

| Field | Value |
| --- | --- |
| evidence source | `docs/paper/v12-evidence-ledger.md`; `docs/paper/live-api-experiment-boundaries.md`; `configs/post_lapi/post_lapi_global_claim_contract.yaml` |
| current completion status | Complete boundary ledger available. |
| required next experiment, if any | None. |
| allowed claim | fail-closed bridge audit |
| denied claim | fixed-target NLL support; teacher-forced scoring support; metric bridge support; `calibrated_proxy_supported`; `vinfo_proxy_supported`; measurement validation; human/external gold validation; paper-grade evidence; selector superiority; global selector superiority; Route 5 unlock; Route 8 unlock |
| whether live API is needed | No. |
| whether human labels are needed | No. |
| paper section target | Appendix claim ledger and denied-claim matrix |
| expected artifact location | `docs/paper/post-lapi-experiment-readiness-ledger.md` |

### Optional Extraction Quality Audit

| Field | Value |
| --- | --- |
| evidence source | `configs/post_lapi/extraction_quality_audit_config.yaml`; `docs/experiments/extraction-quality-audit-protocol.md`; `docs/experiments/P57-extraction-audit-v2-plan.md` |
| current completion status | Optional configuration pending POST-7. |
| required next experiment, if any | POST-7 configuration and dry-run validation only unless owner approves a later audit. |
| allowed claim | candidate operational evidence |
| denied claim | human-validated extraction measurement; measurement validation; theorem transfer to M*; end-to-end validation |
| whether live API is needed | No for configuration; conditional for a later owner-approved audit. |
| whether human labels are needed | No for configuration. |
| paper section target | Optional appendix extraction quality table |
| expected artifact location | `artifacts/experiments/post_lapi_extraction_quality_audit/` |

### Related Work Gap Matrix

| Field | Value |
| --- | --- |
| evidence source | `docs/paper/post-lapi-table-plan.md`; `docs/paper/v12-evidence-ledger.md` |
| current completion status | Table plan available after POST-2. |
| required next experiment, if any | None. |
| allowed claim | fail-closed bridge audit |
| denied claim | selector superiority; global selector superiority; paper-grade evidence |
| whether live API is needed | No. |
| whether human labels are needed | No. |
| paper section target | Related work / limitations appendix |
| expected artifact location | `docs/paper/post-lapi-table-plan.md` |

### Live API Capability Matrix

| Field | Value |
| --- | --- |
| evidence source | `docs/api/live-api-capability-contract.md`; `artifacts/experiments/epf_ws1_live_api_tfs_closure/backend_capability_report.json`; `artifacts/experiments/teacher_forced_logprobe_backend/backend_capability_report.json` |
| current completion status | Existing boundary docs available. |
| required next experiment, if any | None. |
| allowed claim | fail-closed bridge audit |
| denied claim | fixed-target NLL support; teacher-forced scoring support; metric bridge support; Route 5 unlock; Route 8 unlock |
| whether live API is needed | No. |
| whether human labels are needed | No. |
| paper section target | Appendix live API capability matrix |
| expected artifact location | `docs/api/live-api-capability-contract.md` |

## Current Boundary Summary

- Live API calls run for POST-2: no
- New experiments run for POST-2: no
- Raw API responses stored for POST-2: no
- Claim upgrade introduced: no
- Route 5 locked: yes
- Route 8 locked: yes
