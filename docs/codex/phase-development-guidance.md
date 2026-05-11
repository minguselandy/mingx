# Codex Phase Development Guidance

## Purpose

This document governs how Codex should implement development phases in this repository.

Codex is a protocol executor, not an epistemic authority. It may implement artifact binding, schema checks, deterministic outputs, tests, CLI plumbing, and documentation that clarifies already-approved semantics. It must not upgrade the scientific claim level of the repository.

## Valid development unit

Each Codex task must correspond to one bounded work package.

A valid work package has:

- phase name
- task name
- source-of-truth docs
- likely files
- required behavior
- explicit non-goals
- required tests
- validation commands
- final report format

A task is invalid if it asks Codex to generally improve the project without a phase boundary.

## Required workflow

For every development task:

1. Read the source-of-truth docs.
2. Inspect existing implementation and tests.
3. Identify the smallest coherent patch.
4. Implement only the requested phase slice.
5. Add or update focused tests.
6. Run focused tests.
7. Run relevant guardrail tests.
8. Run the full suite when feasible.
9. Report changed files, exact test results, assumptions, limitations, and any paper-boundary risk.

## Claim-boundary rule

Implementation must never increase claim strength unless the task explicitly changes the paper boundary and the relevant docs, tests, and review guidance are updated.

Forbidden claim upgrades include:

- `replay_usable` -> `vinfo_proxy_supported` without fresh matching `MetricBridgeWitness`
- runtime diagnostic -> theorem-level selector-regime proof
- synthetic structural validity -> deployment verification
- extraction bridge audit -> selector-regime diagnosis
- `block_ratio_lcb_star` placeholder -> degree-adaptive star-block estimator
- `gamma_hat` legacy trace-decay alias -> submodularity-ratio estimator

## Determinism rule

Canonical outputs must be stable across repeated runs on the same input.

Forbidden in canonical outputs:

- wall-clock timestamps
- random UUIDs
- absolute local paths
- environment-specific paths
- nondeterministic dictionary ordering
- nondeterministic file traversal ordering

Required:

- stable sort order for dispatch-level outputs
- stable JSON key ordering where practical
- deterministic handling of duplicate or ambiguous records

## Non-inference rule

Codex must not silently reconstruct evidence that was not recorded.

Specifically:

- Do not infer materialization order from selected ids.
- Do not infer excluded candidates unless an explicit complete considered-candidate set is available.
- Do not infer bridge freshness from the existence of a bridge witness.
- Do not infer claim eligibility from runtime artifact presence alone.
- Do not infer theorem-level validity from proxy diagnostics.

## Test rule

Behavioral changes require tests.

Tests should include:

- positive success case
- missing required evidence
- stale or mismatched evidence
- deterministic ordering when output artifacts are produced
- paper-boundary negative cases
- CLI behavior when a CLI is part of the task

Do not weaken existing guardrail tests.

## Documentation rule

Documentation changes must preserve the revised paper boundary.

Do not introduce language implying:

- deployment verification
- theorem-level runtime proof
- proof of weak-submodular regime membership from runtime traces
- proof that extraction audit validates selector-regime assumptions
- proof that placeholder diagnostics are paper-grade estimators

## Allowed implementation behavior

Codex may:

- add dataclasses or typed structures
- add loaders for recorded artifacts
- add deterministic output writers
- add conservative classifiers
- add tests and fixtures
- add CLI entry points
- add docs that clarify current semantics

Codex must not, unless explicitly asked:

- add live model calls
- add network-dependent tests
- add non-deterministic outputs
- change synthetic benchmark semantics
- change metric-bridge claim semantics
- change formal-objective wording
- modify paper-boundary guardrails to pass new tests

## Required final response format

Every implementation response must include:

```text
Changed files:
- ...

Implementation summary:
- ...

Phase-boundary assessment:
- ...

Tests run:
- <command> -> <exact result>

Assumptions:
- ...

Limitations:
- ...

Paper-boundary risk:
- none / describe

Generated artifacts:
- none / list schemas changed
```
