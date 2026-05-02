# Proxy-Regime Certification Matrix

## Purpose

P14 adds a deterministic proxy-regime certification matrix for manuscript-facing CPS diagnostics. The matrix summarizes expected synthetic/proxy regime behavior, observed diagnostic behavior, failure modes, and conservative claim boundaries.

Proxy-regime certification means certification of the proxy diagnostic regime only. It does not certify deployed V-information submodularity, deployed runtime behavior, or measurement validation.

## Inputs

The matrix can be built from:

- a synthetic benchmark artifact directory containing `summary.json`, `diagnostics.jsonl`, and `metric_bridge_witnesses.jsonl`
- an in-memory summary plus optional diagnostic and bridge witness rows

The implementation reuses the P12 evidence ledger and claim gate report, plus the P13 metric bridge gate. It does not create a parallel claim system.

## Matrix Coverage

Synthetic/proxy regime rows:

- `redundancy_dominated`
- `sparse_pairwise_synergy`
- `higher_order_synergy`

Boundary rows:

- `contamination_failed`
- `missing_human_labels`
- `missing_kappa`
- `stale_metric_bridge`
- `missing_metric_bridge`
- `artifact_incomplete`

## Certification Scope

Allowed certification scopes are:

- `proxy_regime_diagnostic_only`
- `synthetic_structural_only`
- `engineering_smoke_only`
- `ambiguous`
- `pilot_only`

Denied scope values include:

- `deployed_V_information_certified`
- `measurement_validated`
- `scientific_validation`

## Claim Boundary

- Synthetic success is not deployed V-information certification.
- Engineering-only evidence is not scientific validation.
- Live API success alone is not measurement validation.
- External runtime success alone is not measurement validation.
- Complete synthetic artifacts alone are not measurement validation.
- Contamination failure forces `pilot_only`.
- Missing human labels deny `measurement_validated`.
- Missing kappa denies `measurement_validated`.
- Missing or stale metric bridge evidence downgrades claims to `operational_utility_only` or `ambiguous`.

P04 remains deferred/operator-required. P09 remains `BLOCKED_OPERATOR_REQUIRED`. `measurement_validated` is not claimed.

## Outputs

Stable writers emit:

- `proxy_regime_matrix.json`
- `proxy_regime_matrix.md`

The Markdown output is intended for manuscript drafting and review. It includes regime assumptions, expected behavior, observed behavior, allowed claim level, certification scope, and reason codes.

## Validation

Recommended checks:

```powershell
python -m compileall cps scripts
pytest tests/test_synthetic_regime_benchmark.py -q
pytest tests/test_evidence_ledger.py -q
pytest tests/test_claim_gate_report.py -q
pytest tests/test_metric_bridge_gate.py -q
pytest tests/test_proxy_regime_matrix.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```
