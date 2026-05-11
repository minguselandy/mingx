# P38 Synthetic Structural Benchmark Hardening Plan

**Milestone:** P38  
**Experiment stack:** Phase A synthetic structural validity  
**Status:** implementation plan  
**Live API:** prohibited  
**Maximum claim:** `vinfo_proxy_supported`


## Source Basis

This document is aligned to:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`
- `docs/experiment-design-overview.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/phase-tree-crosswalk.md`
- `docs/current-work-summary.md`
- `configs/runs/README.md`

Local execution status must always be verified from `git status`, run plans, `run_summary.json`, `events.jsonl`, and concrete artifacts. Paper text and roadmap documents are not run-completion evidence.


## 1. Purpose

P38 strengthens the Phase A synthetic benchmark so that it can serve as the structural-validity floor for the paper's diagnostic protocol. The benchmark tests whether block-ratio LCBs, interaction mass, triple-excess diagnostics, and greedy-vs-augmented gap separate controlled synthetic regimes.

It does not test deployed frontier models, live APIs, scheduler correctness, memory correctness, or scientific measurement validation.


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


## 2. Synthetic Families

### 2.1 Redundancy-dominated

Findings are organized into clusters. The first item in a cluster has high value; subsequent near-duplicates add small residual value. Expected signature:

- high `block_ratio_lcb_b2`
- low positive complementarity mass
- no triple-excess alarm
- small greedy-vs-augmented gap
- `selector_regime_label = greedy_supported`, if the pre-registered threshold is met

### 2.2 Sparse pairwise synergy

The value function contains sparse pairwise bonuses:

```text
f(S) = sum_i w_i 1[i in S] + sum_(i,j in E) beta_ij 1[i,j in S]
```

Expected signature:

- lower pair-block ratio
- detected interaction mass
- seeded augmented greedy improves over plain greedy on a meaningful fraction of instances
- `selector_regime_label = pairwise_escalate` or calibrated warning, depending on thresholds

### 2.3 Higher-order / prerequisite synergy

The value function contains triple or prerequisite-chain bonuses:

```text
f(S) = singleton value + pairwise value + sum_(i,j,k in T) tau_ijk 1[i,j,k in S]
```

Expected signature:

- pairwise diagnostics may look incomplete;
- `block_ratio_lcb_b3` or triple-excess test should fire;
- high-confidence `greedy_supported` must be withheld;
- ambiguous labels are acceptable and must be counted separately.

## 3. Required Outputs

The benchmark must write:

```text
events.jsonl
candidate_pools.jsonl
projection_plans.jsonl
budget_witnesses.jsonl
materialized_contexts.jsonl
metric_bridge_witnesses.jsonl
diagnostics.jsonl
summary.json
report.md
```

The report must include:

- family-level outcome table;
- per-regime diagnostic signature;
- ambiguity count;
- pre-registered gate status;
- failure reasons;
- claim boundary statement.

## 4. Diagnostic Fields

Required current diagnostic fields:

```text
block_ratio_lcb_b2
block_ratio_lcb_star
block_ratio_lcb_b3
interaction_mass
triple_excess
augmented_greedy_gap
metric_claim_level
selector_regime_label
selector_action
```

`TraceDecay` may be reported as a path-local marginal-decay signal only. It must not be used as the headline weak-submodularity diagnostic.

## 5. Pre-Registered Gate

The benchmark passes only if:

1. redundancy-dominated instances mostly receive the expected high block-ratio / low synergy signature;
2. pairwise-synergy instances show detectable pairwise interaction mass or seeded-greedy improvement;
3. higher-order instances do not receive high-confidence `greedy_supported` labels;
4. ambiguity is counted separately and is not counted as a successful regime match;
5. generated artifacts are replayable under the schema version used by P39.

## 6. Recommended Implementation Targets

Potential files:

```text
cps/experiments/synthetic_benchmark.py
cps/experiments/synthetic_report_tables.py
cps/experiments/diagnostic_gate.py
tests/test_synthetic_benchmark_pre_registered_gate.py
tests/test_synthetic_benchmark_outputs.py
```

If the current code already contains these concepts, prefer conservative extension over rewrite.

## 7. Canonical Command

```bash
uv run python -m cps.experiments.synthetic_benchmark   --config configs/runs/synthetic-regime-smoke.json   --output-dir artifacts/experiments/synthetic_regime_smoke
```

## 8. Validation

```bash
uv run pytest tests/test_synthetic_benchmark_pre_registered_gate.py -q
uv run pytest tests/test_synthetic_benchmark_outputs.py -q
```

If test names differ in the local repo, use the closest synthetic benchmark test files and record the exact commands.

## 9. Acceptance Criteria

P38 is accepted when:

- the benchmark emits all required artifacts;
- `summary.json` includes pre-registered gate status;
- `report.md` contains the claim boundary;
- higher-order false-positive greedy-valid cases are caught;
- reviewer can trace every table row to a machine-readable artifact.
