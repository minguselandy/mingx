# Synthetic Regime Benchmark Report

## Summary

- Run id: `synthetic-regime-smoke-20260418`
- Status: `green`
- Dispatches: `3`
- Pre-registered gate passed: `True`
- Ambiguity count: `0`
- Metric claim levels: `structural_synthetic_only: 3`
- Selector regime labels: `escalate: 2, greedy_valid: 1`
- Selector actions: `interaction_aware_local_search: 1, monitored_greedy: 1, seeded_augmented_greedy: 1`
- Expected policy matches (legacy compatibility detail): `3/3`

## Artifact completeness

- Complete artifact sets: `True`
- Required artifacts include `CandidatePool`, `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and diagnostics.

| Artifact | Count |
|---|---:|
| candidate_pools | 3 |
| projection_plans | 3 |
| budget_witnesses | 3 |
| materialized_contexts | 3 |
| MetricBridgeWitness | 3 |
| diagnostics | 3 |

## Pre-registered validity gate

- Gate passed: `True`
- Failure count: `0`
- Block-ratio LCB diagnostics are reported through the `block_ratio_lcb_b2`, `block_ratio_lcb_star`, and `block_ratio_lcb_b3` fields.
- `block_ratio_lcb_star` is currently `placeholder_conservative_min_b2_b3_not_degree_adaptive_star`, not a paper-grade degree-adaptive star-block estimator.

| Gate | Passed |
|---|---|
| ambiguity_accounting | True |
| artifact_completeness | True |
| higher_order_safety | True |
| pairwise_synergy_signature | True |
| redundancy_signature | True |
| triple_excess_detection | True |

## Regime diagnostics table

| Dispatch | Regime | block_ratio_lcb_b2 | block_ratio_lcb_star | block_ratio_lcb_star_semantics | block_ratio_lcb_b3 | trace_decay_proxy | synergy_fraction | positive_interaction_mass_ucb | triple_excess_flag | higher_order_ambiguity_flag | greedy_augmented_gap | metric_claim_level | selector_regime_label | selector_action |
|---|---|---:|---:|---|---:|---:|---:|---:|---|---|---:|---|---|---|
| redundancy_0 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | structural_synthetic_only | greedy_valid | monitored_greedy |
| pairwise_0 | sparse_pairwise_synergy | 0.802198 | 0.802198 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.817259 | 1.124138 | 0.142857 | 0.514286 | none_detected | False | 0.000000 | structural_synthetic_only | escalate | seeded_augmented_greedy |
| higher_order_0 | higher_order_synergy | 0.678955 | 0.678955 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.761905 | 1.000000 | 0.107143 | 0.214286 | positive | True | 0.492711 | structural_synthetic_only | escalate | interaction_aware_local_search |

## Ambiguity accounting

- Ambiguous labels: `0`
- Ambiguous labels are reported as safety outcomes and are not counted as benchmark success.
- Selector regime label counts: `escalate: 2, greedy_valid: 1`

## Higher-order safety check

| Dispatch | Triple flag | Higher-order ambiguity | Regime label | Action |
|---|---|---|---|---|
| higher_order_0 | positive | True | escalate | interaction_aware_local_search |

## Interpretation limits

- All synthetic diagnostic claims in this report are `structural_synthetic_only`.
- Thresholds are provisional calibration bins for synthetic regimes.
- The benchmark validates diagnostic plumbing and controlled regime discrimination only.
- It is not deployment certification and does not certify deployed V-information weak submodularity.
- It does not implement a scheduler, memory architecture, openWorker port, or live benchmark claim.
- It is not a theorem-inheritance claim and not a system-level performance claim.
- Runtime artifacts are sidecar audit records for replay and should not be read as production interfaces.
