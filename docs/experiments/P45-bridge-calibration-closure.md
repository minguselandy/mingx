# P45 Bridge Calibration Closure

P45 is implemented and operator/API-ready, but the current `bio_attribute`
stratum is not bridge-calibrated. This document closes P45 for this stratum and
sets P46 as the next active phase.

## Scope

Closed stratum:

```text
task_family = bio_attribute
materialization_policy = fixed_order_v1
block_size = 1
candidate_slice_band = top_L
metric = model_adjudicated_utility_vs_logloss
```

The live canaries used operator-approved API-generated rows and measured
fixed-model token logprobs. They did not create human labels, human-human kappa,
contamination closure, or measurement validation.

## What P45 Completed

- Implemented the offline/importable one-stratum bridge calibration lane.
- Added fixture coverage for deterministic engineering validation.
- Added operator handoff templates and dry validation workflow.
- Added an opt-in API-generated data scaffold with provider preflight, secret
  hygiene checks, and fail-closed logprob handling.
- Preserved provenance fields for operator/API-generated rows.
- Verified through P45c that the fixed logloss scorer can produce meaningful
  measured `delta_logloss` under explicit target evidence.

Fixture data validates the implementation path only. Fixture rows are not paper
bridge evidence and must not be mixed with operator-provided rows.

## Canary Evidence

P45/P45b/P45c/P45d/P45e produced the following status:

- P45c fixed-logloss positive control passed: the fixed scorer returned usable
  measured logprobs and positive `delta_logloss` for all bounded probes.
- P45d produced positive measured logloss signal, but utility/logloss
  correlation failed the bridge thresholds.
- P45e constrained utility and logloss around candidate-set identification, but
  only two rows were exported for bridge fit and dry validation failed with
  sample-size, effective-sample-size, and `zeta_s` failures.

The failure is informative: the measurement path exists, but the current
utility-to-logloss bridge is not established for this stratum.

## Final Status

Current stratum status:

- bridge established: `false`
- allowed bridge claim: no `calibrated_proxy_supported`
- downstream utility diagnostics: `operational_utility_only`
- P45e calibration artifact status: `ambiguous_metric` because exported fit
  rows were underpowered and failed the configured `zeta_s` gate
- paper evidence eligibility: `false`
- measurement validation claim: `false`

P45 should not be expanded to a 20-30 row pilot for this same stratum without a
new scientific rationale. Acceptable revisit conditions are a new active
stratum, a new fixed-logloss/utility design that changes the measurement
object, or a reviewed protocol that explains why the failed canaries do not
apply.

## Claim Boundary

This closure does not claim:

- `calibrated_proxy_supported` for the current `bio_attribute` stratum
- `measurement_validated`
- human labels
- human-human kappa
- contamination closure
- deployed V-information verification
- scientific validation

No thresholds were relaxed and no additional calibration rows were fabricated.

## Preserved Artifacts

Do not delete the negative canary reports or raw P45 artifacts. They are part of
the claim-gate record.

Key artifact families include:

- `artifacts/experiments/bridge_calibration_one_stratum/`
- `artifacts/experiments/bridge_data_generation_bio_attribute_smoke/`
- `artifacts/experiments/bridge_data_generation_bio_attribute_p45b_canary2/`
- `artifacts/experiments/bridge_logloss_positive_control/`
- `artifacts/experiments/bridge_data_generation_bio_attribute_p45d_canary/`
- `artifacts/experiments/bridge_data_generation_bio_attribute_p45e_canary/`

## P46 Transition

The next active phase is P46 synthetic v12 artifact refresh. P46 should proceed
without retrying P45 bridge calibration indefinitely. Any future P45 revisit
should start from a new stratum or a materially new fixed-logloss/utility design
and should preserve the same fail-closed claim boundaries.
