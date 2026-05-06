# Phase B Replay Readiness Guidance

## Phase B purpose

Phase B tests whether recorded dispatch traces and cached utility/log-loss records are sufficient to reconstruct replay artifacts and classify conservative claim eligibility.

Phase B is offline replay readiness only.

## Phase B allowed work

Allowed:

- load recorded JSONL artifacts
- bind records into dispatch-level bundles
- classify missing fields
- produce `replay_manifest.jsonl`
- produce `missing_fields.json`
- produce `replay_summary.json`
- classify replay status
- classify conservative replay claim scope
- add deterministic schema and output tests

## Phase B forbidden work

Forbidden:

- live inference
- live utility computation
- diagnostic recomputation
- block-ratio recomputation
- Phase C realistic/live experiments
- theorem-level deployment claims
- inferring missing materialization order
- inferring excluded candidates without an explicit complete considered-candidate set
- emitting `Vinfo_proxy_certified` without a fresh matching `MetricBridgeWitness`

## Supported input files for B1/B2

The first replay implementation slice should support:

- `events.jsonl`
- `candidate_pools.jsonl`
- `projection_plans.jsonl`
- `budget_witnesses.jsonl`
- `materialized_contexts.jsonl`
- `metric_bridge_witnesses.jsonl`
- `diagnostics.jsonl`
- `utility_records.jsonl`

Equivalent cached utility/log-loss records may be supported only if an existing repo convention already exists. Do not invent a new live-evaluation path.

## Required outputs for B1/B2

- `replay_manifest.jsonl`
- `missing_fields.json`
- `replay_summary.json`

Do not write `replay_diagnostics.jsonl` during B1/B2 except as an explicitly empty placeholder marked not recomputed.

## Required data structures

### ReplayArtifactBundle

Required fields:

- `run_id`
- `dispatch_id`
- `agent_id`
- `round_id`
- `candidate_pool`
- `projection_plan`
- `budget_witness`
- `materialized_context`
- `metric_bridge_witness`
- `diagnostics`
- `utility_records`
- `source_files`
- `raw_event_records`

### ReplayManifestRow

Required fields:

- `run_id`
- `dispatch_id`
- `agent_id`
- `round_id`
- `replay_status`
- `replay_claim_scope`
- `candidate_pool_present`
- `projection_plan_present`
- `budget_witness_present`
- `materialized_context_present`
- `metric_bridge_witness_present`
- `cached_utility_records_present`
- `selected_ids_present`
- `excluded_ids_present`
- `materialization_order_present`
- `bridge_status`
- `metric_claim_level`
- `missing_required_fields`
- `missing_optional_fields`
- `replay_defects`
- `notes`

### MissingFieldRecord

Required fields:

- `run_id`
- `dispatch_id`
- `agent_id`
- `round_id`
- `field`
- `artifact`
- `severity`
- `required_for`
- `reason`

### ReplaySummary

Required fields:

- `total_dispatches`
- `replay_status_counts`
- `artifact_presence_counts`
- `metric_claim_level_counts`
- `missing_field_counts`
- `replay_usable_dispatches`
- `replay_nonusable_dispatches`

## Dispatch binding rule

Bind records conservatively using dispatch identity.

Preferred key fields:

- `run_id`
- `dispatch_id`
- `agent_id`
- `round_id`

Minimal aliases may be supported only when already used consistently in the repository. Do not create synthetic dispatch identities that hide missing binding evidence.

If there is no usable dispatch key or binding field, classify as `replay_unusable`.

## Replay status precedence

Apply these rules in this exact order. First matching status wins.

### 1. `replay_unusable`

Use when dispatch identity, candidate pool, or selected set cannot be reconstructed.

Examples:

- missing `CandidatePool` or complete candidate-pool equivalent
- missing `ProjectionPlan` and no selected-candidate equivalent
- missing usable dispatch key
- selected ids absent
- selected ids cannot be tied to candidate pool
- candidate pool does not contain the complete considered candidate set
- excluded candidates are absent and no explicit complete considered-candidate set exists

This is a replay substrate failure, not a diagnostic gap.

### 2. `pilot_degraded`

Use when the core dispatch can be reconstructed but realized budget or materialization evidence is incomplete.

Examples:

- missing `BudgetWitness`
- missing `MaterializedContext`
- missing materialization order / section manifest
- missing task metadata needed to reproduce context realization

This is a structural/materialization replay defect. It must not enter headline diagnostic aggregation.

### 3. `replay_partial`

Use when structural dispatch replay is possible but diagnostic or claim-level prerequisites are missing.

Examples:

- missing `MetricBridgeWitness`
- stale `MetricBridgeWitness`
- missing cached utility/log-loss records
- incomplete block/pair/triple utility records
- bridge witness exists but is insufficient for bridge-qualified V-information proxy claims

This may support observability-gap reporting only.

### 4. `replay_usable`

Use only when all required artifacts and cached diagnostic prerequisites are present:

- usable dispatch identity
- `CandidatePool` or complete candidate-pool equivalent
- `ProjectionPlan` or explicit selected-candidate equivalent
- selected ids tied to candidate pool
- excluded ids or explicit complete considered set
- `BudgetWitness`
- `MaterializedContext`
- explicit materialization order / section manifest
- fresh matching `MetricBridgeWitness`
- cached utility/log-loss records sufficient for intended replay claim scope

## Metric bridge rules

A missing or stale `MetricBridgeWitness` should usually produce `replay_partial`, not `pilot_degraded`, unless materialization or budget evidence is also incomplete.

`pilot_degraded` means structural/materialization replay defect.

`replay_partial` means diagnostic/claim-level replay gap.

For a synthetic bridge, preserve:

- `metric_class = synthetic_oracle`
- `utility_metric = synthetic_oracle_value`
- `drift_status = fresh`
- `diagnostic_claim_level = structural_synthetic_only`

For an operational-only bridge:

- `metric_claim_level` must remain `operational_utility_only`

For a stale bridge:

- `replay_status` should usually be `replay_partial`
- `replay_claim_scope` should be `recalibration_required`, `ambiguous`, or `no_bridge_qualified_claim`
- do not bridge-qualify the replay

Do not emit `Vinfo_proxy_certified` unless there is a fresh matching `MetricBridgeWitness`.

## CandidatePool rule

`CandidatePool` is replay substrate.

It must not be counted as one of the four core paper artifacts.

The four core artifacts are:

- `ProjectionPlan`
- `BudgetWitness`
- `MaterializedContext`
- `MetricBridgeWitness`

## Missing-field severity labels

Use conservative severity labels:

- `replay_unusable` — prevents reconstructing dispatch identity, candidate pool, or selected set
- `replay_defect` — structural/materialization replay evidence is incomplete
- `claim_gap` — diagnostic or claim-level prerequisite is missing
- `optional_gap` — useful but not required for current replay classification

## Output determinism

Outputs must be deterministic.

Required:

- stable ordering by `run_id`, `dispatch_id`, `agent_id`, `round_id`
- stable JSON key ordering where practical
- no timestamps
- no random UUIDs
- no absolute local paths
- no environment-specific paths

## Required B1/B2 tests

Add or preserve tests for:

1. complete dispatch bundle -> `replay_usable`
2. missing `MetricBridgeWitness` -> `replay_partial` or equivalent non-usable downgrade; no bridge-qualified claim
3. missing materialization order -> not `replay_usable`; replay defect recorded; normally `pilot_degraded` if no earlier unusable condition applies
4. missing excluded candidates -> not `replay_usable`; replay defect recorded; normally `replay_unusable` unless explicit complete considered-candidate set is available
5. missing candidate pool -> `replay_unusable`
6. operational-only `MetricBridgeWitness` -> `metric_claim_level` remains `operational_utility_only`
7. structural synthetic `MetricBridgeWitness` -> `metric_claim_level` remains `structural_synthetic_only`
8. stale `MetricBridgeWitness` -> conservative/recalibration-required `replay_claim_scope`; no `Vinfo_proxy_certified`
9. CLI writes `replay_manifest.jsonl`, `missing_fields.json`, and `replay_summary.json`
10. `CandidatePool` is recorded as replay substrate, not as a core paper artifact

## Required validation

Run:

```bash
uv run pytest tests/test_phase_b_replay.py
```

Then:

```bash
uv run pytest tests/test_projection_artifacts.py tests/test_synthetic_regime_benchmark.py tests/test_revised_framing_guardrails.py
```

Then, when feasible:

```bash
uv run pytest
```
