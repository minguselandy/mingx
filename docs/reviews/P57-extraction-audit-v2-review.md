phase: P57
phase_name: extraction audit v2 and human-sentinel protocol scaffold
reviewer: codex
date: 2026-05-12
verdict: ACCEPT_WITH_NOTES
blocked: false
requires_operator: false
next_phase_allowed: false
metric_claim_level_max: none
selector_regime_label_max: none
paper_evidence_eligible: false
measurement_validation_claim: false
live_api_used: false
human_labels_present: false
human_human_kappa_present: false
contamination_status: not_applicable

## Scope reviewed

- Files added:
  - `docs/experiments/P57-extraction-audit-v2-plan.md`
  - `docs/templates/extraction-audit-v2-record-template.json`
  - `docs/templates/human-sentinel-extraction-audit-protocol-template.md`
  - `tests/test_p57_extraction_audit_v2.py`
  - `docs/reviews/P57-extraction-audit-v2-review.md`
- Templates:
  - extraction audit v2 JSON record template
  - human-sentinel extraction audit protocol template
- Tests:
  - focused P57 template/claim-boundary tests
- Generated artifacts:
  - none

## Summary

P57 created an extraction-risk audit scaffold and did not execute human labeling. The plan defines value-stratified extraction-risk strata, extraction-specific labels and metrics, a deterministic JSON record template, and a human-sentinel protocol template.

This phase did not import data, run live APIs, produce extraction audit records, create human labels, compute kappa, or upgrade claims.

## Strata and label review

Required strata are covered:

- `simple_factual`
- `complex_conditional`
- `qualifier_heavy`
- `temporal_scope`
- `cross_chunk`
- `long_tail_entity`
- `high_provenance_value`
- `prerequisite`
- `contradictory`
- `adversarial_repetition_sensitive`

Required labels are covered:

- `captured_exact`
- `captured_core_preserved`
- `captured_core_changed`
- `missing`
- `unsupported_added`
- `duplicate_or_overmerged`
- `contradiction_lost`
- `qualifier_lost`
- `temporal_scope_error`
- `provenance_lost`
- `selector_impact_estimate`

`selector_impact_estimate` is explicitly risk-only, not selector validity and not metric support.

## Metric review

P57 uses extraction-specific metrics:

- `extraction_completeness_by_stratum`
- `effective_extraction_completeness`
- `value_weighted_extraction_loss`
- `critical_finding_miss_rate`
- `unsupported_finding_rate`
- `provenance_loss_rate`

The extraction metric list does not include bridge-calibration quantities `c_s` or `zeta_s`; the plan states those names remain separate.

## Human-sentinel protocol review

The human-sentinel protocol is operator-gated and unexecuted. It states that missing human labels or missing kappa must not be filled by model adjudication, model-adjudicated labels are not human labels, and human sentinel evidence is not automatically measurement validation.

## Claim-boundary review

- Metric claim ceiling: `none`
- Selector label ceiling: `none`
- Paper eligibility: `false`
- Measurement validation claim: `false`

P57 confirms extraction audit is extraction-risk evidence only. It is not selector validity, not metric bridge support, not V-information support, not measurement validation, and not paper-grade evidence by itself.

Fixture-only extraction audit remains paper-ineligible. Model-adjudicated audit is not human validation. Human labels and human-human kappa require actual operator-approved human annotation and valid agreement calculation.

## P55/P56 boundary review

P55 remains `failed_closed_no_rows / blocked_operator_required`. Rows imported/validated remain 0. P55 review ceiling remains none. P55 paper evidence remains false. P55 fit metrics remain not computed.

P56 remains `no_imported_traces`. Traces imported/validated remain 0. P56 review ceiling remains none. P56 paper evidence remains false. P56 measurement validation remains false. P56 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.

P57 does not proceed from P55/P56 success. P57 does not repair P55/P56 blocked states.

## Checks run

```text
uv run pytest tests/test_p57_extraction_audit_v2.py
```

Initial RED result before plan/templates existed: exit 1, 7 failed. Failures were expected missing-file errors for `docs/experiments/P57-extraction-audit-v2-plan.md`, `docs/templates/extraction-audit-v2-record-template.json`, and `docs/templates/human-sentinel-extraction-audit-protocol-template.md`.

```text
uv run pytest tests/test_p57_extraction_audit_v2.py
```

Final result: exit 0, 7 passed in 0.09s.

```text
python -m json.tool docs/templates/extraction-audit-v2-record-template.json > $null
```

Result: exit 0.

```text
uv run pytest tests/test_revised_framing_guardrails.py
```

Result: exit 0, 13 passed in 0.68s.

```text
python -m compileall cps tests scripts
```

Result: exit 0.

```text
uv run pytest -q
```

Result: exit 0, 568 passed, 4 skipped in 37.52s.

```text
git diff --check
```

Result: exit 0, with unrelated dirty `AGENTS.md` line-ending warning.

Focused scans:

```text
rg -n "selector validity|metric bridge support|V-information support|measurement validation|human-human kappa|human label|model-adjudicated|paper-grade evidence|c_s|zeta_s" docs/experiments/P57-extraction-audit-v2-plan.md docs/templates/extraction-audit-v2-record-template.json docs/templates/human-sentinel-extraction-audit-protocol-template.md docs/reviews/P57-extraction-audit-v2-review.md tests/test_p57_extraction_audit_v2.py
```

Result: expected denied, gated, protocol, or negative-test contexts only.

```text
rg -n "failed_closed_no_rows|blocked_operator_required|no_imported_traces|P55|P56" docs/experiments/P57-extraction-audit-v2-plan.md docs/reviews/P57-extraction-audit-v2-review.md
```

Result: expected P55/P56 boundary-preservation hits only.

```text
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" docs/templates/extraction-audit-v2-record-template.json docs/templates/human-sentinel-extraction-audit-protocol-template.md docs/experiments/P57-extraction-audit-v2-plan.md docs/reviews/P57-extraction-audit-v2-review.md
```

Result: expected hits only from this review file recording the scan command and prose; templates and plan are clean.

## Checks skipped

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

P57 is a plan/template/test scaffold only. Human-sentinel execution remains future operator-gated work.

## Required changes

None.

## Next-phase decision

Independent review is required before any further phase progression. P58/P59/P60 may not proceed from this P57 scaffold without separate authorization and review.
