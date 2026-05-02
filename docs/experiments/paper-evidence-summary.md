# Paper Evidence Summary

## Purpose

P16 adds a deterministic paper evidence summary builder for CPS runtime-audit evidence. The summary converts existing replay evidence packages into manuscript-facing JSON and Markdown sections for the runtime-audit scaffold, replayable experiment evidence, metric bridge, conservative claim gate, proxy-regime certification, limitations, and denied claims.

This is manuscript/evidence summarization only. It is not scientific validation.

## Inputs

The builder can consume:

- a P15 replay evidence package mapping
- a local directory containing P15 package outputs
- an in-memory summary that can be converted into a replay evidence package

The package-directory path is read-only. P16 does not run experiments, run live APIs, call model providers, or modify source artifacts.

## Outputs

Stable writers emit:

- `paper_evidence_summary.json`
- `paper_evidence_summary.md`

The JSON output contains:

- artifact summaries
- projection bundle summaries
- metric bridge summaries
- claim gate summaries
- proxy-regime summaries
- replay package summaries
- claim ladder summaries
- denied claims and reason codes
- manuscript table rows
- manuscript bullet summaries
- limitations and final claim boundaries

## Manuscript Tables

The builder emits stable table-row groups:

- `artifact_table_rows`
- `claim_gate_table_rows`
- `proxy_regime_table_rows`
- `replay_package_table_rows`
- `limitation_table_rows`

The Markdown output includes matching manuscript-friendly tables plus a suggested paper section mapping.

## Relationship to CPS Evidence

P16 summarizes outputs from:

- `ProjectionBundleV1`
- the P12 evidence ledger
- the P12/P13 claim gate report
- the P13 metric bridge gate
- the P14 proxy-regime matrix
- the P15 replay evidence package

P16 does not create a second claim gate and does not reinterpret evidence outside the existing conservative gates.

## Claim Boundary

- Paper-facing summaries cannot upgrade claim levels.
- Complete artifacts alone do not allow `measurement_validated`.
- Replay package completeness is not scientific validation.
- Missing human labels deny `measurement_validated`.
- Missing kappa denies `measurement_validated`.
- Missing or stale metric bridge evidence downgrades claims to `operational_utility_only` or `ambiguous`.
- Synthetic-only evidence does not certify deployed V-information submodularity.
- Engineering-only evidence does not certify scientific validation.
- Live API success alone is not measurement validation.
- External runtime success alone is not measurement validation.

P04 remains deferred/operator-required. P09 remains `BLOCKED_OPERATOR_REQUIRED`. `measurement_validated` is not claimed.

## Determinism

The builder uses stable ordering for artifacts, table groups, replay package outputs, reason codes, denied claims, and manuscript sections. JSON writers use sorted keys and fixed indentation. Markdown output is deterministic for the same input. The implementation uses no timestamps, UUIDs, randomness, network calls, external SDK imports, or `reference/` access.

## Validation

Recommended checks:

```powershell
python -m compileall cps scripts
pytest tests/test_paper_evidence_summary.py -q
pytest tests/test_replay_evidence_package.py -q
pytest tests/test_proxy_regime_matrix.py -q
pytest tests/test_evidence_ledger.py -q
pytest tests/test_claim_gate_report.py -q
pytest tests/test_metric_bridge_gate.py -q
pytest tests/test_synthetic_regime_benchmark.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```
