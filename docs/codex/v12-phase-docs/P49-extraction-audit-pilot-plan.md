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


# P49 Development Plan — Extraction Audit Pilot

## Objective
Implement a pilot extraction-risk audit for the M* -> M bridge.

## Key Concept
The selector optimizes over extracted candidate pool M, not underlying information space M*. The audit should not reinterpret selection guarantees as end-to-end guarantees.

## Strata
simple factual, qualifier-heavy, temporal-scope, cross-chunk, long-tail entity, high-provenance, prerequisite, contradictory/adversarial.

## Labels
Each ground-truth finding should track extraction outcome, lost qualifiers, temporal scope, provenance loss, selector impact, value band, stratum, and confidence.

## Metrics
`c_s = P(captured correctly | s)`, `c_effective = sum_s p_s c_s`, and value-weighted loss.

## Required Artifacts
```text
extraction_ground_truth_findings.jsonl
extraction_audit_labels.jsonl
stratum_completeness_report.csv
value_weighted_loss.csv
extraction_claim_gate_report.json
extraction_audit_report.md
```

## Claim Boundary
Allowed: `model_adjudicated_extraction_audit`, `extraction_risk_evidence`, `operational_utility_only`. Denied unless separately provided: human validation, kappa, `measurement_validated`, theorem transfer from M to M*.

## Validation
```bash
python -m compileall cps scripts
uv run pytest tests/test_extraction_audit_pilot.py -q
uv run pytest tests/test_revised_framing_guardrails.py -q
uv run pytest -q
git diff --check
```
