# Phase Review

```yaml
phase_id: P17
verdict: ACCEPT
next_phase_allowed: true
next_phase_id: P18
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

phase_id: P17
phase_title: End-to-End Evidence Demo
branch: codex/p17-end-to-end-evidence-demo
verdict: ACCEPT

## Summary

summary: P17 adds a deterministic offline end-to-end runtime-audit evidence demo that wires P10-P16 modules into one reproducible local evidence chain.

## Files changed

files_changed:

- `cps/experiments/end_to_end_evidence_demo.py`
- `tests/test_end_to_end_evidence_demo.py`
- `docs/experiments/end-to-end-evidence-demo.md`
- `docs/reviews/P17-review.md`

## Commands run

commands_run:

- `pytest tests/test_end_to_end_evidence_demo.py -q`
- `python -m compileall cps scripts`
- `pytest tests/test_provider_candidate_normalizer.py -q`
- `pytest tests/test_provider_offline_smoke.py -q`
- `pytest tests/test_evidence_ledger.py -q`
- `pytest tests/test_claim_gate_report.py -q`
- `pytest tests/test_metric_bridge_gate.py -q`
- `pytest tests/test_proxy_regime_matrix.py -q`
- `pytest tests/test_replay_evidence_package.py -q`
- `pytest tests/test_paper_evidence_summary.py -q`
- `pytest tests/test_synthetic_regime_benchmark.py -q`
- `python scripts/framework_guard.py status`
- `python scripts/framework_guard.py validate --profile target`

## Test results

test_results:

- `pytest tests/test_end_to_end_evidence_demo.py -q`: passed.
- Required regression tests: passed.
- `python scripts/framework_guard.py status`: P09 `BLOCKED_OPERATOR_REQUIRED`.
- `python scripts/framework_guard.py validate --profile target`: passed.

## Artifacts created

artifacts_created:

- No persistent experiment artifacts were created in the repo.
- Tests create temporary P17 demo outputs only under pytest temporary directories.

## Demo outputs

demo_outputs:

- `projection_bundles.jsonl`
- `evidence_ledger.json`
- `claim_gate_report.json`
- `claim_gate_report.md`
- `proxy_regime_matrix.json`
- `proxy_regime_matrix.md`
- `replay_package/`
- `paper_evidence_summary.json`
- `paper_evidence_summary.md`
- `demo_manifest.json`
- `demo_summary.md`

## Claim boundary

- P04 remains deferred/operator-required: yes.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`: yes.
- `measurement_validated` claimed: no.
- P17 reported as scientific validation: no.
- replay package completeness claimed as scientific validation: no.
- synthetic success reported as deployed V-information certification: no.
- engineering success reported as scientific validation: no.
- live API success alone treated as measurement validation: no.

## Denied claims

denied_claims:

- `measurement_validated`
- `scientific_validation`
- `deployed_v_information_certification`
- `deployed_v_information_submodularity_certified`
- `runtime_integration_complete`

## State transition

state_transition: P09 BLOCKED_OPERATOR_REQUIRED -> P09 BLOCKED_OPERATOR_REQUIRED

## Dependency changes

dependency_changes: none

## License impact

license_impact: none

## Safety impact

safety_impact: none

## Determinism impact

determinism_impact: deterministic local demo outputs, stable JSON writers, stable Markdown writers, stable output ordering, stable reason-code ordering, no timestamps, no UUIDs, no randomness, no network calls, no external SDK imports

## Known limitations

known_limitations:

- P17 uses fake/local provider input from the offline smoke path.
- P17 does not run live APIs, live cohort, or external runtime integration.
- P17 does not create missing labels, kappa, contamination pass evidence, or fresh deployed metric bridge evidence.
- P04 scientific closure remains operator-required and incomplete.
- P09 runtime adapter implementation remains blocked/operator-required.

## Next recommended step

next_recommended_step: P18 Manuscript Tables and Experiment Section Draft

## Next phase

next_phase_allowed: true
next_phase_id: P18
reason: P17 demo implementation and tests passed while preserving conservative claim boundaries.
