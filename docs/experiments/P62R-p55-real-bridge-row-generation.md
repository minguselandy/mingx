# P62R P55 Real Bridge Row Generation

## P62R purpose

P62R provides the contract-safe row-generation layer from benchmark candidate
pools plus explicit evaluator/log-loss delta records into P55 operator rows for
`evidence_packet_selection_microtask_v1`.

The current bridge-primary route is the controlled HotpotQA subtask:

- `dataset = HotpotQA`
- `task_family = hotpotqa_answer_support_selection`
- `candidate_slice_band = hotpotqa_dev_distractor_context`

FEVER adapter and row-generator support remain present but are paused for
bridge-primary use.

## Current Inputs

HotpotQA candidate pools were generated from real HotpotQA dev distractor data:

- `artifacts/benchmarks/hotpotqa_candidate_pools.jsonl`
- 200 candidate pools

Evaluator/log-loss deltas were generated with the approved bounded DashScope
OpenAI-compatible `qwen3.6-flash` logprob endpoint:

- `artifacts/benchmarks/hotpotqa_p55_delta_records.jsonl`
- 600 delta records generated and validated
- 150 unique instances
- `evaluator_id = approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash::deterministic_logprob_scoring_v1`

The generation report records deterministic evaluator provenance, including
`temperature = 0`, `top_p = 1`, `top_logprobs = 0`, and
`enable_thinking = false`.

## Row Output

P62R generated and validated:

- `artifacts/operator_inputs/p55_evidence_packet_selection_microtask_v1_rows.jsonl`
- 600 P55 operator rows
- 600 rows validated
- 150 unique instances

Evaluator/log-loss deltas use JSONL-by-row-key. The full row key includes
`active_stratum`, `task_family`, `dataset`, `instance_id`,
`candidate_pool_hash`, context L packet IDs, block A packet IDs, `target_y`,
`model_tier`, `materialization_policy`, candidate slice, block size, decoding
policy, and evaluator identity. `replicate_count` is measurement metadata, not
row identity.

## Claim Boundary

This is calibration input only. No P55 calibration has passed yet. P55 remains blocked for calibrated bridge-support interpretation until P63R calibration gates pass and independent review accepts the package.

No bridge calibration was run by P62R. No bridge calibration result is claimed
by P62R. No calibrated_proxy_supported claim. No vinfo_proxy_supported claim.
No measurement validation. No paper evidence claim. P56 remains no_traces /
`no_imported_traces`.

Denied claim upgrades remain:

- Denied: `measurement_validated`.
- Denied: human-label validation.
- Denied: human-human kappa.
- Denied: deployed V-information verification.
- Denied: global calibrated proxy support.
- Denied: global V-information proxy support.
- Denied: paper evidence.
- Denied: P56 unblocked.

Next phase is P63R only after validated rows exist and user approval is given.
