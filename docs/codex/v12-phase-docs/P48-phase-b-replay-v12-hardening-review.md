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


# P48 Review Document — Phase B Replay v12 Hardening

## Review Goal
Verify replay correctness, v12 label semantics, and claim boundaries.

## Checks
- Missing `run_id`, `dispatch_id`, `agent_id`, or `round_id` prevents `replay_usable`.
- Candidate pool, selected set, excluded set, budget, materialization order, and metric bridge witness are reconstructable.
- Active replay outputs use v12 labels only.
- Replay completeness is not treated as measurement validation.
- Reports include replay status counts, defects, metric claim levels, selector labels, and observed-vs-alternative comparison.

## Verdict Format
```text
# P48 Review Verdict
ACCEPT | ACCEPT_WITH_NOTES | REQUEST_CHANGES
## Blocking Issues
## Non-blocking Notes
## Claim Boundary Assessment
## Tests Reviewed
## Final Recommendation
```
