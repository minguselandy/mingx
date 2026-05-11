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


# P50 Optional Development Plan — ReprojectionWitness and Uncertainty-Triggered Projection

## Objective
Optional extension: implement runtime re-projection artifacts and a small uncertainty-triggered projection experiment. This is lower priority than P45-P49.

## Motivation
If worker output indicates missing context or hallucination risk, the runtime may restore dispatch state, expand budget or switch selector, regenerate, and record the event.

## Potential Files
`cps/runtime/reprojection.py`, `cps/experiments/reprojection_benchmark.py`, `tests/test_reprojection_witness.py`, `docs/experiments/reprojection-witness.md`.

## ReprojectionWitness Schema
Fields: `run_id`, `dispatch_id`, `original_projection_plan_hash`, `trigger_type`, `uncertainty_score`, `missing_evidence_hypothesis`, `budget_delta`, `new_selector`, `context_diff_hash`, `before_output_hash`, `after_output_hash`, `quality_delta`, `cost_delta`.

## Experiment Baselines
fixed greedy, always-large context, diagnostic escalation, uncertainty-triggered re-projection.

## Metrics
missing-critical-evidence rate, hallucination-risk rate, sufficiency score, selected tokens, retry rate, cost delta, quality delta.

## Claim Boundary
This is runtime operational evidence unless separately calibrated. Do not claim V-information verification or measurement validation.

## Validation
```bash
python -m compileall cps scripts
uv run pytest tests/test_reprojection_witness.py -q
uv run pytest tests/test_revised_framing_guardrails.py -q
uv run pytest -q
git diff --check
```
