# V12 Evidence Ledger

Status: PAPER-RS live-API operational restructuring ledger
Framing: Proxy-Regime Diagnosis
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Purpose

This ledger summarizes the v12 P45-P60 evidence state for paper and
repository integration. It records what each phase supports, what each phase
does not support, which artifacts are paper-facing, which artifacts remain
appendix or repo-only, which negative results must be preserved, and which
future work remains operator-gated.

PAPER-RS does not create new empirical evidence. It restructures the manuscript
and paper-facing docs so the current evidence state is presented as live-agent
operational diagnosis, fail-closed bridge auditing, and candidate evidence
packaging. Route 5 and Route 8 remain locked.

## Ledger

| phase | artifact_family | primary_files_or_directories | data_source_kind | execution_status | metric_bridge_status | metric_claim_level | selector_label_scope | paper_evidence_eligible | measurement_validation_claim | denied_claims | manuscript_location | caveat_sentence |
|---|---|---|---|---|---|---|---|---:|---:|---|---|---|
| P45 | one-stratum bridge calibration lane | `docs/experiments/P45-bridge-calibration-closure.md`; P45 bridge artifacts | operator/API-ready lane; current `bio_attribute` canaries | executed and closed negative for current stratum | non-calibrated / failed / underpowered for current stratum | `ambiguous_metric` for failed artifact; downstream utility `operational_utility_only` | none from bridge support | false | false | `calibrated_proxy_supported`, `vinfo_proxy_supported`, measurement validation | main paper Section 4.7 / limitations as negative closure | The current `bio_attribute` bridge lane was implemented but did not establish a stable utility-to-logloss bridge; this is fail-closed negative claim-gate evidence, not bridge support. |
| P46 | synthetic structural benchmark | `docs/experiments/synthetic-regime-v12.md`; `artifacts/experiments/synthetic_regime_v12/` | synthetic oracle structural benchmark | executed deterministic structural scaffold | not a real bridge | `ambiguous_metric` / `synthetic_structural_only` | structural signatures only | false | false | synthetic evidence as bridge evidence, deployed V-information verification, measurement validation | main paper as structural stress test only; appendix for artifacts | Synthetic structural diagnostics can illustrate signature separation, but they do not validate deployed V-information or create bridge evidence. |
| P47 | fixture realistic-task/model-adjudicated benchmark | `docs/experiments/realistic-task-model-adjudicated-v12.md`; `artifacts/experiments/realistic_task_model_adjudicated_v12/` | fixture / model-adjudicated | executed deterministic fixture scaffold | missing for paper claims | `operational_utility_only` at most | workflow/model-adjudicated scaffold only | false | false | human labels, human-human kappa, paper-grade validation, calibrated proxy support | appendix/repo-only | Fixture model-adjudicated labels are not human labels and do not provide kappa or paper-grade validation. |
| P48 | Phase B replay hardening | `docs/protocols/phase-b-replay-protocol.md`; `cps/experiments/phase_b_replay.py` | fixture/replay substrate | implemented replay classification hardening | missing/stale bridge fails closed | `operational_utility_only` or `ambiguous_metric` depending bridge state | replay usability and auditability only | false by itself | false | replay usability as metric support, fixture replay as paper evidence | main paper only as auditability infrastructure; details appendix | Replay usability is not metric support; replay completeness cannot substitute for a fresh matching MetricBridgeWitness. |
| P49 | extraction audit pilot | `docs/experiments/extraction-audit-pilot-v12.md`; `artifacts/experiments/extraction_audit_pilot_v12/` | fixture extraction audit | executed deterministic fixture pilot | not a metric bridge | `operational_utility_only` at most | extraction-risk substrate only | false | false | extraction audit as selector validity, bridge support, measurement validation | appendix/repo-only, with conceptual mention in extraction-risk section | Extraction audit results expose M-star to M risk but do not prove selector validity or bridge support. |
| P50 | ReprojectionWitness scaffold | `docs/experiments/reprojection-witness-pilot-v12.md`; `artifacts/experiments/reprojection_witness_pilot_v12/` | fixture operational audit | executed deterministic fixture scaffold | not a metric bridge | `operational_utility_only` or `ambiguous_metric` for fail-closed rows | operational audit trail only | false | false | ReprojectionWitness as deployed runtime improvement, selector correctness, V-information support | appendix/repo-only | ReprojectionWitness records audit trails; it does not prove deployed runtime improvement. |
| P51 | state reconciliation / documentation hygiene | `README.md`; `docs/README.md`; `docs/templates/claim-boundary-checklist.md`; `tests/test_revised_framing_guardrails.py` | documentation | completed and independently reviewed | not applicable | none | none | false | false | evidence claim upgrade, synthetic-only to vinfo mapping | repo navigation / reviewer handoff | P51 reconciles repository state only; it creates no empirical evidence. |
| P52 | manuscript proof repair and evidence-state integration | `docs/archive/context_projection_fixed_v12.md`; `tests/test_revised_framing_guardrails.py` | manuscript/documentation | completed and independently reviewed | not applicable | none | none | false | false | manuscript claim upgrade, P45 calibrated bridge claim | main manuscript anchor | P52 repairs proof/evidence wording and integrates P45 negative closure without adding empirical evidence. |
| P53 | diagnostic threshold contract | `docs/protocols/diagnostic-threshold-contract-v12.md`; `docs/templates/diagnostic-threshold-contract-template.json`; `tests/test_diagnostic_threshold_contract.py` | protocol/template | completed and independently reviewed | contract records witness status; presence is not support | none | none | false | false | validation, post hoc threshold inference, fixture/synthetic/replay upgrades | appendix/protocol reference | The threshold contract is a predeclared audit scaffold, not validation or bridge evidence. |
| P54 | new bridge stratum design | `docs/experiments/P54-new-bridge-stratum-design-v12.md`; `configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json`; `tests/test_p54_bridge_stratum_design.py` | design config; operator-imported rows gated | design completed and independently reviewed; execution blocked until operator approval | no bridge evidence | none | none | false | false | P54 design as `calibrated_proxy_supported`, P54 design as `vinfo_proxy_supported` | appendix/repo-only design record | P54 selects `evidence_packet_selection_microtask_v1` but creates no bridge evidence. |
| P55 | new-stratum bridge pilot scaffold | `cps/experiments/bridge_calibration_pilot.py`; P55 config/tests/docs; `artifacts/experiments/p55_bridge_calibration_pilot/` | operator-imported rows required; absent | blocked no-row report; rows imported/validated = 0 | missing / no rows; no fit metrics | `ambiguous_metric` as blocked artifact status; review ceiling none | none | false | false | P55 blocked/no-row artifact as `calibrated_proxy_supported`, P55 blocked/no-row artifact as `vinfo_proxy_supported`, measurement validation | negative/blocked results table; appendix/repo-only | P55 remains `failed_closed_no_rows / blocked_operator_required`; no `c_s`, `zeta_s`, held-out metrics, or bridge support were computed. |
| P56 | realistic dispatch replay scaffold | `configs/runs/realistic-dispatch-replay-p56.json`; `cps/experiments/realistic_dispatch_replay.py`; `artifacts/experiments/p56_realistic_dispatch_replay/` | operator-imported traces required; absent | blocked no-trace report; traces imported/validated = 0 | missing; no imported traces | `ambiguous_metric` as no-trace artifact status; review ceiling none | replay classification scaffold only | false | false | P56 no-trace scaffold as replay evidence, replay usability as metric support, bridge support from replay-only | negative/blocked results table; appendix/repo-only | The legacy P56 scaffold row remains `no_imported_traces`; it is not the later Route 2 P56-Route2 operational lane. |
| P57 | extraction audit v2 scaffold | `docs/experiments/P57-extraction-audit-v2-plan.md`; `docs/templates/extraction-audit-v2-record-template.json`; `docs/templates/human-sentinel-extraction-audit-protocol-template.md`; `tests/test_p57_extraction_audit_v2.py` | docs/templates/tests only | developed and independently reviewed; not executed; uncommitted at P60 time | not a metric bridge | none | extraction-risk scaffold only | false | false | selector validity, metric bridge support, V-information support, measurement validation, model-adjudicated labels as human labels | appendix/repo-only scaffold | P57 plans extraction-risk measurement and human-sentinel gates; it does not execute labels or prove selector validity. |
| P58 | provenance-aware redundancy diagnostic scaffold | `docs/experiments/P58-provenance-aware-redundancy-plan.md`; `docs/templates/provenance-redundancy-diagnostic-template.json`; `tests/test_p58_provenance_aware_redundancy.py` | docs/templates/tests only | developed and independently reviewed; not executed; uncommitted at P60 time | not a metric bridge | `operational_utility_only` at most for future diagnostics | `ambiguous` heuristic scope | false | false | selector validity, metric bridge support, calibrated proxy support, V-information support, measurement validation | appendix/repo-only scaffold | P58 separates redundancy categories as operational heuristics only; it does not calibrate a selector or bridge. |
| P59 | ReprojectionWitness replay-integration scaffold | `docs/experiments/P59-reprojection-replay-integration-plan.md`; `docs/templates/reprojection-witness-replay-template.json`; `tests/test_p59_reprojection_replay_integration.py` | docs/templates/tests only | developed and independently reviewed; not executed; uncommitted at P60 time | missing by default; witness presence is not support | `operational_utility_only` at most for future audit rows | `ambiguous` audit scope | false | false | deployed runtime improvement, selector validity, metric bridge support, V-information support, measurement validation | appendix/repo-only scaffold | P59 improves ReprojectionWitness auditability only; before/after fixture improvement is not deployed runtime improvement. |
| P60 | evidence ledger / manuscript package | `docs/paper/v12-evidence-ledger.md`; `docs/reviews/P51-P60-v12-phase-summary.md`; `docs/reviews/P60-v12-evidence-ledger-manuscript-package-review.md`; optional checklist | documentation packaging | packaging phase pending independent review | not applicable | none | none | false | false | automatic claim upgrade, paper evidence from scaffolds, measurement validation | paper integration package | P60 is a ledger and manuscript-integration package only; it creates no new evidence. |
| P63R | Route 2 HotpotQA answer bridge | `artifacts/experiments/p55_hotpotqa_bridge_calibration/`; `docs/experiments/P63R-hotpotqa-real-bridge-calibration-report.md` | real HotpotQA candidate pools and reviewed operator rows | executed and failed closed | failed gates | `operational_utility_only` | none from bridge support | false | false | calibrated proxy support, V-information support, measurement validation, paper evidence, P55 bridge support | Section 4.8 / Appendix C as negative bridge result | The HotpotQA answer-NLL bridge failed closed and cannot support metric bridge claims. |
| P63R-FixA | Route 2 circular positive-control diagnostic | `artifacts/experiments/p55_hotpotqa_support_classification_bridge_calibration/`; `docs/experiments/P63R-FixA-hotpotqa-support-classification-bridge.md` | real HotpotQA labels with circular utility construction | executed positive control | positive-control only; not bridge evidence | `positive_control_only` | none | false | false | calibrated proxy support, V-information support, measurement validation, paper evidence | Appendix C as sanity check only | FixA proves the calibration machinery detects a perfectly aligned circular control; it is not independent metric bridge evidence. |
| P63R-FixB | Route 2 non-circular support-classification bridge | `artifacts/experiments/p55_hotpotqa_support_independent_utility_bridge_calibration/`; `docs/experiments/P63R-FixB-hotpotqa-independent-support-utility-bridge.md` | real HotpotQA labels and independent utility path | executed and failed closed | failed gates | `operational_utility_only` | none from bridge support | false | false | calibrated proxy support, V-information support, measurement validation, paper evidence, P55 bridge support | Section 4.8 / Appendix C as negative bridge result | FixB is a valid non-circular negative bridge attempt and does not establish metric bridge support. |
| P56-Route2 | HotpotQA operational dispatch traces | `artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl`; `docs/experiments/P56-hotpotqa-operational-dispatch-traces.md` | real HotpotQA candidate pools | accepted; 2,000 / 2,000 traces validated | bridge witness failed or absent | `operational_utility_only` | operational selector labels only; oracle marked `non_deployable_upper_bound` | false | false | P56 metric support, metric bridge support, calibrated proxy support, V-information support, paper evidence | Section 4.8 / Appendix C as operational replay only | P56 supplies operational HotpotQA replay traces only because bridge gates failed closed. |
| P66-Route2 | HotpotQA operational comparison | `artifacts/experiments/p56_hotpotqa_operational_comparison/`; `docs/experiments/P66-hotpotqa-operational-comparison.md` | accepted P56 HotpotQA traces | accepted; v12 wins 6 / 6 paired recall comparisons against deployable baselines | bridge witness failed or absent | `operational_utility_only` | deployable baseline comparison only; oracle marked `non_deployable_upper_bound` | false | false | global selector superiority, metric bridge support, calibrated proxy support, V-information support, measurement validation, paper evidence | Section 4.8 / Appendix C as operational comparison only | P66 supports only an operational HotpotQA comparison result under matched budgets. |
| P67R | Route 2 operational evidence package and claim ledger | `docs/experiments/P67R-route2-operational-evidence-package.md`; `artifacts/experiments/route2_operational_evidence_package/` | package over accepted Route 2 artifacts | accepted and pushed at `717796a` | no bridge upgrade | `operational_utility_only`; no claim upgrade | operational-only package | false | false | metric bridge support, calibrated proxy support, V-information support, measurement validation, paper evidence | Section 4.8 / Appendix C package reference | P67R packages operational-only Route 2 evidence and preserves the negative bridge results. |
| Route 3A | support-grounded bridge protocol | `docs/experiments/Route3A-pre-registration-plan.md`; `docs/experiments/Route3A-support-grounded-bridge.md`; `artifacts/benchmarks/route3a_hotpotqa_support_grounded_generation_report.json` | real HotpotQA candidate pools and approved live logprob evaluator | executed and failed closed before calibration | below minimum validated rows; calibration did not run | `no_claim_upgrade` | none from bridge support | false | false | support_grounded_bridge_candidate achieved, metric bridge support, calibrated proxy support, V-information support, measurement validation, paper evidence, P55 bridge support | Appendix C / repo-only as negative bridge-repair diagnostic | Route 3A tested a support-grounded bridge protocol but validated only 461 / 600 rows, below the predeclared 500-row threshold. |
| Route 3B | revised support-grounded bridge protocol | `docs/experiments/Route3B-route3a-revision-pre-registration-plan.md`; `docs/experiments/Route3B-support-grounded-bridge-revision.md`; `artifacts/benchmarks/route3b_hotpotqa_support_grounded_generation_report.json`; `artifacts/experiments/route3b_support_grounded_bridge_calibration/` | real HotpotQA candidate pools and approved live logprob evaluator | executed; reached calibration scale; failed closed at gates | failed preregistered sign-agreement, Spearman, and normalized-residual gates | `failed_closed_no_claim_upgrade` | none from bridge support | false | false | support_grounded_bridge_candidate achieved, bridge repaired, repair succeeded, metric bridge support, calibrated proxy support, V-information support, measurement validation, paper evidence, P55 bridge support | Appendix C / repo-only as negative bridge-repair diagnostic | Route 3B fixed row-count attrition and passed non-circularity checks, but calibration failed closed with no claim upgrade. |
| EPF WS0-WS10 / EPF-FINAL | live-API-only candidate evidence package factory with silver-label finalizer | `artifacts/experiments/epf_candidate_package/`; `artifacts/experiments/epf_c_silver_labels/`; `artifacts/experiments/epf_final/`; `docs/experiments/WS0-WS9*`; `docs/experiments/EPF-final-live-api-silver-label-candidate-package.md`; `docs/reviews/WS10-candidate-evidence-independent-review-template.md`; `docs/paper/WS10-paper-positioning-patch-plan.md` | DashScope-compatible live API; normalized outputs only | accepted with notes as candidate operational package; 8 silver-label rows over 2 parent samples | true fixed-target teacher-forced NLL blocked; no continuation-scoring bridge; no human/external gold validation | `operational_utility_only/no_claim_upgrade` | candidate operational diagnostics and LLM-generated silver-label candidate evidence only | false | false | teacher-forced NLL support, fixed-target continuation scoring support, metric bridge support, calibrated proxy support, V-information support, measurement validation, human/external gold validation, paper evidence, global selector superiority, Route 5 unlock, Route 8 unlock | Section 4.9 / Appendix/repo-only candidate package factory; paper-positioning note only | EPF packages live-API operational diagnostics and model-adjudicated silver labels, but the backend lacks true fixed-target continuation scoring and WS5 lacks human/external gold labels, so the package remains candidate operational evidence only. |

## Main-Paper-Safe Evidence Table

These entries can be mentioned in the main paper only with the listed caveats.

| phase | safe paper-facing use | required caveat |
|---|---|---|
| P45 | Negative closure for the current `bio_attribute` bridge lane as fail-closed claim-gate evidence. | The lane is non-calibrated; no `calibrated_proxy_supported` or `vinfo_proxy_supported` claim is allowed. |
| P46 | Synthetic structural diagnostics as a minimal oracle structural stress test. | Synthetic structural evidence is not bridge evidence, measurement validation, or deployed V-information verification. |
| P48 | Replay hardening as auditability/replayability infrastructure. | Replay usability is not metric support and is not paper evidence by itself. |
| P52 | Proof repair and evidence-state integration as manuscript integrity work. | P52 is manuscript alignment only and creates no new empirical evidence. |
| P53 | Diagnostic threshold contract as a predeclared audit protocol. | A contract can govern future diagnostics, but it is not validation or bridge evidence. |
| P66-Route2 | HotpotQA operational replay/comparison result: v12 improves supporting-fact recall against deployable baselines under matched budgets. | Because Route 2 and Route 3 bridge gates failed closed, this remains `operational_utility_only`; it is not metric bridge support, paper evidence, or a global selector superiority claim. |
| EPF WS0-WS10 / EPF-FINAL | Backend-constrained candidate package factory accepted with notes for organizing live-API operational diagnostics and 8 LLM-generated silver-label rows over 2 parent samples. | EPF is not paper evidence and does not support teacher-forced NLL, fixed-target continuation scoring, metric bridge, calibrated proxy, V-information proxy, measurement validation, human/external gold validation, global selector superiority, Route 5 unlock, or Route 8 unlock claims. |

No fixture, synthetic, no-row, no-trace, or scaffold artifact should be described
as validation.

## PAPER-RS Operational Diagnostic Claim Table

This restructuring addendum records the paper-facing route summaries after the
live-API operational package. Each row is an allowed/denied claim boundary, not
new evidence.

| package | current evidence state | allowed paper-facing claim | denied claims |
|---|---|---|---|
| Route 2 operational evidence | P56-Route2 accepted 2,000 HotpotQA operational traces; P66 accepted matched-budget operational comparison; P67R packages the claim ledger. | HotpotQA operational replay shows that the v12 diagnostic policy improves supporting-fact recall against deployable baselines under matched budgets, with claim level `operational_utility_only`. | metric bridge support, P55 bridge support, P56 metric support, calibrated proxy support, V-information support, measurement validation, paper evidence, global selector superiority, deployed V-information verification |
| Route 3 fail-closed bridge attempts | Route 3A failed below the minimum validated-row gate; Route 3B reached calibration scale but failed preregistered calibration gates. | Negative support-grounded bridge-repair diagnostics; `failed_closed_no_claim_upgrade`. | bridge repaired, support_grounded_bridge_candidate achieved, metric bridge support, calibrated proxy support, V-information support, measurement validation, paper evidence |
| Route 4 fail-closed bridge attempts | Route 4A failed closed at gates; Route 4B failed closed underpowered; Route 4C blocked because FEVER source/evidence provenance was unavailable. | Fail-closed redesign diagnostics and future-gated protocol evidence only; `no_claim_upgrade`. | accepted bridge candidate, final bridge support, calibrated proxy support, V-information support, measurement validation, Route 5 unlock |
| Route 6B model-adjudicated measurement candidate | Route 6B scaled model-adjudicated labels to 300 accepted pairs, with raw responses not stored. | Model-adjudicated measurement candidate only under `operational_utility_only/no_claim_upgrade`. | human labels, human-human kappa, measurement validation, human/external gold validation, paper evidence |
| Delta judge-reliability audit | Delta terminal status is `FAILED_CLOSED_JUDGE_RELIABILITY`; Route 4E bridge gates also failed closed. | Fail-closed judge-reliability and model-only operational audit; no claim upgrade. | human measurement validation, calibrated proxy support, V-information support, metric bridge support, selector superiority, global selector superiority |
| Gamma operational expansion | Gamma completed non-FEVER HotpotQA and project-native operational workbench smokes with 76 audited traces. | Operational expansion smoke under matched budgets and shadow claim mode; `operational_utility_only/no_claim_upgrade`. | selector superiority, metric bridge support, measurement validation, calibrated proxy support, V-information support, paper evidence |
| LogProbe / EPN / TFS blocked diagnostic chain | LogProbe switched target design but did not run a bridge repair; TeacherForcedLogProbe reports `BLOCKED_NO_TEACHER_FORCED_BACKEND`; EPN remains blocked. | Backend readiness and blocked diagnostic chain showing why live-API logprobs remain operational confidence diagnostics only. | fixed-target teacher-forced NLL support, fixed-target continuation scoring support, bridge calibration, metric bridge support, Route 5 unlock, Route 8 unlock |
| EPF-FINAL candidate evidence factory | EPF-FINAL accepted with notes; 8 LLM-generated silver-label rows over 2 parent samples; no raw API responses; no human/external gold labels. | Backend-constrained candidate operational evidence factory under `operational_utility_only/no_claim_upgrade`. | teacher-forced NLL support, fixed-target continuation scoring support, metric bridge support, calibrated proxy support, V-information support, measurement validation, human/external gold validation, paper evidence, global selector superiority, Route 5 unlock, Route 8 unlock |

## POST-LAPI operational evaluation and weak-evidence diagnostics

The POST-LAPI freeze integrates POST-3 through POST-7 into the manuscript section titled `Operational evaluation and weak-evidence diagnostics`. The integration is docs-only and uses `artifacts/audits/post_lapi_evidence_freeze/table_inputs.json` as the normalized source of truth. It does not run live API calls, run new experiments, store raw API responses, or change the claim ceiling.

| result | evidence_source | allowed_claim | denied_claim | evidence_tier | live_api_call_count | human_label_status | metric_bridge_status | route_5_status | route_8_status | raw_response_stored |
|---|---|---|---|---|---:|---|---|---|---|---|
| POST-3 judge stability | `artifacts/experiments/post_lapi_judge_stability/` | model-adjudicated weak evidence candidate only | measurement validation; human/external gold validation; calibrated judge; paper-grade evidence | weak/model-adjudicated candidate evidence | 240 | absent | absent | locked | locked | false |
| POST-4 sufficiency / abstention | `artifacts/experiments/post_lapi_sufficiency_abstention/` | sufficiency_abstention_diagnostic_only | truth validation; human-calibrated abstention; measurement validation; paper-grade evidence | operational diagnostic candidate evidence | 50 final artifact calls / 100 total turn calls | absent | absent | locked | locked | false |
| POST-5 reprojection witness | `artifacts/experiments/post_lapi_reprojection_witness/` | operational reprojection witness and omitted-evidence diagnostic | validated repair; truth correction guarantee; selector superiority; metric bridge support | operational omitted-evidence evidence only | 26 | absent | absent | locked | locked | false |
| POST-6 operational replay expansion | `artifacts/experiments/post_lapi_operational_replay/` | scoped operational improvement under matched budgets only | selector superiority; global selector superiority; metric bridge support; paper-grade evidence | scoped operational replay evidence only | 0 | absent | absent | locked | locked | false |
| POST-7 extraction quality audit | `artifacts/experiments/post_lapi_extraction_quality_audit/` | model-adjudicated extraction-risk evidence and operational extraction audit only | human-validated extraction measurement; measurement validation; theorem transfer to M-star | model-adjudicated extraction-risk evidence only | 100 | absent | absent | locked | locked | false |
| Artifact hygiene / raw-response policy | `artifacts/audits/post_lapi_evidence_freeze/` | artifact hygiene evidence for the frozen candidate package | new experiment; new live API evidence; raw response storage | reproducibility and storage-policy evidence only | 0 during SUB-0/SUB-1 synthesis | absent | absent | locked | locked | false |

Summary metrics: POST-3 records 30 examples, 240 normalized rows, duplicate agreement `0.9833`, order-swap agreement `0.9833`, and rubric paraphrase agreement `0.9667`. POST-4 records 50 normalized rows, 50 final artifact calls, 100 total turn calls, and gate `sufficiency_abstention_candidate_ready`. POST-5 records 26 normalized rows, repair candidate rate `0.576923`, label change rate `0.576923`, unsupported-to-supported rate `0.576923`, and parse failed rate `0.0`. POST-6 records 2,000 replay records over 200 candidate pools, budgets `512` and `1024`, and oracle `non_deployable_upper_bound`. POST-7 records 100 extraction audit records, 10 per stratum, value-weighted loss proxy `0.197403`, and gate `post7_extraction_quality_audit_completed`.

Boundary statement: generated-token chat logprobs are operational confidence diagnostics only; model-adjudicated labels are weak evidence only; operational replay is scoped to named datasets, budgets, baselines, metrics, and materialization regime; extraction audit is model-adjudicated extraction-risk evidence only; reprojection witness is operational omitted-evidence evidence only. The current conclusion remains `operational_utility_only/no_claim_upgrade`.

Denied POST-LAPI upgrades: fixed-target NLL support, teacher-forced scoring support, metric bridge support, `calibrated_proxy_supported`, `vinfo_proxy_supported`, measurement validation, human/external gold validation, paper-grade evidence, selector superiority, global selector superiority, Route 5 unlock, and Route 8 unlock.

## Appendix / Repo-Only Scaffold Table

| phase | appendix_or_repo_only_artifact | reason |
|---|---|---|
| P47 | Fixture realistic-task/model-adjudicated benchmark | Fixture/model-adjudicated labels are workflow evidence only, not human labels or kappa. |
| P49 | Fixture extraction audit pilot | Extraction-risk substrate only; not selector validity or bridge support. |
| P50 | Fixture ReprojectionWitness scaffold | Operational audit trail only; not deployed runtime improvement. |
| P53 | Diagnostic threshold contract | Protocol/audit scaffold only. |
| P54 | `evidence_packet_selection_microtask_v1` stratum design | Design only; no bridge evidence created. |
| P55 | Blocked bridge pilot scaffold and no-row artifacts | Operator rows absent; no fit metrics or bridge support. |
| P56 | Blocked realistic dispatch replay scaffold and no-trace artifacts | Imported traces absent; no replay evidence or metric support. |
| P57 | Extraction audit v2 plan/templates/tests | Not executed; no human labels, kappa, or measurement validation. |
| P58 | Provenance-aware redundancy plan/template/tests | Operational diagnostic scaffold only. |
| P59 | ReprojectionWitness replay-integration plan/template/tests | Operational audit scaffold only; no replay intervention executed. |

## Negative Results To Preserve

| phase | negative_or_blocked_result | preservation rule |
|---|---|---|
| P45 | Current `bio_attribute` stratum did not establish stable utility-to-logloss calibration. | Do not hide the fail-closed closure or present it as bridge support. |
| P55 | Operator-imported rows absent; `failed_closed_no_rows / blocked_operator_required`; rows imported/validated = 0. | Do not describe P55 as a successful bridge pilot; no `calibrated_proxy_supported` or `vinfo_proxy_supported` claim. |
| P56 | Imported realistic dispatch traces absent; `no_imported_traces`; traces imported/validated = 0. | Do not describe P56 as successful realistic replay evidence or metric support. |
| P63R | HotpotQA answer-NLL bridge failed closed. | Preserve as a negative bridge result; do not convert it into bridge support. |
| P63R-FixA | Circular positive-control diagnostic. | Preserve as a sanity check only; do not treat perfect metrics as independent bridge evidence. |
| P63R-FixB | Valid non-circular bridge attempt failed closed. | Preserve as a negative bridge result; downstream P56/P66 use remains operational-only. |
| Route 3A | Support-grounded bridge attempt failed below the minimum validated-row gate. | Preserve as failed-closed bridge-repair diagnostic; calibration did not run. |
| Route 3B | Revised support-grounded bridge attempt reached calibration scale but failed gates. | Preserve as failed-closed bridge-repair diagnostic; do not describe this as bridge repair success. |
| EPF WS1 / WS5 / EPF-FINAL | Fixed-target teacher-forced NLL remains blocked; WS5 measurement validation remains blocked without human/external gold labels; EPF-FINAL accepted-with-notes status remains candidate operational only. | Do not convert chat-logprob diagnostics, constrained label-generation proxies, LLM-generated silver labels, or LLM judge labels into metric bridge support, measurement validation, human/external gold validation, paper evidence, Route 5 unlock, or Route 8 unlock. |

## Future Work / Operator-Gated Table

| future_work_item | gate_required | claim_boundary |
|---|---|---|
| P55 bridge progression | contract-compliant operator-imported rows for `evidence_packet_selection_microtask_v1`; active-stratum match; candidate-pool hash stability; ESS and residual gates | May at most support stratum-local `calibrated_proxy_supported` if all P55 gates pass; still no measurement validation. |
| P56 replay progression | imported realistic dispatch traces with full dispatch identity, considered candidate set, materialization and bridge witness binding | Replay comparable does not automatically mean metric support. |
| Human-sentinel extraction audit | operator approval, actual human annotators, valid agreement calculation, contamination review | Human sentinel evidence is not automatically measurement validation. |
| Measurement-validation candidate | human-label/kappa/contamination gates plus relevant metric-bridge review | Requires separate review; model adjudication cannot fill missing human labels or missing kappa. |
| Formal V-information support | log-loss alignment plus fresh fixed-model bridge, reviewed near-optimality argument, or empirical minimization over the declared predictive family | Generic utility/logloss correlation is insufficient. |
| EPF limited-scope candidate claims | accepted-with-notes review plus live-API backend limitations, human/external gold availability, and storage-policy review | Current EPF-FINAL may at most remain a backend-constrained operational candidate package; any stronger claim requires a separate future review and currently unavailable evidence. |

## Forbidden Phrase / Denied Claim Table

| phrase_or_claim | ledger_status | safe_replacement |
|---|---|---|
| `Vinfo_proxy_certified` | denied active wording | use `vinfo_proxy_supported` only if separately justified by formal/fixed-model bridge review |
| `greedy_valid` | denied active wording | use `greedy_supported` only under the predeclared selector and metric gates |
| `measurement_validated` | denied unless separately reviewed | use `measurement_validation_claim: false` for current P45-P60 package |
| deployed V-information verification | denied | proxy-regime diagnosis |
| theorem-level deployed submodularity verification | denied | conditional formal theorem under assumptions |
| fixture evidence as paper-grade evidence | denied | fixture-only engineering/scaffold evidence |
| synthetic evidence as bridge evidence | denied | synthetic structural stress test |
| replay usability as metric support | denied | replay auditability/usability only |
| EPF chat-logprob diagnostics as fixed-target NLL or bridge evidence | denied | backend-constrained operational confidence diagnostics |
| EPF generated-token logprobs as fixed-target continuation scoring support | denied | live-API limitation / blocked teacher-forced backend |
| EPF constrained label generation, LLM-generated silver labels, or LLM judge labels as measurement validation | denied | candidate/weak-source operational diagnostics pending human/external gold |
| Route 5 or Route 8 unlock from EPF-FINAL | denied | both routes remain locked |
| extraction audit as selector validity | denied | extraction-risk evidence |
| ReprojectionWitness as deployed runtime improvement | denied | operational audit witness |
| P55 blocked/no-row artifact as `calibrated_proxy_supported` | denied | blocked no-row report |
| P56 no-trace scaffold as replay evidence | denied | blocked no-trace scaffold |

## Manuscript Integration Checklist

- Main paper should preserve Proxy-Regime Diagnosis framing.
- Formal theorems apply only to formal `f_i^V` under assumptions.
- Utility/logloss/proxy metrics remain separated.
- P45 negative closure must not be hidden.
- P55/P56 blocked states must not be described as successful experiments.
- Synthetic and fixture results must not be described as validation.
- Model-adjudicated labels must not be called human labels.
- Human sentinel work is future/operator-gated unless executed.
- Missing human labels or missing human-human kappa must not be filled by model adjudication.
- Runtime and replay artifacts are audit interfaces, not validation by themselves.

## Current Blocked / Scaffold State Summary

P55 remains `failed_closed_no_rows / blocked_operator_required`. Rows
imported/validated are 0. Review ceiling remains none. Paper evidence remains
false. Fit metrics remain not computed. `vinfo_proxy_supported` and
`calibrated_proxy_supported` remain denied.

The legacy P56 scaffold row remains `no_imported_traces`. This does not describe
the later Route 2 HotpotQA P56-Route2 lane, which has validated operational
traces but no metric-bridge support. Paper evidence remains false. Measurement
validation remains false. `vinfo_proxy_supported` and
`calibrated_proxy_supported` remain denied.

The later Route 2 HotpotQA lane supersedes the old P56 scaffold only for the
separate HotpotQA operational replay/comparison package: P56-Route2 has 2,000
validated HotpotQA operational traces, and P66-Route2 has an accepted matched
budget comparison. Because P63R bridge gates failed closed and FixA is only a
circular positive control, the Route 2 package remains `operational_utility_only`
with no claim upgrade and no metric bridge support.

The subsequent Route 3 support-grounded bridge line remains a negative
diagnostic, not a repair. Route 3A failed closed below the predeclared minimum
validated-row threshold. Route 3B reached calibration scale and passed
non-circularity checks, but failed the preregistered sign-agreement, Spearman,
and normalized-residual gates. Route 3B metric claim level is
`failed_closed_no_claim_upgrade`; `calibrated_proxy_supported`,
`vinfo_proxy_supported`, measurement validation, paper evidence, metric bridge
support, P55 bridge support, P56 metric support, global selector superiority,
and deployed V-information verification remain false.

## Route 2 + Route 3 Final Claim Booleans

| claim_flag | value |
|---|---|
| Route 2 metric_claim_level | `operational_utility_only` |
| Route 3A status | `failed_closed_below_min_rows` |
| Route 3B status | `failed_closed_gate_failed` |
| Route 3B metric_claim_level | `failed_closed_no_claim_upgrade` |
| calibrated_proxy_supported | false |
| vinfo_proxy_supported | false |
| measurement_validation | false |
| paper_evidence | false |
| metric_bridge_support | false |
| p55_bridge_support | false |
| p56_metric_support | false |
| global_selector_superiority | false |
| deployed_v_information_verification | false |

P57 remains extraction-risk scaffold only. P58 remains operational diagnostic
scaffold only. P59 remains operational audit scaffold only. P60 does not convert
any of these scaffold states into empirical validation.

## EPF Final Claim Booleans

| claim_flag | value |
|---|---|
| EPF claim_status | `operational_utility_only/no_claim_upgrade` |
| EPF review_outcome | `ACCEPT_WITH_NOTES` |
| silver_label_rows | 8 |
| silver_label_parent_samples | 2 |
| teacher_forced_fixed_target_nll_available | false |
| raw_api_responses_stored | false |
| ws5_measurement_validation | false |
| calibrated_proxy_supported | false |
| vinfo_proxy_supported | false |
| measurement_validation | false |
| paper_evidence | false |
| metric_bridge_support | false |
| global_selector_superiority | false |
| route5_locked | true |
| route8_locked | true |

Under the available live-API backend, EPF does not expose true fixed-target
teacher-forced continuation scoring. Its outputs are reviewable candidate
operational evidence packages: chat-logprob confidence, constrained
label-generation proxies, LLM-generated silver labels, weak-source judge audits,
multi-benchmark operational robustness summaries, and uncertainty-bounded
reports remain operational diagnostics or candidate evidence only.
