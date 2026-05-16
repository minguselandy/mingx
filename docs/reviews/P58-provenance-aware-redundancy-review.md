phase: P58
phase_name: provenance-aware redundancy diagnostics scaffold
reviewer: codex
date: 2026-05-12
verdict: ACCEPT_WITH_NOTES
blocked: false
requires_operator: false
next_phase_allowed: false
metric_claim_level_max: operational_utility_only
selector_regime_label_max: ambiguous
paper_evidence_eligible: false
measurement_validation_claim: false
live_api_used: false
human_labels_present: false
human_human_kappa_present: false
contamination_status: not_applicable

## Scope reviewed

- Files added:
  - `docs/experiments/P58-provenance-aware-redundancy-plan.md`
  - `docs/templates/provenance-redundancy-diagnostic-template.json`
  - `tests/test_p58_provenance_aware_redundancy.py`
  - `docs/reviews/P58-provenance-aware-redundancy-review.md`
- Templates:
  - provenance-aware redundancy diagnostic JSON template
- Tests:
  - focused P58 template, category, and claim-boundary tests
- Generated artifacts:
  - none

## Summary

P58 created an operational diagnostic scaffold only. It defines provenance-aware redundancy categories, conservative feature fields, claim-gate boundaries, and focused deterministic tests.

This phase did not import operator data, run live APIs, generate artifacts, execute selector changes, or upgrade evidence claims.

## Category review

Required diagnostic categories are covered:

- `duplicate_redundancy`: penalize strongly only when provenance and finding hashes confirm true duplication.
- `independent_corroboration`: preserve when source independence is high and the claim is important.
- `adversarial_repetition`: trigger contradiction/provenance audit, not a simple diversity penalty.
- `source_conflict_pair`: escalate or adjudicate.
- `prerequisite_overlap`: preserve or escalate until the prerequisite chain is resolved.
- `paraphrase_near_duplicate`: lower priority unless provenance differs.
- `qualifier_mismatch`: escalate because qualifier loss can change claim meaning.
- `temporal_scope_mismatch`: escalate because time scope can change claim truth.

Duplicate redundancy and independent corroboration are explicitly separated.

## Feature/template review

The JSON template includes the required identity, provenance, source-span, feature-score, flag, category, selector implication, escalation, audit, claim ceiling, metric claim level, selector label, paper eligibility, measurement validation, and denied-claim fields.

Defaults are conservative:

- `paper_evidence_eligible: false`
- `measurement_validation_claim: false`
- `metric_claim_level: operational_utility_only`
- `selector_regime_label: ambiguous`

The template does not default to `greedy_supported`, `calibrated_proxy_supported`, `vinfo_proxy_supported`, or `measurement_validated`.

## Claim-boundary review

- Metric claim ceiling: `operational_utility_only`
- Selector label ceiling: `ambiguous`
- Paper eligibility: `false`
- Measurement validation claim: `false`

P58 does not establish selector validity. P58 does not establish metric bridge support. P58 does not establish V-information support. P58 does not establish measurement validation. P58 does not make fixture/template outputs paper evidence.

## P55/P56/P57 boundary review

P55 remains failed_closed_no_rows / blocked_operator_required. Rows imported/validated remain 0. P55 review ceiling remains none. P55 paper evidence remains false. P55 fit metrics remain not computed.

P56 remains no_imported_traces. Traces imported/validated remain 0. P56 review ceiling remains none. P56 paper evidence remains false. P56 measurement validation remains false. P56 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.

P57 remains extraction-risk scaffold only. P58 does not proceed from P55/P56 success. P58 does not convert P57 extraction audit into selector validity. P58 does not repair P55/P56 blocked states.

## Checks run

```text
uv run pytest tests/test_p58_provenance_aware_redundancy.py
```

Initial RED result before P58 plan/template/review files existed: exit 1, 7 failed. Failures were expected missing-file errors for:

- `docs/experiments/P58-provenance-aware-redundancy-plan.md`
- `docs/templates/provenance-redundancy-diagnostic-template.json`
- `docs/reviews/P58-provenance-aware-redundancy-review.md`

```text
uv run pytest tests/test_p58_provenance_aware_redundancy.py
```

Final result: exit 0, 7 passed in 0.07s.

```text
git diff --check
```

Result: exit 0, with unrelated dirty `AGENTS.md` line-ending warning.

```text
warning: in the working copy of 'AGENTS.md', LF will be replaced by CRLF the next time Git touches it
```

```text
python -m json.tool docs/templates/provenance-redundancy-diagnostic-template.json
```

Result: exit 0. JSON parsed successfully.

```text
uv run pytest tests/test_revised_framing_guardrails.py
```

Result: exit 0, 13 passed in 0.68s.

```text
python -m compileall cps tests scripts
```

Result: exit 0. Compileall completed for `cps`, `tests`, and `scripts`.

```text
uv run pytest -q
```

Result: exit 0, 575 passed, 4 skipped in 35.63s.

Focused scans:

```text
rg -n "selector validity|metric bridge support|V-information support|measurement validation|paper-grade evidence|calibrated_proxy_supported|vinfo_proxy_supported|measurement_validated|greedy_supported" docs/experiments/P58-provenance-aware-redundancy-plan.md docs/templates/provenance-redundancy-diagnostic-template.json docs/reviews/P58-provenance-aware-redundancy-review.md tests/test_p58_provenance_aware_redundancy.py
```

Result: exit 0. Hits are denied, gated, review, or negative-test contexts only. Representative hits:

```text
docs/experiments/P58-provenance-aware-redundancy-plan.md:17:P58 does not establish selector validity.
docs/experiments/P58-provenance-aware-redundancy-plan.md:18:P58 does not establish metric bridge support.
docs/experiments/P58-provenance-aware-redundancy-plan.md:19:P58 does not establish V-information support.
docs/experiments/P58-provenance-aware-redundancy-plan.md:20:P58 does not establish measurement validation.
docs/templates/provenance-redundancy-diagnostic-template.json:165:    "calibrated_proxy_supported",
docs/templates/provenance-redundancy-diagnostic-template.json:166:    "vinfo_proxy_supported",
docs/templates/provenance-redundancy-diagnostic-template.json:168:    "measurement_validated",
tests/test_p58_provenance_aware_redundancy.py:153:    assert template["selector_regime_label"] != "greedy_supported"
```

```text
rg -n "duplicate_redundancy|independent_corroboration|adversarial_repetition|source_conflict_pair|prerequisite_overlap|paraphrase_near_duplicate|qualifier_mismatch|temporal_scope_mismatch" docs/experiments/P58-provenance-aware-redundancy-plan.md docs/templates/provenance-redundancy-diagnostic-template.json tests/test_p58_provenance_aware_redundancy.py
```

Result: exit 0. Required categories are present in plan, template, and tests.

```text
rg -n "failed_closed_no_rows|blocked_operator_required|no_imported_traces|P55|P56|P57" docs/experiments/P58-provenance-aware-redundancy-plan.md docs/reviews/P58-provenance-aware-redundancy-review.md
```

Result: exit 0. Hits preserve P55/P56/P57 boundary statements only.

```text
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" docs/templates/provenance-redundancy-diagnostic-template.json docs/experiments/P58-provenance-aware-redundancy-plan.md docs/reviews/P58-provenance-aware-redundancy-review.md
```

Result before embedding this check log: exit 1, no matches in the P58 plan/template/review surfaces. The plan and template contain no volatile fields.

## Checks skipped

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

P58 is a docs/template/test scaffold only. Independent review is required before any further phase progression.

## Required changes

None.

## Next-phase decision

Independent review is required before any further phase progression. P59/P60 may not proceed from this P58 scaffold without separate authorization and review.
