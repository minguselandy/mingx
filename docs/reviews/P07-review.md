# Phase Review

```yaml
phase_id: P07
verdict: ACCEPT
next_phase_allowed: true
next_phase_id: P08
license_impact: none
safety_impact: none
dependency_changes: none
live_api_required: false
external_service_required: false
credential_required: false
human_review_required: false
scientific_claim_required: false
operator_required: false
```

## Verdict

phase_id: P07
phase_title: Observability exporters
verdict: ACCEPT

## Summary

summary: P07 added dependency-free dry-run observability exporters for `ProjectionBundleV1`. The implementation maps bundles to local OTel-style, Langfuse-style, and Phoenix-style dictionaries without importing external observability packages, opening sockets, reading `reference/`, or changing CPS runtime behavior.

## Files changed

files_changed:

- `cps/export/__init__.py`
- `cps/export/common.py`
- `cps/export/otel.py`
- `cps/export/langfuse.py`
- `cps/export/phoenix.py`
- `docs/experiments/observability-exporters.md`
- `tests/test_projection_exporters.py`
- `docs/reviews/P07-review.md`

## Commands run

commands_run:

- `git status --short`
- `python scripts/framework_guard.py status`
- `python scripts/framework_guard.py validate --profile target`
- `python -m compileall cps scripts`
- `pytest tests/test_projection_exporters.py -q`
- `pytest tests/test_projection_bundle_v1.py -q`
- `pytest tests/test_mock_cohort_projection_export.py -q`
- `pytest tests/test_synthetic_regime_benchmark.py -q`
- `pytest tests/test_selector_optional_adapters.py -q`
- `pytest tests/test_projection_artifacts.py -q`
- `pytest tests/test_phase_b_replay.py -q`

## Test results

test_results:

- `python scripts/framework_guard.py validate --profile target`: passed.
- `python -m compileall cps scripts`: passed.
- `pytest tests/test_projection_exporters.py -q`: 8 passed.
- `pytest tests/test_projection_bundle_v1.py -q`: 16 passed.
- `pytest tests/test_mock_cohort_projection_export.py -q`: 5 passed.
- `pytest tests/test_synthetic_regime_benchmark.py -q`: 16 passed.
- `pytest tests/test_selector_optional_adapters.py -q`: 9 passed, 2 skipped for unavailable optional dependencies.
- `pytest tests/test_projection_artifacts.py -q`: 2 passed.
- `pytest tests/test_phase_b_replay.py -q`: 10 passed.

## Artifacts created

artifacts_created:

- Local exporter package under `cps/export/`.
- P07 exporter documentation at `docs/experiments/observability-exporters.md`.
- P07 exporter unit tests at `tests/test_projection_exporters.py`.
- This P07 review at `docs/reviews/P07-review.md`.

## Exporter payload shapes

- OTel-style: `name`, `kind`, `trace_id`, `span_id`, `attributes`, and local `events`.
- Langfuse-style: dry-run `trace` and `observation` dictionaries.
- Phoenix-style: `trace_id`, `span_id`, `span_name`, `attributes`, and local evaluation-style metadata.

## Dry-run/no-network behavior

All exporters produce local dictionaries only. They do not import OpenTelemetry, Langfuse, Phoenix, or any client SDK. Langfuse non-dry-run export fails closed when no explicit client is provided, and tests guard against socket creation.

## Optional dependency behavior

dependency_changes: none. No observability package is required or imported.

## Determinism impact

determinism_impact: Exporter output is deterministic under repeated calls, includes the `ProjectionBundleV1` canonical hash, and excludes timestamps, UUIDs, credentials, full rendered context, and reference paths by default. Optional previews are bounded and deterministic.

## Scientific gate impact

- P04 remains deferred/operator-required? yes.
- contamination semantics changed? no.
- annotation requirement changed? no.
- kappa requirement changed? no.
- bridge requirement changed? no.
- measurement_validated claimed? no.
- exporter payloads claimed as scientific validation? no.

## License impact

license_impact: none. No external source code was copied or vendored.

## Safety impact

safety_impact: none. The change is offline and local-only. It does not run live APIs, model providers, Docker, external services, or reference project scripts.

## Risks

risks:

- Future network-capable observability integrations will need separate operator approval, credentials handling, and tests that keep dry-run behavior as the default.

## Required follow-ups

required_followups:

- P08 may add optional provider adapters with fake objects in tests only.
- A future phase may add a dry-run JSONL conversion CLI if needed.

## Next phase

next_phase_allowed: true
next_phase_id: P08
reason: P07 implementation and focused checks passed, no dependencies were added, and the auto-advance safety metadata is safe for P08.
