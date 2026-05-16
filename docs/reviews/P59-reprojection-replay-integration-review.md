phase: P59
phase_name: ReprojectionWitness replay integration scaffold
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
deployed_runtime_improvement_claim: false
contamination_status: not_applicable

## Scope reviewed

- Files added:
  - `docs/experiments/P59-reprojection-replay-integration-plan.md`
  - `docs/templates/reprojection-witness-replay-template.json`
  - `tests/test_p59_reprojection_replay_integration.py`
  - `docs/reviews/P59-reprojection-replay-integration-review.md`
- Templates:
  - ReprojectionWitness replay-integration JSON template
- Tests:
  - focused P59 witness field, trigger, decision-rule, and claim-boundary tests
- Generated artifacts:
  - none

## Summary

P59 created a ReprojectionWitness replay-integration audit scaffold only. It defines required witness fields, replay binding rules, trigger types, fail-closed decision rules, conservative defaults, claim boundaries, and focused deterministic tests.

This phase did not import operator data, run live APIs, generate artifacts, execute replay traces, or upgrade evidence claims.

## Witness field review

The template records required identity, replay binding, trigger, budget, selector, candidate-pool, materialized-context, selected/excluded context, context-diff, output hash, evaluator, uncertainty, bridge, claim-gate, and denied-claim fields.

## Decision-rule review

The template records fail-closed behavior for:

- identity mismatch -> `not_comparable`
- candidate-pool mismatch without documented expansion -> `fail_closed_candidate_pool_mismatch`
- over-budget revised context -> `operational_violation`
- missing/stale/mismatched/underpowered bridge -> `ambiguous_metric` or `operational_utility_only`, with no calibrated or vinfo support
- fixture-only before/after improvement -> operational audit only

## Claim-boundary review

- Metric claim ceiling: `operational_utility_only`
- Selector label ceiling: `ambiguous`
- Paper eligibility: `false`
- Measurement validation claim: `false`
- Deployed runtime improvement claim: `false`

P59 does not prove deployed runtime improvement. P59 does not prove selector validity. P59 does not establish metric bridge support. P59 does not establish V-information support. P59 does not establish measurement validation. P59 does not make fixture/template outputs paper evidence.

## P55/P56/P57/P58 boundary review

P55 remains failed_closed_no_rows / blocked_operator_required. Rows imported/validated remain 0. P55 review ceiling remains none. P55 paper evidence remains false. P55 fit metrics remain not computed.

P56 remains no_imported_traces. Traces imported/validated remain 0. P56 review ceiling remains none. P56 paper evidence remains false. P56 measurement validation remains false. P56 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.

P57 remains extraction-risk scaffold only. P58 remains operational diagnostic scaffold only. P59 does not proceed from P55/P56 success. P59 does not convert P57/P58 scaffolds into evidence claims. P59 does not repair P55/P56 blocked states.

## Checks run

```text
uv run pytest tests/test_p59_reprojection_replay_integration.py
```

Initial RED result before P59 plan/template/review files existed: exit 1, 8 failed. Failures were expected missing-file errors for:

- `docs/experiments/P59-reprojection-replay-integration-plan.md`
- `docs/templates/reprojection-witness-replay-template.json`
- `docs/reviews/P59-reprojection-replay-integration-review.md`

```text
python -m json.tool docs/templates/reprojection-witness-replay-template.json
```

Result: exit 0. JSON parsed successfully.

```text
uv run pytest tests/test_p59_reprojection_replay_integration.py
```

Final result: exit 0, 8 passed in 0.07s.

```text
git diff --check
```

Result: exit 0, with unrelated dirty `AGENTS.md` line-ending warning.

```text
warning: in the working copy of 'AGENTS.md', LF will be replaced by CRLF the next time Git touches it
```

```text
uv run pytest tests/test_revised_framing_guardrails.py
```

Result: exit 0, 13 passed in 0.73s.

```text
python -m compileall cps tests scripts
```

Result: exit 0. Compileall completed for `cps`, `tests`, and `scripts`.

```text
uv run pytest -q
```

Result: exit 0, 583 passed, 4 skipped in 33.34s.

Focused scans:

```text
rg -n "deployed runtime improvement|selector validity|metric bridge support|V-information support|measurement validation|paper-grade evidence|calibrated_proxy_supported|vinfo_proxy_supported|measurement_validated" docs/experiments/P59-reprojection-replay-integration-plan.md docs/templates/reprojection-witness-replay-template.json docs/reviews/P59-reprojection-replay-integration-review.md tests/test_p59_reprojection_replay_integration.py
```

Result: exit 0. Hits are denied, gated, review, or negative-test contexts only. Representative hits:

```text
docs/experiments/P59-reprojection-replay-integration-plan.md:19:P59 does not prove deployed runtime improvement.
docs/experiments/P59-reprojection-replay-integration-plan.md:20:P59 does not prove selector validity.
docs/experiments/P59-reprojection-replay-integration-plan.md:21:P59 does not establish metric bridge support.
docs/experiments/P59-reprojection-replay-integration-plan.md:22:P59 does not establish V-information support.
docs/experiments/P59-reprojection-replay-integration-plan.md:23:P59 does not establish measurement validation.
docs/templates/reprojection-witness-replay-template.json:89:        "calibrated_proxy_supported",
docs/templates/reprojection-witness-replay-template.json:90:        "vinfo_proxy_supported"
```

```text
rg -n "unknown_due_to_missing_context|hallucination_risk|wrong_despite_context|ambiguous|operator_review_requested|budget_overflow|candidate_pool_mismatch" docs/experiments/P59-reprojection-replay-integration-plan.md docs/templates/reprojection-witness-replay-template.json tests/test_p59_reprojection_replay_integration.py
```

Result: exit 0. Required trigger types are present in plan, template, and tests.

```text
rg -n "failed_closed_no_rows|blocked_operator_required|no_imported_traces|P55|P56|P57|P58" docs/experiments/P59-reprojection-replay-integration-plan.md docs/reviews/P59-reprojection-replay-integration-review.md
```

Result: exit 0. Hits preserve P55/P56/P57/P58 boundary statements only.

```text
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" docs/templates/reprojection-witness-replay-template.json docs/experiments/P59-reprojection-replay-integration-plan.md docs/reviews/P59-reprojection-replay-integration-review.md
```

Result before embedding this check log: exit 1, no matches in the P59 plan/template/review surfaces. The template contains no volatile or machine-specific fields.

```text
Get-ChildItem artifacts\experiments -Directory | Where-Object { $_.Name -match 'p59|reprojection.*replay|reprojection-replay' } | Select-Object Name,FullName
```

Result: exit 0, no output. No P59 generated artifact directory was created.

## Checks skipped

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

P59 is a docs/template/test scaffold only. Independent review is required before any further phase progression.

## Required changes

None.

## Next-phase decision

Independent review is required before any further phase progression. P60 may not proceed from this P59 scaffold without separate authorization and review.
