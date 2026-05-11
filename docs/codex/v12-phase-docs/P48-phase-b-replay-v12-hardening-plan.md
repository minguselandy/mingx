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


# P48 Development Plan — Phase B Replay v12 Hardening

## Objective
Harden Phase B offline replay under v12 diagnosis semantics.

## Required Inputs
`events.jsonl`, `candidate_pools.jsonl`, `projection_plans.jsonl`, `budget_witnesses.jsonl`, `materialized_contexts.jsonl`, `metric_bridge_witnesses.jsonl`, `diagnostics.jsonl`, cached utility/log-loss records if available, and task metadata.

## v12 Output Labels
Normalize legacy inputs to v12 outputs: `greedy_valid -> greedy_supported`; old bare `escalate -> pairwise_escalate`, `higher_order_risk`, or `ambiguous`; stale/missing bridge -> `ambiguous_metric` or `operational_utility_only`; synthetic-only evidence remains `synthetic_structural_only` scope.

## Replay Statuses
`replay_usable`, `pilot_degraded`, `replay_partial`, `replay_unusable`.

## Required Reports
```text
replay_status_counts.csv
missing_field_defects.csv
metric_claim_level_counts.csv
selector_regime_label_counts.csv
observed_vs_alternative.csv
phase_b_replay_v12_report.md
```

## Claim Boundary
Replay completeness can support `replayable_artifact_evidence`; it cannot support `measurement_validated`, human validation, or deployed V-information verification.

## Validation
```bash
python -m compileall cps scripts
uv run pytest tests/test_phase_b_replay.py -q
uv run pytest tests/test_replay_evidence_package.py -q
uv run pytest tests/test_revised_framing_guardrails.py -q
uv run pytest -q
git diff --check
```
