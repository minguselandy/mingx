# P49 Extraction Audit Pilot Report

P49 audits the M-star to M extraction boundary using deterministic fixture cases. It is not a selector benchmark and not metric bridge evidence.

## Claim Boundary

- Data source kind: fixture
- Evidence scope: fixture_extraction_audit_only
- Paper evidence eligible: false
- Measurement validation claim: false
- Live API used: false
- Selector-regime claims are not upgraded by this audit.

## Summary

- Cases: 6
- Extracted findings: 10
- Labels: 9
- c_effective: 0.677885
- Value-weighted loss: 0.322115
- Defect counts: `{"contradictory_sources": 2, "duplicate_finding": 2, "missing_critical_finding": 1, "over_merged_finding": 2, "provenance_missing": 3, "source_span_missing": 3, "unsupported_finding": 1}`

## Stratum Completeness

- contradictory_adversarial: c_s=0.5, expected=1, missing=0
- high_provenance: c_s=0.666667, expected=3, missing=0
- qualifier_heavy: c_s=0.0, expected=1, missing=1
- simple_factual: c_s=1.0, expected=4, missing=0

## Claim Gate

- Metric claim level: operational_utility_only
- Calibrated proxy support: false
- V-information proxy support: false
