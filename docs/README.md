# Project Docs

This repository is now documented as a full project instead of a pair of
long-lived `phase0` / `phase1` code roots.

## Read These First

- [architecture.md](./architecture.md)
  Explains the code layout, artifact layout, and migration direction.
- [paper-alignment-v12.md](./paper-alignment-v12.md)
  Repo-facing map for the current v12 paper direction, claim levels, and
  terminology.
- [archive/context_projection_fixed_v12.md](./archive/context_projection_fixed_v12.md)
  Current v12 paper framing: conditional theory, metric bridge,
  proxy-regime diagnosis, auditable runtime artifacts, synthetic structural
  evidence, and extraction as a separate bridge risk.
- [experiment-design-overview.md](./experiment-design-overview.md)
  High-level Phase A/B/C experiment design for context-projection diagnostics.
- [phase-tree-crosswalk.md](./phase-tree-crosswalk.md)
  Crosswalk between the Phase A/B/C experiment stack and the Phase 0/1/2/3/4
  measurement-validity stack.
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
- [protocols/phase-b-replay-protocol.md](./protocols/phase-b-replay-protocol.md)
  Phase B offline replay contract for dispatch traces and diagnostic
  recomputation.
- [protocols/phase1-protocol.md](./protocols/phase1-protocol.md)
  Phase 1 measurement-chain, bridge, and annotation constraints.
- [protocols/phase4-design-skeleton.md](./protocols/phase4-design-skeleton.md)
  Forward-planning skeleton for post-Gate-5 full-study or direct-audit branches.
- [protocols/phase1-contamination-triage-and-question-rewrite.md](./protocols/phase1-contamination-triage-and-question-rewrite.md)
  Human-in-the-loop workflow for AI-assisted contamination judgement and
  minimal question rewrite planning after gate failure.

## P45-P50 v12 Codex Phase Docs

The controlling Codex development/reference package for v12 follow-up work is:

- [P45-P50 v12 Phase Docs](./codex/v12-phase-docs/README.md)
- [Common Guardrails](./codex/v12-phase-docs/COMMON-GUARDRAILS.md)
- [P45 One-Stratum Bridge Calibration Plan](./codex/v12-phase-docs/P45-one-stratum-bridge-calibration-plan.md)

P45, one-stratum metric bridge calibration, is the next priority. P50 is
optional and should not precede P45-P49. These phase docs are planning and
review controls only: they do not claim `measurement_validated` evidence and do
not supply bridge calibration results by themselves.

## P37-P44 Development and Experiment Planning

These documents are planning, protocol, template, and review artifacts. They do
not upgrade the evidence claim level and do not claim measurement validation,
scientific validation, or deployed V-information certification.

Core package links:

- [Mingx Follow-up Development and Experiment Plan v0.2](./roadmaps/mingx-followup-dev-experiment-plan-v0-2.md)
- [P37-P44 Development and Experiment Roadmap](./roadmaps/P37-P44-development-and-experiment-roadmap.md)
- [P37-P44 Documentation Package README](./roadmaps/P37-P44-documentation-package-readme.md)
- [P37-P44 Documentation Package Manifest](./roadmaps/P37-P44-documentation-package-manifest.json)
- [Claim Boundary Checklist](./templates/claim-boundary-checklist.md)
- [Route B Adjudication Manifest Template](./templates/route-b-adjudication-manifest-template.json)
- [P37-P44 Codex Prompt Pack](./templates/codex-prompts/P37-P44-codex-prompt-pack.md)

Planning and protocols:

- [P37 Repo State and Claim Boundary Lock Protocol](./protocols/P37-repo-state-claim-boundary-lock-protocol.md)
- [P39 Artifact Schema Freeze Protocol](./protocols/P39-artifact-schema-freeze-protocol.md)
- [openWorker Trace Audit Protocol](./protocols/openworker-trace-audit-protocol.md)
- [Extraction Uniformity Sidecar Plan](./protocols/extraction-uniformity-sidecar-plan.md)

Experiments:

- [P38 Synthetic Structural Benchmark Plan](./experiments/P38-synthetic-structural-benchmark-plan.md)
- [P40 Phase B Offline Replay Implementation Plan](./experiments/P40-phase-b-offline-replay-implementation-plan.md)
- [P41 Route B Model-Adjudicated Evaluation Plan](./experiments/P41-route-b-model-adjudicated-evaluation-plan.md)
- [P42 Fresh Reduced-Scope Follow-Up Batch Plan](./experiments/P42-fresh-reduced-scope-follow-up-batch-plan.md)
- [P43 Phase C Realistic Task Context Projection Benchmark Plan](./experiments/P43-phase-c-realistic-task-context-projection-benchmark-plan.md)

Paper integration:

- [P44 Manuscript Evidence Integration Plan](./paper/P44-manuscript-evidence-integration-plan.md)

Reviews:

- [P37 Repo State and Claim Boundary Lock Review](./reviews/P37-repo-state-and-claim-boundary-lock-review.md)
- [P38 Synthetic Structural Validity Review](./reviews/P38-synthetic-structural-validity-review.md)
- [P39 Artifact Schema Freeze Review](./reviews/P39-artifact-schema-freeze-review.md)
- [P40 Phase B Offline Replay Review](./reviews/P40-phase-b-offline-replay-review.md)
- [P41 Route B Model-Adjudicated Evaluation Review](./reviews/P41-route-b-model-adjudicated-evaluation-review.md)
- [P42 Follow-Up Live Batch Decision Review](./reviews/P42-follow-up-live-batch-decision-review.md)
- [P43 Phase C Benchmark Readiness Review](./reviews/P43-phase-c-benchmark-readiness-review.md)
- [P44 Manuscript Evidence Integration Review](./reviews/P44-manuscript-evidence-integration-review.md)
- [openWorker Trace Field Availability Map](./reviews/openworker-trace-field-availability-map.md)
- [Extraction Uniformity Sidecar Review](./reviews/extraction-uniformity-sidecar-review.md)

## Documentation Layers

- `protocols/`
  Active protocol documents that guide implementation and execution.
- `roadmaps/`
  Active planning documents. The v12 follow-up plan is
  `mingx-followup-dev-experiment-plan-v0-2.md`; it makes one-stratum metric
  bridge calibration the highest-priority missing experiment and does not
  claim measurement validation.
- `archive/`
  `context_projection_fixed_v12.md` is the current research-framing anchor.
  `context_projection_revised_v10.md` and older paper drafts, including final
  v8, are historical reference material, not default implementation
  entrypoints.
- `paper-alignment-v10.md`
  Legacy v10 repository-to-paper map retained for historical reference. New
  paper-facing work should start from `paper-alignment-v12.md`.

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
