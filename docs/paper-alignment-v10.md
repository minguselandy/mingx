# Paper Alignment V10

This document maps the revised Context Projection Selection paper to the
repository. It is the first stop for deciding what the code and artifacts are
allowed to claim.

## What Mingx Implements

`mingx` implements companion measurement and runtime-audit scaffolds for the
revised paper:

- Phase 0/1 MuSiQue data locking, manifest validation, and smoke checks
- log-probability and `delta_loo` measurement scaffolds
- append-only event storage with `events.jsonl` as run source of truth
- mock/live cohort runners behind API profile resolution
- bridge-calibration and reliability scaffolds
- contamination diagnostics and manual escalation packets
- annotation package materialization and ingestion support
- synthetic structural tests for controlled context-projection regimes
- replayable runtime artifact surfaces such as `ProjectionPlan`,
  `BudgetWitness`, `MaterializedContext`, and `MetricBridgeWitness`
- extraction-audit infrastructure for the `M* -> M` bridge-risk lane

These pieces support measurement, replay, proxy diagnostics, and auditability.
They do not turn the repository into a theorem-level deployment verifier.

## What Mingx Does Not Implement

`mingx` does not implement or certify:

- deployed V-information weak submodularity
- theorem inheritance for retrieval, reranking, MMR, packing, or other heuristic
  pipelines
- a scheduler correctness theorem
- a recursive multi-agent runtime
- a memory architecture
- a generic context-engineering platform
- a PID paper or PID-based deployment claim
- automatic transfer from extracted candidate pool `M` back to the upstream
  information space `M*`

Reduced-scope live runs, synthetic smoke runs, and contamination-failed runs are
not scientific completion. They can be engineering-successful while still being
pilot-only or blocked for measurement interpretation.

## Revised Paper Layers To Repo Modules

| Revised paper layer | Meaning | Repo surface |
|---|---|---|
| Formal layer | Conditional V-information theory for per-round, per-agent, token-budgeted content selection | Paper text only; no code should claim to prove this for deployment |
| Proxy layer | CI, replay, log-loss, or utility finite-difference measurements under bridge conditions | `cps/scoring/`, `cps/analysis/bridge.py`, `cps/experiments/diagnostics.py`, measurement exports |
| Pipeline layer | Retrieval, reranking, MMR, packing, and other heuristics | `cps/runtime/retrieval.py`, synthetic selectors in `cps/experiments/selection.py`, run configs |
| Runtime layer | Auditable artifacts and replay/monitoring interfaces | `cps/experiments/artifacts.py`, `cps/store/measurement.py`, `events.jsonl`, runtime exports |
| Metric bridge | Claim-level gate between V-information proxy claims, calibrated proxy claims, operational-utility-only claims, and ambiguity | `MetricBridgeWitness` in `cps/experiments/artifacts.py`; synthetic runs materialize `structural_synthetic_only` witnesses, while real proxy bridges require future calibration evidence |
| Extraction layer | Separate `M* -> M` bridge-risk audit | Phase 1 contamination, annotation, replacement, follow-up, and extraction-uniformity protocol docs |

The runtime projection chain is:

1. `ProjectionPlan`
2. `BudgetWitness`
3. `MaterializedContext`
4. `MetricBridgeWitness`

`CandidatePool` is required replay substrate. It records what was available for
selection, but it is not one of the four core paper runtime artifacts.

## Claim-Level Reporting Rules

Every report that interprets proxy diagnostics should assign one of these claim
levels:

| Claim level | When allowed | What it may say |
|---|---|---|
| `Vinfo_proxy_certified` | log-loss or CI measurements match the paper's V-information proxy conditions and bridge assumptions are explicitly satisfied with fresh bridge state | Proxy evidence is relevant to the formal V-information object |
| `calibrated_proxy` | a measured bridge links the operational metric to the proxy but does not fully satisfy V-information conditions, with fresh bridge state | Diagnostics are calibrated proxy evidence, not direct theorem evidence |
| `operational_utility_only` | diagnostics are finite differences over task success, rubric score, or other non-decomposable operational utility without a V-information bridge | Diagnostics may guide escalation for the operational metric only |
| `structural_synthetic_only` | the value function is synthetic oracle structure used for controlled Phase A validation | Diagnostics may validate structural plumbing only |
| `ambiguous` | required bridge evidence is missing, conflicting, stale, or unknown | Do not make proxy-regime or theorem-adjacent claims |

Reports must also keep these labels separate:

- `selector_regime_label`: protocol label, one of `greedy_valid`, `escalate`,
  or `ambiguous`
- `selector_action`: operational recommendation, such as `monitored_greedy`,
  `seeded_augmented_greedy`, `interaction_aware_local_search`, or
  `no_certified_switch`
- `metric_claim_level`: bridge-qualified claim scope

Do not collapse these into a single "policy recommendation" or imply theorem
inheritance from them.

## Legacy-To-Revised Terminology

| Legacy term | Revised term / interpretation |
|---|---|
| `gamma_hat` | `trace_decay_proxy` or `legacy_trace_ratio`; not headline gamma |
| post-hoc trace ratio | TraceDecay if path-local, block-ratio LCB if block-based and bridge-qualified |
| policy recommendation | `metric_claim_level` + `selector_regime_label` + `selector_action` |
| v8 canonical framing | revised conditional-theory / metric-bridge / proxy-regime framing |
| synthetic policy match | pre-registered validity gate |
| Phase 1 MuSiQue validation | metric / extraction infrastructure, not selector-regime proof |
| synergy fraction | interaction mass when reported as a revised diagnostic |
| runtime interface requirements | `ProjectionPlan` -> `BudgetWitness` -> `MaterializedContext` -> `MetricBridgeWitness` |

## Practical Reading Rule

When a future contributor reads old artifacts or historical docs, translate old
diagnostic language before drawing conclusions. In particular, a field named
`gamma_hat` in legacy synthetic outputs is a compatibility field unless a
current report explicitly reconstructs a block-ratio LCB diagnostic and assigns
a valid metric-bridge claim level.
