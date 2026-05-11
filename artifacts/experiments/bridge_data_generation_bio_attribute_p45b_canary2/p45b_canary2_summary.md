# P45b Canary 2 Summary

- Total rows: `8`
- Exported P45 rows: `0`
- Measured logprob rows: `8`
- Bridge-uninformative rows: `8`
- Negative delta_logloss rows: `6`
- Low abs delta_logloss rows: `8`
- Delta utility range: `[0.0, 1.0]`
- Delta logloss range: `[-0.0009177988148323379, 0.000585852496591599]`
- Reason counts: `{'delta_logloss_below_informative_threshold': 8, 'negative_delta_logloss': 6, 'unsupported_evidence_strength_band': 7, 'target_clear_failed': 3}`

## Decision

- Do not scale to 20-30 pilot rows yet.
- Utility saturation improved, but measured log-loss signal is still too small or negative.
- No calibrated proxy, measurement validation, human labels, kappa, or deployed V-information verification is claimed.
