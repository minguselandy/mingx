# P47 Model-Adjudicated Realistic-Task Benchmark Report

## Summary

- Run id: `realistic-task-model-adjudicated-v12`
- Task count: 3
- Data source kind: `fixture`
- Live API: `skipped`
- Allowed claim level: `operational_utility_only`
- Paper evidence eligible: false

## Budget Comparability

### Budget-Fair Baselines

These baselines are included in budget-fair selector-policy comparisons:

- `minimal_context`
- `top_k_retrieval`
- `mmr_density_greedy`
- `always_sag`
- `v12_cost_aware_diagnostic_policy`

### Non-Budget Reference Baselines

- `full_context`: an always-large-context reference baseline, not part of budget-fair selector-policy comparison.

Budget-fair aggregate conclusions exclude `full_context`.

## Metrics

The metrics below summarize the v12 cost-aware policy rows, which are budget-comparable.

- Mean sufficiency score: 1.0
- Mean missing-critical-finding rate: 0.0
- Mean redundancy-waste rate: 0.0
- Mean unsupported-claim risk: 0.0
- Mean selected tokens: 30.333333
- Diagnostic/escalation rate: 0.333333
- Ambiguity rate: 0.333333

## Quality Controls

- Duplicate judging stability: `fixture_not_measured`
- Order reversal status: `fixture_not_measured`
- Paraphrase robustness status: `fixture_not_measured`
- Prerequisite ablation status: `fixture_not_measured`
- Unstable-label downgrades: `{"downgraded_task_ids": ["repo_change_review_claim_boundary"], "selector_regime_label": "ambiguous", "unstable_label_count": 1}`

## Claim Boundary

- Fixture labels are not paper evidence.
- Model-adjudicated labels are not human labels.
- Human agreement is absent.
- No bridge-calibrated evidence is used.
- No deployment-level verification claim is made.
