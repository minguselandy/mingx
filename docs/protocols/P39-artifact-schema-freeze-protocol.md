# P39 Artifact Schema Freeze Protocol

**Milestone:** P39  
**Status:** protocol specification  
**Live API:** prohibited  
**Primary goal:** freeze replay-critical runtime artifact schema


## Source Basis

This document is aligned to:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`
- `docs/experiment-design-overview.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/phase-tree-crosswalk.md`
- `docs/current-work-summary.md`
- `configs/runs/README.md`

Local execution status must always be verified from `git status`, run plans, `run_summary.json`, `events.jsonl`, and concrete artifacts. Paper text and roadmap documents are not run-completion evidence.


## 1. Purpose

P39 freezes the artifact schema needed for Phase B replay and manuscript-facing evidence. The schema must support deterministic grouping, stable hashing, replay diagnostics, missing-field downgrade, and claim-level reporting.

The four paper-facing runtime artifacts are:

1. `ProjectionPlan`
2. `BudgetWitness`
3. `MaterializedContext`
4. `MetricBridgeWitness`

`CandidatePool` is required replay substrate but is not one of the four core paper runtime artifacts.


## Claim Boundary Lock

This milestone is part of the Context Projection Selection measurement and runtime-audit scaffold. It must not be reported as deployed V-information certification, theorem inheritance for a heuristic pipeline, scheduler correctness, full system validation, or `measurement_validated` evidence.

Conservative claim rules:

- contamination failure => `pilot_only` and scientific-stop for measurement interpretation
- missing human labels => not `measurement_validated`
- missing human-human kappa => not `measurement_validated`
- stale or missing metric bridge => `operational_utility_only` or `ambiguous`
- synthetic-only evidence => `vinfo_proxy_supported`, not deployed V-information certification
- replay package completeness => replay/observability evidence only, not scientific validation
- model-adjudicated labels => not human labels
- Codex/model audit => not human review
- live API success alone => operational evidence only, not measurement validation


## 2. Artifact Binding Keys

Every artifact must bind to dispatch identity using:

```text
run_id
dispatch_id
agent_id
round_id
artifact_schema_version
created_at or ordering key
```

The schema must avoid relying on incidental file ordering.

## 3. Required Artifact Fields

### 3.1 CandidatePool

Required fields:

```text
run_id
dispatch_id
agent_id
round_id
candidate_pool_id
candidate_pool_hash
candidate_ids
content_hashes or content
candidate_token_costs
provenance metadata
pool_ordering, if applicable
admission_policy
```

### 3.2 ProjectionPlan

Required fields:

```text
candidate_pool_hash
selected_ids
excluded_ids
algorithm
score_config
selection_trace
selected_total_estimated_tokens
exclusion_reasons
```

### 3.3 BudgetWitness

Required fields:

```text
token_budget
estimated_tokens_by_item
realized_tokens_by_section
realized_total_tokens
within_budget
trim_log
tolerance_violations
budget_policy
```

### 3.4 MaterializedContext

Required fields:

```text
materialized_context_hash
selected_ids
section_order
section_boundaries
content_inventory
truncation_or_clipping_record
realized_token_count
materialization_policy
```

### 3.5 MetricBridgeWitness

Required fields:

```text
metric_family
metric_class
metric_claim_level
bridge_status
bridge_epoch
active_stratum
model_tier
utility_metric
materialization_policy
decoding_policy
bridge_scale
bridge_residual
effective_sample_size
drift_status
ambiguity_reason
```

## 4. Stable Hash Rules

Stable hashes must be computed over canonical JSON:

- UTF-8 encoding;
- sorted keys;
- no runtime-only timestamps inside the hash payload unless intentionally part of identity;
- no local absolute paths;
- no secrets;
- explicit schema version.

Changing required fields requires a schema version bump.

## 5. Missing-Field Downgrade

Schema validation must classify missing fields as:

| Missing element | Required downgrade |
|---|---|
| candidate pool or selected ids | `replay_unusable` |
| excluded ids | `replay_partial` or worse; cannot check candidate-pool completeness |
| materialization order | replay defect; do not infer from selected ids |
| realized token counts | `pilot_degraded` or `replay_partial` depending on available diagnostics |
| metric bridge witness | `ambiguous` or observability-only |
| utility records needed for diagnostic recomputation | `replay_partial` |

## 6. Recommended Implementation Targets

```text
cps/experiments/artifact_schema.py
cps/experiments/artifact_hashes.py
cps/experiments/artifact_validation.py
tests/test_artifact_schema_stability.py
tests/test_projection_bundle_v1_hash_stability.py
tests/test_artifact_missing_field_downgrade.py
```

If analogous files already exist, update them conservatively rather than creating duplicate schema definitions.

## 7. Validation

```bash
uv run python -m compileall cps scripts
uv run pytest tests/test_artifact_schema_stability.py -q
uv run pytest tests/test_projection_bundle_v1_hash_stability.py -q
uv run pytest tests/test_artifact_missing_field_downgrade.py -q
```

Record actual commands if local test names differ.

## 8. Acceptance Criteria

P39 is accepted when:

- all replay-critical artifacts have explicit schema versions;
- stable hashes are deterministic;
- missing-field downgrades are tested;
- no artifact uses local absolute paths or secrets in stable identity;
- Phase A artifacts can be validated under the frozen schema;
- the review document records any backward-compatibility exceptions.
