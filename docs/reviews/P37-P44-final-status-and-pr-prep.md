# P37-P44 Final Status and PR Prep

Run timestamp: 2026-05-05T03:02:49.1524352+08:00

## Scope

This final prep pass summarizes the completed no-git DEV phases in `mingx-dev`.
It does not modify implementation code, does not touch the original repo, and does not perform any Git operation.

## Completed DEV Phases

| Phase | Result | Live API | Validation |
| --- | --- | --- | --- |
| P41_DEV_ROUTE_B_MODEL_ADJUDICATED_EVALUATION | completed | skipped | compileall passed; focused Route B tests passed; full pytest passed with 430 passed, 4 skipped |
| P42_DEV_REDUCED_SCOPE_LIVE_SMOKE | completed | skipped | API profile inspection passed; compileall passed; focused offline/live-gate tests passed; full pytest passed with 430 passed, 4 skipped |
| P43_DEV_REALISTIC_TASK_CONTEXT_PROJECTION_BENCHMARK | completed | skipped | compileall passed; focused Phase C benchmark tests passed; full pytest passed with 435 passed, 4 skipped |
| P44_DEV_MANUSCRIPT_EVIDENCE_INTEGRATION | completed | skipped | compileall passed; focused manuscript/framing tests passed; full pytest passed with 435 passed, 4 skipped |

## Files Changed By Phase

### P41

- `cps/experiments/route_b_evidence_package.py`
- `tests/test_route_b_evidence_package.py`
- `docs/experiments/P41-route-b-model-adjudicated-evaluation-plan.md`
- `docs/reviews/P41-route-b-model-adjudicated-evaluation-review.md`

### P42

- `docs/experiments/P42-fresh-reduced-scope-follow-up-batch-plan.md`
- `docs/reviews/P42-follow-up-live-batch-decision-review.md`

### P43

- `cps/experiments/phase_c_benchmark.py`
- `tests/test_phase_c_benchmark.py`
- `docs/experiments/P43-phase-c-realistic-task-context-projection-benchmark-plan.md`
- `docs/reviews/P43-phase-c-benchmark-readiness-review.md`

### P44

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper/P44-manuscript-evidence-integration-plan.md`
- `docs/reviews/P44-manuscript-evidence-integration-review.md`

### Final Prep

- `docs/reviews/P37-P44-final-status-and-pr-prep.md`

Local automation state files under `.codex/automation-state/` are intentionally excluded from the manual commit list.

## Claim Boundary Matrix

| Boundary | Status |
| --- | --- |
| No fabricated human labels | preserved |
| No fabricated kappa | preserved |
| No fabricated contamination pass | preserved |
| No fabricated fresh metric bridge | preserved |
| No `measurement_validated` claim | preserved |
| No scientific validation claim | preserved |
| No deployed V-information certification claim | preserved |
| Route B ceiling | `model_adjudicated_pilot_only` or `operational_utility_only` |
| P04 | deferred/operator-required |
| P09 | BLOCKED_OPERATOR_REQUIRED |

## Manual Commit Backlog

Suggested commit sequence:

1. P41 Route B model-adjudicated evidence package
2. P42 reduced-scope live-smoke decision docs
3. P43 realistic-task context projection benchmark scaffold
4. P44 manuscript evidence integration
5. P37-P44 final status and PR prep

Do not commit:

- `.codex/automation-state/`
- `.uv-cache/`
- `__pycache__/`
- `.env`
- secrets
- raw provider responses
- caches
- checkpoints
- large volatile artifacts

## Manual Sync Backlog

The operator should manually sync accepted DEV changes to the original repo after review:

- P40_SYNC_TO_ORIGINAL
- P41_SYNC_TO_ORIGINAL
- P42_SYNC_TO_ORIGINAL
- P43_SYNC_TO_ORIGINAL
- P44_SYNC_TO_ORIGINAL

Original repo target remains `C:\Users\Mingx\Documents\mx-codex\mingx`.

## Manual Commit Instructions

From `C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev`, review only the intended phase files above, then create manual commits in the suggested sequence. Exclude all local automation state and volatile artifacts.

## Manual Sync Instructions

After DEV commits are reviewed and accepted, copy or cherry-pick the accepted DEV changes into the original repo manually. Re-run the relevant validation in the original repo before pushing. Keep P04 deferred/operator-required and P09 BLOCKED_OPERATOR_REQUIRED unless the operator supplies the missing evidence.

## PR Body Draft

Title: P37-P44 DEV evidence package and manuscript integration

Summary:

- Adds Route B model-adjudicated evidence packaging with explicit pilot-only and operational-utility claim ceilings.
- Documents the reduced-scope live-smoke gate outcome without running live API calls.
- Adds a deterministic realistic-task context projection benchmark scaffold.
- Integrates P41-P43 evidence into manuscript-facing docs without upgrading validation claims.

Validation:

- `python -m compileall cps scripts`
- `uv run pytest tests/test_route_b_evidence_package.py -q`
- `UV_CACHE_DIR=.uv-cache uv run pytest -q tests/test_phase1_request_builder.py tests/test_phase1_backend_runtime.py tests/test_controlled_live_pilot.py`
- `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_phase_c_benchmark.py -q`
- `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_manuscript_tables.py tests/test_paper_evidence_summary.py tests/test_revised_framing_guardrails.py -q`
- `UV_CACHE_DIR=.uv-cache uv run pytest -q`

Claim boundaries:

- This PR does not fabricate human labels, kappa, contamination pass, or fresh metric bridge evidence.
- This PR does not claim `measurement_validated`, scientific validation, or deployed V-information certification.
- Route B remains capped at `model_adjudicated_pilot_only` or `operational_utility_only`.
- P04 remains deferred/operator-required.
- P09 remains BLOCKED_OPERATOR_REQUIRED.

Live API:

- Skipped. P42 live gates were not satisfied, and no raw provider responses were written.
