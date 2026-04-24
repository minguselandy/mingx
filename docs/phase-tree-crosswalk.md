# Phase Tree Crosswalk

## Purpose

This project currently uses two phase vocabularies that are related but not
interchangeable.

The paper-facing experiment stack is:

- Phase A: synthetic regime benchmark
- Phase B: offline replay over dispatch traces
- Phase C: realistic-task context-projection benchmark

The measurement-validity protocol stack is:

- Phase 0: specification lock and protocol setup
- Phase 1: MuSiQue instrumentation-feasibility probe
- Phase 2: parent extraction-uniformity design
- Phase 3: pilot analytical post-processing of Phase 1 data
- Phase 4: full-study or deployment-facing re-audit, deferred

The two stacks are linked by data and artifacts, not by a one-to-one phase
renaming. The most important asymmetry is that the MuSiQue data path can support
both stacks while answering different scientific questions. Phase 1 through
Phase 3 audit the extraction-uniformity assumption. Phase A through Phase C audit
the diagnostic protocol for dispatch-time context projection.

## Crosswalk

| Experiment milestone | Measurement-validity counterpart | Gates | Scientific question | Consumes | Produces | Current status |
|---|---|---|---|---|---|---|
| Phase A synthetic regime benchmark | No direct Phase 0/1/2/3 counterpart; proxy-layer sidecar | None | Do `gamma_hat`, synergy fraction, and greedy-vs-augmented gap separate controlled structural regimes? | Synthetic set-function configs and fixed policy thresholds | `events.jsonl`, candidate pools, `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, diagnostics, report | Implemented, smoke-tested, green, and regime-separating |
| Phase B offline replay | Uses Phase 1 or openWorker traces only if replay fields are present | Gate 2 completion package and Gate 5 feasibility input | Can dispatch traces reconstruct candidate pools, selections, budgets, materialized context, and diagnostics without live inference? | `events.jsonl`, candidate pools, selected and excluded ids, proxy utility signal, materialization order, token accounting | Per-dispatch diagnostic report, missing-field classification, pipeline-vs-proxy alignment summary | Planned; protocol now specified separately |
| Phase C realistic-task benchmark | Overlaps structurally with Phase 2/3/4 on MuSiQue when MuSiQue is selected | Gates 3-5 for MuSiQue-derived inputs | Does diagnostic-guided context projection correlate with realistic task behavior? | Phase B replay schema, task-derived context pools, controlled budgets, task scoring | Task success, token cost, diagnostic labels, selection summaries, failure analysis | Planned after Phase B replay works |
| Phase 1 MuSiQue probe | Measurement-validity stack Phase 1 | Gates 1-3 | Is the `delta_loo` measurement apparatus stable, bridgeable, and label-reliable? | MuSiQue dev split, DashScope model access, annotator process | Measurement store, bridge diagnostics, contamination diagnostic, tertile labels, kappa values | Implementation complete locally; protocol-full live execution remains operationally gated |
| Phase 3 pilot | Measurement-validity stack Phase 3 | Gates 4-5 | Does the Phase 1 sample warrant a full extraction-uniformity study? | Measurement-validated Phase 1 outputs and retrieval simulation configs | Pilot `Delta_hat`, confidence intervals, sensitivity analyses, Gate 5 decision record | Planned analytical post-processing |
| openWorker trace audit | Phase 4 feasibility and Phase B trace-readiness substrate | Gate 2 completion package and Gate 5 input | Are the deployment traces sufficient for replay or direct audit? | Concrete openWorker code path or explicit no-code-path blocker record | Trace-field availability map and engineering effort classification | Template exists; no concrete code-path conclusion in this repository |
| Phase 4 full study or direct audit | Measurement-validity stack Phase 4 | After Gate 5 | Should full-scale MuSiQue or deployment-facing extraction audit proceed? | Gate 5 decision record, Phase 2 Section 7.2 handoff parameters, trace audit outcome | Full-study or direct-audit report | Skeleton only; not an executable protocol |

## MuSiQue overlap

Phase C on MuSiQue and Phase 2/3/4 on MuSiQue can use the same question pools,
paragraph pools, value measurements, and retrieval simulations. They should not
be described as the same experiment.

Phase 2/3/4 asks whether extraction completeness is approximately uniform across
value strata. Its key quantities are `c_high`, `c_low`, `Delta_hat`, bridge
validity, contamination status, and annotation reliability.

Phase C asks whether dispatch-time context projection diagnostics and escalation
policies behave usefully on realistic tasks. Its key quantities are candidate
pool `M`, selected subset `S_i`, token budget `B_i`, `gamma_hat`, synergy
fraction, greedy-vs-augmented gap, `ProjectionPlan`, `BudgetWitness`, and
`MaterializedContext`.

The shared dataset should therefore be treated as common substrate, not common
claim structure.

## Phase 1 as Phase B substrate

Phase 1 outputs become Phase B replay substrate only when the trace record is rich
enough to reconstruct dispatch-time context projection. A Phase 1 run is not a
Phase B replay input merely because it has an `events.jsonl` file.

At minimum, a Phase B-compatible Phase 1-derived trace must include:

- full paragraph candidate pools with stable ids
- selected and excluded context ids
- replayable token budget and realized token counts
- materialization order and content hash
- proxy utility signal sufficient for diagnostic recomputation
- dispatch identity linking candidate pool, selection, budget witness, and
  materialized context

Reduced-scope live pilot artifacts, synthetic smoke artifacts, and derived
summaries must not be treated as Phase B scientific evidence unless they satisfy
the replay protocol directly.

## Reading order

Use this crosswalk as the navigation page when deciding which document answers
which question:

- `docs/experiment-design-overview.md` defines the Phase A/B/C experiment stack.
- `docs/protocols/phase0-specification.md`, `phase1-protocol.md`, and
  `phase2-design.md` define the measurement-validity stack.
- `docs/protocols/execution-readiness-checklist.md` defines the gate sequence.
- `docs/protocols/phase-b-replay-protocol.md` defines the Phase B replay contract.
- `docs/protocols/phase4-design-skeleton.md` records the deferred Phase 4 branch
  structure.
