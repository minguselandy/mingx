# P47 Model-Adjudicated Realistic-Task Benchmark

## Purpose

P47 adds a deterministic, offline/importable realistic-task benchmark lane for
v12 selector diagnostics. The v1 run uses fixture model-adjudicated labels to
exercise the schema, baseline comparison, stability downgrade, and claim-gate
surfaces without live model calls.

This lane does not reuse P45 bridge calibration evidence. The current
`bio_attribute` bridge status remains non-calibrated, so P47 fixture outputs
stay below measurement validation and below calibrated bridge support.

## Task Families

The fixture benchmark includes three small realistic-task families:

- `paper_revision_microtask`
- `multi_hop_evidence_assembly`
- `repo_change_review_microtask`

Each task packet records:

- `task_id`
- `task_family`
- `agent_role`
- `task_prompt`
- `gold_requirements` and `gold_sketch`
- `candidate_findings`
- `token_costs`
- `provenance`
- `expected_critical_findings`

## Label Schema

The model-adjudicated label file uses nested fixture labels for:

- item-level labels: singleton value, relevance band, prerequisite status,
  evidence type, provenance strength, extraction complexity, and confidence.
- pair-level labels: redundant, independent, complementary, or contradictory
  relation plus pairwise excess and prerequisite direction.
- triple/higher-order labels: higher-order type, whether pairs are sufficient,
  triple excess band, and greedy-failure risk.
- subset-level labels: sufficiency score, missing critical findings, redundant
  findings, unsupported-claim risk, expected escalation benefit, and v12
  selector-regime label.

The four-role pipeline fields are present as fixture provenance:

- `generator`
- `structural_labeler`
- `verifier`
- `adjudicator`

These fixture roles are not human labels and do not establish kappa.

## Baselines

Run:

```bash
uv run python -m cps.experiments.realistic_tasks --config configs/runs/realistic-task-model-adjudicated-v12.json
```

The comparison table reports budget-fair selector-policy baselines:

- `minimal_context`
- `top_k_retrieval`
- `mmr_density_greedy`
- `always_sag`
- `v12_cost_aware_diagnostic_policy`

It also reports `full_context` as a non-budget-comparable reference baseline:
an always-large-context reference, not part of budget-fair selector-policy
comparison or aggregate conclusions.

Metrics include sufficiency score, missing-critical-finding rate,
redundancy-waste rate, unsupported-claim risk, selected token cost,
diagnostic/escalation rate, ambiguity rate, selector-regime label distribution,
and cost-aware policy outcome.

Every selector comparison row includes explicit budget comparability fields:

- `budget_comparable`
- `budget_status`
- `budget_tokens`
- `selected_token_count`
- `budget_overrun_tokens`

Budget-comparable rows must be `within_budget` with zero overrun. The
`full_context` rows are marked `over_budget_reference` and excluded from
budget-fair aggregate conclusions.

## Outputs

The deterministic outputs are written to:

```text
artifacts/experiments/realistic_task_model_adjudicated_v12/
```

Required files:

- `realistic_task_packets.jsonl`
- `model_adjudicated_labels.jsonl`
- `label_stability_report.json`
- `realistic_selector_comparison.csv`
- `realistic_claim_gate_report.json`
- `realistic_task_report.md`

The run uses stable row ordering, stable JSON key ordering, no timestamps, no
UUIDs, and no absolute paths in replay-comparable artifacts.

## Quality Controls

Fixture outputs report imported-quality-control slots without pretending they
were measured:

- duplicate judging stability: `fixture_not_measured`
- order reversal status: `fixture_not_measured`
- paraphrase robustness status: `fixture_not_measured`
- prerequisite ablation status: `fixture_not_measured`

If a fixture task is marked unstable, the selector label is downgraded to
`ambiguous` before claim reporting.

## Claim Boundary

Allowed vocabulary for this lane is limited to:

- `model_adjudicated_proxy_evidence`
- `operational_utility_only`
- `ambiguous_metric`

The fixture run sets:

- `data_source_kind = fixture`
- `paper_evidence_eligible = false`
- `measurement_validation_claim = false`
- `live_api_used = false`

The artifacts must not claim:

- `measurement_validated`
- human validation
- human labels or kappa
- deployed V-information verification
- calibrated bridge evidence

Future imported model-adjudicated labels may use the same schema with
`data_source_kind = model_adjudicated_imported`, but they still do not become
human labels, kappa evidence, measurement validation, or calibrated bridge
support.
