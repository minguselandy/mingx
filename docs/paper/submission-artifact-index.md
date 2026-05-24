# Submission Artifact Index

Status: SUB-5 final artifact index
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This index lists paper-facing POST-LAPI artifacts, reports, review docs, and
claim contracts for the operational audit package. It is an index only and
does not create new evidence.

## Core Freeze Artifacts

| artifact | purpose | boundary |
|---|---|---|
| `artifacts/audits/post_lapi_evidence_freeze/manifest.json` | Evidence freeze manifest | claim ceiling preserved; route locks true |
| `artifacts/audits/post_lapi_evidence_freeze/table_inputs.json` | Normalized table source inputs | operational-only table inputs |
| `artifacts/audits/post_lapi_evidence_freeze/checksums.sha256` | Freeze checksums | artifact hygiene only |
| `docs/paper/post-lapi-evidence-freeze-ledger.md` | Human-readable freeze ledger | no claim upgrade |
| `docs/paper/post-lapi-main-results-tables.md` | Paper-ready main results tables | operational and weak-evidence diagnostics only |
| `docs/paper/post-lapi-claim-boundary-summary.md` | Denied-claim and route-lock summary | Route 5 / Route 8 locked |

## Methods Artifact Chain

| component | purpose | boundary |
|---|---|---|
| `ProjectionPlan` | selected, excluded, and considered evidence for a dispatch | audit interface only |
| `BudgetWitness` | estimated and realized token budget, trims, and overflow handling | audit interface only |
| `MaterializedContext` | realized ordering, section boundaries, and content inventory | replay interface only |
| `MetricBridgeWitness` | metric class, active stratum, freshness, and bridge status | claim-level gate, not validation by itself |
| `CounterfactualReplayWitness` | frozen replay state, intervention, evaluator, and replicates | scoped operational replay only |
| `ReprojectionWitness` | uncertainty trigger, restored evidence, context diff, budget delta, selector before/after, and before/after outputs | operational omitted-evidence diagnostic only |
| `ClaimLedger` | allowed/denied claims, Route 5 / Route 8 locks, raw-response state, human/external gold-label state, and claim-upgrade flag | fail-closed boundary control |
| `ProjectionBundleV1` | canonical bundle tying plan, budget, context, witnesses, claim ledger, hashes, and diagnostics | replayable artifact evidence only |

## POST-3 Judge Stability Artifacts

| artifact | purpose | boundary |
|---|---|---|
| `artifacts/experiments/post_lapi_judge_stability/run_manifest.json` | Run manifest, model snapshot, endpoint, call count | weak model-adjudicated candidate evidence only |
| `artifacts/experiments/post_lapi_judge_stability/aggregate_report.json` | Stability aggregate report | not measurement validation |
| `artifacts/experiments/post_lapi_judge_stability/claim_gate_report.json` | Judge stability claim gate | no claim upgrade |
| `artifacts/experiments/post_lapi_judge_stability/claim_ledger.json` | Claim ledger | raw responses not stored |
| `artifacts/experiments/post_lapi_judge_stability/judgments.jsonl` | Normalized judge outputs | no raw provider responses |
| `docs/experiments/POST-LAPI-judge-stability-pilot.md` | Experiment report | weak diagnostics only |
| `docs/paper/post-lapi-judge-stability-table.md` | Paper table | no judge validation claim |

## POST-4 Sufficiency / Abstention Artifacts

| artifact | purpose | boundary |
|---|---|---|
| `artifacts/experiments/post_lapi_sufficiency_abstention/run_manifest.json` | Run manifest | sufficiency / abstention diagnostic only |
| `artifacts/experiments/post_lapi_sufficiency_abstention/aggregate_report.json` | Aggregate report | not truth validation |
| `artifacts/experiments/post_lapi_sufficiency_abstention/claim_gate_report.json` | Claim gate report | no claim upgrade |
| `artifacts/experiments/post_lapi_sufficiency_abstention/claim_ledger.json` | Claim ledger | route locks true |
| `artifacts/experiments/post_lapi_sufficiency_abstention/regime_ledger.json` | Regime ledger | diagnostic only |
| `artifacts/experiments/post_lapi_sufficiency_abstention/sufficiency_records.jsonl` | Normalized sufficiency records | no raw provider responses |
| `docs/experiments/POST-LAPI-sufficiency-abstention-pilot.md` | Experiment report | operational diagnostic only |
| `docs/paper/post-lapi-sufficiency-abstention-table.md` | Paper table | not measurement validation |

## POST-5 Reprojection Witness Artifacts

| artifact | purpose | boundary |
|---|---|---|
| `artifacts/experiments/post_lapi_reprojection_witness/run_manifest.json` | Run manifest | operational witness only |
| `artifacts/experiments/post_lapi_reprojection_witness/aggregate_report.json` | Aggregate report | not validated repair |
| `artifacts/experiments/post_lapi_reprojection_witness/claim_gate_report.json` | Claim gate report | no claim upgrade |
| `artifacts/experiments/post_lapi_reprojection_witness/claim_ledger.json` | Claim ledger | Route 5 / Route 8 locked |
| `artifacts/experiments/post_lapi_reprojection_witness/regime_ledger.json` | Regime ledger | operational omitted-evidence diagnostic |
| `artifacts/experiments/post_lapi_reprojection_witness/witness_records.jsonl` | Normalized witness records | no raw provider responses |
| `docs/experiments/POST-LAPI-reprojection-witness-pilot.md` | Experiment report | not selector superiority |
| `docs/paper/post-lapi-reprojection-witness-table.md` | Paper table | no metric bridge claim |

## POST-6 Operational Replay Artifacts

| artifact | purpose | boundary |
|---|---|---|
| `artifacts/experiments/post_lapi_operational_replay/run_manifest.json` | Run manifest | 0 live API calls |
| `artifacts/experiments/post_lapi_operational_replay/aggregate_report.json` | Aggregate replay report | scoped operational replay only |
| `artifacts/experiments/post_lapi_operational_replay/candidate_pool_manifest.json` | Candidate-pool manifest | replay substrate only |
| `artifacts/experiments/post_lapi_operational_replay/claim_gate_report.json` | Claim gate report | no selector superiority |
| `artifacts/experiments/post_lapi_operational_replay/claim_ledger.json` | Claim ledger | no metric bridge support |
| `artifacts/experiments/post_lapi_operational_replay/comparison_summary.csv` | Comparison summary | scoped matched-budget summary only |
| `artifacts/experiments/post_lapi_operational_replay/cost_latency_ledger.json` | Cost / latency ledger | operational accounting only |
| `artifacts/experiments/post_lapi_operational_replay/paired_comparisons.json` | Paired comparisons | oracle remains non-deployable |
| `artifacts/experiments/post_lapi_operational_replay/replay_records.jsonl` | Replay records | no raw provider responses |
| `docs/experiments/POST-LAPI-operational-replay-expansion.md` | Experiment report | operational-only replay |
| `docs/paper/post-lapi-operational-replay-table.md` | Paper table | no global selector superiority |

## POST-7 Extraction Audit Artifacts

| artifact | purpose | boundary |
|---|---|---|
| `artifacts/experiments/post_lapi_extraction_quality_audit/run_manifest.json` | Run manifest | model-adjudicated extraction-risk diagnostics only |
| `artifacts/experiments/post_lapi_extraction_quality_audit/aggregate_report.json` | Aggregate report | not measurement validation |
| `artifacts/experiments/post_lapi_extraction_quality_audit/audit_records.jsonl` | Normalized extraction audit records | no raw provider responses |
| `artifacts/experiments/post_lapi_extraction_quality_audit/claim_gate_report.json` | Claim gate report | no claim upgrade |
| `artifacts/experiments/post_lapi_extraction_quality_audit/claim_ledger.json` | Claim ledger | route locks true |
| `artifacts/experiments/post_lapi_extraction_quality_audit/cost_latency_ledger.json` | Cost / latency ledger | operational accounting only |
| `artifacts/experiments/post_lapi_extraction_quality_audit/stratum_summary.csv` | Stratum summary table | candidate extraction-risk evidence only |
| `artifacts/experiments/post_lapi_extraction_quality_audit/stratum_summary.json` | Stratum summary data | no theorem transfer |
| `docs/experiments/POST-LAPI-extraction-quality-audit.md` | Experiment report | not human-validated extraction measurement |
| `docs/paper/post-lapi-extraction-quality-table.md` | Paper table | no selector-validity claim |

## Review Docs

| review doc | purpose |
|---|---|
| `docs/reviews/POST-LAPI-baseline-verification.md` | POST-0 baseline state |
| `docs/reviews/POST-LAPI-evidence-freeze-review.md` | SUB-0 evidence freeze review |
| `docs/reviews/POST-LAPI-manuscript-integration-review.md` | SUB-1 integration review |
| `docs/reviews/POST-LAPI-independent-claim-boundary-review.md` | SUB-2 independent review, verdict `ACCEPT_WITH_NOTES` |
| `docs/reviews/POST-LAPI-submission-package-review.md` | SUB-3 package review |
| `docs/reviews/POST-LAPI-gap-filling-decision.md` | SUB-4 decision, `NO_MORE_EXPERIMENTS_RECOMMENDED` |
| `docs/reviews/POST-LAPI-final-readiness-summary.md` | SUB-5 final readiness summary |
| `docs/reviews/reviewer-defense-live-api-operational-paper.md` | Reviewer Q&A defense |

## Submission Docs

| doc | purpose |
|---|---|
| `docs/paper/submission-claim-ledger.md` | Submission claim ledger |
| `docs/paper/submission-experiment-summary.md` | Submission experiment summary |
| `docs/paper/submission-limitations.md` | Limitations |
| `docs/paper/submission-abstract-claim-safe.md` | Claim-safe abstract |
| `docs/paper/submission-conclusion-claim-safe.md` | Claim-safe conclusion |
| `docs/paper/submission-readiness-checklist.md` | Final readiness checklist |
| `docs/paper/submission-artifact-index.md` | Final artifact index |
| `docs/archive/context_projection_fixed_v12.md` | Manuscript anchor |
| `docs/paper/v12-evidence-ledger.md` | v12 evidence ledger |
| `docs/paper/v12-manuscript-integration-checklist.md` | manuscript integration checklist |

## Claim Contracts And Guardrails

| contract / guardrail | purpose |
|---|---|
| `configs/post_lapi/post_lapi_global_claim_contract.yaml` | Global POST-LAPI claim contract |
| `configs/post_lapi/post_lapi_table_manifest.yaml` | Paper table manifest |
| `configs/post_lapi/artifact_replay_integrity_config.yaml` | Artifact replay integrity config |
| `configs/post_lapi/judge_stability_pilot_config.yaml` | POST-3 config |
| `configs/post_lapi/sufficiency_abstention_config.yaml` | POST-4 config |
| `configs/post_lapi/reprojection_witness_config.yaml` | POST-5 config |
| `configs/post_lapi/operational_replay_expansion_config.yaml` | POST-6 config |
| `configs/post_lapi/extraction_quality_audit_config.yaml` | POST-7 config |
| `docs/api/live-api-capability-contract.md` | Live API capability boundary |
| `docs/paper/live-api-experiment-boundaries.md` | Live API experiment boundaries |
| `docs/paper/v12-live-api-operational-paper-claim-table.md` | Claim table |
| `tests/test_revised_framing_guardrails.py` | Framing guardrails |
| `tests/test_live_api_claim_contract.py` | Live API claim contract tests |
| `tests/test_no_teacher_forced_claims_live_api_only.py` | Teacher-forced claim guardrail |

## Boundary Summary

- Claim level: `operational_utility_only/no_claim_upgrade`.
- Route 5: locked.
- Route 8: locked.
- Raw API responses stored: no.
- SUB-4 selected `NO_MORE_EXPERIMENTS_RECOMMENDED`.
- SUB-5 adds no new evidence work.

Denied claims remain denied: measurement validation, metric bridge support,
calibrated proxy support, `vinfo_proxy_supported`, paper evidence, selector
superiority, Route 5 unlock, and Route 8 unlock.
