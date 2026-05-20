# Paper Alignment V12

This document maps the current fixed v12 Context Projection Selection paper
direction to the repository. It is the default paper-alignment entrypoint for
new implementation, review, and evidence-planning work.

Current manuscript anchor:

- `docs/archive/context_projection_fixed_v12.md`

Legacy manuscript and alignment anchors:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`

The v10 files are preserved as historical/archive material. They should not be
used as the default source for new paper-facing terminology.

## Current Paper Direction

The v12 paper is framed as:

```text
conditional theory + metric bridge + proxy-regime diagnosis + minimal structural evidence
```

The active framing is proxy-regime diagnosis, not proxy-regime certification.
The repository remains a measurement and runtime-audit scaffold. It does not
claim deployed V-information verification, measurement validation, scientific
validation, theorem inheritance for heuristic pipelines, or scheduler
correctness.

## V12 Claim Vocabulary

Selector-regime labels should migrate toward:

- `greedy_supported`
- `pairwise_escalate`
- `higher_order_risk`
- `ambiguous`

Metric-claim levels should migrate toward:

- `vinfo_proxy_supported`
- `calibrated_proxy_supported`
- `operational_utility_only`
- `ambiguous_metric`

Deprecated or risky active vocabulary includes:

- `Vinfo_proxy_certified`
- `greedy_valid`
- bare `escalate` when it should distinguish `pairwise_escalate` from
  `higher_order_risk`
- proxy-regime `certification` language when the intended claim is diagnosis

Historical artifacts, old reviews, and denied-claim guardrails may still mention
legacy labels. New paper-facing reports should either use the v12 vocabulary or
explicitly mark legacy vocabulary as compatibility or archive state.

## Repo Evidence Lanes

| V12 paper lane | Repository surface | Current status |
|---|---|---|
| dispatch-time context projection artifacts | `cps/experiments/artifacts.py`, `cps/runtime/projection_export.py`, `cps/schema/projection_bundle_v1.py` | Implemented scaffold for `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and `ProjectionBundleV1` |
| claim-gated proxy-regime diagnosis | `cps/experiments/metric_bridge_gate.py`, `cps/experiments/claim_gate_report.py`, `cps/experiments/proxy_regime_matrix.py` | Implemented guardrail scaffold; terminology migration remains |
| synthetic structural evidence | `cps/experiments/synthetic_benchmark.py`, `docs/experiments/synthetic-regime-benchmark.md`, `docs/experiments/synthetic-regime-v12.md`, `artifacts/experiments/synthetic_regime_v12/` | P46 refreshed deterministic v12 structural artifacts with four families and cost-aware baseline tables; not measurement validation |
| one-stratum metric bridge calibration | `cps/experiments/bridge_calibration.py`, `configs/runs/bridge-calibration-one-stratum.json`, `docs/experiments/bridge-calibration-one-stratum.md`, `docs/experiments/P45-bridge-calibration-closure.md` | P45 lane implemented and operator/API-ready; current `bio_attribute` stratum failed to establish the bridge, so no `calibrated_proxy_supported` claim is allowed |
| Phase B replay | `cps/experiments/phase_b_replay.py`, `cps/experiments/replay_evidence_package.py`, `docs/protocols/phase-b-replay-protocol.md` | P48 hardened replay status vs metric-claim separation, dispatch identity checks, v12 report outputs, and fail-closed fixture/synthetic boundaries |
| Route 2 HotpotQA operational replay/comparison | `docs/experiments/P67R-route2-operational-evidence-package.md`, `artifacts/experiments/route2_operational_evidence_package/`, `artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl`, `artifacts/experiments/p56_hotpotqa_operational_comparison/` | P63R bridge attempts failed closed or were positive-control only; P56/P66 were accepted as HotpotQA operational replay/comparison evidence under `operational_utility_only`; no metric bridge support claim is allowed |
| Route 3 HotpotQA support-grounded bridge diagnostics | `docs/experiments/Route3A-support-grounded-bridge.md`, `docs/experiments/Route3B-support-grounded-bridge-revision.md`, `artifacts/benchmarks/route3a_hotpotqa_support_grounded_generation_report.json`, `artifacts/benchmarks/route3b_hotpotqa_support_grounded_generation_report.json`, `artifacts/experiments/route3b_support_grounded_bridge_calibration/` | Route 3A failed closed below the minimum validated-row gate; Route 3B reached calibration scale but failed preregistered gates; no claim upgrade |
| live-API-only EPF candidate package factory | `cps/experiments/live_api_evidence_package_factory.py`, `artifacts/experiments/epf_candidate_package/`, `docs/experiments/WS0-WS9*`, `docs/reviews/WS10-candidate-evidence-independent-review-template.md` | WS0-WS10 produced a reviewable candidate operational package under DashScope-compatible live-API constraints; true fixed-target teacher-forced NLL and WS5 measurement validation remain blocked, so no metric bridge, calibrated proxy, V-information proxy, paper evidence, or global selector superiority claim is allowed |
| model-adjudicated evidence | `cps/experiments/route_b_evidence_package.py`, `cps/experiments/model_adjudicated_labels.py`, `cps/experiments/realistic_tasks.py`, `docs/experiments/realistic-task-model-adjudicated-v12.md`, `artifacts/experiments/realistic_task_model_adjudicated_v12/` | P47 added an offline fixture realistic-task benchmark; model-adjudicated proxy evidence only, not human labels or kappa |
| extraction audit | `cps/experiments/extraction_audit.py`, `docs/experiments/extraction-audit-pilot-v12.md`, `artifacts/experiments/extraction_audit_pilot_v12/` | P49 added a deterministic fixture extraction audit pilot for the M-star to M boundary; fixture audit only, not paper evidence |
| optional re-projection witness | `cps/experiments/reprojection_witness.py`, `docs/experiments/reprojection-witness-pilot-v12.md`, `artifacts/experiments/reprojection_witness_pilot_v12/` | P50 added a deterministic fixture ReprojectionWitness scaffold; operational audit only, not paper evidence |

## Bridge Calibration Closure

P45 implemented the offline/importable lane and the opt-in API-generated data
scaffold. Fixture inputs validate engineering behavior only. Live canaries
verified that the fixed-model measured-logprob path works under explicit target
evidence, but the current `bio_attribute` stratum did not establish a stable
utility-to-logloss bridge.

The target quantities remain:

- `c_s`
- `zeta_s`
- sign agreement
- rank correlation
- held-out residual bound
- claim downgrade behavior

For the current `bio_attribute` stratum, no `calibrated_proxy_supported` claim
is allowed. Downstream utility or model-adjudicated diagnostics should remain
`operational_utility_only`; the P45e canary artifact itself is
`ambiguous_metric` because the exported bridge-fit rows were underpowered and
failed the configured `zeta_s` gate. Synthetic structural evidence remains
structural evidence only.

Do not expand this same stratum to a 20-30 row P45 pilot without a new
scientific rationale, a new active stratum, or a materially new
fixed-logloss/utility design.

## Route 2 HotpotQA Operational Evidence Package

Route 2 adds a real-data HotpotQA lane as an operational replay and
negative-bridge case study. The package pushed at commit `717796a` is anchored
by `docs/experiments/P67R-route2-operational-evidence-package.md`,
`artifacts/experiments/route2_operational_evidence_package/`, the P56
HotpotQA dispatch traces, and the P66 operational comparison artifacts.

The paper-facing claim is deliberately limited:

```text
HotpotQA operational replay shows that the v12 diagnostic policy improves
supporting-fact recall against deployable baselines under matched budgets.
Because Route 2 and Route 3 bridge gates failed closed, this is
operational_utility_only, not calibrated metric support.
```

The original P63R HotpotQA bridge and the non-circular FixB bridge failed
closed. FixA is retained only as a circular positive-control diagnostic. P56
validated 2,000 HotpotQA operational traces, and P66 found v12 wins in all six
paired recall comparisons against deployable baselines at budgets 512 and 1024.
The `gold_support_oracle_upper_bound` selector is reported only as
`non_deployable_upper_bound`.

Route 2 does not authorize `calibrated_proxy_supported`,
`vinfo_proxy_supported`, measurement validation, paper evidence, P55 bridge
support, P56 metric support, metric bridge support, global selector superiority,
or deployed V-information verification.

## Route 3 Support-grounded Bridge Diagnostics

Route 3 is a separate metric-bridge repair line informed by the Route 2
negative results. It is not a P63R-compatible repair and does not reinterpret
Route 2 as bridge support.

Route 3A tested a support-grounded utility bridge and failed closed below the
predeclared minimum validated-row threshold: 600 rows were attempted, 461
validated, calibration did not run, and `operator_rows_written` remained false.

Route 3B prospectively revised the sampling protocol to all eligible HotpotQA
instances. It reached calibration scale with 792 attempted rows, 613 validated
rows, and 197 unique original instances. Non-circularity checks passed, but
calibration failed the preregistered sign-agreement, Spearman, and normalized
residual gates. Its metric claim level is `failed_closed_no_claim_upgrade`.

Route 3 therefore reinforces the paper boundary: the HotpotQA replay/comparison
result remains operational-only. It does not authorize `calibrated_proxy_supported`,
`vinfo_proxy_supported`, measurement validation, paper evidence, P55 bridge
support, P56 metric support, metric bridge support, global selector superiority,
or deployed V-information verification.

## Live-API-Only EPF Candidate Package Factory

The Evidence Package Factory (EPF) packages live-API-only operational
diagnostics into a reviewable candidate evidence package. The current backend is
the DashScope-compatible chat API surface. It does not expose true fixed-target
teacher-forced continuation scoring, so EPF does not provide teacher-forced NLL
support or a metric bridge.

EPF outputs are backend-constrained operational diagnostics and candidate
evidence packages only. Chat-logprob confidence rows, constrained
label-generation proxies, weak-source judge audits, multi-benchmark operational
robustness summaries, and uncertainty-bounded reports can support review of
operational behavior, but they do not establish `calibrated_proxy_supported`,
`vinfo_proxy_supported`, measurement validation, paper evidence, metric bridge
support, or global selector superiority. WS5 remains blocked without
human/external gold labels. Route 5 and Route 8 remain locked, and generated
WS6 nested `claim_ledger.json` artifacts remain local-only shadow artifacts.

| Evidence component | Status | Claim ceiling |
| --- | --- | --- |
| WS1 teacher-forced NLL closure | blocked | no metric bridge |
| WS2 chat-logprob confidence | available | operational diagnostic only |
| WS3 constrained label proxy | available | candidate proxy only |
| WS4 judge weak-source audit | available | weak supervision only |
| WS5 hybrid validation | blocked | no measurement validation |
| WS6 multi-benchmark operational robustness | available | scoped operational candidate |
| WS8 uncertainty-bounded reporting | available | candidate operational reporting |

## P46 Synthetic v12 Refresh

P46 refreshes the synthetic structural benchmark under v12 labels. The
deterministic run at `artifacts/experiments/synthetic_regime_v12/` contains
four families: redundancy-dominated, pairwise-synergy, higher-order
prerequisite, and adversarial redundancy.

The paper-facing v12 files are:

- `synthetic_confusion_v12.csv`
- `synthetic_metrics_v12.csv`
- `synthetic_cost_table_v12.csv`
- `synthetic_run_manifest_v12.json`
- `synthetic_report_v12.md`

The refreshed run remains synthetic structural evidence only:

- `metric_claim_level = ambiguous_metric`
- `diagnostic_scope = synthetic_structural_only`
- `evidence_scope = synthetic_structural_only`
- `paper_evidence_eligible = false`

It does not use P45 as bridge evidence and does not upgrade the current
`bio_attribute` stratum.

## P47 Model-Adjudicated Realistic-Task Benchmark

P47 adds a deterministic offline realistic-task benchmark with fixture
model-adjudicated labels. The run covers `paper_revision_microtask`,
`multi_hop_evidence_assembly`, and `repo_change_review_microtask`, then compares
minimal context, full context, top-k retrieval, MMR/density greedy, always-SAG,
and the v12 cost-aware diagnostic policy.

The artifact set is:

- `realistic_task_packets.jsonl`
- `model_adjudicated_labels.jsonl`
- `label_stability_report.json`
- `realistic_selector_comparison.csv`
- `realistic_claim_gate_report.json`
- `realistic_task_report.md`

The fixture run is schema and workflow evidence only:

- `data_source_kind = fixture`
- `paper_evidence_eligible = false`
- `measurement_validation_claim = false`
- `live_api_used = false`

It does not create human labels, kappa, deployed V-information verification,
measurement validation, or calibrated bridge support. Future imported
model-adjudicated labels may use the same schema, but they still require their
own claim gate and cannot be treated as human labels.

## P48 Phase B Replay v12 Hardening

P48 hardens Phase B replay under v12 proxy-regime diagnosis semantics. Replay
usability is now separated from metric claim level through explicit fields:

- `replay_status`
- `replay_claim_scope`
- `metric_claim_level`
- `selector_regime_label`
- `diagnostic_scope`
- `evidence_scope`
- `headline_eligible`
- `headline_exclusion_reason`
- `paper_evidence_eligible`
- `measurement_validation_claim`

Replay classification requires complete dispatch identity:

- `run_id`
- `dispatch_id`
- `agent_id`
- `round_id`

Missing identity blocks replay-comparable use. Missing, stale, incomplete,
fixture-only, or synthetic-only bridge evidence cannot produce calibrated proxy
support. Fixture-only replay remains engineering evidence, not paper-grade
evidence.

Replay provenance also binds candidate-pool evidence by `candidate_pool_hash`.
Identity mismatch or candidate-pool hash mismatch fails closed: no headline
eligibility, no paper evidence eligibility, and no `vinfo_proxy_supported` or
`calibrated_proxy_supported` upgrade from a mismatched bridge witness.

The v12 replay writer emits deterministic JSON/JSONL, CSV summaries, and
`phase_b_replay_v12_report.md` without live API calls.

## P49 Extraction Audit Pilot

P49 adds a deterministic fixture audit for the upstream extraction boundary:

```text
raw source records -> extraction gate -> structured findings -> candidate pool M
```

The artifact set is:

- `extraction_audit_cases.jsonl`
- `extraction_audit_findings.jsonl`
- `extraction_audit_labels.jsonl`
- `extraction_audit_defects.csv`
- `extraction_audit_summary.json`
- `extraction_claim_gate_report.json`
- `extraction_audit_manifest.json`
- `extraction_audit_report.md`

The run checks source-span traceability, provenance handles, missing critical
findings, unsupported findings, duplicate or over-merged findings, contradictory
source cases, deterministic finding hashes, and deterministic candidate-pool
hashes.

The fixture run remains audit substrate only:

- `data_source_kind = fixture`
- `evidence_scope = fixture_extraction_audit_only`
- `paper_evidence_eligible = false`
- `measurement_validation_claim = false`
- `live_api_used = false`

It does not upgrade selector-regime claims, metric bridge claims, P47 realistic
task evidence, or P48 replay evidence.

## P50 Optional ReprojectionWitness Scaffold

P50 adds a deterministic fixture scaffold for optional re-projection decisions:

```text
initial candidate pool M -> initial projection -> trigger -> revised projection -> ReprojectionWitness
```

The artifact set is:

- `reprojection_cases.jsonl`
- `reprojection_witnesses.jsonl`
- `reprojection_actions.csv`
- `reprojection_trigger_counts.csv`
- `reprojection_claim_gate_report.json`
- `reprojection_summary.json`
- `reprojection_manifest.json`
- `reprojection_report.md`

The fixture run records trigger reasons, finding-level context diffs, projection
hashes, materialized-context hashes, candidate-pool provenance, full dispatch
identity, and budget status. Identity mismatch, candidate-pool mismatch, and
over-budget re-projection remain conservative audit rows.

The P50 run remains operational audit substrate only:

- `data_source_kind = fixture`
- `evidence_scope = fixture_reprojection_witness_only`
- `paper_evidence_eligible = false`
- `measurement_validation_claim = false`
- `live_api_used = false`
- `calibrated_proxy_supported = false`
- `vinfo_proxy_supported = false`

It does not upgrade P47, P48, or P49 evidence claims.

## Active Planning Reference

The controlling Codex development/reference package for v12 follow-up work is:

- `docs/codex/v12-phase-docs/README.md`
- `docs/codex/v12-phase-docs/P45-one-stratum-bridge-calibration-plan.md`
- `docs/experiments/P45-bridge-calibration-closure.md`
- `docs/codex/v12-phase-docs/P46-synthetic-v12-artifact-refresh-plan.md`
- `docs/experiments/synthetic-regime-v12.md`
- `docs/codex/v12-phase-docs/P47-model-adjudicated-realistic-benchmark-plan.md`
- `docs/experiments/realistic-task-model-adjudicated-v12.md`
- `docs/codex/v12-phase-docs/P48-phase-b-replay-v12-hardening-plan.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/codex/v12-phase-docs/P49-extraction-audit-pilot-plan.md`
- `docs/experiments/extraction-audit-pilot-v12.md`
- `docs/codex/v12-phase-docs/P50-optional-reprojection-witness-plan.md`
- `docs/experiments/reprojection-witness-pilot-v12.md`

P45 is closed for the current `bio_attribute` stratum as implemented but
non-calibrated. P46 has refreshed the deterministic synthetic v12 artifacts.
P47 has added an offline fixture realistic-task benchmark. P48 has hardened
Phase B replay. P49 has added a deterministic fixture extraction audit pilot.
P50 has added the optional fixture ReprojectionWitness scaffold. The
phase-doc package supplies plans and reviews only; it does not claim
`measurement_validated` evidence and does not provide bridge calibration
results by itself.

The active follow-up roadmap is:

- `docs/roadmaps/mingx-followup-dev-experiment-plan-v0-2.md`

That roadmap supersedes v10-era roadmap references for the next development
cycle. It does not authorize live APIs, fabricate bridge values, fabricate
human labels, fabricate kappa, or claim `measurement_validated`.

## Practical Reading Rule

For new work, read this file with `docs/archive/context_projection_fixed_v12.md`
before using older v10 planning documents. If an older file uses
`Vinfo_proxy_certified`, `greedy_valid`, or bare `escalate`, treat that wording
as legacy unless the file explicitly marks it as a denied claim or compatibility
field.
