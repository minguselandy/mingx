# Phase Review

```yaml
phase_id: P11
verdict: ACCEPT
next_phase_allowed: true
next_phase_id: P12
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

phase_id: P11
phase_title: Provider-to-Selector Offline Smoke Path
verdict: ACCEPT

## Summary

summary: P11 adds an offline provider-to-selector smoke path that converts fake Graphiti-style and LangExtract-style records into provider candidates, normalizes them through the P10 alias bridge, and materializes complete replayable CPS artifacts with ProjectionBundleV1 coverage. The claim level is `engineering_smoke_only`.

## Files changed

files_changed:

- `cps/experiments/provider_offline_smoke.py`
- `tests/test_provider_offline_smoke.py`
- `docs/experiments/provider-offline-smoke.md`
- `docs/reviews/P11-review.md`

## Commands run

commands_run:

- `git status --short`
- `git branch --show-current`
- `git log --oneline -8`
- `python scripts/framework_guard.py status`
- `python scripts/framework_guard.py validate --profile target`
- `python -m compileall cps scripts`
- `pytest tests/test_provider_adapters.py -q`
- `pytest tests/test_provider_candidate_normalizer.py -q`
- `pytest tests/test_provider_offline_smoke.py -q`
- `pytest tests/test_projection_bundle_v1.py -q`
- `pytest tests/test_projection_artifacts.py -q`
- `pytest tests/test_selector_optional_adapters.py -q`
- `pytest tests/test_synthetic_regime_benchmark.py -q`

## Test results

test_results:

- `python -m compileall cps scripts`: passed.
- `pytest tests/test_provider_adapters.py -q`: 9 passed.
- `pytest tests/test_provider_candidate_normalizer.py -q`: 20 passed.
- `pytest tests/test_provider_offline_smoke.py -q`: 7 passed.
- `pytest tests/test_projection_bundle_v1.py -q`: 16 passed.
- `pytest tests/test_projection_artifacts.py -q`: 3 passed.
- `pytest tests/test_selector_optional_adapters.py -q`: 9 passed, 2 skipped because optional dependencies are absent.
- `pytest tests/test_synthetic_regime_benchmark.py -q`: 18 passed.
- `python scripts/framework_guard.py status`: P09 `BLOCKED_OPERATOR_REQUIRED`.
- `python scripts/framework_guard.py validate --profile target`: passed.

## Artifacts created

artifacts_created:

- No persistent experiment artifacts were created in the repo.
- Tests create temporary provider smoke outputs only under pytest temporary directories.
- The smoke runner can emit `provider_candidates.jsonl`, `normalized_candidates.jsonl`, projection artifacts, `projection_bundles.jsonl`, `events.jsonl`, and `summary.json` to caller-provided output directories.

## Scope and behavior

provider_adapter_behavior:

- Fake Graphiti-style and LangExtract-style inputs use the existing P08 provider adapters.
- Provider candidate payloads are normalized with `normalize_candidate_pool(...)`.
- Selection is deterministic input-order first-fit under `budget_tokens`.
- ProjectionBundleV1 payloads include canonical hashes and reconstruct in tests.
- Artifact completeness requires projection bundles and passes for the temporary smoke outputs.

claim_boundary:

- P04 remains deferred/operator-required: yes.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`: yes.
- `measurement_validated` claimed: no.
- scientific validation claimed: no.
- deployed V-information submodularity certified: no.
- engineering success reported as scientific validation: no.
- allowed claim level: `engineering_smoke_only`.

## State transition

state_transition: P09 BLOCKED_OPERATOR_REQUIRED -> P09 BLOCKED_OPERATOR_REQUIRED

## Dependency changes

dependency_changes: none

## License impact

license_impact: none

## Safety impact

safety_impact: none

## Determinism impact

determinism_impact: deterministic local fake inputs, input-order selection, stable ProjectionBundleV1 canonical hashes, no timestamps, no UUIDs, no random network-dependent behavior

## Risks

risks:

- P11 is an offline smoke path only and is not wired into live cohort defaults.
- The first-fit selector is a compatibility path, not an optimization claim.
- Optional selector/oracle dependencies remain absent and skipped in optional-adapter tests.

## Required follow-ups

required_followups:

- P12 should add the evidence ledger and conservative claim gate report.
- P04 scientific closure remains operator-required and incomplete.
- P09 runtime adapter implementation remains blocked/operator-required.

## Next phase

next_phase_allowed: true
next_phase_id: P12
reason: P11 implementation and tests passed, and claim boundaries remain conservative.
