# Common Guardrails for Mingx v12 Development

These phase documents are for the local repository:

`C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev`

Current paper direction:
- Current manuscript anchor: `docs/archive/context_projection_fixed_v12.md`
- Current alignment anchor: `docs/paper-alignment-v12.md`
- Framing: **Proxy-Regime Diagnosis**, not broad certification
- Selector-regime labels: `greedy_supported`, `pairwise_escalate`, `higher_order_risk`, `ambiguous`
- Metric-claim levels: `vinfo_proxy_supported`, `calibrated_proxy_supported`, `operational_utility_only`, `ambiguous_metric`
- Synthetic-only evidence: `metric_claim_level = ambiguous_metric` and `diagnostic_scope/evidence_scope = synthetic_structural_only`

Hard constraints:
- No live API unless an explicit operator-approved live plan is supplied.
- No fabricated bridge calibration results.
- No fabricated human labels, kappa, or contamination closure.
- No `measurement_validated` claim.
- No deployed V-information verification claim.
- Preserve legacy v10 materials as archive/compatibility references only.
- Prefer deterministic artifacts: stable JSON key ordering, stable row ordering, no timestamps/UUIDs/absolute paths in replay-comparable outputs.
- All reports must distinguish metric claim level, selector-regime label, and evidence/diagnostic scope.


# P46 Development Plan — Synthetic v12 Artifact Refresh and Cost-Aware Comparison

## Objective
Refresh the synthetic structural benchmark under v12 labels and add cost-aware comparison outputs.

## Required Labels
Selector labels: `greedy_supported`, `pairwise_escalate`, `higher_order_risk`, `ambiguous`.
Synthetic-only metric claim: `ambiguous_metric`.
Synthetic evidence scope: `synthetic_structural_only`.

## Scope
Update or extend `cps/experiments/synthetic_benchmark.py`, `synthetic_regimes.py`, `selection.py`, `diagnostics.py`, `reporting.py`, `configs/runs/synthetic-regime-v12.json`, `tests/test_synthetic_regime_benchmark.py`, and `docs/experiments/synthetic-regime-v12.md`.

## Benchmark Families
1. redundancy-dominated
2. pairwise synergy
3. higher-order prerequisite
4. adversarial redundancy

## Baselines
Random budgeted, top-k relevance, reranker-only greedy if available, MMR/density greedy, seeded augmented greedy, pair-aware local search if available, OPT/near-OPT, and the v12 cost-aware diagnostic policy. Optional: AdaGReS-style redundancy-aware greedy and CI-Value/LOO pruning proxy.

## Required Metrics
- confusion matrix by true regime and selector label
- false `greedy_supported` rate, especially on higher-order prerequisite
- pairwise escalation recall
- `Greedy/OPT`, `SAG/OPT`, `LocalSearch/OPT`, `SAG gap / OPT`
- diagnostic call count, pair samples, SAG trigger rate, ambiguity rate, selected token cost

## Required Artifacts
```text
synthetic_confusion_v12.csv
synthetic_metrics_v12.csv
synthetic_cost_table_v12.csv
synthetic_run_manifest_v12.json
synthetic_report_v12.md
```

## Claim Boundary
Do not claim deployed V-information verification, `measurement_validated`, bridge calibration, or human validation.

## Validation
```bash
python -m compileall cps scripts
uv run pytest tests/test_synthetic_regime_benchmark.py -q
uv run pytest tests/test_experiment_diagnostics.py -q
uv run pytest tests/test_revised_framing_guardrails.py -q
uv run pytest -q
git diff --check
```
