# AGENTS.md - mingx Codex operating contract

## Project identity

This repository implements a measurement and runtime-audit scaffold for the
current v12 Context Projection Selection paper direction:

**Context Projection Selection in Multi-Agent Systems: Conditional Theory,
Metric Bridge, and Proxy-Regime Diagnosis.**

The implementation must remain aligned with the revised paper boundary.

Current source manuscript anchor: `docs/archive/context_projection_fixed_v12.md`.
Current alignment map: `docs/paper-alignment-v12.md`.

Current proposed follow-up cycle:

- `docs/experiments/P51-P60-v12-followup-dev-experiment-plan.md`
- `docs/reviews/P51-P60-v12-review-claim-gate-protocol.md`

This P51-P60 package is planning and review control only. It does not mark any
P51-P60 phase complete and does not upgrade evidence claims.

Current Route 2 real-data development-control entrypoints:

- `docs/roadmaps/mingx-route2-real-data-dev-experiment-plan.md`
- `docs/roadmaps/mingx-route2-development-control-chat-prompt.md`

Route 2 is the proposed P61R-P70R real-data evidence package. Its starting
state is P45-P60 scaffold/evidence-state package complete, P55
`failed_closed_no_rows` / `blocked_operator_required`, and P56
`no_imported_traces`. Route 2 exists to produce real public-benchmark candidate
pools, P55 bridge rows, P55 bridge calibration, realistic P56 dispatch traces,
matched-budget baseline comparisons, ablations, manuscript integration, and an
independent claim audit. It does not relax the v12 evidence boundary.

Legacy v10 references remain preserved as archive material:
`docs/archive/context_projection_revised_v10.md` and
`docs/paper-alignment-v10.md`.

## Mandatory reading before phase-development edits

For implementation tasks, read:

- `docs/codex/phase-development-guidance.md`
- the relevant file under `docs/codex/phases/`
- `docs/paper-alignment-v12.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/protocols/phase-b-readiness-and-first-replay-plan.md`
- for P51-P60 work, `docs/experiments/P51-P60-v12-followup-dev-experiment-plan.md`
- for P51-P60 work, `docs/reviews/P51-P60-v12-review-claim-gate-protocol.md`
- for Route 2 / P61R-P70R work, `docs/roadmaps/mingx-route2-real-data-dev-experiment-plan.md`
- for Route 2 development-control work, `docs/roadmaps/mingx-route2-development-control-chat-prompt.md`
- for P55/P56 repair work, current `docs/reviews/*P55*` and `docs/reviews/*P56*` evidence-state reviews

For review tasks, read:

- `docs/codex/post-development-review-agent.md`
- `docs/codex/guidance-document-review.md`
- the relevant phase guidance under `docs/codex/phases/`
- for P51-P60 reviews, `docs/reviews/P51-P60-v12-review-claim-gate-protocol.md`
- for Route 2 reviews, `docs/roadmaps/mingx-route2-real-data-dev-experiment-plan.md` and the relevant P61R-P70R report/review docs

## Core scientific boundaries

- Do **not** claim theorem-level deployment verification.
- Do **not** claim runtime diagnostics prove selector-regime validity.
- The formal objective is predictive V-information.
- The theory is conditional on an approximate / weak-submodular regime hypothesis.
- Runtime diagnostics are proxy-regime / operational-utility signals depending on `MetricBridgeWitness` status.
- Extraction audit is a separate `M* -> M` bridge-risk audit, not selector-regime proof.
- Do **not** emit `vinfo_proxy_supported` without a fresh matching `MetricBridgeWitness`.
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
- Route 2 real-data success can support stratum-local claims only.
- `calibrated_proxy_supported` requires a fresh matching `MetricBridgeWitness`
  with residual and stability gates passed for the active stratum and calibration
  epoch.
- Replay completeness alone is not metric support, selector validity, or
  V-information proxy evidence.
- Operational superiority claims must name the dataset, budget, baseline,
  metric, evaluator/materialization regime, and statistical test status.
- Public benchmark success must not be converted into `measurement_validated`,
  human-label validation, human-human kappa, global calibrated proxy support, or
  deployed V-information verification.

Allowed active Route 2 metric labels:

- `vinfo_proxy_supported`
- `calibrated_proxy_supported`
- `operational_utility_only`
- `ambiguous_metric`

Allowed active Route 2 selector labels:

- `greedy_supported`
- `pairwise_escalate`
- `higher_order_risk`
- `ambiguous`

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

## Route 2 real-data controller

Route 2 phases must proceed in order unless the user explicitly changes scope:

1. P61R public benchmark adapters and candidate pools
2. P62R P55 bridge row generator
3. P63R P55 real bridge calibration
4. P64R baseline selector suite
5. P65R realistic dispatch trace generation
6. P66R comparative realistic replay experiment
7. P67R ablation and error analysis
8. P68R manuscript integration package
9. P69R independent review and claim audit
10. P70R release / submission package

Do not skip ahead to P56 comparison before P55 row generation and trace schema
validation are working. Start with the shortest validating path: FEVER adapter
dry-run, FEVER bridge-row generation, FEVER bridge calibration, minimal baseline
interface, then one realistic replay dataset and two budgets.

Route 2 public benchmark adapters should support local mirrors and fail closed
with a blocked-data report when data are unavailable. No proprietary live API or
evaluator is allowed unless the user/operator explicitly approves it. Public
benchmark downloads are allowed only when the local environment and project
policy permit them. Missing evaluator/log-loss outputs must produce
`blocked_no_evaluator` or `failed_closed_no_evaluator_or_rows`, not fabricated
rows or traces.

Keep these out of commits unless explicitly approved:

- `.codex/automation-state/`
- `artifacts/operator_inputs/`
- `artifacts/experiments/synthetic_regime_v12/events.jsonl`
- duplicate `docs/mingx-v12-*` upload files
- post-commit independent review leftovers unrelated to the active phase

Every Route 2 phase report must include:

```text
Phase:
Branch / HEAD:
Files changed:
Artifacts produced:
Tests run:
Test results:
Data status:
Claim status:
Allowed paper claim:
Denied paper claims:
Blocked items:
Next recommended phase:
Commit recommendation:
```

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

For Route 2 phases, prefer the focused acceptance commands from the route plan
for the active P61R-P70R phase. At minimum, run the relevant targeted pytest
file or package, the current framing guardrail test path when claims or reports
change, and `python -m compileall cps` when Python implementation files under
`cps/` change. If a dataset, evaluator, or optional dependency is unavailable,
record the blocked command/result explicitly instead of substituting synthetic
evidence.

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
