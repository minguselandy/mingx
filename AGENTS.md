# AGENTS.md — mingx Codex operating contract

## Project identity

This repository implements a measurement and runtime-audit scaffold for:

**“Context Projection Selection in Multi-Agent Systems: Conditional Theory, Metric Bridge, and Proxy-Regime Certification.”**

The implementation must remain aligned with the revised paper boundary.

## Mandatory reading before phase-development edits

For implementation tasks, read:

- `docs/codex/phase-development-guidance.md`
- the relevant file under `docs/codex/phases/`
- `docs/paper-alignment-v10.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/protocols/phase-b-readiness-and-first-replay-plan.md`

For review tasks, read:

- `docs/codex/post-development-review-agent.md`
- `docs/codex/guidance-document-review.md`
- the relevant phase guidance under `docs/codex/phases/`

## Core scientific boundaries

- Do **not** claim theorem-level deployment verification.
- Do **not** claim runtime diagnostics prove selector-regime validity.
- The formal objective is predictive V-information.
- The theory is conditional on an approximate / weak-submodular regime hypothesis.
- Runtime diagnostics are proxy-regime / operational-utility signals depending on `MetricBridgeWitness` status.
- Extraction audit is a separate `M* -> M` bridge-risk audit, not selector-regime proof.
- Do **not** emit `Vinfo_proxy_certified` without a fresh matching `MetricBridgeWitness`.
- Do **not** describe `block_ratio_lcb_star` as a paper-grade degree-adaptive star-block estimator.
- `gamma_hat` is legacy compatibility only.
- `gamma_hat_semantics` must remain `legacy_trace_decay_alias_not_submodularity_ratio`.
- `TraceDecay` is path-local marginal decay only: `marginal_gain / singleton_gain`.
- contamination failure => `pilot_only`.
- missing human labels => `not measurement_validated`.
- missing kappa => `not measurement_validated`.
- stale/missing metric bridge => `operational_utility_only` or ambiguous.
- synthetic benchmark success does not certify deployed V-information submodularity.
- engineering success must not be reported as scientific validation.

## Core artifact ontology

The four core runtime paper artifacts are:

1. `ProjectionPlan`
2. `BudgetWitness`
3. `MaterializedContext`
4. `MetricBridgeWitness`

`CandidatePool` is replay support / substrate only. It is not one of the four core paper artifacts.

## Current Phase B boundary

Phase B is offline replay readiness only.

Allowed:

- artifact binding
- missing-field classification
- replay manifest generation
- replay summary generation
- conservative claim-level eligibility classification

Forbidden unless explicitly requested:

- live inference
- diagnostic recomputation
- block-ratio recomputation
- Phase C realistic/live experiments
- theorem-level deployment claims
- inference of missing materialization order
- inference of excluded candidates without an explicit complete considered-candidate set
- promotion of runtime diagnostics to deployment verification

## Development workflow

Before editing:

- inspect the relevant docs
- inspect existing implementation and tests
- identify the smallest coherent patch
- preserve current semantics unless the task explicitly requests a migration

When changing behavior:

- add focused tests
- preserve deterministic output ordering
- avoid timestamps, UUIDs, absolute paths, or environment-specific values in canonical artifacts
- do not weaken revised framing guardrails to make tests pass

## Automation workflow

For agentic-development phases:

1. Read `AGENTS.md`.
2. Read `docs/phase-plan.md`.
3. Read `.state/codex/current_phase.json`.
4. Execute only the current phase.
5. Respect allowed files, forbidden changes, and operator gates.
6. Run focused checks.
7. Write a phase review under `docs/reviews/`.
8. Advance state only when the review protocol and `scripts/framework_guard.py` allow it.

Do not merge framework guidance into scientific claims. The automation layer manages work; it does not validate the science.

## Review verdicts

Allowed phase review verdicts:

- `ACCEPT`
- `ACCEPT_WITH_NOTES`
- `REQUEST_CHANGES`
- `BLOCKED_OPERATOR_REQUIRED`
- `REJECT`

## Safe auto-advance rules

Auto-advance is allowed only for offline deterministic engineering phases where:

- the review verdict is `ACCEPT` or `ACCEPT_WITH_NOTES`;
- review metadata explicitly sets `next_phase_allowed: true`;
- target validation and required checks pass, or skips are documented;
- `blocked` is false and `requires_operator` is false;
- no live API, credential, external service, human annotation, license, security, or scientific-claim gate exists.

Stop automation when a phase requires live APIs, human labels, kappa evaluation, external services, credentials, license review, or scientific claim upgrades.

## Testing rules

For Phase B replay work, run:

```bash
uv run pytest tests/test_phase_b_replay.py
```

Then run the guardrail set:

```bash
uv run pytest tests/test_projection_artifacts.py tests/test_synthetic_regime_benchmark.py tests/test_revised_framing_guardrails.py
```

Before reporting completion, run the full suite when feasible:

```bash
uv run pytest
```

For automation-only phases, run:

```bash
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
python -m compileall scripts
```

Do not run live API tests unless the phase explicitly requires operator approval for live execution.

## Dependency / optional integration rules

- Do not install dependencies unless the current phase explicitly allows it.
- Optional integrations must be guarded so the base test suite runs without optional packages.
- Provider, observability, graph, and extraction adapters must use fake objects or dry-run mappings in tests unless an operator explicitly approves live services.
- Missing optional dependencies must produce clear skip or unavailable behavior, not import-time failure.

## Commit policy

- Do not stage, commit, reset, clean, push, or discard changes unless explicitly asked.
- Always review `git status --short` and relevant diffs before any requested commit.
- Keep baseline dirty files separate from current phase changes in reports.

## Reference repo policy

- Treat external reference repositories and downloaded examples as read-only references.
- Do not copy external code into this repository without license review.
- Do not run scripts from reference repositories.
- Do not use reference behavior to weaken mingx scientific guardrails.
- Local external references may exist under `reference/`. They are read-only research material, may be inspected for design ideas, must not be executed, vendored, copied, or committed, and must not become required dependencies.

## Required final report for implementation tasks

Every implementation task must report:

1. changed files
2. implementation summary
3. why the change stays within the phase boundary
4. tests run
5. exact test results
6. assumptions
7. limitations
8. whether any paper-boundary guardrail was touched
9. whether any generated artifact schema changed
