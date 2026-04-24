# Project Docs

This repository is now documented as a full project instead of a pair of
long-lived `phase0` / `phase1` code roots.

## Read These First

- [architecture.md](./architecture.md)
  Explains the code layout, artifact layout, and migration direction.
- [archive/final_paper_context_projection_submission_final_v8.md](./archive/final_paper_context_projection_submission_final_v8.md)
  Current canonical paper framing: conditional theory, bridge statement,
  runtime observability requirements, and extraction as a separate bridge risk.
- [phase1-implementation-completion-report.md](./phase1-implementation-completion-report.md)
  Summarizes what has been implemented and locally verified for the current
  Phase 1 development plan.
- [phase1-live-mini-batch-report.md](./phase1-live-mini-batch-report.md)
  Summarizes the completed reduced-scope live mini-batch run and its current
  scientific gate outcome.
- [current-work-summary.md](./current-work-summary.md)
  Consolidated summary of the currently completed runtime, triage, reprobe, and
  replacement work.
- [project-reading-prompt.md](./project-reading-prompt.md)
  Copy-paste onboarding prompt for another AI agent to read the repository in
  the right order and with the right gate semantics.
- [recent-change-handoff-prompt.md](./recent-change-handoff-prompt.md)
  Copy-paste prompt focused on the recent repo modifications and current
  runtime assumptions.
- [phase1-usable-models.md](./phase1-usable-models.md)
  Regenerated live probe report listing models that currently satisfy the
  Phase 1 logprob contract.
- [../api/README.md](../api/README.md)
  Explains API profiles, backend factories, and provider/model resolution.
- [../configs/runs/README.md](../configs/runs/README.md)
  Lists the canonical run-plan entrypoints.
- [protocols/execution-readiness-checklist.md](./protocols/execution-readiness-checklist.md)
  Highest-priority execution-order and gate document.
- [protocols/phase1-protocol.md](./protocols/phase1-protocol.md)
  Phase 1 measurement-chain, bridge, and annotation constraints.
- [protocols/phase1-contamination-triage-and-question-rewrite.md](./protocols/phase1-contamination-triage-and-question-rewrite.md)
  Human-in-the-loop workflow for AI-assisted contamination judgement and
  minimal question rewrite planning after gate failure.

## Documentation Layers

- `protocols/`
  Active protocol documents that guide implementation and execution.
- `archive/`
  The final v8 paper is the current research-framing anchor. Older paper
  drafts in this directory are historical reference material, not default
  implementation entrypoints.

## Code Semantics

`api/` owns provider/model profiles, backend factories, and API smoke helpers.

`cps/` is now the canonical implementation package.

`phase0/` and `phase1/` remain in the repository as compatibility shims so
existing tests, imports, and runtime commands do not break during migration.

Until the migration is fully complete, keep these rules:

- Prefer `cps.*` for new imports
- Prefer `api/*` for provider/model switching instead of adding provider
  branches to runtime entrypoints
- Keep `events.jsonl` as source of truth
- Do not break existing live plans or run artifacts
