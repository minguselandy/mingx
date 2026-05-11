# P45e Candidate-Set Constrained Canary Summary

- Total task packets: `8`
- Measured-logprob rows: `8`
- Positive `delta_logloss` rows: `5`
- Sufficient-signal rows: `3`
- Low-signal rows: `2`
- Negative-delta rows: `3`
- Accepted/exported rows: `2`
- Bridge-fit-eligible rows: `6`
- Utility without range: `[0.0, 0.0]`
- Utility with range: `[0.0, 1.0]`
- Delta utility range: `[0.0, 1.0]`
- Utility unique values: `[0.0, 0.5, 0.75, 1.0]`
- Candidate-set size before distribution: `{'8': 8}`
- Candidate-set size after distribution: `{'1': 2, '2': 4, '4': 1, '8': 1}`
- Delta logloss range: `[-0.03001067159334525, 0.01920193757450761]`
- Median delta logloss: `0.0005973971105959208`
- Evidence-strength band distribution: `{'irrelevant': 1, 'weak_hint': 1, 'partial_constraint': 2, 'strong_clue': 2, 'explicit_answer': 2}`

## Boundary

- P45e exports fit-eligible accepted rows only.
- Fixed logloss scorer scores only the exact correct candidate string.
- Reviewer/adjudicator output cannot provide log-loss.
- No human labels, kappa, deployed V-information verification, or measurement validation are claimed.
- Paper evidence eligibility remains false for this live canary unless separately promoted by operator review.

## Dry Validation

- Threshold validation status: `failed`
- Metric claim level: `ambiguous_metric`
- `c_s`: `56.092845501063664`
- `zeta_s`: `0.6149804388887039`
- Sign agreement: `1.0`
- Pearson: `1.0`
- Spearman: `1.0`
- Reason codes: `['effective_sample_size_failed', 'sample_size_failed', 'zeta_failed']`
- Calibration artifacts generated: `false`
