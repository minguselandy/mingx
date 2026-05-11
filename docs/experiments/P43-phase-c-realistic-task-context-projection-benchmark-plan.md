# P43 Phase C Realistic-Task Context Projection Benchmark Plan

**Milestone:** P43
**Experiment stack:** Phase C realistic-task projection behavior
**Status:** implemented offline scaffold
**Live API:** optional and separately gated
**Maximum claim:** `operational_utility_only` for the implemented scaffold


## Source Basis

This document is aligned to:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`
- `docs/experiment-design-overview.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/phase-tree-crosswalk.md`
- `docs/current-work-summary.md`
- `configs/runs/README.md`

Local execution status must always be verified from the no-git automation state, run plans, concrete artifacts, and validation logs. Paper text and roadmap documents are not run-completion evidence.


## 1. Purpose

P43 evaluates context-projection behavior on realistic tasks after artifact schema and Phase B replay are working. It asks whether diagnostic-guided context projection behaves usefully under realistic candidate pools, budgets, and task metrics.

It does not claim scheduler optimality, multi-agent superiority, or deployed V-information weak submodularity.

Implemented scaffold:

- `cps/experiments/phase_c_benchmark.py` builds two deterministic realistic-task fixtures:
  - `realistic_bridge_lookup`
  - `realistic_runtime_triage`
- The default run evaluates four separated conditions:
  - `no_cps_baseline`
  - `heuristic_selector_baseline`
  - `cps_runtime_audit_scaffold`
  - `diagnostic_guided_escalation`
- Each dispatch writes replay-compatible `CandidatePool`, `ProjectionPlan`,
  `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and
  diagnostics records to the caller-provided output directory.
- Task metrics are operational support-coverage metrics, not V-information or
  log-loss bridge metrics.
- Missing or operational-only metric bridge evidence remains capped at
  `operational_utility_only`.


## Claim Boundary Lock

This milestone is part of the Context Projection Selection measurement and runtime-audit scaffold. It must not be reported as deployed V-information certification, theorem inheritance for a heuristic pipeline, scheduler correctness, full system validation, or `measurement_validated` evidence.

Conservative claim rules:

- contamination failure => `pilot_only` and scientific-stop for measurement interpretation
- missing human labels => not `measurement_validated`
- missing human-human kappa => not `measurement_validated`
- stale or missing metric bridge => `operational_utility_only` or `ambiguous`
- synthetic-only evidence => `vinfo_proxy_supported`, not deployed V-information certification
- replay package completeness => replay/observability evidence only, not scientific validation
- model-adjudicated labels => not human labels
- Codex/model audit => not human review
- live API success alone => operational evidence only, not measurement validation


## 2. Candidate Benchmark Substrate

MuSiQue is the preferred initial substrate because it provides multi-hop questions and paragraph-level context structure that can be transformed into candidate pools.

The benchmark should distinguish:

- Phase C context-projection behavior;
- Phase 2/3/4 extraction-uniformity and measurement-validity work.

They may share data, but they do not share claim structure.

## 3. Experimental Conditions

Recommended conditions:

| Condition | Description |
|---|---|
| `no_cps_baseline` | fixed or naïve context assembly |
| `heuristic_selector_baseline` | retrieval / reranking / MMR / packing without full audit chain |
| `cps_runtime_audit_scaffold` | selector plus artifacts, diagnostics, and claim gate |
| `diagnostic_guided_escalation`, optional | seeded augmented greedy or local search when diagnostics trigger escalation |

## 4. Required Per-Dispatch Artifacts

Each task dispatch must write:

```text
CandidatePool
ProjectionPlan
BudgetWitness
MaterializedContext
MetricBridgeWitness
diagnostics
selection_summary
task_output
task_score, if available
claim_gate_record
```

## 5. Metrics

### 5.1 Structural diagnostics

```text
block_ratio_lcb_b2
block_ratio_lcb_star
block_ratio_lcb_b3
interaction_mass
triple_excess
augmented_greedy_gap
selector_regime_label
selector_action
```

### 5.2 Selection metrics

```text
selected_token_cost
budget_utilization
selected_set_overlap_across_conditions
redundancy_rate
diversity_score
candidate_pool_coverage
```

### 5.3 Replay metrics

```text
replay_status
artifact_completeness
missing_field_count
hash_consistency
materialization_order_present
metric_bridge_witness_present
```

### 5.4 Task metrics

Use the task metric appropriate to the benchmark:

```text
exact_match
F1
answer logprob or log-loss, if available
rubric or operational utility
model-adjudicated score, if Route B is used
```

If the metric is not log-loss aligned or bridge-calibrated, assign `operational_utility_only`.

## 6. Metric Bridge Assignment

Every condition-level result must be tagged as one of:

```text
vinfo_proxy_supported
calibrated_proxy_supported
operational_utility_only
ambiguous_metric
```

For Phase C, `vinfo_proxy_supported` requires fresh bridge evidence, not task success alone. The deterministic Phase C scaffold should normally remain `operational_utility_only`.

## 7. Implemented Targets

```text
cps/experiments/phase_c_benchmark.py
tests/test_phase_c_benchmark.py
```

## 8. Outputs

```text
phase_c_manifest.json
phase_c_dispatches.jsonl
phase_c_condition_results.json
phase_c_replay_status.json
phase_c_diagnostics_summary.json
phase_c_task_metrics.json
phase_c_claim_gate_report.json
phase_c_report.md
```

The implementation writes these outputs under the supplied `--output-dir`.
Persistent benchmark artifacts are not required for the P43 commit candidate;
tests exercise temporary output directories and Phase B replay compatibility.

## 9. Acceptance Criteria

P43 is accepted when:

- every condition writes replayable artifacts;
- task metrics are separated from structural diagnostics;
- metric-bridge scope is explicit;
- results do not claim theorem inheritance;
- Phase B can replay at least the benchmark's artifact records;
- report distinguishes operational usefulness from measurement validation.

Current validation:

```text
python -m compileall cps scripts => passed
uv run pytest tests/test_phase_c_benchmark.py -q => 5 passed
uv run pytest -q => 435 passed, 4 skipped
```
