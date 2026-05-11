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


# P47 Development Plan — Model-Adjudicated Realistic-Task Benchmark

## Objective
Build a small model-adjudicated realistic-task benchmark for v12 context projection diagnosis.

## Allowed Claim Level
`model_adjudicated_proxy_evidence`, `operational_utility_only`, or `ambiguous_metric`. No `measurement_validated`.

## Scope
Add or extend `cps/experiments/realistic_tasks.py`, `model_adjudicated_labels.py`, `realistic_task_reporting.py`, `configs/runs/realistic-task-model-adjudicated-v12.json`, `tests/test_realistic_task_model_adjudicated.py`, and `docs/experiments/realistic-task-model-adjudicated-v12.md`.

## Task Families
1. paper-revision microtasks
2. multi-hop QA/evidence assembly packets
3. code-review/repo-modification microtasks

## Four-Role Pipeline
Generator, Structural labeler, Verifier, Adjudicator. First implementation may support imported JSONL labels instead of live model calls.

## Required Labels
Item labels, pair labels, triple labels, subset sufficiency labels, stability fields, and unstable-label downgrade to `ambiguous`.

## Baselines
Minimal/no context, full/large context, top-k retrieval, MMR greedy, always-SAG, and cost-aware diagnostic policy.

## Artifacts
```text
realistic_task_packets.jsonl
model_adjudicated_labels.jsonl
label_stability_report.json
realistic_selector_comparison.csv
realistic_claim_gate_report.json
realistic_task_report.md
```

## Validation
```bash
python -m compileall cps scripts
uv run pytest tests/test_realistic_task_model_adjudicated.py -q
uv run pytest tests/test_model_adjudicated_labels.py tests/test_route_b_evidence_package.py -q
uv run pytest tests/test_revised_framing_guardrails.py -q
uv run pytest -q
git diff --check
```
