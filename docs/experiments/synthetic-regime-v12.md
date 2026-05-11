# Synthetic Regime v12 Artifact Refresh

## Purpose

P46 refreshes the deterministic synthetic structural benchmark under the v12
diagnostic vocabulary. It is an offline, synthetic-only artifact lane for
selector-regime diagnostics and cost-aware baseline comparison.

This lane does not use P45 bridge calibration evidence. P45 is closed for the
current `bio_attribute` stratum as implemented but non-calibrated, so P46
synthetic outputs keep `metric_claim_level = ambiguous_metric` and
`diagnostic_scope = synthetic_structural_only`.

## Families

The v12 run config exercises four families:

- `redundancy-dominated`: near-duplicate clusters with diminishing returns.
- `pairwise-synergy`: sparse pair bonuses that should trigger
  `pairwise_escalate`.
- `higher-order-prerequisite`: prerequisite triples that must not be falsely
  labeled `greedy_supported`.
- `adversarial-redundancy`: redundancy-looking inputs with adversarial ambiguity
  risk, reported conservatively as `ambiguous`.

## Baselines

The cost table reports deterministic comparisons for:

- `random_budgeted`
- `top_k_relevance`
- `mmr_density_greedy`
- `seeded_augmented_greedy`
- `pair_aware_local_search`
- `opt_or_near_opt`
- `v12_cost_aware_diagnostic_policy`

All baselines use synthetic oracle values only. There are no model-provider or
live API calls.

## Outputs

Run:

```bash
uv run python -m cps.experiments.synthetic_benchmark --config configs/runs/synthetic-regime-v12.json
```

The deterministic v12 outputs are written to:

```text
artifacts/experiments/synthetic_regime_v12/
```

Required paper-facing files:

- `synthetic_confusion_v12.csv`
- `synthetic_metrics_v12.csv`
- `synthetic_cost_table_v12.csv`
- `synthetic_run_manifest_v12.json`
- `synthetic_report_v12.md`

The v12 manifest uses relative paths, stable JSON key ordering, no timestamps,
and no UUIDs.

## Metrics

The v12 metrics table includes:

- confusion matrix by true family and selector label
- false `greedy_supported` rate
- higher-order false `greedy_supported` rate
- pairwise escalation recall
- `Greedy/OPT`, `SAG/OPT`, and `LocalSearch/OPT`
- `SAG residual gap / OPT = max(0, OPT - SAG) / OPT`
- `SAG improvement over Greedy / OPT = (SAG - Greedy) / OPT`
- diagnostic call count
- pair sample count
- SAG trigger rate
- ambiguity rate
- selected token cost
- cost-aware policy outcome

## Claim Boundary

Synthetic v12 artifacts are structural diagnostics only. They must not claim:

- `vinfo_proxy_supported`
- `calibrated_proxy_supported`
- `measurement_validated`
- deployed V-information verification
- human validation
- human labels or kappa

If the synthetic benchmark is green, the correct paper-facing status remains
`ambiguous_metric` for metric claims and `synthetic_structural_only` for
evidence scope.
