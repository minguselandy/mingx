# Phase Review

```yaml
phase_id: P20
verdict: ACCEPT
next_phase_allowed: true
next_phase_id: P21
license_impact: none
safety_impact: none
dependency_changes: none
live_api_required: false
external_service_required: false
credential_required: false
human_review_required: false
scientific_claim_required: false
operator_required: false
```

## Verdict

phase_id: P20
phase_title: Context Projection v10 Manuscript Integration Decision
branch: codex/p20-manuscript-integration-decision
verdict: ACCEPT

## Target Manuscript

target_manuscript_path: `docs/archive/context_projection_revised_v10.md`

The source manuscript was inspected and left unchanged. P20 decides the integration strategy for P21.

## Recommended Integration Strategy

recommended_strategy: `INTEGRATE_CORE_TABLES_ONLY`

Rationale:

- The manuscript already has strong bridge, proxy-regime, runtime-audit, and limitations material.
- Full P18 insertion would duplicate existing Section 3.4, Section 4.3.1, Section 6, and Section 9.
- P21 should integrate compact core evidence and claim-boundary material into the body.
- Detailed P18 proxy-regime and replay package tables should remain companion/appendix evidence unless later restructuring approves them.

## Files Changed

files_changed:

- `docs/paper/context_projection_v10_manuscript_integration_decision.md`
- `docs/reviews/P20-review.md`

## Validation Commands

commands_run:

- `python -m compileall cps scripts`
- `python scripts/framework_guard.py status`
- `python scripts/framework_guard.py validate --profile target`
- `pytest tests/test_manuscript_tables.py -q`
- `pytest tests/test_end_to_end_evidence_demo.py -q`
- `pytest tests/test_paper_evidence_summary.py -q`

## Decision Summary

decision_summary:

- Integrate compact Table 1 material into Section 6.2.
- Integrate compact Table 2 material near Section 3.4 or 4.2.
- Keep full Table 3 proxy-regime matrix in companion/appendix evidence for now.
- Keep full Table 4 replay evidence package summary in companion/appendix evidence for now.
- Integrate compact Table 5 non-claims material into Section 9.
- Apply risky-certification-term guardrails in P21.

## Claim Boundary

- P20 is manuscript-integration decision only: yes.
- Source manuscript modified: no.
- P20 upgrades claim levels: no.
- P04 remains deferred/operator-required: yes.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`: yes.
- `measurement_validated` claimed: no.
- P17 reported as scientific validation: no.
- replay package completeness claimed as scientific validation: no.
- synthetic success reported as deployed V-information certification: no.
- paper-facing summaries upgrade claim levels: no.

## Denied Claims

denied_claims:

- `measurement_validated`
- `scientific_validation`
- `deployed_v_information_certification`
- `deployed_v_information_submodularity_certified`
- `runtime_integration_complete`

## Known Limitations

known_limitations:

- P20 does not apply manuscript edits; P21 is required for source manuscript changes.
- P20 does not add human labels, kappa, contamination closure, or fresh metric bridge evidence.
- P20 does not run live APIs, live cohort, model providers, or external runtime integration.
- P04 scientific closure remains operator-required and incomplete.
- P09 runtime adapter implementation remains blocked/operator-required.

## Next Recommended Step

next_recommended_step: P21 Context Projection v10 Manuscript Integration Patch Application

P21 should apply only the approved compact subset of P18/P20 edits directly to `docs/archive/context_projection_revised_v10.md`.
