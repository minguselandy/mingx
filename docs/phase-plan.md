# mingx Automation Phase Plan

This plan governs Codex-assisted work in this isolated `mingx-dev` repository. Execute only the current phase from `.state/codex/current_phase.json`.

Global rules:

- Do not implement work outside the active phase.
- Do not weaken scientific guardrails in `AGENTS.md`.
- Do not run live APIs unless the phase explicitly reaches an operator gate.
- Do not install dependencies unless the phase explicitly allows guarded optional dependencies.
- Do not stage, commit, reset, clean, or discard changes unless explicitly asked.
- Every phase requires a review under `docs/reviews/`.

## P00 - Automation management finalization

Goal: Merge AGENTS rules, confirm target framework validation, and prepare project-specific phases.

Allowed files:

- `AGENTS.md`
- `docs/phase-plan.md`
- `docs/reviews/**`
- `.state/codex/**`

Forbidden changes:

- CPS implementation or runtime logic.
- Scientific gate semantics.
- Dependency installation.
- Live API calls.
- Git staging, commits, resets, cleans, or discards.

Required checks:

- `python scripts/framework_guard.py status`
- `python scripts/framework_guard.py validate --profile target`
- `python -m compileall scripts`

Expected artifacts:

- Updated `AGENTS.md`.
- Updated `docs/phase-plan.md`.
- `docs/reviews/P00-review.md`.
- Updated `.state/codex/current_phase.json` if accepted.
- Appended `.state/codex/phase_history.jsonl` if accepted.

Review checklist:

- Existing mingx-specific rules are preserved.
- Required scientific guardrails are explicit.
- Phase plan includes P00 through P09.
- Validation and compileall pass.

Advancement rule: Safe auto-advance yes. Advance to P01 only after an ACCEPT or ACCEPT_WITH_NOTES review.

## P01 - ProjectionBundleV1 schema

Goal: Wrap existing `CandidatePool`, `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and `ProjectionDiagnostics` into a deterministic `ProjectionBundleV1`.

Allowed files:

- `cps/**`
- `tests/**`
- `docs/**`

Forbidden changes:

- Live inference paths.
- Scientific claim upgrades.
- Reclassification of `CandidatePool` as a core paper artifact.
- Non-deterministic serialization.
- Optional dependency installation.

Required checks:

- Focused tests for the bundle schema and canonical serialization.
- Relevant guardrail tests for artifact ontology and revised framing.
- `python scripts/framework_guard.py validate --profile target`

Expected artifacts:

- `ProjectionBundleV1` schema or dataclass.
- Deterministic canonical serialization path.
- Tests covering ordering, missing evidence, and paper-boundary negatives.
- Phase review.

Review checklist:

- Bundle wraps existing artifacts without changing their semantics.
- `CandidatePool` remains replay substrate only.
- Serialization has stable key and record ordering.
- No scientific claim level is upgraded.

Advancement rule: Safe auto-advance yes if checks pass and no operator gate is triggered.

## P02 - Live/mock cohort projection event export

Goal: Emit per-dispatch projection artifact events from cohort paths without changing scientific gates.

Allowed files:

- `cps/runtime/**`
- `cps/experiments/**`
- `tests/**`
- `docs/**`

Forbidden changes:

- Live API execution during automated work.
- Scientific gate changes.
- Runtime diagnostic recomputation unless already part of the path.
- Dependency installation.

Required checks:

- Mock-only tests for cohort event export.
- Deterministic event ordering tests.
- Relevant runtime and guardrail tests.
- `python scripts/framework_guard.py validate --profile target`

Expected artifacts:

- Per-dispatch projection artifact event export in mock/offline paths.
- Tests showing no live API requirement.
- Phase review.

Review checklist:

- Mock-only tests pass.
- Live API paths remain gated.
- Scientific classifications are unchanged.
- Exported events are deterministic.

Advancement rule: Safe auto-advance yes for mock-only tests; stop before live API.

## P03 - Follow-up CLI

Goal: Add CLI wrapper around `cps.runtime.followup.build_followup_package`.

Allowed files:

- `cps/runtime/**`
- `scripts/**`
- `tests/**`
- `docs/**`

Forbidden changes:

- Changes to follow-up package semantics unless explicitly required.
- Live API calls.
- Scientific claim upgrades.
- Dependency installation.

Required checks:

- CLI unit tests.
- Existing follow-up package tests.
- Relevant guardrail tests.
- `python scripts/framework_guard.py validate --profile target`

Expected artifacts:

- CLI wrapper for follow-up package generation.
- Tests for arguments, output path handling, and failure modes.
- Phase review.

Review checklist:

- CLI delegates to existing implementation.
- Outputs are deterministic.
- Errors are clear.
- No live execution or scientific validation claim is introduced.

Advancement rule: Safe auto-advance yes if checks pass and no operator gate is triggered.

## P04 - Phase 1 scientific closure

Goal: Run fresh follow-up, contamination check, human annotation ingest, kappa, and bridge evaluation.

Allowed files:

- `docs/**`
- `artifacts/**`
- `configs/**`
- Review reports and operator-provided evidence.

Forbidden changes:

- Automated live API execution without operator approval.
- Upgrading claims without human labels, kappa, contamination status, and bridge evidence.
- Treating engineering completion as scientific validation.
- Silent modification of recorded evidence.

Required checks:

- Operator-approved follow-up run commands.
- Contamination check.
- Human annotation ingest.
- Kappa evaluation.
- Metric bridge evaluation.
- Guardrail tests.

Expected artifacts:

- Follow-up package or run report.
- Contamination report.
- Human annotation ingest report.
- Kappa report.
- Bridge evaluation report.
- Phase review.

Review checklist:

- contamination failure => `pilot_only`.
- missing human labels => `not measurement_validated`.
- missing kappa => `not measurement_validated`.
- stale/missing metric bridge => `operational_utility_only` or ambiguous.
- Engineering success is not reported as scientific validation.

Advancement rule: Safe auto-advance no. Operator required.

## P05 - Synthetic regime benchmark

Goal: Implement redundancy-dominated, pairwise-synergy, and higher-order-synergy synthetic regimes with pre-registered validity table.

Allowed files:

- `cps/experiments/**`
- `tests/**`
- `docs/protocols/**`
- `docs/**`

Forbidden changes:

- Claims that synthetic success certifies deployed V-information submodularity.
- Live API calls.
- Non-deterministic benchmark outputs.
- Dependency installation.

Required checks:

- Synthetic regime tests.
- Pre-registered validity table checks.
- Revised framing guardrail tests.
- `python scripts/framework_guard.py validate --profile target`

Expected artifacts:

- Synthetic regime implementations.
- Pre-registered validity table.
- Tests for redundancy, pairwise synergy, and higher-order synergy.
- Phase review.

Review checklist:

- Synthetic benchmark success remains synthetic-only.
- Outputs are deterministic.
- Validity table is explicit.
- No deployed-regime certification is claimed.

Advancement rule: Safe auto-advance yes if checks pass and no scientific claim upgrade occurs.

## P06 - Selector baselines and oracle

Goal: Add optional `submodlib` selector and OR-Tools exact oracle.

Note: External projects under `reference/` are local ZIP-extracted references only. They may inform adapter design but must not be treated as vendored dependencies.

Allowed files:

- `cps/**`
- `tests/**`
- `docs/**`
- Optional dependency configuration only if guarded.

Forbidden changes:

- Mandatory optional dependencies.
- Import-time failures when optional packages are missing.
- Live API calls.
- Scientific claim upgrades.

Required checks:

- Tests with optional dependencies absent.
- Tests with fake or skipped optional integrations.
- Baseline/oracle deterministic output tests.
- `python scripts/framework_guard.py validate --profile target`

Expected artifacts:

- Guarded selector baseline adapter.
- Guarded exact oracle adapter.
- Tests for unavailable optional dependencies.
- Phase review.

Review checklist:

- Base suite works without optional packages.
- Optional adapters fail closed or skip clearly.
- Deterministic behavior is preserved.
- Claims remain operational/engineering only.

Advancement rule: Safe auto-advance yes if optional dependencies are guarded.

## P07 - Observability exporters

Goal: Add dry-run OTel/Langfuse/Phoenix-style `ProjectionBundleV1` export mapping.

Note: External projects under `reference/` are local ZIP-extracted references only. They may inform adapter design but must not be treated as vendored dependencies.

Allowed files:

- `cps/**`
- `tests/**`
- `docs/**`

Forbidden changes:

- Network export during tests.
- Required observability services.
- Secrets or credentials.
- Scientific claim upgrades.

Required checks:

- Dry-run exporter mapping tests.
- Fake sink tests.
- Deterministic serialization tests.
- `python scripts/framework_guard.py validate --profile target`

Expected artifacts:

- Dry-run export mapping.
- Fake sink tests.
- Documentation of non-live behavior.
- Phase review.

Review checklist:

- No network calls occur.
- No credentials are required.
- Mapping preserves `ProjectionBundleV1` semantics.
- Export output is deterministic.

Advancement rule: Safe auto-advance yes if checks pass and no external service is required.

## P08 - Provider adapters

Goal: Add optional Graphiti and LangExtract conversion adapters using fake objects in tests.

Note: External projects under `reference/` are local ZIP-extracted references only. They may inform adapter design but must not be treated as vendored dependencies.

Allowed files:

- `cps/**`
- `tests/**`
- `docs/**`

Forbidden changes:

- Required provider dependencies.
- Live provider calls.
- Credential requirements.
- Scientific claim upgrades.

Required checks:

- Fake object adapter tests.
- Optional dependency absence tests.
- Serialization and mapping tests.
- `python scripts/framework_guard.py validate --profile target`

Expected artifacts:

- Optional Graphiti conversion adapter.
- Optional LangExtract conversion adapter.
- Fake-object tests.
- Phase review.

Review checklist:

- Tests use fake objects only.
- Missing providers are handled gracefully.
- No live model or service calls occur.
- Claims remain unchanged.

Advancement rule: Safe auto-advance yes if checks pass and providers remain optional.

## P09 - Runtime adapter prototype

Goal: Add optional LangGraph/OpenClaw adapter prototype.

Note: External projects under `reference/` are local ZIP-extracted references only. They may inform adapter design but must not be treated as vendored dependencies.

Allowed files:

- `cps/**`
- `tests/**`
- `docs/**`

Forbidden changes:

- Required external runtime services.
- Live model calls.
- Credential requirements.
- Auto-merge or unattended deployment.
- Scientific claim upgrades.

Required checks:

- Offline prototype tests.
- Fake runtime adapter tests.
- Optional dependency absence tests.
- `python scripts/framework_guard.py validate --profile target`

Expected artifacts:

- Optional runtime adapter prototype.
- Offline tests with fake runtime objects.
- Documentation of external-service stop conditions.
- Phase review.

Review checklist:

- Prototype is optional.
- External services and live models remain gated.
- No deployment or auto-merge path is introduced.
- Scientific guardrails remain unchanged.

Advancement rule: Safe auto-advance no if external services or live models are required.
