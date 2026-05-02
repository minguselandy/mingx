# Replay Evidence Package

## Purpose

P15 adds an offline replay evidence package builder for CPS runtime-audit artifacts. The package collects existing projection artifacts, `ProjectionBundleV1` hashes, the P12 evidence ledger, the P13 claim gate report, and optional P14 proxy-regime matrix outputs into a deterministic review bundle.

Replay packaging is for inspection, comparison, and manuscript citation support. It is not scientific validation.

## Inputs

The builder can consume:

- an artifact directory from a local synthetic, smoke, or replay run
- an in-memory summary compatible with the P12 evidence ledger
- an optional proxy-regime matrix

The artifact-directory path is read-only. The builder does not modify source artifacts or run experiments.

## Package Contents

Stable writers emit:

- `manifest.json`
- `artifact_counts.json`
- `projection_bundle_hashes.json`
- `evidence_ledger.json`
- `claim_gate_report.json`
- `claim_gate_report.md`
- `proxy_regime_matrix.json` when a matrix is provided or can be built from local synthetic artifacts
- `proxy_regime_matrix.md` when a matrix is provided or can be built from local synthetic artifacts
- `replay_package_summary.md`

## Relationship to CPS Artifacts

The package is a wrapper around already materialized CPS evidence:

- `ProjectionBundleV1` supplies canonical projection hashes.
- The evidence ledger summarizes artifact completeness and replay availability.
- The claim gate report applies conservative scientific claim boundaries.
- The metric bridge gate constrains claims when bridge evidence is missing, stale, or operational only.
- The proxy-regime matrix summarizes synthetic/proxy diagnostic behavior when available.

P15 does not create a second claim gate and does not reinterpret evidence outside the P12/P13 rules.

## Claim Boundary

- Replay package completeness is not scientific validation.
- Complete artifacts alone do not allow `measurement_validated`.
- Missing human labels deny `measurement_validated`.
- Missing kappa denies `measurement_validated`.
- Contamination failure forces `pilot_only`.
- Missing or stale metric bridge evidence downgrades claims to `operational_utility_only` or `ambiguous`.
- Synthetic-only packages do not certify deployed V-information submodularity.
- Engineering-only packages do not certify scientific validation.
- Live API success alone is not measurement validation.
- External runtime success alone is not measurement validation.

P04 remains deferred/operator-required. P09 remains `BLOCKED_OPERATOR_REQUIRED`. `measurement_validated` is not claimed.

## Determinism

The builder uses stable ordering for artifact names, projection bundle hashes, denied claims, and reason codes. JSON writers use sorted keys and fixed indentation. Markdown output is deterministic for the same input. The implementation uses no timestamps, UUIDs, randomness, network calls, external SDK imports, or `reference/` access.

## Validation

Recommended checks:

```powershell
python -m compileall cps scripts
pytest tests/test_replay_evidence_package.py -q
pytest tests/test_proxy_regime_matrix.py -q
pytest tests/test_evidence_ledger.py -q
pytest tests/test_claim_gate_report.py -q
pytest tests/test_metric_bridge_gate.py -q
pytest tests/test_synthetic_regime_benchmark.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```
