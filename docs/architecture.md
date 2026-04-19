# Architecture Notes

## Current State

This repository is no longer just a Phase 0 starter. It is a runnable MuSiQue
Gate 1 / Phase 1 project with:

- Phase 0 artifact validation and smoke
- Phase 1 mock/live scoring
- append-only measurement storage
- cohort runner support
- bridge and export scaffolds
- protocol and reference documentation

## Canonical Structure

The project now has three main semantics:

### 1. `docs/`

Protocols, architecture notes, and archived research material.

### 2. `cps/`

Canonical code package, organized by capability:

- `data/`
- `store/`
- `providers/`
- `scoring/`
- `runtime/`
- `analysis/`

### 3. `artifacts/`

Real run outputs and reproducibility material.

Phase labels still belong here because they describe run stages and outputs,
not long-term code-module boundaries.

## Compatibility Policy

`phase0/` and `phase1/` now act as compatibility shims over `cps/`.

That means:

- `cps/` is the implementation source of truth
- legacy imports remain valid
- run plans stay under `configs/runs/`
- artifact layouts stay unchanged

## Not In Scope For This Migration

- No artifact cleanup
- No retrieval-platform expansion
- No full-study Phase 2/3 platform work
- No live-contract changes
