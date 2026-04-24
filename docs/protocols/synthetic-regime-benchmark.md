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
- `diagnostics.jsonl`
- `summary.json`
- `report.md`

`events.jsonl` is the source of truth for replaying the run summary. The JSONL
artifact files are derived audit views for inspection.

## Diagnostics

The benchmark reports:

- `gamma_hat`
- synergy fraction
- greedy-vs-seeded-augmented gap
- policy recommendation

Default provisional policy bins:

- `monitored_greedy`: `gamma_hat >= 0.75`, synergy fraction `<= 0.10`, gap `<= 0.05`
- `seeded_augmented_greedy`: `gamma_hat >= 0.45`, gap `<= 0.15`
- `interaction_aware_local_search`: fallback when the above bins do not apply

These are calibration bins for synthetic experiments only. They should not be
reported as production thresholds.

## Non-Goals

- No new scheduler.
- No recursive multi-agent framework.
- No memory architecture redesign.
- No system-level performance claim.
- No theorem-inheritance claim from diagnostics.
- No openWorker port before trace availability is established.
