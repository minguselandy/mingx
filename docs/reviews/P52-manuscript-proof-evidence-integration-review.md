phase: P52
phase_name: manuscript proof repair and evidence-state integration
reviewer: codex
date: 2026-05-11
verdict: ACCEPT
blocked: false
requires_operator: false
next_phase_allowed: true
metric_claim_level_max: none
selector_regime_label_max: none
paper_evidence_eligible: false
measurement_validation_claim: false
live_api_used: false
human_labels_present: false
human_human_kappa_present: false
contamination_status: not_applicable

## Scope reviewed

- Changed files:
  - `docs/archive/context_projection_fixed_v12.md`
  - `tests/test_revised_framing_guardrails.py`
  - `docs/reviews/P52-manuscript-proof-evidence-integration-review.md`
- Generated artifacts: none.

## Summary

P52 repaired the manuscript alignment around Appendix B proof integrity, the P45 bridge-calibration closure, remaining bridge-work language, and the `vinfo_proxy_supported` definition. The edit is manuscript and guardrail hygiene only; it does not start P53 or upgrade any evidence claim.

## Manuscript proof review

Appendix B no longer contains the damaged `sum_{j 0` summation text. The manuscript contains the required pairwise-additive telescoping step, the degree-cap step, and the final summation:

- `\sum_{j<i}\eta(x_i,x_j\mid L)`
- `\Delta f(x_i\mid L)+\min(i-1,d)\eta_{\max}`
- `A(L,S)+\psi_{s,d}\eta_{\max}`

The proof remains conditional and does not imply theorem-level deployed submodularity verification.

## Evidence-state integration review

The manuscript now records that the P45 bridge-calibration lane was implemented for the current `bio_attribute` stratum and closed as non-calibrated. It states that the current stratum did not establish a stable utility-to-logloss bridge, that allowed downstream labels remain `operational_utility_only` or `ambiguous_metric`, and that the result is fail-closed claim-gate evidence, not bridge support.

## Claim-boundary review

- Metric claim ceiling: `none`
- Selector label ceiling: `none`
- Paper eligibility: `false`
- Measurement validation claim: `false`
- No claim upgrade
- No certification framing introduced

The manuscript also tightens `vinfo_proxy_supported` so generic utility-to-logloss correlation is not formal V-information support by itself; support requires log-loss alignment plus a fresh fixed-model-to-`V_i` bridge, a reviewed near-optimality argument, or empirical minimization over the declared predictive family.

## Checks run

- `uv run pytest tests/test_revised_framing_guardrails.py`
  - Result: exit 0; `13 passed in 0.62s`.
- `git diff --check`
  - Result: exit 0; no whitespace errors. Git printed LF-to-CRLF warnings for tracked dirty files.
- `if (Select-String -Path 'docs/reviews/P52-manuscript-proof-evidence-integration-review.md' -Pattern '[ \t]+$') { exit 1 } else { 'no trailing whitespace in P52 review file' }`
  - Result: exit 0; `no trailing whitespace in P52 review file`.
- `python -m compileall cps tests scripts`
  - Result: exit 0; compile completed with no errors.
- `rg -n -F "sum_{j 0" docs/archive/context_projection_fixed_v12.md`
  - Result: exit 1; no matches.
- `rg -n "bio_attribute|non-calibrated|calibrated_proxy_supported|operational_utility_only|ambiguous_metric" docs/archive/context_projection_fixed_v12.md`
  - Result: exit 0; relevant hits at lines 309, 464, 468, 470, 716, and 762.
- `rg -n "Vinfo_proxy_certified|greedy_valid|measurement_validated" docs/archive/context_projection_fixed_v12.md`
  - Result: exit 0; matches are denied or non-upgrade contexts at lines 264, 268-270, 499, and 593.
- `rg -n "deployed V-information verification|theorem-level deployed submodularity verification" docs/archive/context_projection_fixed_v12.md`
  - Result: exit 0; matches are denied boundary statements at lines 37, 273, and 760. The theorem-level phrase had no active claim hit.
- `rg -n "vinfo_proxy_supported|fixed-model-to|Generic utility-to-log-loss correlation" docs/archive/context_projection_fixed_v12.md`
  - Result: exit 0; relevant hits at lines 284, 288, 358, 363, and 468.
- `rg -n "to be measured" docs/archive/context_projection_fixed_v12.md`
  - Result: exit 1; no matches.
- `uv run pytest`
  - Result: exit 0; `523 passed, 4 skipped in 40.70s`.

## Checks not run

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

None.

## Required changes

None.

## Next-phase decision

P53 may proceed after independent review of this P52 phase.
