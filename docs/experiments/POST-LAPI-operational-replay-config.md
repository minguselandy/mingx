# POST-LAPI Operational Replay Expansion Config

Status: configuration only
Goal ID: POST-6-CONFIG
Claim level: `operational_utility_only/no_claim_upgrade`

## Scope

This configuration prepares a matched-budget operational replay expansion
registry without running live API calls or an operational replay pilot. It
extends the LAPI-6 replay configuration surface into a POST-LAPI registry that
can be reviewed before any owner-approved run.

No dataset-scale experiment execution was performed for this goal. No raw API
responses are stored. Route 5 and Route 8 remain locked.

## Source References

- `docs/experiments/P67R-route2-operational-evidence-package.md`
- `docs/experiments/P66-hotpotqa-operational-comparison.md`
- `artifacts/experiments/route2_operational_evidence_package/claim_ledger.json`
- `configs/experiments/hotpotqa_operational_replay_v1.yaml`
- `configs/experiments/fever_style_sufficiency_v1.yaml`
- `docs/paper/v12-evidence-ledger.md`

## Dataset Registry

| priority | dataset | config | status | run now |
|---:|---|---|---|---|
| 1 | HotpotQA continuation / additional slices | `configs/experiments/hotpotqa_operational_replay_v1.yaml` | configured for later owner-approved run | no |
| 2 | FEVER-style support / contradict / insufficient | `configs/experiments/fever_style_sufficiency_v1.yaml` | configured but gated after HotpotQA acceptance | no |
| 3 | 2Wiki / MuSiQue | none | deferred until this config passes and owner approves | no |

## Baseline Registry

Deployable baselines:

- `random_budget`
- `topk_relevance_or_token_budget`
- `mmr_density_greedy`
- `v12_cost_aware_diagnostic_policy_operational_only`

Optional candidates are not enabled by this config because this goal did not
verify safe implementations:

- `dashscope_llm_prune_extract_operational_only`
- `adaptive_budget_router_operational_only`

Oracle baseline:

- `gold_support_oracle_upper_bound`, reported only as
  `non_deployable_upper_bound`

## Matched-Budget Conditions

Comparisons are valid only when the candidate pool hash, token budget,
downstream prompt hash, model snapshot, endpoint, thinking mode, decoding
policy, and token budget accounting are fixed. Budget mismatches, prompt hash
drift, model snapshot mismatches, endpoint drift, decoding drift, and candidate
pool mismatches stop fail closed.

## Metrics

Configured metrics are `supporting_fact_recall`, `evidence_recall`,
`selected_tokens`, `quality_per_1k_tokens`, `latency`, `cost`,
`parse_success_rate`, `claim_gate_distribution`, and `abstain_rate`.

## Claim Boundary

Allowed claims are limited to scoped operational improvement under matched
budgets and `operational_utility_only`.

Denied claims include selector superiority, global selector superiority,
metric bridge support, measurement validation, V-information verification,
`calibrated_proxy_supported`, `vinfo_proxy_supported`, teacher-forced NLL
support, Route 5 unlock, and Route 8 unlock.

## Execution Record

- Live API calls run: no
- Operational replay pilot run: no
- Dataset-scale experiment run: no
- Raw API responses stored: no
- Claim upgrade introduced: no
- Route 5 locked: yes
- Route 8 locked: yes
