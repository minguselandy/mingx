# End-to-End Evidence Demo

## Purpose

P17 adds a deterministic offline demo that wires the CPS runtime-audit evidence modules into one minimal reproducible pipeline.

The demo path is:

```text
provider/synthetic input
  -> provider candidate normalization
  -> provider-to-selector offline smoke evidence
  -> ProjectionBundleV1 / projection artifacts
  -> evidence ledger
  -> conservative claim gate report
  -> metric bridge gate
  -> proxy-regime matrix
  -> replay evidence package
  -> paper evidence summary
```

P17 is offline runtime-audit evidence only. It is not a live API run, not a live cohort, not external runtime integration, and not scientific validation.

## Running the Demo

Function API:

```python
from cps.experiments.end_to_end_evidence_demo import build_end_to_end_evidence_demo

build_end_to_end_evidence_demo("tmp/p17-demo")
```

Offline CLI:

```powershell
python -m cps.experiments.end_to_end_evidence_demo --output-root tmp/p17-demo
```

The CLI writes deterministic local outputs and does not modify source artifacts outside the requested output root.

## Outputs

The demo writes:

- `projection_bundles.jsonl`
- `evidence_ledger.json`
- `claim_gate_report.json`
- `claim_gate_report.md`
- `proxy_regime_matrix.json`
- `proxy_regime_matrix.md`
- `replay_package/`
- `replay_package/replay_package_summary.md`
- `paper_evidence_summary.json`
- `paper_evidence_summary.md`
- `demo_manifest.json`
- `demo_summary.md`

## Reading the Reports

`claim_gate_report.md` shows the conservative claim gate result, denied claims, reason codes, and metric bridge gate status. Missing labels, missing kappa, missing or stale metric bridge evidence, and operator-required phases remain visible as limitations.

`proxy_regime_matrix.md` summarizes proxy/synthetic diagnostic rows and boundary rows. Proxy-regime certification is not deployed V-information certification.

`replay_package/replay_package_summary.md` summarizes replay package completeness, projection bundle hashes, denied claims, and replay limitations. Replay package completeness is not scientific validation.

`paper_evidence_summary.md` converts the replay package into manuscript-facing tables and limitations. Paper-facing summaries do not upgrade claim levels.

## Claim Boundary

- P17 is offline runtime-audit evidence only.
- P17 is not scientific validation.
- P17 does not claim `measurement_validated`.
- Synthetic success does not certify deployed V-information submodularity.
- Replay package completeness does not imply scientific validation.
- Paper-facing summaries do not upgrade claim levels.
- Engineering success is not scientific validation.
- Live API success alone does not imply measurement validation.
- External runtime success alone does not imply measurement validation.

P04 remains deferred/operator-required. P09 remains `BLOCKED_OPERATOR_REQUIRED`.

## Determinism

The demo uses deterministic local fake provider inputs from the P11 smoke path. It uses stable JSON serialization, stable Markdown output, stable output file ordering, and stable reason-code ordering. It uses no timestamps, UUIDs, randomness, network calls, external SDK imports, live cohort execution, external runtime integration, or `reference/` access.

## Validation

Recommended checks:

```powershell
python -m compileall cps scripts
pytest tests/test_end_to_end_evidence_demo.py -q
pytest tests/test_provider_candidate_normalizer.py -q
pytest tests/test_provider_offline_smoke.py -q
pytest tests/test_evidence_ledger.py -q
pytest tests/test_claim_gate_report.py -q
pytest tests/test_metric_bridge_gate.py -q
pytest tests/test_proxy_regime_matrix.py -q
pytest tests/test_replay_evidence_package.py -q
pytest tests/test_paper_evidence_summary.py -q
pytest tests/test_synthetic_regime_benchmark.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```
