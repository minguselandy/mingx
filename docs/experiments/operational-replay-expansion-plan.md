# Operational Replay Expansion Plan

Status: LAPI-6 config-only plan
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This plan prepares matched-budget operational evidence configs for later controlled runs. No replay run has been executed, and no live API call has been made by this goal.

## Scope

The first config targets HotpotQA operational replay. The second config prepares a FEVER-style closed-label sufficiency task after HotpotQA acceptance. 2WikiMultihopQA and MuSiQue remain deferred.

The only allowed claim level is `scoped_operational_improvement_under_matched_budgets_only`. This means matched-budget operational evidence for named datasets, budgets, candidate pools, prompts, and model snapshots. It is not selector superiority, not metric bridge support, not measurement validation, not calibrated proxy support, not V-information proxy support, not paper evidence, not Route 5 unlock, and not Route 8 unlock.

## Configs

- `configs/experiments/hotpotqa_operational_replay_v1.yaml`
- `configs/experiments/fever_style_sufficiency_v1.yaml`

Both files are JSON-compatible YAML so they can be parsed without adding a YAML dependency.

## Initial Budgets

- 512 tokens
- 1024 tokens

An optional 2048-token budget is recorded for a later pilot only.

## Baselines

Deployable baselines:

- `random_budget`
- `topk_relevance_or_token_budget`
- `mmr_density_greedy`
- `v12_cost_aware_diagnostic_policy_operational_only`

Optional later baselines:

- `seeded_augmented_greedy_operational_only`
- `pair_aware_local_search_operational_only`
- `adaptive_budget_router_operational_only`

Non-deployable upper bound:

- `gold_support_oracle_upper_bound`

The oracle is reported only as a non-deployable upper bound.

## Metrics

Hard operational metrics:

- `supporting_fact_recall`
- `evidence_recall`
- `selected_gold_support_packets`
- `selected_tokens`
- `quality_per_1k_tokens`
- `latency`
- `estimated_cost`

Weak diagnostic metrics:

- `judge_support_rate`
- `judge_insufficient_rate`
- `abstain_rate`
- `order_swap_agreement`
- `parse_failure_rate`

## Controls

The configs require matched candidate pools, budgets, prompt hashes, model snapshots, endpoints, thinking modes, and decoding policies. Budget mismatch, prompt-hash drift, missing claim ledgers, raw-response storage, or unauthorized live API calls stop fail closed.

Route 5 locked: true. Route 8 locked: true. Raw provider bodies stored: false. Replay run performed: false.
