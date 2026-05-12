# P56 Realistic Dispatch Replay Protocol v12

## Status and Scope

P56 defines a realistic dispatch replay import and classification scaffold for v12 Proxy-Regime Diagnosis. It is a replay/audit scaffold only. It is not bridge evidence, not measurement validation, and not a continuation from successful P55 bridge calibration.

P55 remains blocked as `failed_closed_no_rows` / `blocked_operator_required`. P56 must not inherit metric support, paper evidence, or phase progression from P55.

## Purpose

The protocol moves replay checking from fixture-only engineering checks toward importable realistic dispatch traces with deterministic identity, candidate-pool, materialization, and MetricBridgeWitness binding. Its output is a conservative replay classification and claim-gate report.

Replay usability is not metric support. Replay completeness is not bridge evidence. Fresh matching MetricBridgeWitness status is required before any metric claim inheritance, and this P56 scaffold does not itself emit `vinfo_proxy_supported` or `calibrated_proxy_supported`.

## Input Trace Path

The configured operator/import path is:

```text
artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl
```

If this file is absent, empty, blank-only, malformed, or contains invalid traces, P56 fails closed. It must not fabricate traces and must not use unit-test fixtures as paper evidence.

## Required Trace Fields

Each replayable realistic dispatch trace must include:

```text
run_id
dispatch_id
agent_id
round_id
candidate_pool_hash
considered_candidate_ids
selected_candidate_ids
excluded_candidate_ids
projection_plan_hash
budget_witness_hash
materialized_context_hash
materialization_policy
metric_bridge_witness_status
metric_bridge_contract_id
metric_bridge_active_stratum
metric_bridge_freshness
replay_intervention_id
evaluator_policy
metric_policy
replicate_count
effective_sample_size
data_source_kind
trace_schema_version
```

Optional fields may record `candidate_pool_items_hash`, `candidate_pool_count`, token estimates, budget limit, projection bundle hash, source trace identity, operator approval reference, and contamination status.

## Binding Rules

The trace must preserve complete dispatch identity: `run_id`, `dispatch_id`, `agent_id`, and `round_id`.

The candidate-pool hash must bind to the complete declared considered candidate set. The P56 config uses `sha256_json_sorted_considered_candidate_ids_v1`. A selected-only trace is not selector-comparable.

The trace must bind to a `ProjectionPlan`, `BudgetWitness`, and `MaterializedContext` through their hashes. Missing hashes are recorded as defects and prevent replay-comparable claim inheritance.

`MetricBridgeWitness` records bridge status and provenance. Presence alone is not support. Missing, stale, mismatched, underpowered, failed, or ambiguous witness status downgrades the metric claim surface.

## Classification Labels

P56 uses these conservative replay labels:

```text
replay_comparable
replay_usable_metric_downgraded
not_replay_comparable
not_selector_comparable
fail_closed_candidate_pool_mismatch
fixture_only_engineering_evidence
no_imported_traces
```

## Classification Rules

If complete identity, complete considered candidate set, stable candidate-pool hash, `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, and fresh active-stratum-matched MetricBridgeWitness are present, classify as `replay_comparable`.

`replay_comparable` does not automatically mean metric support. Metric support depends on a fresh valid bridge and a phase-specific claim gate outside this replay scaffold.

If the trace is otherwise replay-usable but has missing, stale, mismatched, underpowered, failed, or ambiguous MetricBridgeWitness status, classify as `replay_usable_metric_downgraded`.

If any dispatch identity field is missing, classify as `not_replay_comparable`.

If selected candidates are present but the complete considered candidate set is missing, classify as `not_selector_comparable`.

If the candidate-pool hash does not match the declared considered candidate set, classify as `fail_closed_candidate_pool_mismatch`.

If the data source is fixture/test-only, classify as `fixture_only_engineering_evidence`. Fixture-only traces are paper-ineligible and cannot emit `vinfo_proxy_supported` or `calibrated_proxy_supported`.

If no imported traces are present, classify the run as `no_imported_traces` and produce a blocked/no-trace report.

## Claim Gate

The P56 claim gate reports:

```text
phase
data_source_kind
trace_file_status
traces_imported
traces_validated
trace_validation_failures
replay_classification_counts
metric_bridge_status_counts
candidate_pool_mismatch_count
selected_only_count
paper_evidence_eligible
metric_claim_level
selector_regime_label
measurement_validation_claim
vinfo_proxy_supported_allowed
calibrated_proxy_supported_allowed
denied_claims
next_phase_allowed
```

Default behavior with no valid imported traces:

```text
metric_claim_level: ambiguous_metric
review_ceiling: none
selector_regime_label: none
paper_evidence_eligible: false
measurement_validation_claim: false
vinfo_proxy_supported_allowed: false
calibrated_proxy_supported_allowed: false
next_phase_allowed: false
```

The artifact may record `ambiguous_metric` as a blocked artifact status, but the phase review ceiling remains `none`.

## Claim Boundaries

P56 does not claim measurement validation, human-label validation, human-human kappa, deployed V-information verification, theorem-level deployed submodularity verification, synthetic evidence as bridge evidence, fixture evidence as paper-grade evidence, replay usability as metric support, extraction audit as selector validity, or ReprojectionWitness as deployed runtime improvement.

P56 does not claim `calibrated_proxy_supported` or `vinfo_proxy_supported`.

Deprecated labels such as `Vinfo_proxy_certified`, `greedy_valid`, and `measurement_validated` are not active P56 labels.

## Deterministic Outputs

If no imported traces are present, P56 emits:

```text
artifacts/experiments/p56_realistic_dispatch_replay/manifest.json
artifacts/experiments/p56_realistic_dispatch_replay/claim_gate_report.json
artifacts/experiments/p56_realistic_dispatch_replay/report.md
```

If valid traces are present, P56 may also emit:

```text
artifacts/experiments/p56_realistic_dispatch_replay/realistic_dispatch_replay_records.jsonl
artifacts/experiments/p56_realistic_dispatch_replay/realistic_dispatch_replay_summary.csv
```

Canonical outputs must avoid timestamps, UUIDs, absolute paths, machine-specific paths, secrets, API keys, and nondeterministic ordering.
