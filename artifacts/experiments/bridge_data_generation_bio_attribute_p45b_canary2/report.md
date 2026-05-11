# P45 API-Generated Bridge Calibration Data Report

- Mode: `live_operator_approved`
- Accepted rows: `0`
- Rejected rows: `4`
- Ambiguous rows: `0`
- Unusable rows: `8`
- Bridge-uninformative rows: `8`
- Negative `delta_logloss` rows: `6`
- `delta_logloss` is accepted only when sourced from `measured_logprob`.
- Strong-model review may adjudicate utility but must not estimate log-loss.
- Run P45 `--dry-validate` on accepted rows before artifact generation.
- No human labels, kappa, deployed V-information verification, or measurement validation are claimed.
- `measurement_validated` remains a denied claim.
