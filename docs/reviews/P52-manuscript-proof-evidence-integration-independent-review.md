phase: P52
phase_name: manuscript proof repair and evidence-state integration independent review
reviewer: codex-independent-review
date: 2026-05-11
verdict: ACCEPT_WITH_NOTES
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

- Out-of-scope worktree items:
  - Modified from earlier phases: `AGENTS.md`, `README.md`, `docs/README.md`, `docs/codex/README.md`, `docs/templates/claim-boundary-checklist.md`.
  - Pre-existing untracked items: `.codex/automation-state/`, `artifacts/experiments/synthetic_regime_v12/events.jsonl`, P51-P60 planning/protocol docs, P51 review files, and P52 implementation review file while untracked.
  - Optional `docs/paper/P52-manuscript-evidence-integration-note.md` is not present.

## Summary

P52 updates the v12 manuscript anchor and focused guardrail tests only. The manuscript now tightens the `vinfo_proxy_supported` boundary, records P45 `bio_attribute` as an implemented but non-calibrated bridge lane, removes stale future-only bridge-calibration wording, and preserves the fail-closed P45 negative result. The P52 review note records the phase as manuscript alignment only.

## Proof review

Appendix B no longer contains damaged summation text such as `sum_{j 0`. It contains the required telescoping / pairwise-additive step with `\sum_{j<i}\eta(x_i,x_j\mid L)`, the degree-cap step with `\Delta f(x_i\mid L)+\min(i-1,d)\eta_{\max}`, and the final `A(L,S)+\psi_{s,d}\eta_{\max}` summation. The proof remains a conditional formal proof for the mathematical value function and does not imply deployed theorem verification.

## Evidence-state integration review

The manuscript acknowledges that the P45 bridge-calibration lane was implemented for the current `bio_attribute` stratum. It states that the current stratum is non-calibrated, did not establish a stable utility-to-logloss bridge, and supports only `operational_utility_only` or `ambiguous_metric` downstream labels. P45 closure is framed as fail-closed negative claim-gate evidence, not bridge support. Future bridge work is described as requiring a materially new active stratum or materially new fixed-logloss/utility design.

## vinfo_proxy_supported review

The definition is stricter. Generic utility-to-logloss correlation is explicitly insufficient for formal V-information support. The manuscript now requires log-loss alignment plus a fresh fixed-model-to-`V_i` bridge, a reviewed near-optimality argument, or actual empirical minimization over the declared predictive family, while preserving the separation among utility proxies, fixed-model logloss, and formal predictive V-information.

## Claim-boundary review

- Metric claim ceiling: `none`
- Selector label ceiling: `none`
- Paper eligibility: `false`
- Measurement validation claim: `false`
- Denied claims remain denied: `measurement_validated`, deployed V-information verification, theorem-level deployed submodularity verification, synthetic evidence as bridge evidence, fixture evidence as paper-grade evidence, replay usability as metric support, extraction audit as selector validity, `ReprojectionWitness` as deployed runtime improvement, current P45 `bio_attribute` as `calibrated_proxy_supported`, human-label validation, human-human kappa, and deployed runtime improvement.
- No claim was upgraded.

## Guardrail test review

The new tests are narrow, deterministic, and claim-safe. They check for the damaged Appendix B proof string, required proof fragments, P45 non-calibrated closure wording, absence of stale Section 4.7 `to be measured` wording, and the stricter `vinfo_proxy_supported` definition. They do not introduce live API calls, absolute local paths, timestamps, UUIDs, or nondeterministic output dependencies. The test count increase from 11 to 13 is plausible.

## Checks run

```text
git status --short
Result: exit 0.
 M AGENTS.md
 M README.md
 M docs/README.md
 M docs/archive/context_projection_fixed_v12.md
 M docs/codex/README.md
 M docs/templates/claim-boundary-checklist.md
 M tests/test_revised_framing_guardrails.py
?? .codex/automation-state/
?? artifacts/experiments/synthetic_regime_v12/events.jsonl
?? docs/experiments/P51-P60-v12-followup-dev-experiment-plan.md
?? docs/mingx-v12-p51-p60-followup-dev-experiment-plan.md
?? docs/mingx-v12-p51-p60-review-protocol.md
?? docs/reviews/P51-P60-v12-review-claim-gate-protocol.md
?? docs/reviews/P51-followup-doc-entrypoint-cleanup-independent-review.md
?? docs/reviews/P51-followup-doc-entrypoint-cleanup-review.md
?? docs/reviews/P51-v12-state-reconciliation-independent-review.md
?? docs/reviews/P51-v12-state-reconciliation-review.md
?? docs/reviews/P52-manuscript-proof-evidence-integration-review.md

git diff -- docs/archive/context_projection_fixed_v12.md tests/test_revised_framing_guardrails.py docs/reviews/P52-manuscript-proof-evidence-integration-review.md
Result: exit 0. Non-empty tracked diff for docs/archive/context_projection_fixed_v12.md and tests/test_revised_framing_guardrails.py. The untracked P52 implementation review file was read directly because plain git diff does not show untracked file contents. Output ended with LF-to-CRLF warnings for the two tracked P52 files.

git diff --check
Result: exit 0. Output contained only LF-to-CRLF warnings for AGENTS.md, README.md, docs/README.md, docs/archive/context_projection_fixed_v12.md, docs/codex/README.md, docs/templates/claim-boundary-checklist.md, and tests/test_revised_framing_guardrails.py.

uv run pytest tests/test_revised_framing_guardrails.py
Result: exit 0. 13 passed in 0.69s.

python -m compileall cps tests scripts
Result: exit 0. Listed cps, tests, tests\\.tmp subdirectories, and scripts with no compile errors.

uv run pytest
Result: exit 0. 523 passed, 4 skipped in 34.44s.

rg -n -F "sum_{j 0" docs/archive/context_projection_fixed_v12.md
Result: exit 1. No matches.

rg -n "bio_attribute|non-calibrated|calibrated_proxy_supported|operational_utility_only|ambiguous_metric" docs/archive/context_projection_fixed_v12.md
Result: exit 0. Matches at lines 271, 272, 309, 359, 360, 361, 367, 464, 468, 470, 716, and 762. P45-specific matches describe the current bio_attribute stratum as implemented, non-calibrated, fail-closed, and limited to operational_utility_only or ambiguous_metric.

rg -n "vinfo_proxy_supported|fixed-model-to-V_i|near-optimality|empirical minimization|utility/logloss correlation" docs/archive/context_projection_fixed_v12.md
Result: exit 0. Matches at lines 284, 288, 358, and 468. The relevant lines require fresh bridge / near-optimality / empirical minimization evidence and deny vinfo_proxy_supported for current P45.

rg -n "Vinfo_proxy_certified|greedy_valid|measurement_validated" docs/archive/context_projection_fixed_v12.md
Result: exit 0. Matches at lines 264, 268, 269, 270, 499, and 593. These are denied, gate, or non-upgrade contexts; no active deprecated-label claim was found.

rg -n "deployed V-information verification|theorem-level deployed submodularity verification" docs/archive/context_projection_fixed_v12.md
Result: exit 0. Matches at lines 37, 273, and 760. These deny deployed V-information verification; no active theorem-level deployed submodularity verification claim was found.

rg -n "to be measured|future work|new stratum|materially new" docs/archive/context_projection_fixed_v12.md
Result: exit 0. Matches at lines 470, 716, and 762. The stale Section 4.7 to-be-measured bridge table is gone; matches describe future bridge work as requiring materially new stratum/design.

rg -n "P53|P54|P55|P56|P57|P58|P59|P60|diagnostic threshold contract|new bridge stratum|bridge pilot|replay substrate expansion|extraction audit v2|provenance-aware redundancy|re-projection replay integration|evidence ledger" docs/archive/context_projection_fixed_v12.md tests/test_revised_framing_guardrails.py docs/reviews/P52-manuscript-proof-evidence-integration-review.md
Result: exit 0. Matches are limited to P51-P60 plan/protocol path constants in tests, the P52 review statement that P53 was not started / may proceed after independent review, and ordinary future-work wording for provenance-aware redundancy in the manuscript. No P53-P60 implementation was found in P52 target files.

if (Select-String -Path 'docs/reviews/P52-manuscript-proof-evidence-integration-review.md' -Pattern '[ \t]+$') { exit 1 } else { 'no trailing whitespace in P52 review file' }
Result: exit 0. no trailing whitespace in P52 review file
```

## Checks not run

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

- Unrelated dirty and untracked worktree items from prior P45-P51 work remain outside the P52 scope.
- `git diff --check` continues to print LF-to-CRLF warnings only.

## Required changes

None.

## Next-phase decision

P53 may proceed. P52 has an `ACCEPT_WITH_NOTES` verdict, no operator/scientific gate is triggered, no proof damage remains, and no claim-boundary violation remains.
