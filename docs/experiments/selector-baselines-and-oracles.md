# Selector Baselines And Oracles

## Purpose

P06 adds optional offline adapters for comparing native CPS synthetic benchmark behavior against external-style selector and oracle baselines. These adapters are engineering diagnostics for synthetic and replay experiments only.

They do not change live cohort defaults, scientific gates, P04 status, or claim levels.

## Optional Dependency Policy

- `submodlib` and OR-Tools are not required dependencies.
- Importing `cps.selectors` must work when optional packages are absent.
- Optional imports happen lazily inside adapter functions.
- Missing packages are reported as structured unavailable results unless strict mode is requested.
- Dependencies must not be installed automatically during this phase.
- Local ZIP references under `reference/` may inform architecture only; they must not be imported, copied, executed, or vendored.

## Submodlib Selector Role

The submodlib adapter provides a facility-location selector baseline when `submodlib` is available. It accepts candidate IDs, token costs, a budget, and either feature or similarity data.

When unavailable, the adapter returns:

- `selector_available: false`
- empty `selected_ids`
- all candidates in `excluded_ids`
- `unavailable_reason: submodlib is not installed`

The native synthetic benchmark selector remains the default.

## OR-Tools Oracle Role

The OR-Tools adapter provides a CP-SAT oracle for small budgeted selection instances when OR-Tools is available. It supports a modular knapsack objective and guarded pairwise bonuses.

When unavailable, the adapter returns:

- `oracle_available: false`
- `solver_status: unavailable`
- empty `selected_ids`
- `unavailable_reason: ortools is not installed`

The existing stdlib brute-force oracle remains the default small-instance oracle.

## Synthetic Benchmark Integration

The synthetic benchmark accepts optional config fields:

- `selector_backend`: `native_greedy` or `submodlib`
- `oracle_backend`: `brute_force`, `ortools`, or `none`
- `strict_optional_dependencies`: `false` by default

Optional selector/oracle results are recorded as sidecar diagnostics in `diagnostics.jsonl`, `summary.json`, and `ProjectionBundleV1` payloads. They do not replace the default projection plan unless future phases explicitly request a guarded behavior change.

## Claim Boundary

Optional selector and oracle results are offline engineering baselines. They must not be reported as deployed V-information certification and must never produce `measurement_validated`.

P04 scientific closure remains deferred and operator-required. Synthetic or replay adapter success does not satisfy contamination, human annotation, kappa, or metric bridge gates.
