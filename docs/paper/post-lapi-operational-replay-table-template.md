# POST-LAPI Operational Replay Table Template

Status: template only; no POST-6 replay results are reported here.
Claim level: `operational_utility_only/no_claim_upgrade`.

Use this table only after an owner-approved matched-budget replay run. Oracle
rows must be marked `non_deployable_upper_bound`. Do not use this template to
claim selector superiority, global selector superiority, metric bridge support,
measurement validation, V-information verification, Route 5 unlock, or Route 8
unlock.

| dataset | slice | budget | baseline | deployable status | supporting fact recall | evidence recall | selected tokens | quality per 1k tokens | latency | cost | parse success rate | claim gate distribution | abstain rate | claim boundary |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| HotpotQA continuation | additional slice | 512 | random_budget | deployable | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| HotpotQA continuation | additional slice | 512 | topk_relevance_or_token_budget | deployable | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| HotpotQA continuation | additional slice | 512 | mmr_density_greedy | deployable | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| HotpotQA continuation | additional slice | 512 | v12_cost_aware_diagnostic_policy_operational_only | deployable | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| HotpotQA continuation | additional slice | 512 | gold_support_oracle_upper_bound | non_deployable_upper_bound | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `non_deployable_upper_bound` |

Required run manifest fields before filling results:

- candidate pool hash
- budget
- downstream prompt hash
- model snapshot
- endpoint
- thinking mode
- decoding policy
- token budget accounting
- deployable baseline list
- oracle upper-bound label
- claim ledger path
- cost and latency ledger path
