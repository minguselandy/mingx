# Experiment Design Overview

## 1. Purpose

The experiments for this project validate measurement, replay, monitoring, and
escalation scaffolds for dispatch-time context projection selection. They do not
prove that deployed models inherit the paper's formal theorem, and they do not
claim scheduler correctness, memory-system correctness, or system-level
optimality.

The revised paper studies per-round, per-agent, token-budgeted selection from a
candidate pool `M` into a selected subset `S_i`. The experimental stack focuses
on whether candidate pools, selections, budgets, diagnostics, metric-bridge
claim levels, and runtime artifacts are observable and replayable.

The phases are intentionally layered:

- Phase A tests synthetic structural validity of diagnostics under controlled
  set functions.
- Phase B tests offline replay and artifact sufficiency over real or generated
  dispatch traces.
- Phase C tests context projection behavior on realistic tasks and benchmarks.

The relation between this Phase A/B/C stack and the Phase 0/1/2/3/4
measurement-validity stack is specified in `docs/phase-tree-crosswalk.md`.

None of these phases should be interpreted as a claim that the context selector
is globally optimal, that a scheduler is correct, or that synthetic diagnostics
prove deployed LLM behavior.

## 2. Paper-To-Experiment Mapping

| Paper object | Experimental counterpart | Status |
|---|---|---|
| candidate pool `M` | synthetic items in Phase A; replayed candidates in Phase B; task-derived context items in Phase C | Phase A implemented; Phase B planned; Phase C planned |
| selected subset `S_i` | selected context ids emitted by the selector or reconstructed from replay | Phase A implemented; Phase B planned; Phase C planned |
| token budget `B_i` | synthetic cost budget in Phase A; replay or task budget in later phases | Phase A implemented; Phase B planned; Phase C planned |
| block-ratio LCB | proxy diagnostic family for local weak-submodularity behavior: `block_ratio_lcb_b2`, `block_ratio_lcb_star`, `block_ratio_lcb_b3` | Phase A currently implements deterministic b=2/b=3 synthetic samples; `block_ratio_lcb_star` is a conservative placeholder, not a degree-adaptive star-block estimator |
| interaction mass | pairwise interaction diagnostic over sampled or enumerated candidate pairs | Phase A implemented; Phase B planned; Phase C planned |
| triple-excess diagnostics | higher-order interaction diagnostic for prerequisite-chain regimes | Phase A implemented for synthetic oracle triples; Phase B/C require cached triple or block utility records |
| greedy-vs-augmented gap | escalation diagnostic comparing greedy selection against seeded augmented greedy | Phase A implemented; Phase B planned; Phase C planned |
| `ProjectionPlan` | selected and excluded candidate artifact, including algorithm and trace metadata | Phase A implemented as sidecar artifact; Phase B/C should reuse or extend conservatively |
| `BudgetWitness` | realized token or cost accounting for the selected context | Phase A implemented as sidecar artifact; Phase B/C require stable realized counts |
| `MaterializedContext` | realized prompt or context sequence after projection | Phase A implemented as sidecar artifact; Phase B/C require deterministic reconstruction |
| `MetricBridgeWitness` | claim-level artifact qualifying whether diagnostics support V-information proxy, calibrated proxy, operational-utility-only, or ambiguous claims | Phase A implemented for synthetic oracle claims; Phase B/C require bridge-qualified extensions |
| selector action | `monitored_greedy`, `seeded_augmented_greedy`, `interaction_aware_local_search`, or `no_certified_switch` as operational labels | Phase A emits `selector_action`, `selector_regime_label`, and `metric_claim_level`; `selector_regime_label` is limited to `greedy_valid`, `escalate`, or `ambiguous`; legacy policy terminology is compatibility only |

The status column records experimental readiness, not theoretical validity.
Block-ratio diagnostics are proxy-layer estimates under bridge assumptions, not
certificates of the formal worst-case parameter.

## 3. Experimental Phases

### Phase A - Synthetic Structural Validity

Purpose:

- Validate whether diagnostics separate known structural regimes.
- Exercise the artifact schema, event logging, CLI, and report generation
  without relying on live model behavior.

Regimes:

- redundancy-dominated
- sparse pairwise synergy
- higher-order synergy

Expected outputs:

- block-ratio LCB family where available
- interaction mass
- triple-excess diagnostics where available
- greedy-vs-seeded-augmented gap
- `metric_claim_level`
- `selector_regime_label`
- `selector_action`
- Markdown report
- replayable artifacts and events

Scientific claim:

- The diagnostics behave as intended under controlled synthetic structure.
- The benchmark is a pre-registered validity gate, not deployed LLM validation.

Engineering claim:

- The event schemas, runtime artifacts, CLI entry point, and report generation
  are functional enough to support the next experimental layer.

Current status:

- Implemented as a synthetic benchmark sidecar.
- Current synthetic smoke passes under the pre-registered structural gate when
  tests are run.
- Regimes separate as intended under the current selector-action labels:
  redundancy maps to `monitored_greedy`, sparse pairwise synergy maps to
  `seeded_augmented_greedy`, and higher-order synergy maps to
  `interaction_aware_local_search`.

Open review items:

- Confirm Phase B replay traces can provide enough cached singleton, block, and
  joint utility signals to reconstruct the same diagnostics.
- Confirm artifacts can reproduce the report tables without reading derived
  summaries as the source of truth.

### Phase B - Offline Replay Over Dispatch Traces

Purpose:

- Test diagnostics on real or generated context-projection traces.
- Validate whether observability requirements are sufficient to reconstruct
  candidate pools, selections, budgets, materialized contexts, metric bridge
  witnesses, and diagnostics.

Inputs:

- `events.jsonl`
- candidate pools
- `ProjectionPlan`
- `BudgetWitness`
- `MaterializedContext`
- `MetricBridgeWitness` or enough metadata to construct one
- selected context ids

Required capabilities:

- Replay candidate pools.
- Reconstruct selections.
- Recompute diagnostics.
- Assign claim-level status.
- Compare pipeline selections against diagnostic-guided alternatives.

Outputs:

- per-dispatch diagnostic report
- block-ratio LCB distribution where replayable
- interaction mass by task family
- triple-excess diagnostics where replayable
- greedy-vs-augmented gaps
- pipeline-vs-proxy alignment summary
- metric-bridge claim-level summary

Scientific claim:

- Phase B tests whether the diagnostic protocol is usable on realistic trace
  structure.
- It still does not prove Condition A or any theorem inheritance property.

Engineering claim:

- Phase B validates observability requirements needed for replay, audit, and
  escalation analysis.

The replay contract, required trace fields, recomputation path, and
missing-field status labels are specified in
`docs/protocols/phase-b-replay-protocol.md`.

### Phase C - Real-Task Benchmark

Purpose:

- Evaluate context projection behavior under realistic task distributions.
- Measure whether diagnostic-guided context projection correlates with
  downstream task behavior after metric-bridge qualification.

Candidate benchmark families:

- Multi-hop QA, with MuSiQue as the first candidate because the repository
  already has related data, scoring, and paragraph-level context structure.
- HotpotQA-style tasks as a secondary candidate if they stress context
  projection under the chosen setup.
- Code-agent or repo-grounded tasks only if the current runtime already supports
  clean trace capture for candidates, selected contexts, exclusions, budgets,
  metric bridge witnesses, and materialized prompts.
- Tool-use tasks only after artifact completeness and replay are cleanly
  supported.

Selection criteria:

- The benchmark must stress context selection.
- The benchmark must allow candidate pool construction.
- The benchmark must allow controlled budgets.
- The benchmark must expose redundancy, pairwise complementarity, or higher-order
  dependency.
- The benchmark must not require building a new scheduler.

## 4. Minimal Viable Experimental Path

The recommended order is:

1. Review the Phase A implementation.
2. Freeze the artifact schema for `ProjectionPlan`, `BudgetWitness`,
   `MaterializedContext`, and `MetricBridgeWitness`.
3. Add a Phase A paper-facing report table that can be regenerated from events
   and artifacts.
4. Design the Phase B replay schema.
5. Run replay on small controlled traces.
6. Choose the Phase C benchmark only after Phase B replay works.

This path keeps the work incremental and auditable. Later phases should not
depend on stale artifacts or derived reports as stable rules; `events.jsonl` and
explicit runtime artifacts should remain the replay source of truth.

## 5. Metrics

Structural diagnostics:

- block-ratio LCB family: `block_ratio_lcb_b2`, `block_ratio_lcb_star`,
  `block_ratio_lcb_b3`
- interaction mass
- triple-excess diagnostics
- greedy-vs-augmented gap
- TraceDecay as a path-local marginal-decay statistic only, not a
  submodularity-ratio estimator

Selection metrics:

- selected token cost
- redundancy rate
- selected item diversity
- budget utilization

Replay and observability metrics:

- artifact completeness
- replay success rate
- materialization determinism
- missing-field rate
- metric-bridge claim-level coverage

Task metrics:

- task success
- exact match or F1 for QA tasks
- resolved rate for code tasks, if code traces become supported
- tool-call success only if tool-use traces become supported

These metrics should remain separated by layer. Structural diagnostics explain
the proxy regime; replay metrics explain whether the run can be audited; task
metrics explain downstream behavior.

## 6. Claims And Non-Claims

Claims allowed:

- Diagnostics separate the synthetic regimes in Phase A.
- Runtime artifacts support replay when required fields are present.
- Replay can expose pipeline-vs-proxy mismatch.
- Benchmark results can inform selector action and escalation policy.
- Metric-bridge qualification can separate V-information proxy claims,
  calibrated proxy claims, operational-utility-only claims, and ambiguity.

Claims not allowed:

- Legacy trace ratios estimate true worst-case gamma.
- TraceDecay is not a submodularity-ratio estimator.
- Synthetic validation transfers directly to deployed LLM behavior.
- Context selection proves scheduler optimality.
- Multi-agent execution is better than single-agent execution.
- Diagnostics imply theorem inheritance.
- Memory redesign is part of this experiment.
- Scheduler redesign is part of this experiment.
- System-level performance claims follow from these diagnostics alone.

## 7. Development Roadmap

No implementation is part of this overview. Later work should proceed in small,
reviewable steps.

Phase A review:

- inspect emitted artifacts
- validate report reproducibility from events and sidecar artifacts
- strengthen documentation around diagnostic interpretation limits

Phase B design:

- define replay input schema
- define required event fields
- define diagnostic recomputation path
- define how missing replay fields are reported
- define `MetricBridgeWitness` reporting rules

Phase C design:

- choose the benchmark only after Phase B replay works
- implement the smallest realistic benchmark first
- preserve the existing project boundaries around runtime resolution, artifacts,
  and append-only events
