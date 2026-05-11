# Synthetic Regime Benchmark Report

## Summary

- Run id: `synthetic-regime-v12`
- Status: `green`
- Dispatches: `40`
- Pre-registered gate passed: `True`
- Ambiguity count: `15`
- Metric claim levels: `ambiguous_metric: 40`
- Diagnostic scopes: `synthetic_structural_only: 40`
- Selector regime labels: `ambiguous: 15, greedy_supported: 10, higher_order_risk: 5, pairwise_escalate: 10`
- Selector actions: `interaction_aware_local_search: 5, monitored_greedy: 10, no_certified_switch: 15, seeded_augmented_greedy: 10`
- Expected policy matches (legacy compatibility detail): `35/40`

## Artifact completeness

- Complete artifact sets: `True`
- Required artifacts include `CandidatePool`, `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and diagnostics.

| Artifact | Count |
|---|---:|
| candidate_pools | 40 |
| projection_plans | 40 |
| budget_witnesses | 40 |
| materialized_contexts | 40 |
| MetricBridgeWitness | 40 |
| diagnostics | 40 |
| ProjectionBundleV1 | 40 |

## Pre-registered validity gate

- Gate passed: `True`
- Failure count: `0`
- Block-ratio LCB diagnostics are reported through the `block_ratio_lcb_b2`, `block_ratio_lcb_star`, and `block_ratio_lcb_b3` fields.
- `block_ratio_lcb_star` is currently `placeholder_conservative_min_b2_b3_not_degree_adaptive_star`, not a paper-grade degree-adaptive star-block estimator.

| Gate | Passed |
|---|---|
| adversarial_redundancy_conservative | True |
| ambiguity_accounting | True |
| artifact_completeness | True |
| higher_order_safety | True |
| pairwise_synergy_signature | True |
| redundancy_signature | True |
| triple_excess_detection | True |

## Regime diagnostics table

| Dispatch | Regime | block_ratio_lcb_b2 | block_ratio_lcb_star | block_ratio_lcb_star_semantics | block_ratio_lcb_b3 | trace_decay_proxy | synergy_fraction | positive_interaction_mass_ucb | triple_excess_flag | higher_order_ambiguity_flag | greedy_augmented_gap | oracle_status | oracle_gap | metric_claim_level | diagnostic_scope | selector_regime_label | selector_action |
|---|---|---:|---:|---|---:|---:|---:|---:|---|---|---:|---|---:|---|---|---|---|
| adversarial_0 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| adversarial_1 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| adversarial_2 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| adversarial_3 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| adversarial_4 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| adversarial_5 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| adversarial_6 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| adversarial_7 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| adversarial_8 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| adversarial_9 | adversarial_redundancy | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | ambiguous | True | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| higher_order_0 | higher_order_synergy | 0.678531 | 0.678531 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.760371 | 1.000000 | 0.107143 | 0.214802 | positive | True | 0.485244 | available | 0.485244 | ambiguous_metric | synthetic_structural_only | higher_order_risk | interaction_aware_local_search |
| higher_order_1 | higher_order_synergy | 0.678883 | 0.678883 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.761134 | 1.000000 | 0.107143 | 0.216029 | positive | True | 0.500135 | available | 0.500135 | ambiguous_metric | synthetic_structural_only | higher_order_risk | interaction_aware_local_search |
| higher_order_2 | higher_order_synergy | 0.804461 | 0.798544 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.798544 | 1.000000 | 0.071429 | 0.132846 | ambiguous | True | 0.497432 | available | 0.497432 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| higher_order_3 | higher_order_synergy | 0.807246 | 0.800697 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.800697 | 1.000000 | 0.071429 | 0.132040 | ambiguous | True | 0.490065 | available | 0.490065 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| higher_order_4 | higher_order_synergy | 0.679989 | 0.679989 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.762303 | 1.000000 | 0.107143 | 0.226919 | positive | True | 0.492022 | available | 0.492022 | ambiguous_metric | synthetic_structural_only | higher_order_risk | interaction_aware_local_search |
| higher_order_5 | higher_order_synergy | 0.804410 | 0.798951 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.798951 | 1.000000 | 0.071429 | 0.136997 | ambiguous | True | 0.488998 | available | 0.488998 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| higher_order_6 | higher_order_synergy | 0.801914 | 0.796588 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.796588 | 1.000000 | 0.071429 | 0.140985 | ambiguous | True | 0.491075 | available | 0.491075 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| higher_order_7 | higher_order_synergy | 0.802635 | 0.796384 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.796384 | 1.000000 | 0.071429 | 0.143638 | ambiguous | True | 0.487347 | available | 0.487347 | ambiguous_metric | synthetic_structural_only | ambiguous | no_certified_switch |
| higher_order_8 | higher_order_synergy | 0.679224 | 0.679224 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.761639 | 1.000000 | 0.107143 | 0.241841 | positive | True | 0.490672 | available | 0.490672 | ambiguous_metric | synthetic_structural_only | higher_order_risk | interaction_aware_local_search |
| higher_order_9 | higher_order_synergy | 0.675956 | 0.675956 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.761966 | 1.000000 | 0.107143 | 0.243949 | positive | True | 0.485509 | available | 0.485509 | ambiguous_metric | synthetic_structural_only | higher_order_risk | interaction_aware_local_search |
| pairwise_0 | sparse_pairwise_synergy | 0.801006 | 0.801006 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.818635 | 1.124300 | 0.142857 | 0.517622 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| pairwise_1 | sparse_pairwise_synergy | 0.798854 | 0.798854 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.819295 | 1.123668 | 0.142857 | 0.521893 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| pairwise_2 | sparse_pairwise_synergy | 0.801939 | 0.801939 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.814019 | 1.122282 | 0.142857 | 0.528149 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| pairwise_3 | sparse_pairwise_synergy | 0.802430 | 0.802430 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.817793 | 1.124794 | 0.142857 | 0.537866 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| pairwise_4 | sparse_pairwise_synergy | 0.803116 | 0.803116 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.819698 | 1.124476 | 0.142857 | 0.544069 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| pairwise_5 | sparse_pairwise_synergy | 0.803412 | 0.803412 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.819567 | 1.126347 | 0.142857 | 0.555617 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| pairwise_6 | sparse_pairwise_synergy | 0.803745 | 0.803745 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.817647 | 1.127262 | 0.142857 | 0.562626 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| pairwise_7 | sparse_pairwise_synergy | 0.803427 | 0.803427 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.819654 | 1.123908 | 0.142857 | 0.565917 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| pairwise_8 | sparse_pairwise_synergy | 0.804823 | 0.804823 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.818370 | 1.126541 | 0.142857 | 0.576978 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| pairwise_9 | sparse_pairwise_synergy | 0.801307 | 0.801307 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 0.815982 | 1.123095 | 0.142857 | 0.585818 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | pairwise_escalate | seeded_augmented_greedy |
| redundancy_0 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |
| redundancy_1 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |
| redundancy_2 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |
| redundancy_3 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |
| redundancy_4 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |
| redundancy_5 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |
| redundancy_6 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |
| redundancy_7 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |
| redundancy_8 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |
| redundancy_9 | redundancy_dominated | 1.000000 | 1.000000 | placeholder_conservative_min_b2_b3_not_degree_adaptive_star | 1.000000 | 1.000000 | 0.000000 | 0.000000 | none_detected | False | 0.000000 | available | 0.000000 | ambiguous_metric | synthetic_structural_only | greedy_supported | monitored_greedy |

## Ambiguity accounting

- Ambiguous labels: `15`
- Ambiguous labels are reported as safety outcomes and are not counted as benchmark success.
- Selector regime label counts: `ambiguous: 15, greedy_supported: 10, higher_order_risk: 5, pairwise_escalate: 10`

## Higher-order safety check

| Dispatch | Triple flag | Higher-order ambiguity | Regime label | Action |
|---|---|---|---|---|
| higher_order_0 | positive | True | higher_order_risk | interaction_aware_local_search |
| higher_order_1 | positive | True | higher_order_risk | interaction_aware_local_search |
| higher_order_2 | ambiguous | True | ambiguous | no_certified_switch |
| higher_order_3 | ambiguous | True | ambiguous | no_certified_switch |
| higher_order_4 | positive | True | higher_order_risk | interaction_aware_local_search |
| higher_order_5 | ambiguous | True | ambiguous | no_certified_switch |
| higher_order_6 | ambiguous | True | ambiguous | no_certified_switch |
| higher_order_7 | ambiguous | True | ambiguous | no_certified_switch |
| higher_order_8 | positive | True | higher_order_risk | interaction_aware_local_search |
| higher_order_9 | positive | True | higher_order_risk | interaction_aware_local_search |

## Interpretation limits

- Synthetic-only metric claims remain `ambiguous_metric`; diagnostic scope records `synthetic_structural_only`.
- The evidence remains a synthetic structural smoke check, not deployed V-information proxy support or bridge calibration.
- Thresholds are provisional calibration bins for synthetic regimes.
- The benchmark validates diagnostic plumbing and controlled regime discrimination only.
- It is not deployment certification and does not certify deployed V-information weak submodularity.
- It does not implement a scheduler, memory architecture, openWorker port, or live benchmark claim.
- It is not a theorem-inheritance claim and not a system-level performance claim.
- Runtime artifacts are sidecar audit records for replay and should not be read as production interfaces.
