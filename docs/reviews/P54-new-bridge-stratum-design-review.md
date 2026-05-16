phase: P54
phase_name: materially new bridge-calibration stratum design
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

- Changed files: none.
- Added files:
  - `docs/experiments/P54-new-bridge-stratum-design-v12.md`
  - `configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json`
  - `tests/test_p54_bridge_stratum_design.py`
  - `docs/reviews/P54-new-bridge-stratum-design-review.md`
- Generated artifacts: none.

## Summary

P54 selects exactly one materially new bridge-calibration stratum for a future P55 pilot: `evidence_packet_selection_microtask_v1`. The phase adds a design document, a dry-run JSON config, focused config/design tests, and this self-review. It does not execute P55, import rows, generate rows, run live APIs, create bridge evidence, validate a metric bridge, or upgrade claims.

## Stratum design review

- Selected stratum: `evidence_packet_selection_microtask_v1`
- Material distinction from P45: P45 `bio_attribute` remains a closed, non-calibrated stratum. P54 changes the task family, target type, candidate pool shape, utility definition, and logloss target evidence path. It does not scale or retry the failed P45 canaries.
- Selected target type: forced-choice or exact short field with explicit target evidence.
- Logloss measurement path: fixed-model target logloss over the declared answer, using token logprobs or forced-choice likelihood. `delta_logloss` must not be fabricated from utility or preference scores.
- Utility metric: `decomposable_answer_correctness_v1`.
- Candidate slice / block size: fixed top-8 candidate packet slice; block size 1 or 2.
- Model/materialization/decoding policy: fixed evaluated model tier, `fixed_order_evidence_packet_v1`, and `deterministic_logloss_scoring_no_generation`.

## Negative controls

Included:

- redundancy-heavy cases;
- pairwise-complementarity cases;
- underpowered/noisy cases expected to produce `ambiguous_metric`;
- stale bridge witness fail-closed cases;
- mismatched bridge witness fail-closed cases;
- candidate-pool hash mismatch cases expected to be paper-ineligible;
- distractor evidence packets;
- prerequisite-missing cases;
- qualifier-sensitive cases;
- source-conflict cases.

## Operator gates

P55 requires independent acceptance of this P54 design and operator approval for the selected data source before imported rows may be used. Live API execution and human-labeled rows remain separately blocked unless the operator explicitly approves them in a later phase. P54 itself used no live API and no human labels.

## Claim-boundary review

- Metric claim ceiling: `none`
- Selector label ceiling: `none`
- Paper eligibility: `false`
- Measurement validation claim: `false`
- Design review only
- No bridge evidence created
- No claim upgrade

The current P45 `bio_attribute` stratum remains non-calibrated, fail-closed, not bridge support, and not `calibrated_proxy_supported`. P54 does not claim `vinfo_proxy_supported` or `calibrated_proxy_supported`.

## Checks run

- `python -m json.tool configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json`
  - Result: exit 0; JSON parsed and pretty-printed successfully.
- `uv run pytest tests/test_p54_bridge_stratum_design.py`
  - Result: exit 0; `5 passed in 0.04s`.
- `if (Select-String -Path 'docs/experiments/P54-new-bridge-stratum-design-v12.md','configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json','tests/test_p54_bridge_stratum_design.py','docs/reviews/P54-new-bridge-stratum-design-review.md' -Pattern '[ \t]+$') { exit 1 } else { 'no trailing whitespace in P54 files' }`
  - Result: exit 0; `no trailing whitespace in P54 files`.
- `rg -n "bio_attribute|evidence_packet_selection_microtask_v1|task_family|target_type|logloss|negative_controls|operator_gates|measurement_validated|calibrated_proxy_supported|vinfo_proxy_supported" docs/experiments/P54-new-bridge-stratum-design-v12.md configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json docs/reviews/P54-new-bridge-stratum-design-review.md`
  - Result: exit 0; expected hits show P45 distinction, selected stratum, required fields, logloss path, operator gates, and denied claim boundaries. Review-file matches are self-documenting command/result lines or claim-boundary statements.
- `rg -n "live API|operator-approved|human labels|kappa|paper-grade|deployed V-information verification|theorem-level deployed submodularity verification" docs/experiments/P54-new-bridge-stratum-design-v12.md configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json docs/reviews/P54-new-bridge-stratum-design-review.md`
  - Result: exit 0; expected hits are blocked, denied, metadata-false, or operator-gated boundary statements. Review-file matches are self-documenting command/result lines or claim-boundary statements.
- `uv run pytest tests/test_revised_framing_guardrails.py`
  - Result: exit 0; `13 passed in 0.69s`.
- `python -m compileall cps tests scripts`
  - Result: exit 0; compile completed with no errors and compiled `tests\test_p54_bridge_stratum_design.py`.
- `git diff --check`
  - Result: exit 0; no whitespace errors. Git printed LF-to-CRLF warnings for pre-existing tracked dirty files.
- `uv run pytest`
  - Result: exit 0; `535 passed, 4 skipped in 37.01s`.

## Checks not run

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

- The dry-run config is a P54 design artifact only; it does not point to input rows or output artifacts.
- The worktree still contains unrelated tracked modifications and untracked prior-phase files outside P54 scope.
- `git diff --check` continues to print LF-to-CRLF warnings for pre-existing tracked dirty files.

## Required changes

None.

## Next-phase decision

P55 may proceed only after independent review accepts this P54 design and the operator approves the selected data source. Imported, live, or human-labeled rows remain blocked until that approval is explicit.
