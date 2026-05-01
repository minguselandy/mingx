# Phase Review

```yaml
phase_id: P08
verdict: ACCEPT
next_phase_allowed: true
next_phase_id: P09
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

phase_id: P08
phase_title: Provider adapters
verdict: ACCEPT

## Summary

summary: P08 added pure local provider-output adapters for Graphiti-style temporal facts/episodes and LangExtract-style extraction spans/records. The adapters convert fake/local objects into native CPS candidate payloads without importing Graphiti, LangExtract, reference code, network clients, or external dependencies.

## Files changed

files_changed:

- `cps/providers/common.py`
- `cps/providers/graphiti_provider.py`
- `cps/providers/langextract_provider.py`
- `cps/providers/__init__.py`
- `docs/experiments/provider-adapters.md`
- `tests/test_provider_adapters.py`
- `docs/reviews/P08-review.md`

## Commands run

commands_run:

- `git status --short`
- `python scripts/framework_guard.py status`
- `python scripts/framework_guard.py validate --profile target`
- `pytest tests/test_provider_adapters.py -q` initial RED run
- `python -m compileall cps scripts`
- `pytest tests/test_provider_adapters.py -q`
- `pytest tests/test_projection_bundle_v1.py -q`
- `pytest tests/test_projection_exporters.py -q`
- `pytest tests/test_mock_cohort_projection_export.py -q`
- `pytest tests/test_synthetic_regime_benchmark.py -q`
- `pytest tests/test_selector_optional_adapters.py -q`
- `pytest tests/test_projection_artifacts.py -q`
- `pytest tests/test_phase_b_replay.py -q`

## Test results

test_results:

- Initial `pytest tests/test_provider_adapters.py -q`: failed as expected because provider adapter modules were missing.
- `python scripts/framework_guard.py validate --profile target`: passed.
- `python -m compileall cps scripts`: passed.
- `pytest tests/test_provider_adapters.py -q`: 9 passed.
- `pytest tests/test_projection_bundle_v1.py -q`: 16 passed.
- `pytest tests/test_projection_exporters.py -q`: 8 passed.
- `pytest tests/test_mock_cohort_projection_export.py -q`: 5 passed.
- `pytest tests/test_synthetic_regime_benchmark.py -q`: 16 passed.
- `pytest tests/test_selector_optional_adapters.py -q`: 9 passed, 2 skipped for unavailable optional dependencies.
- `pytest tests/test_projection_artifacts.py -q`: 2 passed.
- `pytest tests/test_phase_b_replay.py -q`: 10 passed.

## Artifacts created

artifacts_created:

- Native candidate conversion helpers under `cps/providers/`.
- Provider adapter documentation at `docs/experiments/provider-adapters.md`.
- Fake-object provider adapter tests at `tests/test_provider_adapters.py`.
- This P08 review at `docs/reviews/P08-review.md`.

## Provider adapter behavior

- Graphiti-style facts, episodes, and generic records convert to native candidate payloads with deterministic `content_hash`, generated `candidate_id`, provenance, metadata, confidence, and temporal validity when present.
- LangExtract-style spans, extractions, and generic records convert to native candidate payloads with document provenance, source offsets, extraction type, confidence, metadata, deterministic `content_hash`, and generated `candidate_id`.
- Adapter outputs can be embedded in a `ProjectionBundleV1` candidate pool.

## Fake-object/no-dependency behavior

Tests use dicts and simple fake objects only. The adapter modules do not import Graphiti or LangExtract packages, even lazily. No dependency installation or optional dependency configuration changed.

## Reference repo policy compliance

`reference/` was not imported, copied, executed, vendored, or treated as a dependency. The adapters are native CPS code only.

## Determinism impact

determinism_impact: Candidate IDs, content hashes, and fallback token costs are deterministic. No timestamps or UUIDs are introduced by the adapters.

## Scientific gate impact

- P04 remains deferred/operator-required? yes.
- contamination semantics changed? no.
- annotation requirement changed? no.
- kappa requirement changed? no.
- bridge requirement changed? no.
- measurement_validated claimed? no.
- provider adapter output claimed as scientific validation? no.

## License impact

license_impact: none. No external source code was copied or vendored.

## Safety impact

safety_impact: none. The change is offline and local-only. It does not run live APIs, model providers, Docker, external services, or reference project scripts.

## Risks

risks:

- Future real provider integrations must remain optional and should get separate operator review before using external services or credentials.

## Required follow-ups

required_followups:

- P09 is operator-required and should begin with a plan-only runtime adapter prototype discussion.

## Next phase

next_phase_allowed: true
next_phase_id: P09
reason: P08 implementation and focused checks passed, no dependencies were added, and all safety metadata is clear for activating P09 as operator-required.
