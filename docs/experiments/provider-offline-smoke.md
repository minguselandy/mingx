# Provider-to-Selector Offline Smoke Path

## Purpose

The P11 provider offline smoke path checks that fake/local provider candidates can move through the CPS adapter boundary, the P10 candidate normalizer, and a selector/materializer-compatible artifact path.

This is engineering smoke evidence only. It is not live cohort execution, external runtime integration, measurement validation, or deployed V-information certification.

## Flow

The smoke runner creates deterministic fake provider records for Graphiti-style memory facts and LangExtract-style extraction spans. It converts them with the P08 provider adapters, normalizes them with `normalize_candidate_pool(...)`, and then builds replayable CPS artifacts:

- provider candidates
- normalized candidates
- candidate pools
- projection plans
- budget witnesses
- materialized contexts
- metric bridge witnesses
- diagnostics
- projection bundles
- summary

Selection uses deterministic input-order first-fit under the configured token budget. The algorithm name is `deterministic_provider_smoke_first_fit`. It is a compatibility smoke path, not an optimization claim.

## Claim Boundary

The only allowed claim level is:

```text
engineering_smoke_only
```

The smoke path does not validate measurement, certify V-information, certify submodularity, certify metric bridge freshness, certify deployment claims, unblock P04, or unblock P09.

P04 remains deferred/operator-required. P09 remains `BLOCKED_OPERATOR_REQUIRED`. `measurement_validated` is not claimed.

## Validation

Recommended checks:

```powershell
python -m compileall cps scripts
pytest tests/test_provider_adapters.py -q
pytest tests/test_provider_candidate_normalizer.py -q
pytest tests/test_provider_offline_smoke.py -q
pytest tests/test_projection_bundle_v1.py -q
pytest tests/test_projection_artifacts.py -q
pytest tests/test_selector_optional_adapters.py -q
pytest tests/test_synthetic_regime_benchmark.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

The runner is offline-only and uses no external SDKs, network calls, live APIs, live cohort execution, or `reference/` code.
