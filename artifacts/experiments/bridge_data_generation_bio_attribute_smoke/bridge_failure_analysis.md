# P45 Bridge Failure Analysis

## Summary

The API live smoke produced accepted rows with measured fixed-model log-loss, but the bridge gate failed closed. The failure is not a missing-logprob problem; it is an alignment problem between semantic utility deltas and exact target replay log-loss deltas.

## Aggregate Diagnostics

- `n`: `7`
- `c_s`: `960.4606707120654`
- `zeta_s`: `0.8932582871166177`
- `sign_agreement`: `0.8571428571428571`
- `pearson`: `-0.1821705413148583`
- `spearman`: `-0.20412414523193148`
- `mean_absolute_residual`: `0.4527212243151168`
- `utility_variance`: `0.0012244897959183669`
- `delta_logloss_variance`: `1.814578363418953e-07`
- `utility_range`: `{'min': 0.75, 'max': 0.85, 'span': 0.09999999999999998, 'unique_values': [0.75, 0.85]}`
- `delta_logloss_range`: `{'min': -4.503910304265446e-05, 'max': 0.0012593122260113887, 'span': 0.0013043513290540432, 'unique_values_count': 7}`
- `residual_quantiles`: `{'p50': 0.5245702181807255, 'p90': 0.7993106003839043, 'p95': 0.8462844437502609, 'p100': 0.8932582871166177}`
- `reason_codes`: `['pearson_failed', 'sign_agreement_failed', 'spearman_failed', 'zeta_failed']`

## Per-Row Patterns

| pair_id | delta_utility | delta_logloss | signs agree | abs residual | baseline sufficient? | added decisive? | pattern |
|---|---:|---:|---|---:|---|---|---|
| `p45-bio-attribute-smoke-001` | 0.850000 | 0.001259312 | true | 0.359520 | false | false | `utility_saturation_low_variance` |
| `p45-bio-attribute-smoke-002` | 0.750000 | 0.000695791 | true | 0.081720 | true | false | `utility_saturation_low_variance` |
| `p45-bio-attribute-smoke-003` | 0.850000 | 0.000879446 | true | 0.005327 | true | true | `utility_saturation_low_variance` |
| `p45-bio-attribute-smoke-004` | 0.850000 | 0.000117986 | true | 0.736679 | true | true | `utility_high_logloss_delta_tiny` |
| `p45-bio-attribute-smoke-005` | 0.850000 | 0.000293636 | true | 0.567974 | true | true | `utility_high_logloss_delta_tiny` |
| `p45-bio-attribute-smoke-007` | 0.850000 | -0.000045039 | false | 0.893258 | true | true | `sign_mismatch_logloss_worsened_or_unchanged` |
| `p45-bio-attribute-smoke-008` | 0.850000 | 0.000338827 | true | 0.524570 | true | true | `utility_high_logloss_delta_tiny` |

## Likely Causes

- `utility_saturation`: present. delta_utility has 2 unique values over n=7; 6 rows are 0.85.
- `low_variance_in_utility_scores`: present. population variance=0.001224489796, range=0.750000..0.850000.
- `baseline_already_sufficient`: present. 6/7 accepted rows have tiny baseline loss, tiny delta_logloss, or baseline keyword overlap: ['p45-bio-attribute-smoke-002', 'p45-bio-attribute-smoke-003', 'p45-bio-attribute-smoke-004', 'p45-bio-attribute-smoke-005', 'p45-bio-attribute-smoke-007', 'p45-bio-attribute-smoke-008'].
- `non_decisive_intervention_for_fixed_model`: present. 4/7 rows have |delta_logloss| <= 0.0005; negative delta_logloss rows: ['p45-bio-attribute-smoke-007'].
- `target_string_tokenization_sensitivity`: present. loss values are very small and deltas are around 1e-3 or smaller, so exact replay/tokenization noise can dominate the measured delta.
- `direction_sign_convention_issue`: present. delta_logloss is defined as loss_without - loss_with; ['p45-bio-attribute-smoke-007'] is negative while utility is positive. This indicates row-level objective mismatch, not a global sign inversion because 6/7 signs agree.
- `judge_logloss_objective_mismatch`: present. the strong reviewer scores semantic sufficiency of evidence blocks, while fixed-model log-loss measures exact target replay probability; high semantic utility does not reliably change replay likelihood for generic target strings.
- `small_sample_instability`: present. n=7 accepted rows; one negative or saturated row is enough to fail sign/correlation thresholds.

## Claim Boundary

- `metric_claim_level`: `operational_utility_only`
- `paper_evidence_eligible`: `false`
- `measurement_validation_claim`: `false`
- No `calibrated_proxy_supported` claim is made by this analysis.
- No human labels, kappa, or deployed V-information verification are created by this analysis.

## Recommended Fixes Before Scaling

- Create less generic target answers whose baseline context does not already make exact replay highly probable.
- Make added_block the only decisive evidence for the target answer; avoid task templates where the question itself strongly cues the answer.
- Ask the reviewer to emit utility_without and utility_with separately and preserve those fields for audit, not only delta_utility.
- Add a canary screen that rejects rows with very small |delta_logloss| or negative delta_logloss before spending a full pilot budget.
- Increase accepted pilot rows to 20-30 only after row design produces wider utility and logloss-delta variance in a small dry analysis.
