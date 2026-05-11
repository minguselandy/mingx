# Synthetic Regime v12 Report

## Scope
Deterministic synthetic structural diagnostics only.
metric_claim_level: ambiguous_metric
diagnostic_scope: synthetic_structural_only
evidence_scope: synthetic_structural_only
paper_evidence_eligible: false

## Cost-Aware Baseline Summary
- n: 40
- false_greedy_supported_rate: 0.0
- higher_order_false_greedy_supported_rate: 0.0
- pairwise_escalate_recall: 1.0
- avg_greedy_over_opt: 0.877288
- avg_sag_over_opt: 1.0
- avg_local_search_over_opt: 1.0
- avg_sag_residual_gap_over_opt: 0.0
- avg_sag_improvement_over_greedy_over_opt: 0.122712
- avg_diagnostic_call_count: 344.0
- avg_pair_sample_count: 28.0
- sag_trigger_rate: 0.25
- ambiguity_rate: 0.375
- avg_selected_token_cost: 18.0

## Family Summary
- adversarial-redundancy: n=10, ambiguity_rate=1.0, pairwise_recall=None, avg_sag_over_opt=1.0
- higher-order-prerequisite: n=10, ambiguity_rate=0.5, pairwise_recall=None, avg_sag_over_opt=1.0
- pairwise-synergy: n=10, ambiguity_rate=0.0, pairwise_recall=1.0, avg_sag_over_opt=1.0
- redundancy-dominated: n=10, ambiguity_rate=0.0, pairwise_recall=None, avg_sag_over_opt=1.0

## Interpretation
Redundancy-dominated cases should mostly certify monitored greedy. Pairwise-synergy cases should trigger pairwise escalation. Higher-order prerequisite cases are guarded against false greedy support. Adversarial redundancy is reported conservatively as ambiguous.
