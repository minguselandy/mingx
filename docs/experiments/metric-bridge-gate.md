# Metric Bridge Gate

## Purpose

P13 hardens the metric bridge portion of the CPS claim gate. It adds a deterministic helper that evaluates bridge-related evidence and feeds the result into the P12 claim gate report.

This is an audit and claim-boundary layer only. It does not run live APIs, run live cohort, start external runtime integration, or create scientific validation evidence.

## Relationship to MetricBridgeWitness

The gate consumes Evidence Ledger-style fields derived from projection artifacts and `MetricBridgeWitness` payloads:

- `metric_bridge_witness_count`
- `bridge_freshness`
- `metric_class`
- `diagnostic_claim_level`
- `human_labels_present`
- `kappa_present`
- `contamination_status`
- `evidence_mode`
- `required_artifacts_present`
- `projection_bundle_count`
- `live_api_used`
- `external_runtime_used`

Defaults are conservative. Missing bridge evidence is treated as missing. Missing labels and kappa deny measurement validation. Missing or stale bridge freshness prevents validation-level claims.

## Integration with P12

`build_claim_gate_report(...)` now includes:

- `metric_bridge_gate_status`
- `allowed_bridge_claim_level`
- `metric_bridge_reason_codes`
- `measurement_validated_allowed`
- `denied_claims`
- `allowed_claim_level`

P13 does not create a second claim gate. It provides a stricter bridge evaluator that the P12 report uses.

## Gate Statuses

Implemented bridge gate statuses:

- `failed`
- `artifact_incomplete`
- `missing_bridge`
- `stale_bridge`
- `evidence_limited`
- `eligible_for_measurement_review`

The eligible status means only that the supplied ledger has bridge-side evidence fields consistent with measurement review. It is not a deployed measurement claim.

## Conservative Rules

- Contamination failure forces `pilot_only`.
- Missing `MetricBridgeWitness` count yields `missing_metric_bridge`.
- Missing bridge freshness yields `missing_metric_bridge`.
- Stale bridge freshness yields `stale_metric_bridge`.
- Missing human labels yields `missing_human_labels` and denies `measurement_validated`.
- Missing kappa yields `missing_kappa` and denies `measurement_validated`.
- `metric_class: operational_only` denies `measurement_validated`.
- `diagnostic_claim_level: operational_utility_only` denies `measurement_validated`.
- Synthetic evidence denies deployed V-information certification.
- Engineering-only evidence denies scientific validation.
- Complete artifacts alone do not allow measurement validation.
- Live API success alone does not allow measurement validation.
- External runtime success alone does not allow measurement validation.

## Claim Boundary

P13 does not validate measurement, certify V-information, certify submodularity, certify metric bridge freshness, certify deployment claims, unblock P04, or unblock P09.

P04 remains deferred/operator-required. P09 remains `BLOCKED_OPERATOR_REQUIRED`. `measurement_validated` is not claimed.

## Validation

Recommended checks:

```powershell
python -m compileall cps scripts
pytest tests/test_provider_adapters.py -q
pytest tests/test_provider_candidate_normalizer.py -q
pytest tests/test_provider_offline_smoke.py -q
pytest tests/test_projection_bundle_v1.py -q
pytest tests/test_projection_artifacts.py -q
pytest tests/test_selector_optional_adapters.py -q
pytest tests/test_synthetic_regime_benchmark.py -q
pytest tests/test_evidence_ledger.py -q
pytest tests/test_claim_gate_report.py -q
pytest tests/test_metric_bridge_gate.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```
