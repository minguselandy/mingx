# P63R-FixB HotpotQA Independent Support Utility Bridge

## Purpose

P63R-FixB is a non-circular HotpotQA support-classification bridge attempt.
It separates support-label NLL scoring from independent support-label classifier correctness utility.

## Design

- Task family: `hotpotqa_support_classification_independent_utility`
- Metric design: `independent_live_api_support_classifier_utility_v1`
- `delta_logloss`: support-label NLL improvement from `approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash::support_label_nll_v1`.
- `delta_utility`: `per_row_support_label_correctness_delta_from_independent_classifier_outputs` from `approved_live_api_classifier_endpoint::dashscope::qwen3.6-flash::support_label_classifier_v1`.
- Utility source: `independent_live_api_support_classifier_accuracy_delta`.
- Logprob prompt version: `hotpotqa_support_label_logprob_prompt_v1`
- Classifier prompt version: `hotpotqa_support_label_classifier_prompt_v1`
- Utility does not use NLL, logprobs, `delta_logloss`, ranks, clipping, rounding, or affine transforms.

## Artifacts

- Delta records: `artifacts/benchmarks/hotpotqa_support_independent_utility_delta_records.jsonl`
- Generation report: `artifacts/benchmarks/hotpotqa_support_independent_utility_generation_report.json`
- Operator rows: `artifacts/operator_inputs/p55_hotpotqa_support_independent_utility_rows.jsonl`
- Calibration output: `artifacts/experiments/p55_hotpotqa_support_independent_utility_bridge_calibration`

## Results

- Delta records validated: `826`
- Operator rows validated: `826`
- Unique instances: `826`
- Gate result: `failed_closed_gate_failed`
- Metric claim level: `operational_utility_only`
- Claim status: `operational_utility_only; no_claim_upgrade`
- Sign agreement: `0.0`
- Spearman rho: `None`
- Normalized residual: `31159457568.380623`

## Claim Boundary

- No final `calibrated_proxy_supported` claim is introduced here.
- No `vinfo_proxy_supported` claim is introduced here.
- No measurement validation, paper evidence, P56 unblock, or selector superiority claim is introduced here.
- This package requires independent review before any claim-ledger, manuscript, P56, P65, or P66 work.
