# Codex guidance system for mingx

This directory defines the control system for Codex-assisted development.

## Files

- `phase-development-guidance.md`
  Instructions for implementation agents.

- `phases/phase-b-replay-readiness.md`
  Phase-specific boundary and status rules for Phase B.

- `post-development-review-agent.md`
  Instructions for a separate review agent that audits Codex-generated diffs.

- `guidance-document-review.md`
  Instructions for reviewing the guidance documents themselves before using them.

- `prompts/`
  Reusable prompt files for implementation, post-development review, and guidance review.

## Intended workflow

1. Write or update phase guidance.
2. Run guidance-document review.
3. Revise guidance until approved.
4. Give Codex one bounded development task.
5. Run focused tests and guardrail tests.
6. Run the post-development review agent.
7. Merge only after tests and review pass.

## Separation of duties

Guidance authoring, implementation, and review are separate roles.

Codex may automate code development, but it must not automate scientific claim expansion.
