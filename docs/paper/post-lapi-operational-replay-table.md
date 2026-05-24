# POST-LAPI Operational Replay Table

Status: POST-6-RUN result under `operational_utility_only/no_claim_upgrade`

These rows are scoped operational comparison evidence only. They do not claim selector superiority, global selector superiority, metric bridge support, measurement validation, V-information verification, paper evidence, Route 5 unlock, or Route 8 unlock.

| dataset | slice | budget | baseline | deployable status | supporting fact recall | evidence recall | selected tokens | quality per 1k tokens | latency | cost | parse success rate | claim gate distribution | abstain rate | claim boundary |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 512 | gold_support_oracle_upper_bound | non_deployable_upper_bound | 1.0 | 1.0 | 505.075 | 1.979904 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `non_deployable_upper_bound` |
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 512 | mmr_density_greedy | deployable_operational_baseline | 0.860167 | 0.860167 | 505.425 | 1.701869 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `operational_utility_only/no_claim_upgrade` |
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 512 | random_budget | deployable_operational_baseline | 0.572917 | 0.572917 | 505.085 | 1.134298 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `operational_utility_only/no_claim_upgrade` |
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 512 | topk_relevance_or_token_budget | deployable_operational_baseline | 0.866167 | 0.866167 | 505.16 | 1.714639 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `operational_utility_only/no_claim_upgrade` |
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 512 | v12_cost_aware_diagnostic_policy_operational_only | deployable_operational_baseline | 0.907833 | 0.907833 | 505.465 | 1.796035 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `operational_utility_only/no_claim_upgrade` |
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 1024 | gold_support_oracle_upper_bound | non_deployable_upper_bound | 1.0 | 1.0 | 845.77 | 1.182355 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `non_deployable_upper_bound` |
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 1024 | mmr_density_greedy | deployable_operational_baseline | 0.980417 | 0.980417 | 845.61 | 1.15942 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `operational_utility_only/no_claim_upgrade` |
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 1024 | random_budget | deployable_operational_baseline | 0.95 | 0.95 | 845.805 | 1.12319 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `operational_utility_only/no_claim_upgrade` |
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 1024 | topk_relevance_or_token_budget | deployable_operational_baseline | 0.980833 | 0.980833 | 845.82 | 1.159624 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `operational_utility_only/no_claim_upgrade` |
| HotpotQA_continuation | existing_p56_hotpotqa_operational_traces | 1024 | v12_cost_aware_diagnostic_policy_operational_only | deployable_operational_baseline | 0.995833 | 0.995833 | 846.085 | 1.176989 | 0.0 | 0.0 | 1.0 | operational_utility_only/no_claim_upgrade | 0.0 | `operational_utility_only/no_claim_upgrade` |

## Boundary Fields

| Field | Value |
| --- | --- |
| live API calls run | `0` |
| raw API responses stored | `false` |
| claim level | `operational_utility_only/no_claim_upgrade` |
| diagnostic claim level | `scoped_operational_improvement_under_matched_budgets_only` |
| oracle treatment | `non_deployable_upper_bound` |
| Route 5 locked | `true` |
| Route 8 locked | `true` |
| claim upgrade introduced | `false` |
