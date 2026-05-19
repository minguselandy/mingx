# Next LogProbe Repair Plan

Claim status: operational_utility_only/no_claim_upgrade

## Current finding

The existing bridge evidence remains failed closed. The audit found target-verbalization/tokenization risk, weak utility-logloss alignment, model-judge reliability limits, and underpowered model-adjudicated bridge slices. A stricter claim gate is not the defect; it is preventing unsupported upgrades.

## Locked routes

- Do not unlock Route 5 or Route 8.
- Do not start fixed-model logloss proxy verification until an accepted metric bridge candidate exists.
- Do not update manuscript claims or claim ledgers from this audit.

## Repair sequence

1. Freeze a target-verbalization contract before any new scoring: exact target string, tokenization policy, allowed labels, and invalid-output handling.
2. Separate logprobe stability from bridge utility design. If live scoring is later approved, repeat a small fixed row set under the same target contract and report variance before fitting a bridge.
3. Repair utility-logloss alignment before scale-up. The currently weak routes are: Route4A, Route4B, DeltaRoute4E.
4. Keep model-adjudicated labels as operational evidence only. Human labels and kappa remain absent.
5. Rerun bridge gates only after stability, target-contract, and non-circular utility checks pass.

## Denied claims

- measurement_validation
- metric_bridge_support
- calibrated_proxy_supported
- vinfo_proxy_supported
- paper_evidence
- selector_superiority
- deployed_v_information_verification
