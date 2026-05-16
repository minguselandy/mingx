# Codex guidance system for mingx

This directory defines the control system for Codex-assisted development.

## Files

- `phase-development-guidance.md`
  Instructions for implementation agents.

- `phases/phase-b-replay-readiness.md`
  Phase-specific boundary and status rules for Phase B.

- `v12-phase-docs/`
  Completed P45-P50 Codex development/reference package for v12 evidence/audit
  scaffold work. P45-P50 are reference material, not current execution plans.
  The current P45 `bio_attribute` stratum is non-calibrated; its negative
  result is fail-closed claim-gate evidence, not bridge support.

- `post-development-review-agent.md`
  Instructions for a separate review agent that audits Codex-generated diffs.

- `guidance-document-review.md`
  Instructions for reviewing the guidance documents themselves before using them.

- `prompts/`
  Reusable prompt files for implementation, post-development review, and guidance review.

## Intended workflow

1. For current v12 follow-up work, start from
   `../experiments/P51-P60-v12-followup-dev-experiment-plan.md` and
   `../reviews/P51-P60-v12-review-claim-gate-protocol.md`.
2. Treat `v12-phase-docs/README.md` as the completed P45-P50 scaffold
   reference package. Do not expand the same P45 `bio_attribute` stratum by
   inertia.
3. P51 state reconciliation is completed and independently reviewed with
   `ACCEPT_WITH_NOTES`.
4. The immediate next active development phase is P52 manuscript proof repair
   and evidence-state integration.
5. P53 diagnostic threshold contract follows P52.
6. Run guidance-document review when guidance changes.
7. Give Codex one bounded development task.
8. Run focused tests and guardrail tests.
9. Run the matching review document after implementation.
10. Merge only after tests and review pass.

## Separation of duties

Guidance authoring, implementation, and review are separate roles.

Codex may automate code development, but it must not automate scientific claim expansion.
The v12 phase docs do not claim `measurement_validated` evidence and do not
supply bridge calibration results by themselves.
