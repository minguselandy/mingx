# P63R HotpotQA Real Bridge Calibration Report

## Summary

- Dataset: `HotpotQA`
- Task family: `hotpotqa_answer_support_selection`
- Active stratum: `evidence_packet_selection_microtask_v1`
- Calibration epoch: `P63R-HotpotQA-qwen36flash-600x150-v1`
- Gate result: `failed_closed_gate_failed`
- Metric claim level: `operational_utility_only`
- Claim status: `operational_utility_only; no_claim_upgrade`
- Rows validated: `600`
- Unique instances: `150`
- P56 status: `no_imported_traces`

## Fit Metrics

- Train rows: `420`
- Heldout rows: `180`
- Heldout fraction: `0.3`
- `c_hat_s`: `-19.102648602616423`
- `zeta_hat_s`: `0.9671598037016339`
- Normalized residual: `4.352219116658005`
- Sign agreement: `0.16666666666666666`
- Spearman rho: `-0.2252188038852718`
- Effective sample size: `600`

## Gate Reasons

- `normalized_residual_failed`
- `sign_agreement_failed`
- `spearman_rho_failed`

## Claim Boundary

- This is a HotpotQA stratum-local P63R calibration run.
- Passing gates would only produce `calibrated_proxy_supported_candidate` pending independent review.
- No final `calibrated_proxy_supported` claim is introduced here.
- No `vinfo_proxy_supported` claim is introduced here.
- No measurement validation, human-label validation, human-human kappa, deployed V-information verification, or paper evidence claim is introduced here.
- P56 remains `no_imported_traces`.
