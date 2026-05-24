# POST-LAPI Reprojection Witness Pilot

Goal ID: POST-5-RUN / Reprojection witness pilot
Run ID: `post_lapi_reprojection_witness_live_pilot_v1`
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

This owner-approved pilot ran a bounded DashScope-compatible reprojection witness pass over flagged POST-4 sufficiency and omitted-evidence cases. Outputs are model-adjudicated candidate operational evidence only. They are not validated repair, truth correction guarantees, metric bridge support, selector superiority, Route 5 unlock evidence, or Route 8 unlock evidence.

## Run Metadata

- Eligible flagged cases: `26`
- Live API call count: `26`
- Model snapshot: `qwen3.6-flash`
- Endpoint family: `dashscope_openai_compatible_chat_completions`
- Endpoint: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Raw API responses stored: `false`
- Route 5 locked: `true`
- Route 8 locked: `true`
- Claim upgrade introduced: `false`
- Gate status: `reprojection_witness_candidate_ready`

## Cost And Latency Deltas

- Before tokens total: `13924`
- After tokens total: `16150`
- Delta tokens total: `2226`
- Delta tokens mean: `85.615`
- Monetary cost status: `not_calculated_without_provider_pricing_config`
- Mean latency delta ms: `213.5`
- Median latency delta ms: `234.0`
- P95 latency delta ms: `1001.0`

## Aggregate Metrics

- Repair candidate rate: `0.5769230769230769`
- Label change rate: `0.5769230769230769`
- Abstain-to-support rate: `0.5769230769230769`
- Unsupported-to-supported rate: `0.5769230769230769`
- Position sensitivity rate: `0.6153846153846154`
- Parse failed rate: `0.0`

## Claim Boundary

Allowed interpretation: operational reprojection witness, omitted-evidence operational diagnostic, and replayable artifact evidence. Denied interpretation: validated repair, truth correction guarantee, metric bridge support, selector superiority, or any route unlock.

## Artifact Index

- `artifacts/experiments/post_lapi_reprojection_witness/witness_records.jsonl`
- `artifacts/experiments/post_lapi_reprojection_witness/regime_ledger.json`
- `artifacts/experiments/post_lapi_reprojection_witness/aggregate_report.json`
- `artifacts/experiments/post_lapi_reprojection_witness/run_manifest.json`
- `artifacts/experiments/post_lapi_reprojection_witness/claim_ledger.json`
