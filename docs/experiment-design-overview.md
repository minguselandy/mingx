# Experiment Design Overview

## 1. Purpose

The experiments for this project are designed to validate the paper's verification,
monitoring, and escalation protocol for dispatch-time context projection selection.
They do not prove that deployed models inherit the paper's formal theorem, and
they do not claim scheduler correctness, memory-system correctness, or
system-level optimality.

The paper studies per-round, per-agent, token-budgeted selection from a candidate
pool `M` into a selected subset `S_i`. The experimental stack should therefore
focus on whether candidate pools, selections, budgets, diagnostics, and runtime
artifacts are observable and replayable.

The phases are intentionally layered:

- Phase A tests structural regime discrimination under controlled synthetic set
  functions.
- Phase B tests replayability and diagnostic recomputation over real or generated
  dispatch traces.
- Phase C tests context projection behavior on realistic tasks and benchmarks.

The relation between this Phase A/B/C stack and the Phase 0/1/2/3/4
measurement-validity stack is specified in `docs/phase-tree-crosswalk.md`.

None of these phases should be interpreted as a claim that the context selector is
globally optimal, that a scheduler is correct, or that synthetic diagnostics prove
deployed LLM behavior.

## 2. Paper-to-experiment mapping

| Paper object | Experimental counterpart | Status |
|---|---|---|
| candidate pool `M` | synthetic items in Phase A; replayed candidates in Phase B; task-derived context items in Phase C | Phase A implemented; Phase B planned; Phase C planned |
| selected subset `S_i` | selected context ids emitted by the selector or reconstructed from replay | Phase A implemented; Phase B planned; Phase C planned |
| token budget `B_i` | synthetic cost budget in Phase A; replay or task budget in later phases | Phase A implemented; Phase B planned; Phase C planned |
| `gamma_hat` | proxy diagnostic for approximate diminishing returns behavior | Phase A implemented; Phase B planned; Phase C planned |
| synergy fraction | pairwise interaction diagnostic over sampled or enumerated candidate pairs | Phase A implemented; Phase B planned; Phase C planned |
| greedy-vs-augmented gap | escalation diagnostic comparing greedy selection against seeded augmented greedy | Phase A implemented; Phase B planned; Phase C planned |
| `ProjectionPlan` | selected and excluded candidate artifact, including algorithm and trace metadata | Phase A implemented as sidecar artifact; Phase B/C should reuse or extend conservatively |
| `BudgetWitness` | realized token or cost accounting for the selected context | Phase A implemented as sidecar artifact; Phase B/C require stable realized counts |
| `MaterializedContext` | realized prompt or context sequence after projection | Phase A implemented as sidecar artifact; Phase B/C require deterministic reconstruction |
| escalation policy | `monitored_greedy`, `seeded_augmented_greedy`, or `interaction_aware_local_search` | Phase A implemented and smoke-tested; Phase B/C planned |

The status column records experimental readiness, not theoretical validity. In
particular, `gamma_hat` is a diagnostic estimate used for monitoring and
escalation decisions, not a certified value of the formal worst-case parameter.

## 3. Experimental phases

### Phase A - Synthetic regime benchmark

Purpose:

- Validate whether diagnostics separate known structural regimes.
- Exercise the artifact schema, event logging, CLI, and report generation without
  relying on live model behavior.

Regimes:

- redundancy-dominated
- sparse pairwise synergy
- higher-order synergy

Expected outputs:

- `gamma_hat`
- synergy fraction
- greedy-vs-augmented gap
- policy recommendation
- Markdown report
- replayable artifacts and events

Scientific claim:

- The diagnostics behave as intended under controlled synthetic structure.
- The benchmark does not validate deployed LLM context selection.

Engineering claim:

- The event schemas, runtime artifacts, CLI entry point, and report generation are
  functional enough to support the next experimental layer.

Current status:

- Implemented as a synthetic benchmark sidecar.
- Smoke-tested with green status.
- Regimes separate as intended:
  - redundancy maps to `monitored_greedy`
  - sparse pairwise synergy maps to `seeded_augmented_greedy`
  - higher-order synergy maps to `interaction_aware_local_search`

Open review items:

- Confirm regime labels are derived from diagnostics, not from the regime name.
- Confirm artifacts can reproduce the report tables without reading derived
  summaries as the source of truth.
- Confirm documentation consistently treats `gamma_hat` as a proxy diagnostic, not
  as true gamma.

### Phase B - Offline replay over dispatch traces

Purpose:

- Test diagnostics on real or generated context-projection traces.
- Validate whether the observability requirements are sufficient to reconstruct
  candidate pools, selections, budgets, materialized contexts, and diagnostics.

Inputs:

- `events.jsonl`
- `ProjectionPlan`
- `BudgetWitness`
- `MaterializedContext`
- candidate pools
- selected context ids

Required capabilities:

- Replay candidate pools.
- Reconstruct selections.
- Recompute diagnostics.
- Compare pipeline selections against diagnostic-guided alternatives.

Outputs:

- per-dispatch diagnostic report
- distribution of `gamma_hat`
- synergy fraction by task family
- greedy-vs-augmented gaps
- pipeline-vs-proxy alignment summary

Scientific claim:

- Phase B tests whether the diagnostic protocol is usable on realistic trace
  structure.
- It still does not prove Condition A or any theorem inheritance property.

Engineering claim:

- Phase B validates the observability requirements needed for replay, audit, and
  escalation analysis.

The replay contract, required trace fields, recomputation path, and missing-field
status labels are specified in
`docs/protocols/phase-b-replay-protocol.md`.

Risks:

- insufficient trace completeness
- missing realized token counts
- missing excluded candidates
- no proxy utility signal
- materialization ordering not replayable

### Phase C - Real-task benchmark

Purpose:

- Evaluate context projection behavior under realistic task distributions.
- Measure whether diagnostic-guided context projection correlates with downstream
  task behavior.

Candidate benchmark families:

- Multi-hop QA, with MuSiQue as the first candidate because the repository already
  has related data, scoring, and paragraph-level context structure.
- HotpotQA-style tasks as a secondary candidate if they stress context projection
  under the chosen setup.
- Code-agent or repo-grounded tasks only if the current runtime already supports
  clean trace capture for candidates, selected contexts, exclusions, budgets, and
  materialized prompts.
- Tool-use tasks only after artifact completeness and replay are cleanly supported.

Selection criteria:

- The benchmark must stress context selection.
- The benchmark must allow candidate pool construction.
- The benchmark must allow controlled budgets.
- The benchmark must expose redundancy, pairwise complementarity, or higher-order
  dependency.
- The benchmark must not require building a new scheduler.

Outputs:

- task success
- token cost
- diagnostic regime label
- selected context size
- pipeline-vs-proxy comparison
- failure analysis

Scientific claim:

- Phase C tests whether diagnostic-guided context projection correlates with task
  behavior on realistic distributions.
- It does not claim state-of-the-art results or general agent superiority.

When Phase C uses MuSiQue, it may share data and artifacts with the
measurement-validity protocol stack, but it asks a different question. The
distinction is recorded in `docs/phase-tree-crosswalk.md`.

## 4. Minimal viable experimental path

The recommended order is:

1. Review the Phase A implementation.
2. Freeze the artifact schema for `ProjectionPlan`, `BudgetWitness`, and
   `MaterializedContext`.
3. Add a Phase A paper-facing report table that can be regenerated from events and
   artifacts.
4. Design the Phase B replay schema.
5. Run replay on small controlled traces.
6. Choose the Phase C benchmark only after Phase B replay works.

This path keeps the work incremental and auditable. Later phases should not depend
on stale artifacts or derived reports as stable rules; `events.jsonl` and explicit
runtime artifacts should remain the replay source of truth.

## 5. Dataset and benchmark selection principles

Benchmarks should not be chosen because they are popular. They should be chosen
because they expose the structural pressures that dispatch-time context projection
is meant to handle.

Datasets and traces should be favored when they provide:

- redundant evidence
- pairwise complementary evidence
- higher-order prerequisite chains
- controllable context budgets
- replayable candidate pools
- measurable downstream utility

Likely candidates:

- Synthetic regime benchmark: already implemented and appropriate for controlled
  diagnostic validation.
- MuSiQue: strong first realistic candidate because multi-hop structure can create
  higher-order dependency and the repository already has related scaffold.
- HotpotQA-style tasks: useful as a secondary multi-hop benchmark, but only if the
  setup genuinely stresses context projection rather than simple retrieval.
- Code-agent traces: attractive if the repository already records the needed
  projection artifacts; otherwise they risk becoming a scheduler or agent-runtime
  project.
- Tool-use benchmarks: later-stage only, after trace replay and materialized
  context reconstruction are mature.

## 6. Metrics

Structural diagnostics:

- `gamma_hat`
- synergy fraction
- greedy-vs-augmented gap

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

Task metrics:

- task success
- exact match or F1 for QA tasks
- resolved rate for code tasks, if code traces become supported
- tool-call success only if tool-use traces become supported

These metrics should remain separated by layer. Structural diagnostics explain the
selection regime; replay metrics explain whether the run can be audited; task
metrics explain downstream behavior.

## 7. Claims and non-claims

Claims allowed:

- Diagnostics separate the synthetic regimes in Phase A.
- Runtime artifacts support replay when required fields are present.
- Replay can expose pipeline-vs-proxy mismatch.
- Benchmark results can inform escalation policy.

Claims not allowed:

- `gamma_hat` estimates true worst-case gamma.
- Synthetic validation transfers directly to deployed LLM behavior.
- Context selection proves scheduler optimality.
- Multi-agent execution is better than single-agent execution.
- Diagnostics imply theorem inheritance.
- Memory redesign is part of this experiment.
- Scheduler redesign is part of this experiment.
- System-level performance claims follow from these diagnostics alone.

## 8. Development roadmap

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

Phase C design:

- choose the benchmark only after Phase B replay works
- implement the smallest realistic benchmark first
- preserve the existing project boundaries around runtime resolution, artifacts,
  and append-only events

## 9. Open questions

- What proxy utility signal is available for replay?
- Can `MaterializedContext` be reconstructed exactly?
- Are excluded candidates logged?
- Is budget accounting stable across replay and live runs?
- How should task families be stratified?
- What thresholds should define greedy-valid, ambiguous, and escalate regimes?
- What is the smallest real benchmark that stresses context projection without
  requiring scheduler development?
