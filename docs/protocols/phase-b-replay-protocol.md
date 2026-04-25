# Phase B Replay Protocol: Dispatch Trace Diagnostics

**Document status:** Protocol specification for offline replay. This document does
not authorize live inference, new benchmark execution, scheduler changes, memory
changes, or benchmark-logic changes.

## 1. Scope

Phase B tests whether dispatch-time context projection traces can be replayed well
enough to recompute the paper's proxy diagnostics and compare observed pipeline
selections against diagnostic-guided alternatives.

Phase B is an offline replay protocol. It consumes recorded traces and cached
proxy-utility records. It must not depend on re-running live inference to fill
missing replay fields.

Phase B validates observability and diagnostic recomputation. It does not prove
Condition A, certify deployed V-information weak submodularity, validate
scheduler correctness, or make a system-level performance claim.

## 2. Required replay inputs

Each replayable dispatch record must bind the following inputs by stable
`run_id`, `dispatch_id`, `agent_id`, and `round_id`.

| Input | Required fields | Replay purpose |
|---|---|---|
| `events.jsonl` | append-only events with run, dispatch, agent, round, event type, timestamp or ordering key, and payload | Source of truth for grouping and reconstruction |
| `CandidatePool` | candidate ids, content or content hash, token cost, provenance, candidate-pool hash, pool ordering if applicable | Reconstruct `M` and candidate-slice diagnostics |
| `ProjectionPlan` | selected ids, excluded ids, algorithm, score config, selection trace, candidate-pool hash | Reconstruct `S_i` and observed pipeline selection |
| `BudgetWitness` | token budget, estimated tokens, realized tokens, within-budget flag, tolerance violations | Reconstruct `B_i` and budget compliance |
| `MaterializedContext` | selected ids, section order, content hash, truncation or clipping record, realized token count | Reconstruct actual context sent downstream |
| `MetricBridgeWitness` | metric family, bridge evidence, claim level, ambiguity reason if any, proxy or utility scope | Qualify whether diagnostics support V-information proxy, calibrated proxy, operational-utility-only, or ambiguous claims |
| diagnostics, if replaying prior diagnostic outputs | prior `block_ratio_*`, interaction, triple-excess, gap, claim-level, regime-label, and selector-action fields with diagnostic version | Compare prior outputs against recomputed replay diagnostics |
| cached utility/log-loss records | singleton values, per-step marginal values, pairwise utility records, block utility records, triple utility records, log-loss records, or cached scoring table, with utility model metadata | Recompute diagnostics without live inference |
| task metadata | task family, dataset id, split, seed, model/profile ids where applicable | Stratify diagnostic distributions and alignment summaries |

If a concrete openWorker path is unavailable, the Phase B record should say
`no_concrete_code_path_available` rather than inventing trace availability.

## 3. Diagnostic recomputation path

Replay proceeds dispatch by dispatch:

1. Group events by `run_id`, `dispatch_id`, `agent_id`, and `round_id`.
2. Verify that candidate-pool hashes agree across `ProjectionPlan`,
   `BudgetWitness`, `MaterializedContext`, and diagnostic records.
3. Rebuild `M` from the candidate pool and `S_i` from selected ids.
4. Rebuild `B_i` from `BudgetWitness` and verify selected token cost against the
   realized budget fields.
5. Rebuild materialized context order from `MaterializedContext`; do not infer
   order from selected ids when an explicit order is absent.
6. Recompute block-ratio LCB diagnostics from cached singleton, block, and
   marginal values where the trace supports them:
   `block_ratio_lcb_b2`; `block_ratio_lcb_star`, if configured; and
   `block_ratio_lcb_b3`, if higher-order stress is configured.
7. Recompute `TraceDecay` as a path-local marginal-decay statistic only. It is
   not a headline weak-submodularity diagnostic.
8. Recompute pairwise interaction mass from the configured top-L candidate
   slice using cached singleton and pairwise utility records.
9. Recompute triple excess where cached triple or block utility records exist.
10. Recompute the greedy-vs-augmented gap by replaying greedy and seeded
    augmented greedy over the cached utility table and budget.
11. Derive `metric_claim_level` using `MetricBridgeWitness`.
12. Derive `selector_regime_label` as `greedy_valid`, `escalate`, or
    `ambiguous`, then derive `selector_action` as `monitored_greedy`,
    `seeded_augmented_greedy`, `interaction_aware_local_search`, or
    `no_certified_switch`.
13. Compare the observed pipeline selection against the diagnostic-guided
    alternatives.

Legacy `gamma_hat` may appear in older artifacts only as `TraceDecay` /
legacy-trace-ratio compatibility data. `gamma_hat is not a true gamma estimator`
and must not be described as the headline weak-submodularity diagnostic.

The comparison must report at least:

- selected-set overlap
- selected token cost and budget utilization
- observed value under the cached proxy utility
- `metric_claim_level`
- `selector_regime_label`
- `selector_action`
- whether the observed algorithm matches the diagnostic recommendation
- any missing fields that weaken interpretation

## 4. Missing-field outcomes

Every replay attempt must receive exactly one status label.

| Status | Definition | Allowed use |
|---|---|---|
| `replay_usable` | `M`, `S_i`, `B_i`, selected and excluded ids, materialization order, realized token counts, replay diagnostics, metric bridge witness, and proxy utility records are all present | Full Phase B diagnostic report |
| `pilot_degraded` | Structural diagnostics can be recomputed, but materialized context, realized token counts, or task metadata are incomplete | Exploratory pilot only; no task-facing claim |
| `replay_partial` | Dispatch identity, candidate pool, and selected set are recoverable, but one or more core diagnostics cannot be recomputed | Observability gap report only |
| `replay_unusable` | Candidate pool, selected set, or dispatch binding cannot be reconstructed | Exclude from diagnostic aggregation; report as trace failure |

Missing excluded candidates are a core replay defect because they prevent
candidate-pool completeness checks. Missing materialization order is a replay
defect even if selected ids are present, because context order can affect utility
and downstream behavior.

## 5. Claim-level downgrade rules

Phase B reports must downgrade claim level before reporting selector-regime
conclusions:

| Condition | Required downgrade |
|---|---|
| Missing `MetricBridgeWitness` | `ambiguous` or observability-only; do not emit a bridge-qualified claim |
| stale bridge | `ambiguous`; recalibrate before making proxy-regime claims |
| operational-only utility | `operational_utility_only`, not `Vinfo_proxy_certified` |
| missing triple evidence under higher-order risk | `ambiguous`; do not emit high-confidence `greedy_valid` |
| insufficient denominator signal | `ambiguous`; denominator-uninformative block-ratio samples are not low-ratio failures |

## 6. Outputs

Phase B produces:

- replay manifest with one row per dispatch
- per-dispatch diagnostic records
- missing-field report
- block-ratio LCB distributions where supported
- interaction mass by task family
- triple-excess diagnostics where supported
- greedy-vs-augmented gap distribution
- pipeline-vs-proxy alignment summary
- `metric_claim_level`, `selector_regime_label`, and `selector_action` summary
- replay status counts

The report must state which dispatches were `replay_usable` and must not mix
`pilot_degraded`, `replay_partial`, or `replay_unusable` records into headline
diagnostic claims.

## 7. Non-goals

Phase B does not implement:

- live model inference
- a new scheduler
- a recursive multi-agent framework
- a memory architecture redesign
- an openWorker port
- benchmark scoring changes
- theorem-inheritance claims

Phase B is an audit and replay layer. Any implementation that requires changing
runtime control flow to create missing trace data belongs to a separate
observability engineering plan.
