# Route 6A External Sufficiency Measurement Pilot

Status: model_adjudication_completed
Claim status: `no_claim_upgrade`

## Inputs

- Route 4A rows available: `600`
- Candidate pools available: `200`
- Context-pair sample size: `24`

## Rubric Boundary

- Rubric version: `route6a_external_sufficiency_rubric_v1`
- The judge-visible sample hides logloss, utility scores, gold-support labels, and Route 4 bridge measurements.
- Model-adjudicated labels are not human labels and do not count for kappa.

## Claim Boundary

- `measurement_validation_candidate_allowed`: `false`
- `calibrated_proxy_supported`: denied
- `vinfo_proxy_supported`: denied
- `operational_utility_only / no_claim_upgrade` remains active.

## Storage Boundary

- Live API used: `true`
- Raw API responses stored: `false`
- Operator inputs written: `false`
