# Phase Tree Crosswalk

## Purpose

This project currently uses two phase vocabularies that are related but not
interchangeable.

The paper-facing experiment stack is:

- Phase A: synthetic structural validity of diagnostics
- Phase B: offline replay and artifact sufficiency
- Phase C: realistic-task projection behavior

The measurement-validity protocol stack is:

- Phase 0: specification lock and protocol setup
- Phase 1: MuSiQue instrumentation-feasibility probe
- Phase 2: parent extraction-uniformity design
- Phase 3: pilot analytical post-processing of Phase 1 data
- Phase 4: full-study or deployment-facing re-audit, deferred

The two stacks are linked by data and artifacts, not by a one-to-one phase
renaming. Phase 1 through Phase 4 build measurement, bridge, contamination,
annotation, and extraction-validity infrastructure. They do not prove selector
regimes or theorem inheritance for heuristic pipelines.

## Extraction Boundary

The revised paper separates projection diagnostics from extraction quality:
formal approximation statements apply to optimization over extracted candidate pool `M`, after a candidate pool has already been formed.

The extraction audit is therefore an `M* -> M bridge risk` audit. It measures
candidate-pool quality, extraction completeness, contamination status,
annotation reliability, and bridge usability as end-to-end bottlenecks before
selector diagnostics are interpreted.

Extraction uniformity is a testable assumption, not a theorem. Positive
extraction-risk evidence can support `MetricBridgeWitness` qualification or
extraction-risk reporting, but it does not prove selector-regime validity and
does not extend the weak-submodular theorem from `M` to `M*`.

Phase 1/2/3/4 are metric, contamination, annotation, bridge, and
extraction-validity infrastructure. They do not prove selector-regime validity.

## Crosswalk

| Experiment milestone | Measurement-validity counterpart | Gates | Scientific question | Consumes | Produces | Current status |
|---|---|---|---|---|---|---|
| Phase A synthetic structural benchmark | No direct Phase 0/1/2/3 counterpart; proxy-layer sidecar | None | Do block-ratio LCB, interaction mass, triple-excess diagnostics, and greedy-vs-augmented gap separate controlled structural regimes? | Synthetic set-function configs and fixed reporting thresholds | `events.jsonl`, candidate pools, `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, diagnostics, report | Implemented, smoke-tested, green, and regime-separating as a pre-registered validity gate |
| Phase B offline replay | Uses Phase 1 or openWorker traces only if replay fields are present | Gate 2 completion package and Gate 5 feasibility input | Can dispatch traces reconstruct candidate pools, selections, budgets, materialized context, metric bridge witnesses, and diagnostics without live inference? | `events.jsonl`, candidate pools, selected and excluded ids, proxy utility signal, materialization order, token accounting | Per-dispatch diagnostic report, missing-field classification, pipeline-vs-proxy alignment summary, claim-level labels | Planned; protocol now specified separately |
| Phase C realistic-task benchmark | Overlaps structurally with Phase 2/3/4 on MuSiQue when MuSiQue is selected | Gates 3-5 for MuSiQue-derived inputs | Does diagnostic-guided context projection correlate with realistic task behavior under explicit metric-bridge qualification? | Phase B replay schema, task-derived context pools, controlled budgets, task scoring | Task success, token cost, diagnostic labels, selector regime labels, selection summaries, failure analysis | Planned after Phase B replay works |
| Phase 1 MuSiQue probe | Measurement-validity stack Phase 1 | Gates 1-3 | Is the `delta_loo` measurement apparatus stable, bridgeable, contamination-aware, and label-reliable? | MuSiQue dev split, DashScope model access, annotator process | Measurement store, bridge diagnostics, contamination diagnostic, tertile labels, kappa values | Implementation complete locally; protocol-full live execution remains operationally gated |
| Phase 3 pilot | Measurement-validity stack Phase 3 | Gates 4-5 | Does the Phase 1 sample warrant a full extraction-uniformity study? | Measurement-validated Phase 1 outputs and retrieval simulation configs | Pilot `Delta_hat`, confidence intervals, sensitivity analyses, Gate 5 decision record | Planned analytical post-processing |
| openWorker trace audit | Phase 4 feasibility and Phase B trace-readiness substrate | Gate 2 completion package and Gate 5 input | Are deployment traces sufficient for replay, metric-bridge qualification, or direct extraction audit? | Concrete openWorker code path or explicit no-code-path blocker record | Trace-field availability map and engineering effort classification | Template exists; no concrete code-path conclusion in this repository |
| Phase 4 full study or direct audit | Measurement-validity stack Phase 4 | After Gate 5 | Should full-scale MuSiQue or deployment-facing extraction audit proceed? | Gate 5 decision record, Phase 2 Section 7.2 handoff parameters, trace audit outcome | Full-study or direct-audit report | Skeleton only; not an executable protocol |

## Revised Diagnostic Language

The headline weak-submodularity diagnostic is now block-ratio LCB, not the old
trace ratio. Reports should use the following family where available:

- `block_ratio_lcb_b2`
- `block_ratio_lcb_star`
- `block_ratio_lcb_b3`
- interaction mass
- triple-excess diagnostics
- greedy-vs-augmented gap
- `metric_claim_level`
- `selector_regime_label`
- `selector_action`

`TraceDecay` is retained only as a path-local marginal-decay statistic. It can
help describe whether value decays along a realized selection path, but it is
not a submodularity-ratio estimator and must not be used as the headline
weak-submodularity diagnostic.

## MuSiQue Overlap

Phase C on MuSiQue and Phase 2/3/4 on MuSiQue can use the same question pools,
paragraph pools, value measurements, and retrieval simulations. They should not
be described as the same experiment.

Phase 2/3/4 asks whether extraction completeness is approximately uniform across
value strata. Its key quantities are `c_high`, `c_low`, `Delta_hat`, bridge
validity, contamination status, and annotation reliability.

Phase C asks whether dispatch-time context projection diagnostics and escalation
policies behave usefully on realistic tasks. Its key quantities are candidate
pool `M`, selected subset `S_i`, token budget `B_i`, block-ratio LCB,
interaction mass, triple-excess diagnostics, greedy-vs-augmented gap,
`ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, and
`MetricBridgeWitness`.

The shared dataset should therefore be treated as common substrate, not common
claim structure.

## Phase 1 As Phase B Substrate

Phase 1 outputs become Phase B replay substrate only when the trace record is
rich enough to reconstruct dispatch-time context projection. A Phase 1 run is
not a Phase B replay input merely because it has an `events.jsonl` file.

At minimum, a Phase B-compatible Phase 1-derived trace must include:

- full paragraph candidate pools with stable ids
- selected and excluded context ids
- replayable token budget and realized token counts
- materialization order and content hash
- proxy utility signal sufficient for diagnostic recomputation
- metric-bridge witness or enough metadata to assign a claim level
- dispatch identity linking candidate pool, selection, budget witness,
  materialized context, and metric bridge witness

Reduced-scope live pilot artifacts, synthetic smoke artifacts, and derived
summaries must not be treated as Phase B scientific evidence unless they satisfy
the replay protocol directly.

## Reading Order

Use this crosswalk as the navigation page when deciding which document answers
which question:

- `docs/paper-alignment-v10.md` maps the revised paper to repository modules.
- `docs/experiment-design-overview.md` defines the Phase A/B/C experiment stack.
- `docs/protocols/phase0-specification.md`, `phase1-protocol.md`, and
  `phase2-design.md` define the measurement-validity stack.
- `docs/protocols/execution-readiness-checklist.md` defines the gate sequence.
- `docs/protocols/phase-b-replay-protocol.md` defines the Phase B replay
  contract.
- `docs/protocols/phase4-design-skeleton.md` records the deferred Phase 4
  branch structure.
