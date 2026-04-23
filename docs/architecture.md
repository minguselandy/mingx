# Architecture Notes

## Current State

This repository is no longer just a Phase 0 starter. It is a runnable MuSiQue
Gate 1 / Phase 1 project with:

- Phase 0 artifact validation and smoke
- Phase 1 mock/live scoring
- append-only measurement storage
- cohort runner support
- bridge and export scaffolds
- API profile and backend abstraction
- protocol and reference documentation

## Canonical Structure

The project now has four main semantics:

### 1. `docs/`

Protocols, architecture notes, and archived research material.

### 2. `api/`

Provider/model profile resolution, backend factories, and API-facing smoke
helpers.

Key responsibilities:

- `settings.py`
  Resolves the active API profile, provider metadata, and role-model mapping.
- `backends.py`
  Builds live/mock scoring backends so runtime code does not branch on
  provider names.

### 3. `cps/`

Canonical code package, organized by capability:

- `data/`
- `store/`
- `providers/`
- `scoring/`
- `runtime/`
- `analysis/`

### 4. `artifacts/`

Real run outputs and reproducibility material.

Phase labels still belong here because they describe run stages and outputs,
not long-term code-module boundaries.

## API Resolution Flow

The implementation now separates protocol locks from transport details.

1. `phase1.yaml` still records the locked Phase 1 provider/model family.
2. `.env` and generic `API_*` overrides are resolved by `api/settings.py`.
3. `api/backends.py` maps the resolved API profile to a concrete scoring
   backend.
4. `cps/runtime/*` consumes generic `frontier` / `small` / `coding` roles and
   does not branch on provider-specific runtime logic.
5. `cps/providers/openai_compatible.py` contains the concrete OpenAI-compatible
   transport implementation.
6. `cps/providers/dashscope.py` and `phase1/*` remain compatibility shims for
   older imports.

## Compatibility Policy

`phase0/` and `phase1/` now act as compatibility shims over `cps/`.

That means:

- `api/` is the source of truth for provider/model switching
- `cps/` is the implementation source of truth
- legacy imports remain valid
- run plans stay under `configs/runs/`
- artifact layouts stay unchanged

## Not In Scope For This Migration

- No artifact cleanup
- No retrieval-platform expansion
- No full-study Phase 2/3 platform work
- No live-contract changes
