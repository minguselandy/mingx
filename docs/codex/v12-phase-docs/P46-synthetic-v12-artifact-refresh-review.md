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


# P46 Review Document — Synthetic v12 Artifact Refresh

## Review Goal
Verify that refreshed synthetic artifacts are v12-aligned, deterministic, and claim-safe.

## Checks
- Active outputs use `greedy_supported`, `pairwise_escalate`, `higher_order_risk`, `ambiguous`.
- Active outputs do not emit `greedy_valid`, bare `escalate`, or `Vinfo_proxy_certified`.
- Synthetic-only artifacts report `metric_claim_level = ambiguous_metric` and `diagnostic_scope/evidence_scope = synthetic_structural_only`.
- Higher-order prerequisite has near-zero false `greedy_supported`.
- Pairwise synergy frequently triggers `pairwise_escalate`.
- Adversarial redundancy is mostly `ambiguous` unless provenance-aware logic justifies stronger labels.
- Cost accounting reports diagnostic calls, pair samples, SAG trigger rate, selected token cost, and ambiguity rate.

## Verdict Format
```text
# P46 Review Verdict
ACCEPT | ACCEPT_WITH_NOTES | REQUEST_CHANGES
## Blocking Issues
## Non-blocking Notes
## Claim Boundary Assessment
## Tests Reviewed
## Final Recommendation
```
