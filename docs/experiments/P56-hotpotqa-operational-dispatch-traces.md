# P56 HotpotQA Operational Dispatch Traces

## Purpose

P56 generates HotpotQA realistic dispatch traces for operational replay only.
The current P63R bridge attempts failed or are positive-control only, so these traces do not carry metric bridge support.

## Inputs

- Candidate pools: `artifacts/benchmarks/hotpotqa_candidate_pools.jsonl`
- Dataset: `HotpotQA`
- Task family: `hotpotqa_answer_support_selection`

## Outputs

- Traces: `artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl`
- Generation report: `artifacts/benchmarks/p56_hotpotqa_trace_generation_report.json`

## Results

- Traces generated: `2000`
- Traces validated: `2000`
- Budgets: `[512, 1024]`
- Selectors: `['random_budget', 'topk_relevance_or_token_budget', 'mmr_density_greedy', 'v12_cost_aware_diagnostic_policy_operational_only', 'gold_support_oracle_upper_bound']`
- Metric claim level: `operational_utility_only`
- Bridge witness status: `failed_or_absent`

## Claim Boundary

- Allowed claim: P56 HotpotQA operational dispatch traces generated and validated under `operational_utility_only`.
- No `calibrated_proxy_supported` claim is introduced.
- No `vinfo_proxy_supported` claim is introduced.
- No measurement validation, paper evidence, P55 bridge support, or selector superiority claim is introduced.
- P66 comparison artifacts are intentionally not created here.
