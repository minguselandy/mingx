# P45d Graded Positive-Control Canary Summary

- Total task packets: `8`
- Measured-logprob rows: `8`
- Positive `delta_logloss` rows: `8`
- Sufficient-signal rows: `8`
- Low-signal rows: `0`
- Negative-delta rows: `0`
- Accepted/exported rows: `6`
- Bridge-fit-eligible rows: `6`
- Utility without range: `[0.0, 0.0]`
- Utility with range: `[0.0, 1.0]`
- Delta utility range: `[0.0, 1.0]`
- Utility unique values: `[0.0, 0.25, 0.5, 0.75, 1.0]`
- Delta logloss range: `[0.03410711737615202, 0.31896887282164244]`
- Median delta logloss: `0.16120272938749736`
- Evidence-strength band distribution: `{'irrelevant': 1, 'weak_hint': 1, 'partial_constraint': 2, 'strong_clue': 2, 'explicit_answer': 2}`

## Boundary

- P45d exports fit-eligible accepted rows only.
- Reviewer/adjudicator output cannot provide log-loss.
- No human labels, kappa, deployed V-information verification, or measurement validation are claimed.
- Paper evidence eligibility remains false for this live canary unless separately promoted by operator review.

## Dry Validation

- Threshold validation status: `failed`
- Metric claim level: `operational_utility_only`
- `c_s`: `3.062489130554791`
- `zeta_s`: `0.7158349753750926`
- Sign agreement: `1.0`
- Pearson: `-0.4214132811442798`
- Spearman: `-0.3086066999241838`
- Reason codes: `['pearson_failed', 'spearman_failed', 'zeta_failed']`
- Calibration artifacts generated: `false`
