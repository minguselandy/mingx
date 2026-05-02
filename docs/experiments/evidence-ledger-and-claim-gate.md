# Evidence Ledger and Claim Gate Report

## Purpose

P12 adds a deterministic audit/reporting layer over CPS runtime-audit artifacts. The evidence ledger summarizes what evidence exists for a run, and the claim gate report computes the highest allowed claim level under conservative fail-closed rules.

This layer is reporting only. It does not run live APIs, run live cohort, start external runtime integration, import external SDKs, or create scientific validation evidence.

## Evidence Ledger

The ledger can be built from an artifact directory or from an in-memory summary. For artifact directories, `events.jsonl` is used when present and artifact JSONL files are cross-checked for required evidence counts.

Required projection artifacts are:

- `candidate_pools`
- `projection_plans`
- `budget_witnesses`
- `materialized_contexts`
- `metric_bridge_witnesses`
- `diagnostics`
- `projection_bundles`

Missing, zero, or mismatched required artifact counts fail closed. Missing `projection_bundles` is treated as incomplete replay evidence.

Conservative defaults are used unless explicit evidence is supplied:

- `human_labels_present: false`
- `kappa_present: false`
- `contamination_status: unknown`
- `bridge_freshness: missing`
- `live_api_used: false`
- `external_runtime_used: false`
- `p04_status: BLOCKED_OPERATOR_REQUIRED`
- `p09_status: BLOCKED_OPERATOR_REQUIRED`

## Claim Gate Report

The claim gate report consumes a ledger and returns:

- `allowed_claim_level`
- `denied_claims`
- `reason_codes`
- `measurement_validated_allowed`
- `p04_status`
- `p09_status`
- a deterministic summary string

Implemented claim levels are:

- `engineering_compatibility_only`
- `engineering_smoke_only`
- `replayable_artifact_evidence`
- `synthetic_structural_only`
- `operational_utility_only`
- `ambiguous`
- `pilot_only`
- `measurement_validated`

The report includes `measurement_validated` as a denied claim when evidence is missing. That is not a validation claim.

## Fail-Closed Rules

- Contamination failure forces `pilot_only`.
- Missing human labels denies `measurement_validated`.
- Missing kappa denies `measurement_validated`.
- Missing or stale metric bridge prevents validation-level claims and keeps the result at `operational_utility_only` or `ambiguous`.
- Missing required artifacts lowers the claim to `ambiguous`.
- Missing `projection_bundles` lowers the claim to `ambiguous`.
- Engineering-only evidence remains engineering-only.
- Synthetic-only evidence never certifies deployed V-information submodularity.

## Metric Bridge Relationship

P12 supports the paper's Metric Bridge section by making the bridge evidence state explicit and auditable. A missing or stale bridge is recorded as a reason code. The report does not make bridge freshness true by inference and does not convert replayable artifacts into measurement validation.

## Claim Boundary

P12 does not validate measurement, certify V-information, certify submodularity, certify metric bridge freshness, certify deployment claims, unblock P04, or unblock P09.

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
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```
