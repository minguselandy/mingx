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


# P47 Review Document — Model-Adjudicated Realistic-Task Benchmark

## Review Goal
Check that the realistic-task benchmark is useful, reproducible, and claim-safe.

## Checks
- Model-adjudicated labels are not treated as human labels.
- No artifact claims `measurement_validated`, human kappa, human validation, or deployed V-information verification.
- Generator, labeler, verifier, and adjudicator outputs are represented separately or imported with provenance.
- Unstable labels are downgraded to `ambiguous`.
- Baselines use the same task packet, candidate pool, model/evaluator setup, and budget constraints.
- Reports include sufficiency, missing-critical-finding rate, redundancy waste, selected tokens, escalation rate, and ambiguity rate.

## Verdict Format
```text
# P47 Review Verdict
ACCEPT | ACCEPT_WITH_NOTES | REQUEST_CHANGES
## Blocking Issues
## Non-blocking Notes
## Claim Boundary Assessment
## Tests Reviewed
## Final Recommendation
```
