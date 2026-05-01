# Phase Review

```yaml
phase_id: P06
verdict: ACCEPT
next_phase_allowed: true
next_phase_id: P07
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

phase_id: P06
phase_title: Selector baselines and oracle
verdict: ACCEPT

## Summary

summary: P06 added optional, guarded selector/oracle adapters for offline synthetic and replay experiments. The new selector package imports safely without `submodlib` or OR-Tools installed, records unavailable optional backends deterministically, and keeps native synthetic benchmark behavior as the default.

## Files changed

files_changed:

- `cps/selectors/common.py`
- `cps/selectors/__init__.py`
- `cps/selectors/submodlib_selector.py`
- `cps/selectors/ortools_oracle.py`
- `cps/experiments/synthetic_benchmark.py`
- `tests/test_selector_optional_adapters.py`
- `docs/experiments/selector-baselines-and-oracles.md`
- `docs/reviews/P06-review.md`

## Commands run

commands_run:

- `git status --short`
- `python scripts/framework_guard.py status`
- `python scripts/framework_guard.py validate --profile target`
- `python -c "import importlib.util; ..."`
- `pytest tests/test_selector_optional_adapters.py -q`
- `pytest tests/test_synthetic_regime_benchmark.py -q`
- `pytest tests/test_projection_bundle_v1.py -q`
- `pytest tests/test_mock_cohort_projection_export.py -q`
- `pytest tests/test_projection_artifacts.py -q`
- `pytest tests/test_phase_b_replay.py -q`
- `python -m compileall cps scripts`

## Test results

test_results:

- `python scripts/framework_guard.py status`: passed; current phase was P06 READY.
- `python scripts/framework_guard.py validate --profile target`: passed.
- `python -m compileall cps scripts`: passed.
- `pytest tests/test_selector_optional_adapters.py -q`: passed, 9 passed and 2 skipped because optional dependencies are absent.
- `pytest tests/test_synthetic_regime_benchmark.py -q`: passed, 16 tests.
- `pytest tests/test_projection_bundle_v1.py -q`: passed, 16 tests.
- `pytest tests/test_mock_cohort_projection_export.py -q`: passed, 5 tests.
- `pytest tests/test_projection_artifacts.py -q`: passed, 2 tests.
- `pytest tests/test_phase_b_replay.py -q`: passed, 10 tests.

## Artifacts created

artifacts_created:

- Optional selector adapter package under `cps/selectors/`.
- Optional backend status fields in synthetic benchmark diagnostics and summary.
- Offline documentation for selector baselines and oracle adapters.

## Optional dependency behavior

optional_dependency_behavior:

- `submodlib` availability in current environment: false.
- OR-Tools availability in current environment: false.
- Missing dependencies return structured unavailable results by default.
- Strict mode fails closed with `OptionalDependencyUnavailable`.
- No dependency was installed and `pyproject.toml` was not changed.

## Submodlib adapter behavior

submodlib_adapter_behavior:

- `cps.selectors.submodlib_selector` imports without `submodlib`.
- `select_with_submodlib` lazily imports `submodlib`.
- Missing dependency is recorded as `selector_available: false`.
- If installed later, the adapter uses a facility-location selector and enforces token budget.

## OR-Tools oracle behavior

ortools_oracle_behavior:

- `cps.selectors.ortools_oracle` imports without OR-Tools.
- `solve_knapsack_with_ortools` lazily imports `ortools.sat.python.cp_model`.
- Missing dependency is recorded as `oracle_available: false` and `solver_status: unavailable`.
- If installed later, the adapter supports modular knapsack and guarded pairwise bonuses.

## Synthetic benchmark compatibility

synthetic_benchmark_compatibility:

- Default selector backend remains `native_greedy`.
- Default oracle backend remains `brute_force`.
- Optional backends are sidecar diagnostics and do not replace the default projection plan.
- `ProjectionBundleV1` rows remain reconstructable when optional backends are unavailable.

## State transition

state_transition: P06 READY -> P06 ACCEPT; P07 may be activated only after `framework_guard.py can-advance` passes.

## Dependency changes

dependency_changes: none

## License impact

license_impact: none

No external reference code was copied, vendored, imported, or executed.

## Safety impact

safety_impact: none

No live API, model provider, external service, Docker, or dependency installation was used.

## Determinism impact

determinism_impact: deterministic local files only. Optional unavailable states are stable, default native benchmark behavior remains deterministic, and optional solver tests skip when packages are absent.

## Scientific gate impact

- P04 remains deferred/operator-required? yes
- contamination semantics changed? no
- annotation requirement changed? no
- kappa requirement changed? no
- bridge requirement changed? no
- `measurement_validated` claimed? no
- optional oracle/selector results claimed as deployed V-information certification? no

## Risks

risks:

- Real `submodlib` and OR-Tools execution paths were not exercised because the packages are absent.
- Optional adapter APIs may need adjustment if future installed package versions differ.
- Optional results are engineering diagnostics only and must not be used as scientific validation.

## Required follow-ups

required_followups:

- If optional packages are installed later, run the skipped tiny adapter tests.
- P07 may add dry-run observability exporters only with no network calls in tests.
- P04 scientific closure remains deferred and must be revisited before validation claims.

## Next phase

next_phase_allowed: true
next_phase_id: P07
reason: P06 implementation and focused validation passed, optional dependencies are guarded, default behavior remains native/offline, and no scientific gate semantics changed.
