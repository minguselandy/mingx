# Mingx P37-P44 Development and Experiment Document Pack

This pack contains repository-ready Markdown documents for the next development and experiment cycle of the `mingx` Context Projection Selection project.

The documents are intended to be copied into the repository root while preserving the `docs/...` paths.

Current status note: this package is preserved as the P37-P44/v10-era
document pack. The current v12 follow-up planning entrypoint is
`docs/roadmaps/mingx-followup-dev-experiment-plan-v0-2.md`, and the current
paper-alignment entrypoint is `docs/paper-alignment-v12.md`. The v10 files
remain legacy/archive references.

## Files

| Path | Purpose |
|---|---|
| `docs/roadmaps/P37-P44-development-and-experiment-roadmap.md` | Master roadmap for P37 through P44 |
| `docs/protocols/P37-repo-state-claim-boundary-lock-protocol.md` | Protocol for repo-state reconciliation and claim-boundary lock |
| `docs/experiments/P38-synthetic-structural-benchmark-plan.md` | Phase A synthetic benchmark hardening plan |
| `docs/protocols/P39-artifact-schema-freeze-protocol.md` | Artifact schema freeze protocol |
| `docs/experiments/P40-phase-b-offline-replay-implementation-plan.md` | Phase B replay implementation plan |
| `docs/experiments/P41-route-b-model-adjudicated-evaluation-plan.md` | Route B model-adjudicated evaluation plan |
| `docs/experiments/P42-fresh-reduced-scope-follow-up-batch-plan.md` | Fresh replacement-batch pilot plan |
| `docs/experiments/P43-phase-c-realistic-task-context-projection-benchmark-plan.md` | Phase C realistic-task benchmark plan |
| `docs/paper/P44-manuscript-evidence-integration-plan.md` | Manuscript evidence integration plan |
| `docs/protocols/openworker-trace-audit-protocol.md` | Sidecar protocol for concrete trace-field availability audit |
| `docs/protocols/extraction-uniformity-sidecar-plan.md` | Sidecar plan for extraction-uniformity / `M* -> M` risk |
| `docs/reviews/*.md` | Milestone review documents and acceptance checklists |
| `docs/templates/claim-boundary-checklist.md` | Reusable claim-boundary checklist |
| `docs/templates/codex-prompts/P37-P44-codex-prompt-pack.md` | Codex-ready implementation prompts |
| `docs/templates/route-b-adjudication-manifest-template.json` | Route B manifest template |

## Intended Sequence

1. P37 repo-state and claim-boundary lock
2. P38 synthetic structural benchmark hardening
3. P39 artifact schema freeze
4. P40 Phase B offline replay implementation
5. P41 Route B model-adjudicated evaluation
6. P42 fresh reduced-scope follow-up batch, only after explicit live approval
7. P43 Phase C realistic-task context projection benchmark
8. P44 manuscript evidence integration

Sidecars:

- openWorker trace audit
- extraction-uniformity / `M* -> M` bridge-risk pilot

## Safety and Claim Rule

These documents intentionally preserve the paper's conservative evidence posture. They do not authorize live APIs, human-label fabrication, kappa fabrication, or `measurement_validated` claims.
