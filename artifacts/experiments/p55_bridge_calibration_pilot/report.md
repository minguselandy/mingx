# P55 New-Stratum Bridge Calibration Pilot Report

## Summary

- Stratum: `evidence_packet_selection_microtask_v1`
- Input rows reference: `artifacts/operator_inputs/p55_evidence_packet_selection_microtask_v1_rows.jsonl`
- Input file status: `absent`
- Pilot status: `blocked_operator_required`
- Claim gate status: `failed_closed_no_rows`
- Metric claim level: `ambiguous_metric`
- Paper evidence eligible: `false`
- Measurement validation claim: `false`
- Live API used: `false`
- Human labels present: `false`
- Human-human kappa present: `false`
- Blocked operator required: `true`
- Next phase allowed: `false`

## Row Validation

- Rows present: `false`
- Rows imported: `0`
- Rows validated: `0`
- Rows accepted for evaluation: `0`
- Active stratum match: `false`
- Candidate-pool hash status: `missing`
- Data source kind: `missing`
- Contamination status: `not_applicable`
- Drift status: `missing`

## Fit

- Development rows: `0`
- Held-out rows: `0`
- `c_s`: `None`
- `zeta_s`: `None`
- Held-out sign agreement: `None`
- Held-out rank correlation: `None`
- Residual stability: `unavailable`
- Fit metrics computed: `false`

## Claim Gate Reasons

- `no_operator_imported_rows`
- `operator_rows_required`

## Boundary

- P55 does not claim measurement validation.
- P55 does not claim deployed V-information verification.
- Fixture/test-only rows cannot emit `calibrated_proxy_supported` or `vinfo_proxy_supported`.
- Missing operator-imported rows fail closed without fabricated evidence.
