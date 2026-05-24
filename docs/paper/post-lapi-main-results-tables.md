# POST-LAPI Main Results Tables

Status: paper-ready SUB-0 synthesis tables
Claim ceiling: `operational_utility_only/no_claim_upgrade`

Every table below is candidate operational evidence or claim-boundary synthesis only. No table unlocks Route 5 or Route 8, supplies human labels, supplies a metric bridge, or upgrades the current claim. Every caption states evidence tier, allowed claim, denied claim, human-label status, metric-bridge status, and Route 5 / Route 8 lock status.

SUB-1 manuscript integration cross-references these tables to the manuscript section titled `Operational evaluation and weak-evidence diagnostics`. The integration is docs-only and runs no live API calls or new experiments.

## T1. Backend capability and claim boundary

Caption: Evidence tier: backend capability boundary only. Allowed claim: backend-constrained operational diagnostics only. Denied claim: teacher-forced NLL support, fixed-target continuation scoring support, and metric bridge support. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Field | Value |
|---|---|
| Evidence source | `LAPI + POST-LAPI contracts and docs/paper/v12-live-api-operational-paper-claim-table.md` |
| Sample size / row count / call count | No new samples in SUB-0; summarizes backend constraints |
| Primary metric | fixed-target teacher-forced continuation scoring unavailable; claim ceiling preserved |
| Allowed claim | backend-constrained operational diagnostics only |
| Denied claim | teacher-forced NLL support; fixed-target continuation scoring support; metric bridge support |
| Evidence tier | backend capability boundary only |
| Live API call count | 0 during SUB-0/SUB-1 synthesis |
| Paper section target | Operational evaluation and weak-evidence diagnostics / backend limits and claim boundary |
| Manuscript cross-reference | `docs/archive/context_projection_fixed_v12.md` section `Operational evaluation and weak-evidence diagnostics` |
| Human labels present | `false` |
| Metric bridge present | `false` |
| Route 5 unlocked | `false` |
| Route 8 unlocked | `false` |
| raw_response_stored | `false` |

## T2. POST-3 judge stability

Caption: Evidence tier: weak/model-adjudicated candidate evidence. Allowed claim: model-adjudicated weak diagnostics only. Denied claim: human validation, measurement validation, calibrated judge, and paper-grade evidence. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Field | Value |
|---|---|
| Evidence source | `artifacts/experiments/post_lapi_judge_stability/` |
| Sample size / row count / call count | 30 examples / 240 normalized rows / 240 live API calls |
| Primary metric | duplicate agreement 0.9833; order-swap agreement 0.9833; rubric paraphrase agreement 0.9667 |
| Allowed claim | model-adjudicated weak diagnostics only |
| Denied claim | human validation; measurement validation; calibrated judge; paper-grade evidence |
| Evidence tier | weak/model-adjudicated candidate evidence |
| Live API call count | 240 |
| Paper section target | Operational evaluation and weak-evidence diagnostics / judge stability diagnostics |
| Manuscript cross-reference | `docs/archive/context_projection_fixed_v12.md` section `Operational evaluation and weak-evidence diagnostics` |
| Human labels present | `false` |
| Metric bridge present | `false` |
| Route 5 unlocked | `false` |
| Route 8 unlocked | `false` |
| raw_response_stored | `false` |

## T3. POST-4 sufficiency / abstention

Caption: Evidence tier: sufficiency-abstention diagnostic. Allowed claim: sufficiency-abstention diagnostics only. Denied claim: truth validation, human-calibrated abstention, measurement validation, and paper-grade evidence. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Field | Value |
|---|---|
| Evidence source | `artifacts/experiments/post_lapi_sufficiency_abstention/` |
| Sample size / row count / call count | 50 final normalized rows / 50 final artifact calls / 100 total turn calls |
| Primary metric | gate sufficiency_abstention_candidate_ready |
| Allowed claim | sufficiency-abstention diagnostics only |
| Denied claim | truth validation; human-calibrated abstention; measurement validation; paper-grade evidence |
| Evidence tier | operational diagnostic candidate evidence |
| Live API call count | 50 final artifact calls / 100 total turn calls |
| Paper section target | Operational evaluation and weak-evidence diagnostics / sufficiency and abstention diagnostics |
| Manuscript cross-reference | `docs/archive/context_projection_fixed_v12.md` section `Operational evaluation and weak-evidence diagnostics` |
| Human labels present | `false` |
| Metric bridge present | `false` |
| Route 5 unlocked | `false` |
| Route 8 unlocked | `false` |
| raw_response_stored | `false` |

## T4. POST-5 reprojection witness

Caption: Evidence tier: candidate operational evidence. Allowed claim: candidate operational evidence only. Denied claim: validated repair, truth correction guarantee, selector superiority, and metric bridge support. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Field | Value |
|---|---|
| Evidence source | `artifacts/experiments/post_lapi_reprojection_witness/` |
| Sample size / row count / call count | 26 normalized rows / 26 live API calls |
| Primary metric | repair candidate rate 0.576923; label change rate 0.576923; unsupported-to-supported rate 0.576923; parse failed rate 0.0 |
| Allowed claim | candidate operational evidence only |
| Denied claim | validated repair; truth correction guarantee; selector superiority; metric bridge support |
| Evidence tier | candidate operational evidence |
| Live API call count | 26 |
| Paper section target | Operational evaluation and weak-evidence diagnostics / reprojection witness diagnostics |
| Manuscript cross-reference | `docs/archive/context_projection_fixed_v12.md` section `Operational evaluation and weak-evidence diagnostics` |
| Human labels present | `false` |
| Metric bridge present | `false` |
| Route 5 unlocked | `false` |
| Route 8 unlocked | `false` |
| raw_response_stored | `false` |

## T5. POST-6 matched-budget operational replay

Caption: Evidence tier: matched-budget operational replay only. Allowed claim: scoped operational replay only. Denied claim: selector superiority, global selector superiority, metric bridge support, and paper-grade evidence. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Field | Value |
|---|---|
| Evidence source | `artifacts/experiments/post_lapi_operational_replay/` |
| Sample size / row count / call count | 2,000 normalized replay records / 200 candidate pools / 0 live API calls |
| Primary metric | budgets 512 and 1024; gold-support oracle retained as non_deployable_upper_bound |
| Allowed claim | scoped operational replay only |
| Denied claim | selector superiority; global selector superiority; metric bridge support; paper-grade evidence |
| Evidence tier | scoped operational replay evidence only |
| Live API call count | 0 |
| Paper section target | Operational evaluation and weak-evidence diagnostics / matched-budget operational replay |
| Manuscript cross-reference | `docs/archive/context_projection_fixed_v12.md` section `Operational evaluation and weak-evidence diagnostics` |
| Human labels present | `false` |
| Metric bridge present | `false` |
| Route 5 unlocked | `false` |
| Route 8 unlocked | `false` |
| raw_response_stored | `false` |

## T6. POST-7 extraction quality audit

Caption: Evidence tier: extraction-risk diagnostics. Allowed claim: extraction-risk diagnostics only. Denied claim: human-validated extraction measurement, measurement validation, and theorem transfer to M-star. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Field | Value |
|---|---|
| Evidence source | `artifacts/experiments/post_lapi_extraction_quality_audit/` |
| Sample size / row count / call count | 100 normalized extraction audit records / 10 per stratum / 100 live API calls |
| Primary metric | value-weighted loss proxy 0.197403; gate post7_extraction_quality_audit_completed |
| Allowed claim | extraction-risk diagnostics only |
| Denied claim | human-validated extraction measurement; measurement validation; theorem transfer to M* |
| Evidence tier | model-adjudicated extraction-risk evidence only |
| Live API call count | 100 |
| Paper section target | Operational evaluation and weak-evidence diagnostics / extraction quality audit diagnostics |
| Manuscript cross-reference | `docs/archive/context_projection_fixed_v12.md` section `Operational evaluation and weak-evidence diagnostics` |
| Human labels present | `false` |
| Metric bridge present | `false` |
| Route 5 unlocked | `false` |
| Route 8 unlocked | `false` |
| raw_response_stored | `false` |

## T7. Artifact hygiene and evidence freeze

Caption: Evidence tier: replayable artifact evidence. Allowed claim: artifact hygiene and evidence-freeze evidence only. Denied claim: new experiment, new live API evidence, and raw response storage. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Field | Value |
|---|---|
| Evidence source | `SUB-0 validation over POST-3 through POST-7 frozen artifacts` |
| Sample size / row count / call count | 27 JSON files / 5 JSONL files / 2,416 JSONL rows |
| Primary metric | secret scan passed; raw-response-storage scan passed; forbidden-path scan passed; compileall passed |
| Allowed claim | artifact hygiene evidence for frozen candidate package |
| Denied claim | new experiment; new live API evidence; raw response storage |
| Evidence tier | reproducibility and storage-policy evidence only |
| Live API call count | 0 during SUB-0/SUB-1 synthesis |
| Paper section target | Operational evaluation and weak-evidence diagnostics / reproducibility and artifact hygiene appendix |
| Manuscript cross-reference | `docs/archive/context_projection_fixed_v12.md` section `Operational evaluation and weak-evidence diagnostics` |
| Human labels present | `false` |
| Metric bridge present | `false` |
| Route 5 unlocked | `false` |
| Route 8 unlocked | `false` |
| raw_response_stored | `false` |

## T8. Denied claims / no-claim-upgrade table

Caption: Evidence tier: claim-boundary synthesis only. Allowed claim: operational_utility_only/no_claim_upgrade. Denied claim: fixed-target teacher-forced NLL support, fixed-target continuation scoring support, metric bridge support, measurement validation, human/external gold validation, selector superiority, global selector superiority, Route 5 unlock, and Route 8 unlock. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Field | Value |
|---|---|
| Evidence source | `POST-LAPI claim gate contracts and manuscript integration docs` |
| Sample size / row count / call count | No new samples in SUB-0; boundary table only |
| Primary metric | all denied claims remain denied; Route 5 and Route 8 remain locked |
| Allowed claim | operational_utility_only/no_claim_upgrade |
| Denied claim | teacher-forced NLL support; fixed-target continuation scoring support; metric bridge support; calibrated_proxy_supported; vinfo_proxy_supported; measurement validation; human/external gold validation; paper-grade evidence; selector superiority; global selector superiority; Route 5 unlock; Route 8 unlock |
| Evidence tier | claim-boundary synthesis only |
| Live API call count | 0 during SUB-0/SUB-1 synthesis |
| Paper section target | Operational evaluation and weak-evidence diagnostics / claim boundary and limitations |
| Manuscript cross-reference | `docs/archive/context_projection_fixed_v12.md` section `Operational evaluation and weak-evidence diagnostics` |
| Human labels present | `false` |
| Metric bridge present | `false` |
| Route 5 unlocked | `false` |
| Route 8 unlocked | `false` |
| raw_response_stored | `false` |
