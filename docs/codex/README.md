# Codex guidance system for mingx

This directory defines the control system for Codex-assisted development.

## Files

- `phase-development-guidance.md`
  Instructions for implementation agents.

- `phases/phase-b-replay-readiness.md`
  Phase-specific boundary and status rules for Phase B.

- `v12-phase-docs/`
  Controlling P45-P50 Codex development/reference package for v12 follow-up
  work. P45 is the next priority; P50 is optional and must not precede
  P45-P49.

- `post-development-review-agent.md`
  Instructions for a separate review agent that audits Codex-generated diffs.

- `guidance-document-review.md`
  Instructions for reviewing the guidance documents themselves before using them.

- `prompts/`
  Reusable prompt files for implementation, post-development review, and guidance review.

## Intended workflow

1. For v12 follow-up work, start from `v12-phase-docs/README.md`.
2. Use `P45-one-stratum-bridge-calibration-plan.md` as the next bounded task.
3. Do not run P50 before P45-P49 are complete or explicitly deferred.
4. Run guidance-document review when guidance changes.
5. Give Codex one bounded development task.
6. Run focused tests and guardrail tests.
7. Run the matching review document after implementation.
8. Merge only after tests and review pass.

## Separation of duties

Guidance authoring, implementation, and review are separate roles.

Codex may automate code development, but it must not automate scientific claim expansion.
The v12 phase docs do not claim `measurement_validated` evidence and do not
supply bridge calibration results by themselves.
