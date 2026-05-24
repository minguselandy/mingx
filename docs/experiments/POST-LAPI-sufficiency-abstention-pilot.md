# POST-LAPI Sufficiency / Abstention Pilot

Goal ID: POST-4-RUN / Sufficiency and abstention pilot
Run ID: `post_lapi_sufficiency_abstention_live_pilot_v1`
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

This owner-approved pilot ran a bounded DashScope-compatible live API sufficiency and abstention diagnostic over HotpotQA candidate-pool cases. Outputs are model-adjudicated candidate operational evidence only. They are not truth validation, human-calibrated abstention, measurement validation, paper-grade evidence, Route 5 unlock evidence, or Route 8 unlock evidence.

## Run Metadata

- Live API call count: `50`
- Example count: `50`
- Model snapshot: `qwen3.6-flash`
- Endpoint family: `dashscope_openai_compatible_chat_completions`
- Endpoint: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Raw API responses stored: `false`
- Route 5 locked: `true`
- Route 8 locked: `true`
- Claim upgrade introduced: `false`
- Gate status: `sufficiency_abstention_candidate_ready`

## Cost And Latency Summary

- Input tokens total: `23699`
- Output tokens total: `2884`
- Total tokens: `26583`
- Token cost per case mean: `531.66`
- Monetary cost status: `not_calculated_without_provider_pricing_config`
- Mean latency ms: `2301.6`
- Median latency ms: `2197.5`
- P95 latency ms: `2926.0`

## Aggregate Metrics

- Support rate: `0.42`
- Insufficient rate: `0.56`
- Contradict rate: `0.0`
- Uncertain rate: `0.02`
- Parse failed rate: `0.0`
- Abstain recommended rate: `0.58`
- Abstain when insufficient rate: `1.0`
- Unsafe answer rate: `0.3`

## Claim Boundary

The pilot may support only a sufficiency / abstention operational diagnostic. It does not establish truth validation, human-calibrated abstention, measurement validation, paper-grade evidence, or any route unlock.

## Artifact Index

- `artifacts/experiments/post_lapi_sufficiency_abstention/sufficiency_records.jsonl`
- `artifacts/experiments/post_lapi_sufficiency_abstention/regime_ledger.json`
- `artifacts/experiments/post_lapi_sufficiency_abstention/aggregate_report.json`
- `artifacts/experiments/post_lapi_sufficiency_abstention/run_manifest.json`
- `artifacts/experiments/post_lapi_sufficiency_abstention/claim_ledger.json`
