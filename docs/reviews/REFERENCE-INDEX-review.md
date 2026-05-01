# Phase Review

```yaml
phase_id: REFERENCE-INDEX
verdict: ACCEPT_WITH_NOTES
next_phase_allowed: false
next_phase_id: P02
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

phase_id: REFERENCE-INDEX
phase_title: Local ZIP reference indexing
verdict: ACCEPT_WITH_NOTES

## Summary

summary: Documented ZIP-extracted local reference repositories under `reference/`, added local ignore coverage through `.git/info/exclude`, and added narrow policy notes to `AGENTS.md` and future reference-dependent phases. Commit SHAs are unavailable because the references are ZIP extractions without `.git` metadata.

## Files changed

files_changed:

- .git/info/exclude
- AGENTS.md
- docs/phase-plan.md
- docs/reference-projects-local.md
- docs/reviews/REFERENCE-INDEX-review.md

## Commands run

commands_run:

- git status --short
- python scripts/framework_guard.py status
- python scripts/framework_guard.py validate --profile target
- Get-ChildItem -Force -Name reference
- Get-Content -Raw .git/info/exclude
- Test-Path checks for `.git` metadata in each extracted reference project
- python -m compileall scripts
- git check-ignore -v reference/graphiti-main.zip

## Test results

test_results:

- Target-profile validation passed before and after the maintenance update.
- `python -m compileall scripts` passed.
- `git check-ignore -v reference/graphiti-main.zip` confirmed `/reference/` is ignored by `.git/info/exclude`.

## Artifacts created

artifacts_created:

- `docs/reference-projects-local.md`
- `docs/reviews/REFERENCE-INDEX-review.md`

## State transition

state_transition: none; repository remains at P02 READY.

## Dependency changes

dependency_changes: none

## License impact

license_impact: none

## Safety impact

safety_impact: none

## Determinism impact

determinism_impact: documentation-only maintenance with no generated runtime artifacts.

## Risks

risks:

- Commit SHAs are unavailable for the local references because they were extracted from ZIP archives and contain no `.git` metadata.

## Required follow-ups

required_followups:

- Keep `reference/` read-only and untracked.
- Perform license review before copying any external code, which this maintenance step did not do.

## Next phase

next_phase_allowed: false
next_phase_id: P02
reason: This was out-of-band reference maintenance and did not advance or implement the current CPS phase.
