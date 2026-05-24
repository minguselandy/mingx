# POST-LAPI Judge Weak-Evidence Stability Pilot

Goal ID: POST-3-RUN / Judge weak-evidence stability pilot
Run ID: `post_lapi_judge_stability_live_pilot_v1`
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

This owner-approved pilot ran a bounded DashScope-compatible live API judge stability diagnostic over 30 examples. Outputs are weak/model-adjudicated candidate evidence only. They are not human or external gold labels, measurement validation, judge validation, paper-grade evidence, selector superiority evidence, or Route 5/Route 8 unlock evidence.

## Run Metadata

- Live API call count: `240`
- Example count: `30`
- Model snapshot: `qwen3.6-flash`
- Endpoint family: `dashscope_openai_compatible_chat_completions`
- Endpoint: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Raw API responses stored: `false`
- Route 5 locked: `true`
- Route 8 locked: `true`
- Claim upgrade introduced: `false`
- Gate status: `weak_evidence_candidate_ready`
- Allowed claim after gate: `model_adjudicated_weak_evidence`

## Cost And Latency Summary

- Input tokens total: `115232`
- Output tokens total: `17574`
- Total tokens: `132806`
- Token cost per judgment mean: `553.358`
- Monetary cost status: `not_calculated_without_provider_pricing_config`
- Mean latency ms: `2425.058`
- Median latency ms: `2262.5`
- P95 latency ms: `3587.0`

## Stability Metrics

- Parse failure rate: `0.0`
- Duplicate agreement: `0.9833333333333333`
- Order-swap agreement: `0.9833333333333333`
- Rubric paraphrase agreement: `0.9666666666666667`
- Confidence bucket stability: `0.833333`
- Position bias rate: `0.016667`
- Uncertain rate: `0.0`

## Claim Boundary

If stability thresholds fail, the model-adjudicated weak-evidence claim is suppressed as ambiguous. If they pass, the strongest permitted statement remains weak operational diagnostic evidence from model adjudication only.

Denied claims remain denied: human gold, human/external gold validation, measurement validation, judge validation, paper-grade evidence, selector superiority, Route 5 unlock, and Route 8 unlock.

## Artifact Index

- `artifacts/experiments/post_lapi_judge_stability/judgments.jsonl`
- `artifacts/experiments/post_lapi_judge_stability/run_manifest.json`
- `artifacts/experiments/post_lapi_judge_stability/aggregate_report.json`
- `artifacts/experiments/post_lapi_judge_stability/claim_ledger.json`
