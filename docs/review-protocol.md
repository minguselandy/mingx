# Review Protocol

Every completed phase must produce a review report under `docs/reviews/`.

## Required Fields

The top of every review must contain a fenced `yaml` metadata block:

```yaml
phase_id: <PHASE_ID>
verdict: ACCEPT
next_phase_allowed: true
next_phase_id: <NEXT_PHASE_ID or null>
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

`scripts/framework_guard.py can-advance --review <path>` requires this metadata block. Missing metadata fails closed, and review prose alone is not sufficient for auto-advance.

Human-readable review sections must still include:

- `phase_id`
- `phase_title`
- `verdict`
- `summary`
- `files_changed`
- `commands_run`
- `test_results`
- `artifacts_created`
- `state_transition`
- `dependency_changes`
- `license_impact`
- `safety_impact`
- `determinism_impact`
- `risks`
- `required_followups`
- `next_phase_allowed`
- `next_phase_id`
- `reason`

## Verdict Enum

- `ACCEPT`: Phase meets the plan and required checks pass.
- `ACCEPT_WITH_NOTES`: Phase is acceptable with documented non-blocking notes.
- `REQUEST_CHANGES`: Phase needs fixes before acceptance.
- `BLOCKED_OPERATOR_REQUIRED`: Automation must stop for human/operator action.
- `REJECT`: Phase conflicts with constraints or should not proceed.

## Review Rules

- The review must be artifact-first: cite created files, state files, and check results.
- The reviewer must not implement fixes in the same review step.
- Missing required checks must be documented with a reason.
- License, credential, live API, external service, scientific claim, and human review risks must block automation.
- Accepting reviews do not imply merge readiness.

## Machine-Readable Convention

Review files must keep the required fenced `yaml` metadata block near the top of the file. The guard parses that block with a simple line-based parser and accepts only explicit safe values for auto-advance.
