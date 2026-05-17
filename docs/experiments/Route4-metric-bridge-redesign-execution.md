# Route 4 Metric-bridge Redesign Execution

Status: Route 4A HotpotQA sufficiency-grounded pilot
Claim status: `no_claim_upgrade`

## Dataset Readiness

- FEVER is recorded as blocked when complete candidate pools and evaluator records are absent.
- HotpotQA uses existing real candidate pools and approved answer-NLL delta records.

## Evaluator Readiness

- Scoring source: existing approved HotpotQA answer-NLL delta records from the bounded live logprob endpoint.
- No raw API responses are written.

## Utility Definition

- Utility definition: `route4_hotpotqa_sufficiency_coverage_v1`
- Utility source: `hotpotqa_gold_support_packets_and_source_doc_ids`
- Utility uses gold support packet IDs and source document IDs only.
- Utility does not use NLL, logprobs, model probabilities, ranks, clipping, rounding, or affine transforms.

## Pilot Result

- Rows attempted: `600`
- Rows validated: `600`
- Unique original instances: `150`
- Calibration run: `True`
- Gate result: `failed_closed_gate_failed`
- Metric claim level: `failed_closed_no_claim_upgrade`

## Claim Boundary

- No final `calibrated_proxy_supported` claim is introduced.
- No `vinfo_proxy_supported` claim is introduced.
- No measurement validation, paper evidence, P55/P56 metric support, global selector superiority, or deployed V-information verification is introduced.
- Any candidate status remains pending independent validation.

## Next Recommended Decision

Submit the Route 4A package for major review before any claim-ledger or manuscript update.
