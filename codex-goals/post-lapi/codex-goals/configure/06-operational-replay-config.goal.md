# Goal ID: POST-6-CONFIG / Matched-budget operational replay expansion configuration

## Objective

Configure matched-budget operational replay expansion without running new live API calls. Prepare datasets, baseline registry, metrics, manifests, and table templates.

## Hard constraints

- Configuration only.
- No live API calls.
- No new dataset-scale experiment execution.
- No teacher-forced NLL.
- No metric bridge claim.
- No calibrated_proxy_supported.
- No vinfo_proxy_supported.
- No selector superiority or global superiority.
- No Route 5 or Route 8 unlock.
- No raw API responses.
- Maintain matched budget and fixed downstream condition requirements.

## Read first

- `configs/post-lapi/operational_replay_expansion_config.yaml` if installed
- Route 2 HotpotQA operational replay docs and artifacts
- LAPI-6 matched-budget operational replay config
- `docs/paper/v12-evidence-ledger.md`

## Create or update

- `configs/post_lapi/operational_replay_expansion_config.yaml`
- `docs/experiments/POST-LAPI-operational-replay-config.md`
- `docs/paper/post-lapi-operational-replay-table-template.md`
- `tests/test_post_lapi_operational_replay_config.py`

## Preferred datasets

1. HotpotQA continuation / additional slices
2. FEVER-style support / contradict / insufficient if configured
3. Do not start MuSiQue / 2Wiki until this config passes and owner approves.

## Baselines

Deployable:
- random_budget
- topk_relevance_or_token_budget
- mmr_density_greedy
- v12_cost_aware_diagnostic_policy_operational_only

Optional only if already implemented safely:
- dashscope_llm_prune_extract_operational_only
- adaptive_budget_router_operational_only

Oracle:
- gold_support_oracle_upper_bound
- must be marked non_deployable_upper_bound

## Metrics

- supporting_fact_recall
- evidence_recall
- selected_tokens
- quality_per_1k_tokens
- latency
- cost
- parse_success_rate
- claim_gate_distribution
- abstain_rate if applicable

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

## Checks

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py tests/test_post_lapi_operational_replay_config.py -q
python -m compileall cps tests scripts
```

## Done condition

- Replay config and registry are present.
- Table template is written.
- Tests pass without API calls.
- No claim upgrade is introduced.
- Do not commit automatically unless explicitly instructed after review.


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
