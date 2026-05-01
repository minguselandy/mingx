# Phase Review

```yaml
phase_id: P03
verdict: ACCEPT
next_phase_allowed: true
next_phase_id: P04
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

phase_id: P03
phase_title: Follow-up CLI
verdict: ACCEPT

## Summary

summary: Added a command-line entry point for `cps.runtime.followup` that wraps `build_followup_package`, requires an operator decision sheet, returns success only for execution-ready packages, and never runs cohorts or live APIs.

## Files changed

files_changed:

- `cps/runtime/followup.py`
- `tests/test_phase1_followup.py`
- `docs/reviews/P03-review.md`

## Commands run

commands_run:

- `git status --short`
- `python scripts/framework_guard.py status`
- `python scripts/framework_guard.py validate --profile target`
- `pytest tests/test_phase1_followup.py -q` before implementation, expected RED for missing CLI `main`
- `pytest tests/test_phase1_followup.py -q`
- `python -m compileall cps scripts`
- `pytest tests/test_phase1_contamination.py -q`
- `pytest tests/test_phase1_bridge.py -q`
- `pytest tests/test_phase1_annotation.py -q`
- `pytest tests/test_projection_bundle_v1.py -q`
- `pytest tests/test_mock_cohort_projection_export.py -q`

## Test results

test_results:

- RED check: `pytest tests/test_phase1_followup.py -q` failed with four expected `AttributeError` failures because `cps.runtime.followup.main` was missing.
- `python scripts/framework_guard.py validate --profile target`: passed.
- `python -m compileall cps scripts`: passed.
- `pytest tests/test_phase1_followup.py -q`: 13 passed.
- `pytest tests/test_phase1_contamination.py -q`: 2 passed.
- `pytest tests/test_phase1_bridge.py -q`: 4 passed.
- `pytest tests/test_phase1_annotation.py -q`: 2 passed.
- `pytest tests/test_projection_bundle_v1.py -q`: 16 passed.
- `pytest tests/test_mock_cohort_projection_export.py -q`: 5 passed.

## Artifacts created

artifacts_created:

- Follow-up CLI wrapper exposed through `python -m cps.runtime.followup`.
- CLI tests for success, missing arguments, invalid replacement manifests, non-execution-ready packages, and no cohort execution.
- P03 review report.

## State transition

state_transition: READY -> REVIEW -> ACCEPT

## Dependency changes

dependency_changes: none

## License impact

license_impact: none

## Safety impact

safety_impact: none. The CLI builds and validates package artifacts only; it does not run cohorts, live APIs, or external services.

## Determinism impact

determinism_impact: deterministic local CLI behavior around existing package generation. Existing generated package timestamps remain part of the pre-existing follow-up package writer semantics and were not changed.

## Scientific gate impact

- contamination semantics changed: no
- annotation requirement changed: no
- kappa requirement changed: no
- bridge requirement changed: no
- measurement_validated claimed: no
- live follow-up executed: no
- cohorts executed by CLI: no

## Risks

risks:

- The CLI can create a non-execution-ready package before returning a nonzero exit code when the decision sheet is present but fails readiness checks. This preserves existing package-generation semantics while making automation fail closed.
- P04 remains operator-required because scientific closure requires fresh follow-up execution and evidence review.

## Required follow-ups

required_followups:

- Operator approval is required before P04 scientific closure work.
- Do not run live follow-up from this CLI without explicit operator approval through the normal cohort entry point.

## Next phase

next_phase_allowed: true
next_phase_id: P04
reason: P03 implementation and focused checks passed, and P04 is an operator-required scientific closure gate rather than an auto-executed development phase.
