# Synthetic Regime Benchmark Protocol

This protocol defines the Phase A synthetic diagnostic benchmark for controlled
context-projection set functions.

## Purpose

The benchmark checks whether proxy-layer diagnostics separate three controlled
regimes:

- redundancy-dominated
- sparse pairwise synergy
- higher-order synergy

It is intentionally narrow. It does not implement a scheduler, memory
architecture, openWorker trace port, live benchmark, or theorem-inheritance
claim.

## Command

```bash
python -m cps.experiments.synthetic_benchmark \
  --config configs/runs/synthetic-regime-smoke.json \
  --output-dir artifacts/experiments/synthetic_regime_smoke
```

## Outputs

The output directory contains:

- `events.jsonl`
- `candidate_pools.jsonl`
- `projection_plans.jsonl`
- `budget_witnesses.jsonl`
- `materialized_contexts.jsonl`
- `metric_bridge_witnesses.jsonl`
- `diagnostics.jsonl`
- `summary.json`
- `report.md`

`events.jsonl` is the source of truth for replaying the run summary. The JSONL
artifact files are derived audit views for inspection.

## Diagnostics

The benchmark reports:

- block-ratio LCB family where available:
  `block_ratio_lcb_b2`, `block_ratio_lcb_star`, `block_ratio_lcb_b3`
- interaction mass
- triple-excess diagnostics where available
- greedy-vs-seeded-augmented gap
- `metric_claim_level`
- `selector_regime_label`
- `selector_action`

Triple-excess flags use `positive`, `none_detected`, `ambiguous`, or
`not_evaluable`. Higher-order-risk instances with missing triple/block evidence
must be escalated or marked ambiguous; pairwise-healthy diagnostics alone are
not enough to emit a high-confidence greedy-valid label.

Default selector-regime labels are limited to `greedy_valid`, `escalate`, and
`ambiguous`. Default provisional selector actions:

- `monitored_greedy`: high block-ratio LCB, low interaction mass, and small gap
- `seeded_augmented_greedy`: moderate block-ratio LCB and bounded gap
- `interaction_aware_local_search`: positive higher-order evidence requiring
  stronger search
- `no_certified_switch`: missing, stale, or insufficient bridge/diagnostic
  evidence

These are calibration bins for synthetic experiments only. They should not be
reported as production thresholds. Legacy synthetic configs may still contain
old trace-ratio threshold field names; read those as compatibility inputs for
the pre-registered validity gate, not as headline weak-submodularity
diagnostics.

## Non-Goals

- No new scheduler.
- No recursive multi-agent framework.
- No memory architecture redesign.
- No system-level performance claim.
- No theorem-inheritance claim from diagnostics.
- No openWorker port before trace availability is established.
