# P43 Phase C Benchmark Readiness Review


## Verdict

- Verdict: `ACCEPT`
- Reviewer: Codex automation
- Date: 2026-05-05
- Branch: no-git direct development
- Commit range: none; operator will commit manually

Allowed verdicts:

- `ACCEPT`
- `ACCEPT_WITH_MINOR_REVISIONS`
- `ACCEPT_WITH_MAJOR_REVISIONS`
- `REJECT_UNSAFE_OVERCLAIM`
- `REJECT_INCOMPLETE_ARTIFACTS`
- `PENDING_REVIEW`

## Claim Boundary Review

Confirm:

- [x] no live API was run unless the milestone explicitly allowed it and approval was recorded
- [x] no human labels were fabricated
- [x] no human-human kappa was fabricated
- [x] no `measurement_validated` claim was made unless all required gates were satisfied
- [x] synthetic evidence was not described as deployed V-information certification
- [x] replay evidence was not described as scientific validation
- [x] Route B/model-adjudicated labels were not described as human labels
- [x] contamination failures, if present, caused `pilot_only` / scientific-stop interpretation


## Scope

Review whether the realistic-task context-projection benchmark is ready to run or interpret.

P43 implements a deterministic offline scaffold in
`cps/experiments/phase_c_benchmark.py`. The scaffold uses two fixture tasks and
four separated conditions:

- `no_cps_baseline`
- `heuristic_selector_baseline`
- `cps_runtime_audit_scaffold`
- `diagnostic_guided_escalation`

The scaffold writes replay-compatible artifacts to a caller-provided output
directory and reports task support metrics as `operational_utility_only`.

## Readiness Gates

- [x] P39 artifact schema freeze complete
- [x] P40 Phase B replay works on at least synthetic artifacts
- [x] candidate-pool builder implemented
- [x] benchmark conditions specified
- [x] metric bridge assignment implemented
- [x] task metrics separated from structural diagnostics
- [x] output artifacts are replayable
- [x] claim boundary included in report template

## Condition Table

| Condition | Implemented? | Artifact-complete? | Metric scope | Notes |
|---|---|---|---|---|
| `no_cps_baseline` | yes | yes | `operational_utility_only` | fixed author-order packing baseline |
| `heuristic_selector_baseline` | yes | yes | `operational_utility_only` | heuristic score-density packing baseline |
| `cps_runtime_audit_scaffold` | yes | yes | `operational_utility_only` | audited singleton-value greedy scaffold |
| `diagnostic_guided_escalation` | yes | yes | `operational_utility_only` | optional synergy-seeded escalation path |

## Required Conclusion

Phase C is ready as an offline dry-run scaffold. It can write replay-compatible
artifact records and can be interpreted for operational utility only. It should
not be interpreted as measurement validation, deployed V-information
certification, or scientific validation.

## Files Changed

- `cps/experiments/phase_c_benchmark.py`
- `tests/test_phase_c_benchmark.py`
- `docs/experiments/P43-phase-c-realistic-task-context-projection-benchmark-plan.md`
- `docs/reviews/P43-phase-c-benchmark-readiness-review.md`

## Validation

Commands run:

```text
python -m compileall cps scripts
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_phase_c_benchmark.py -q
UV_CACHE_DIR=.uv-cache uv run pytest -q
```

Results:

- `python -m compileall cps scripts`: passed
- `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_phase_c_benchmark.py -q`: `5 passed`
- `UV_CACHE_DIR=.uv-cache uv run pytest -q`: `435 passed, 4 skipped`

Risky claim scan was run over changed P43 files for:

```text
measurement_validated
scientific validation
deployed V-information certification
Vinfo_proxy_certified
certified greedy-valid
human labels
kappa
pilot_only
model_adjudicated_pilot_only
operational_utility_only
```

All occurrences are denied claims, boundary conditions, claim-gate rules,
explicit non-claims, Route B ceilings, or pilot ceilings.
