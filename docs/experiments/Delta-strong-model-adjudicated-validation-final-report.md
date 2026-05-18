# Delta Strong-Model Adjudicated Validation Final Report

Terminal status: `FAILED_CLOSED_JUDGE_RELIABILITY`
Claim status: `operational_utility_only/no_claim_upgrade`

## Delta-0 IW And Beta State

- Required branch: `codex/integrated-validation-workbench`.
- Beta portfolio status: `BETA_FAILED_CLOSED_NO_CLAIM_UPGRADE`.
- Beta reinterpreted: `false`.

## Delta-1 Protocol Freeze

- Protocol version: `delta_strong_model_judge_protocol_v1`.
- Label schema: `delta_strong_model_sufficiency_label_v1`.
- Raw response storage: `false`.

## Delta-2 Scale-Up

- Status: `failed_closed_underpowered`.
- Adjudicated items: `800`.
- Unique parent items: `600`.
- Unique original instances: `150`.
- Three-view items: `0`.
- Live API used: `false`.
- Live fill-in attempt status: `timeout_no_durable_labels_written`.
- Reason codes:
- `live_adjudication_not_run_for_missing_delta_views`
- `three_view_item_count_below_minimum`
- `unique_original_instance_count_below_delta_minimum`

## Delta-3 Reliability Audit

- Status: `FAILED_CLOSED_JUDGE_RELIABILITY`.
- Challenge-set status: `failed`.
- Duplicate consistency count: `0`.
- Order-reversal count: `200`.
- Prompt-sensitivity count: `0`.

## Delta-4 Route 4E Bridge

- Status: `FAILED_CLOSED_BRIDGE_GATES`.
- Rows validated: `800`.
- Unique original instances: `150`.
- `calibrated_proxy_supported`: `false`.
- `vinfo_proxy_supported`: `false`.

## Delta-5 Route 7 Selector Comparison

- Status: `completed_model_adjudicated_operational_selector_comparison`.
- Selector superiority claimed: `false`.
- Global selector superiority claimed: `false`.

## Delta-6 Claim Boundary

- Human annotation was not requested and missing human labels were not treated as a blocker.
- Model-only labels remain model-adjudicated evidence, not human measurement validation.
- No manuscript claim upgrade was performed.
- No claim-ledger upgrade was performed.
- Denied claims remain:
- `human measurement validation`
- `human-validated evidence`
- `measurement validation`
- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- `paper evidence`
- `metric bridge support`
- `selector superiority`
- `global selector superiority`
- `deployed V-information verification`
