# Phase 4 Design Skeleton

**Document status:** Forward-planning skeleton only. This is not an executable
Phase 4 protocol and should not be used to launch experiments without a later
full design document.

## 1. Purpose

Phase 4 is the deferred full-study or deployment-facing audit stage. This
skeleton exists so a positive Gate 5 decision does not bottleneck on deciding the
basic branch structure.

Phase 4 direct audits report extraction-completeness and `M* -> M bridge risk`
status separately from projection diagnostics. They can support
`MetricBridgeWitness` qualification or extraction-risk reporting, but they do
not prove selector-regime validity and do not extend the weak-submodular theorem
from `M` to `M*`.

Phase 4 inherits the Phase 2 Section 7.2 handoff parameters:

- pilot `Delta_hat` point estimate and variance
- pilot within-stratum variance
- bridge-form sensitivity, especially linear versus isotonic results
- top-K sensitivity and prioritization

Phase 4 also consumes the openWorker trace-field audit classification:

- `one-week port`
- `one-month effort`
- `multi-month project`

## 2. Branch selection

| Gate 5 outcome | openWorker audit outcome | Default Phase 4 branch |
|---|---|---|
| Full study warranted | `one-week port` | openWorker direct-audit branch can proceed, with MuSiQue full study retained as fallback or comparison |
| Full study warranted | `one-month effort` | choose between MuSiQue full study and openWorker direct audit based on calendar budget; document the tradeoff |
| Full study warranted | `multi-month project` | MuSiQue full-study branch first; openWorker audit becomes future work |
| Full study not warranted | `one-week port` or `one-month effort` | optional openWorker direct audit if deployment-facing claims remain central |
| Full study not warranted | `multi-month project` | conclude MuSiQue workstream with scope caveat; defer openWorker |
| Indeterminate | any audit outcome | apply the Phase 2 contextual adjudication pathway before choosing a branch |
| No concrete openWorker code path | any Gate 5 outcome | record the blocker explicitly; do not infer trace availability |

This branch table is a planning default. A later executable Phase 4 protocol must
record the final branch choice and justification.

## 3. MuSiQue full-study branch

The MuSiQue branch scales the Phase 2 design beyond the Phase 3 pilot.

Planned inherited defaults:

- full-study size: `N_full = 450` unless Phase 3 power recalculation changes it
- primary retrieval target: bi-encoder plus cross-encoder
- sensitivity targets: BM25, bi-encoder-only, hybrid RRF
- top-K sweep: `K in {3, 5, 10}`
- bridge sensitivity: linear and isotonic at minimum
- composition-robustness: added as the Phase 2 full-study sensitivity arm

Expected outputs:

- full-study extraction-uniformity result
- `c_high`, `c_low`, and `Delta_hat` with confidence intervals
- sensitivity analysis report
- bridge-form sensitivity report
- contamination and measurement-validity caveats inherited from Phase 1

This branch remains a MuSiQue retrieval-plus-reranking audit. It does not close
the openWorker extraction-gate transfer gap by itself.

## 4. openWorker direct-audit branch

The openWorker branch audits deployment-facing traces directly, but only if the
trace-field audit finds sufficient replay support or a bounded export path.

Minimum trace requirements:

- candidate pool
- greedy trace or equivalent selection trace
- selected and excluded sets
- budget witness
- materialized context
- extraction alignment from source evidence to structured item
- stable round-level binding across all records

Expected outputs:

- trace-field availability map
- engineering effort classification
- replayability status counts
- extraction-completeness or projection-diagnostic report, depending on available
  utility signal
- explicit scope caveats for any missing fields

This branch must not require a scheduler redesign, memory architecture redesign,
or full runtime rewrite. If those are necessary, the branch is classified as a
multi-month project and moved out of the current experimental program.

## 5. Later protocol requirements

A future executable Phase 4 protocol must specify:

- final branch selection and rationale
- sample size or trace count
- exact candidate-pool and materialization schema
- utility signal used for value stratification or projection diagnostics
- confidence interval and bootstrap procedure
- missing-field exclusion rules
- reporting templates
- claim limits and paper-section update path

Until that document exists, this file is only a planning skeleton.
