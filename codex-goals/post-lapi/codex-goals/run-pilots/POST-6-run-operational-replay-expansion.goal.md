# Goal ID: POST-6-RUN / Matched-budget operational replay expansion

## Objective

Expand matched-budget operational replay under existing claim boundaries. This result may support scoped operational improvement only.

## Required owner approval gate

Before starting any new live API or dataset-scale experiment, verify that the user has explicitly written:

`APPROVE_POST_6_OPERATIONAL_REPLAY_EXPANSION=true`

If absent, stop and report blocked.

## Preferred datasets

1. HotpotQA continuation / additional slices
2. FEVER-style closed-label support / contradict / insufficient if configured
3. Do not start MuSiQue / 2Wiki until this goal passes and owner approves.

## Hard constraints

- No teacher-forced NLL.
- No metric bridge claim.
- No calibrated_proxy_supported.
- No vinfo_proxy_supported.
- No selector superiority or global superiority.
- No Route 5 or Route 8 unlock.
- Store no raw API responses.
- Maintain matched budgets and fixed downstream conditions.

## Baselines

Deployable:
- random_budget
- topk_relevance_or_token_budget
- mmr_density_greedy
- v12_cost_aware_diagnostic_policy_operational_only

Optional if already implemented safely:
- dashscope_llm_prune_extract_operational_only
- adaptive_budget_router_operational_only

Oracle:
- gold_support_oracle_upper_bound
- must be marked non_deployable_upper_bound

## Outputs

- `artifacts/experiments/post_lapi_operational_replay/`
- `docs/experiments/POST-LAPI-operational-replay-expansion.md`
- `docs/paper/post-lapi-operational-replay-table.md`

## Claim rules

Allowed:
- scoped operational improvement under matched budgets
- operational_utility_only

Denied:
- selector superiority
- global selector superiority
- metric bridge support
- measurement validation
- V-information verification

## Done condition

- Replay artifacts and paper table are produced.
- Matched budget conditions are documented.
- Non-deployable oracle is clearly marked.
- No claim upgrade is introduced.


Report format:
- Goal ID:
- Branch:
- HEAD:
- Changed files:
- Staged files:
- Checks run:
- Check results:
- Live API calls run: yes/no
- Raw API responses stored: yes/no
- Claim level:
- Claim upgrade introduced: yes/no
- Route 5 locked: yes/no
- Route 8 locked: yes/no
- Unrelated leftovers staged: yes/no
- Next recommended goal:
