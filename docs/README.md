# Project Docs

This repository is now documented as a full project instead of a pair of
long-lived `phase0` / `phase1` code roots.

## Read These First

- [architecture.md](./architecture.md)
  Explains the code layout, artifact layout, and migration direction.
- [../api/README.md](../api/README.md)
  Explains API profiles, backend factories, and provider/model resolution.
- [../configs/runs/README.md](../configs/runs/README.md)
  Lists the canonical run-plan entrypoints.
- [protocols/execution-readiness-checklist.md](./protocols/execution-readiness-checklist.md)
  Highest-priority execution-order and gate document.
- [protocols/phase1-protocol.md](./protocols/phase1-protocol.md)
  Phase 1 measurement-chain, bridge, and annotation constraints.

## Documentation Layers

- `protocols/`
  Active protocol documents that guide implementation and execution.
- `archive/`
  Research drafts and historical reference material, not the default
  implementation entrypoint.

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
