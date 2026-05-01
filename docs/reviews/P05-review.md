# Phase Review

```yaml
phase_id: P05
verdict: ACCEPT
next_phase_allowed: true
next_phase_id: P06
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

phase_id: P05
phase_title: Synthetic regime benchmark
verdict: ACCEPT

## Summary

summary: P05 implemented the offline synthetic regime benchmark extensions. The existing benchmark now supports configurable deterministic synthetic regimes, brute-force small-instance oracle summaries, ProjectionBundleV1 JSONL rows and events, conservative metric claim levels, and documentation of the synthetic-only claim boundary.

This is offline engineering work only. It does not change P04 scientific status, does not run live APIs, does not fill labels, does not compute kappa, does not validate a bridge, and does not claim `measurement_validated`.

## Files changed

files_changed:

- `cps/experiments/synthetic_regimes.py`
- `cps/experiments/selection.py`
- `cps/experiments/synthetic_benchmark.py`
- `cps/experiments/artifacts.py`
- `cps/experiments/reporting.py`
- `tests/test_synthetic_regime_benchmark.py`
- `docs/experiments/synthetic-regime-benchmark.md`
- `docs/protocols/synthetic-regime-benchmark.md`
- `docs/reviews/P05-review.md`

## Commands run

commands_run:

- `git status --short`
- `python scripts/framework_guard.py status`
- `python scripts/framework_guard.py validate --profile target`
- `pytest tests/test_synthetic_regime_benchmark.py -q`
- `pytest tests/test_projection_bundle_v1.py -q`
- `pytest tests/test_mock_cohort_projection_export.py -q`
- `pytest tests/test_projection_artifacts.py -q`
- `pytest tests/test_phase_b_replay.py -q`
- `pytest tests/test_synthetic_regimes.py -q`
- `pytest tests/test_experiment_diagnostics.py -q`
- `python -m compileall cps scripts`

## Test results

test_results:

- `python scripts/framework_guard.py status`: passed; current phase was P05 READY.
- `python scripts/framework_guard.py validate --profile target`: passed.
- `python -m compileall cps scripts`: passed.
- `pytest tests/test_synthetic_regime_benchmark.py -q`: passed, 16 tests.
- `pytest tests/test_projection_bundle_v1.py -q`: passed, 16 tests.
- `pytest tests/test_mock_cohort_projection_export.py -q`: passed, 5 tests.
- `pytest tests/test_projection_artifacts.py -q`: passed, 2 tests.
- `pytest tests/test_phase_b_replay.py -q`: passed, 10 tests.
- `pytest tests/test_synthetic_regimes.py -q`: passed, 2 tests.
- `pytest tests/test_experiment_diagnostics.py -q`: passed, 12 tests.
- Optional `pytest tests/test_revised_framing_guardrails.py -q` was run and failed on pre-existing AGENTS/docs/codex wording outside P05 scope; P05 did not modify `docs/codex/`.

## Artifacts created

artifacts_created:

- `docs/experiments/synthetic-regime-benchmark.md`
- P05 benchmark output support for `projection_bundles.jsonl`.
- P05 benchmark event support for `projection_bundle_materialized`.
- Tests covering deterministic generation, oracle behavior, projection bundle reconstruction, forbidden claim levels, and no reference/live API access.

## State transition

state_transition: P05 READY -> P05 ACCEPT; P06 may be activated only after `framework_guard.py can-advance` passes.

## Dependency changes

dependency_changes: none

## License impact

license_impact: none

## Safety impact

safety_impact: none

No external reference code was copied, imported, executed, or made a dependency. The implementation uses native mingx code and Python stdlib paths already present in the project.

## Determinism impact

determinism_impact: deterministic local files only. Synthetic instance generation is seed-controlled, JSONL outputs use stable serialization, and each `ProjectionBundleV1` row carries a canonical hash.

## Scientific gate impact

- contamination semantics changed: no
- annotation requirement changed: no
- kappa requirement changed: no
- bridge requirement changed: no
- `measurement_validated` claimed: no
- P04 scientific closure status changed: no

## Risks

risks:

- P05 oracle coverage is brute-force only for small instances and intentionally skips larger instances.
- The synthetic benchmark remains structural and offline; it must not be interpreted as deployed V-information certification.
- The broader revised-framing guardrail suite still has pre-existing failures in forbidden/baseline docs outside this phase.

## Required follow-ups

required_followups:

- P06 may add optional selector baselines and exact oracle adapters only if optional dependencies remain guarded.
- P04 scientific closure must be revisited before any scientific validation claim.

## Next phase

next_phase_allowed: true
next_phase_id: P06
reason: P05 implementation and focused validation passed, no dependencies were added, no live APIs or external references were used, and no scientific gate semantics were changed.
