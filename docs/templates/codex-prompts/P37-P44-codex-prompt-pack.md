# P37-P44 Codex Prompt Pack

These prompts are designed to be pasted into Codex or a coding agent. They preserve the project's conservative claim boundaries.

---

## P37 Repo-State and Claim-Boundary Lock

```text
You are preparing the next development milestone for the mingx project.

Goal:
Create a repo-state and claim-boundary lock report that reconciles the current repository state, local branch state, revised v10 paper framing, current Phase A/B/C experiment stack, and live-mini-batch evidence status.

Do not:
- run live APIs
- fabricate human labels
- fabricate kappa
- claim measurement_validated
- push main
- merge branches
- modify reference/
- stage unrelated untracked files

Required checks:
1. git status --short
2. git branch --show-current
3. git log --oneline -20
4. verify docs/archive/context_projection_revised_v10.md exists
5. verify cps/ is the canonical package for new code
6. verify docs/paper-alignment-v10.md exists
7. verify docs/experiment-design-overview.md exists
8. verify docs/protocols/phase-b-replay-protocol.md exists
9. verify docs/phase-tree-crosswalk.md exists
10. search for unsafe overclaims:
    - measurement_validated
    - scientific validation
    - deployed V-information certification
    - certified greedy-valid
    - human labels
    - human-human kappa
    - kappa

Produce:
docs/reviews/P37-repo-state-and-claim-boundary-lock-review.md

Validation:
uv run pytest -q

If uv is unavailable, report validation skipped and why.
```

---

## P38 Synthetic Structural Benchmark Hardening

```text
You are implementing P38 synthetic structural benchmark hardening.

Goal:
Strengthen Phase A synthetic benchmark outputs and report generation for redundancy-dominated, sparse pairwise-synergy, and higher-order/prerequisite regimes.

Boundary:
This is vinfo_proxy_supported evidence. It is not deployed V-information certification and not scientific validation.

Required outputs:
- events.jsonl
- candidate_pools.jsonl
- projection_plans.jsonl
- budget_witnesses.jsonl
- materialized_contexts.jsonl
- metric_bridge_witnesses.jsonl
- diagnostics.jsonl
- summary.json
- report.md

Diagnostics:
- block_ratio_lcb_b2
- block_ratio_lcb_star, or explicit placeholder limitation
- block_ratio_lcb_b3
- interaction mass
- triple-excess
- greedy-vs-augmented gap
- metric_claim_level
- selector_regime_label
- selector_action

Run:
uv run python -m cps.experiments.synthetic_benchmark --config configs/runs/synthetic-regime-smoke.json --output-dir artifacts/experiments/synthetic_regime_smoke
uv run pytest tests/test_synthetic_benchmark_pre_registered_gate.py -q
```

---

## P39 Artifact Schema Freeze

```text
You are implementing P39 artifact schema freeze.

Goal:
Freeze versioned, stable, replay-critical schemas for CandidatePool, ProjectionPlan, BudgetWitness, MaterializedContext, MetricBridgeWitness, and ProjectionBundleV1 if used.

Do not change experiment semantics or run live APIs.

Required features:
- stable canonical JSON hashes
- schema versions
- dispatch binding keys: run_id, dispatch_id, agent_id, round_id
- missing-field downgrade logic
- tests for hash stability and missing-field downgrade

Validation:
uv run python -m compileall cps scripts
uv run pytest tests/test_artifact_schema_stability.py -q
uv run pytest tests/test_projection_bundle_v1_hash_stability.py -q
uv run pytest tests/test_artifact_missing_field_downgrade.py -q
```

---

## P40 Phase B Offline Replay

```text
You are implementing P40 Phase B offline replay.

Goal:
Implement a replay runner that consumes recorded artifacts and cached utility/log-loss records to recompute diagnostics without live inference.

Do not:
- run live inference
- change scheduler behavior
- redesign memory
- claim measurement_validated

Required replay statuses:
- replay_usable
- pilot_degraded
- replay_partial
- replay_unusable

Required outputs:
- replay_manifest.json
- replay_manifest.jsonl
- per_dispatch_diagnostics.jsonl
- missing_field_report.json
- pipeline_proxy_alignment.json
- metric_claim_level_summary.json
- selector_regime_summary.json
- replay_status_counts.json
- report.md

Validation:
uv run python -m compileall cps scripts
uv run pytest tests/test_phase_b_replay_status.py -q
uv run pytest tests/test_phase_b_recompute_diagnostics.py -q
uv run pytest tests/test_phase_b_missing_field_downgrade.py -q
uv run pytest tests/test_phase_b_pipeline_proxy_alignment.py -q
```

---

## P41 Route B Model-Adjudicated Evaluation

```text
You are implementing P41 Route B model-adjudicated evaluation.

Goal:
Create a fully automated model-adjudicated evaluation route with prelabels, model/Codex audit, adjudication, and evidence packaging.

Boundary:
Route B cannot claim measurement_validated. Model-adjudicated labels are not human labels. Model agreement is not human-human kappa.

Required manifest fields:
- human_labels_present = false
- kappa_present = false
- human_human_kappa_established = false
- measurement_validated_allowed = false
- label_source = model_adjudicated
- max_claim = model_adjudicated_pilot_only or operational_utility_only

Validation:
uv run python -m compileall cps scripts
uv run pytest tests/test_route_b_claim_gate.py -q
uv run pytest tests/test_model_adjudicated_not_human_labels.py -q
uv run pytest tests/test_route_b_manifest_validation.py -q
uv run pytest tests/test_route_b_dry_run.py -q
```

---

## P42 Fresh Reduced-Scope Follow-Up Batch

```text
You are preparing P42 fresh reduced-scope follow-up batch.

This prompt does not authorize live API calls. First prepare dry-run and readiness artifacts only.

Replacement candidates:
- 2hop__132929_684936
- 3hop1__409517_547811_80702
- 4hop3__373866_5189_38229_86687

Boundary:
The previous contamination-failed live mini-batch remains pilot_only and must not be rerun or reinterpreted as measurement_validated.

Readiness validation:
uv run python -m api --show-profiles
uv run python -m api --export-phase1-env --profile dashscope-qwen-phase1
uv run pytest -q tests/test_phase1_request_builder.py tests/test_phase1_backend_runtime.py

Live tests only after explicit operator approval:
PHASE1_ENABLE_LIVE_TESTS=1 uv run pytest -q tests/test_phase1_live_api.py tests/test_phase1_live_run.py
```

---

## P43 Phase C Realistic-Task Benchmark

```text
You are designing P43 Phase C realistic-task context projection benchmark.

Goal:
Evaluate context projection behavior on realistic tasks under explicit metric-bridge qualification.

Prerequisites:
- P39 artifact schema freeze complete
- P40 Phase B replay working on at least synthetic artifacts

Conditions:
- no_cps_baseline
- heuristic_selector_baseline
- cps_runtime_audit_scaffold
- diagnostic_guided_escalation, optional

Do not claim scheduler correctness, multi-agent superiority, theorem inheritance, or measurement_validated.

Validation:
uv run pytest tests/test_phase_c_candidate_pool_builder.py -q
uv run pytest tests/test_phase_c_artifact_completeness.py -q
uv run pytest tests/test_phase_c_claim_level_assignment.py -q
```

---

## P44 Manuscript Evidence Integration

```text
You are integrating new evidence into docs/archive/context_projection_revised_v10.md.

Goal:
Add evidence summaries and tables from P38-P43 without claim inflation.

Do not:
- claim measurement_validated unless all gates are actually satisfied
- describe Route B labels as human labels
- describe replay package completeness as scientific validation
- describe synthetic structural evidence as deployed V-information certification

Required unsafe-claim search:
rg -n "measurement_validated|scientific validation|certified deployed|theorem inheritance|human-human kappa|human labels" docs/archive/context_projection_revised_v10.md docs/paper docs/reviews

Produce:
- manuscript patch or direct markdown changes
- docs/reviews/P44-manuscript-evidence-integration-review.md
```
