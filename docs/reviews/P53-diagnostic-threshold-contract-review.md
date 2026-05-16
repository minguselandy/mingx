phase: P53
phase_name: diagnostic threshold contract and MetricBridgeWitness contract hardening
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
  - `docs/protocols/diagnostic-threshold-contract-v12.md`
  - `docs/templates/diagnostic-threshold-contract-template.json`
  - `tests/test_diagnostic_threshold_contract.py`
  - `docs/reviews/P53-diagnostic-threshold-contract-review.md`
- Generated artifacts: none.

## Summary

P53 adds a predeclared diagnostic threshold contract protocol, a deterministic JSON template, and focused tests for the contract surface. The phase is protocol/audit scaffold only. It does not create bridge evidence, validate a metric bridge, upgrade empirical claims, or start P54/P55 work.

## Contract review

The protocol and template record:

- active stratum;
- calibration epoch;
- thresholds for signal, ratio LCB, pairwise excess, SAG gap, triple sentinel, and ESS;
- LCB method and conservative fallback;
- ESS gate;
- drift policy for `fresh`, `stale`, `ambiguous`, `missing`, and `mismatched`;
- underpowered policy;
- fixture and synthetic fail-closed policies.

Runtime/schema code was not modified. Existing replay and bridge-calibration surfaces already preserve conservative MetricBridgeWitness and fixture/synthetic behavior, so P53 stayed as a doc/template/test scaffold.

## Decision logic review

Every diagnostic label in the contract is traceable to predeclared thresholds or explicit fail-closed rules. The template encodes precedence for hard claim-boundary failures, metric-bridge failures, fixture/synthetic restrictions, signal and ESS checks, higher-order checks, pairwise-escalation checks, greedy-supported checks, and ambiguous fallback. Earlier fail-closed conditions block later upgraded labels.

## MetricBridgeWitness semantics review

The protocol and template state that MetricBridgeWitness records bridge status and provenance, and that presence alone is not bridge support. Stale, missing, mismatched, underpowered, incomplete, or failed witness states downgrade claims. Replay usability, synthetic structural signatures, fixture success, extraction audit completeness, ReprojectionWitness rows, and model-adjudicated labels do not imply metric support.

## Claim-boundary review

- Metric claim ceiling: `none`
- Selector label ceiling: `none`
- Paper eligibility: `false`
- Measurement validation claim: `false`
- No claim upgrade
- Protocol scaffold only

The current P45 `bio_attribute` closure remains non-calibrated, fail-closed, not bridge support, and not `calibrated_proxy_supported`.

## Checks run

- `python -m json.tool docs/templates/diagnostic-threshold-contract-template.json`
  - Result: exit 0; JSON parsed and pretty-printed successfully.
- `uv run pytest tests/test_diagnostic_threshold_contract.py`
  - Result: exit 0; `7 passed in 0.05s`.
- `rg -n "contract_id|calibration_epoch|active_stratum|min_effective_sample_size|ratio_lcb_method|underpowered_policy|fixture_policy|synthetic_policy" docs/protocols/diagnostic-threshold-contract-v12.md docs/templates/diagnostic-threshold-contract-template.json`
  - Result: exit 0; required field hits were present in the protocol and template, including template lines 2, 4, 5, 37, 51, 79, 96, and 108, and protocol lines 54, 56, 57, 61, 67, 69, 70, 71, 76, 195, and 196.
- `rg -n "Vinfo_proxy_certified|greedy_valid|measurement_validated" docs/protocols/diagnostic-threshold-contract-v12.md docs/templates/diagnostic-threshold-contract-template.json`
  - Result: exit 0; matches only in protocol denied/legacy examples at lines 44-46. No template matches.
- `rg -n "validation|validated|paper-grade|deployed V-information verification|theorem-level deployed submodularity verification" docs/protocols/diagnostic-threshold-contract-v12.md`
  - Result: exit 0; matches are denial or non-validation boundary statements at lines 11, 46, 207-209, 211, and 216.
- `uv run pytest tests/test_revised_framing_guardrails.py`
  - Result: exit 0; `13 passed in 0.70s`.
- `uv run pytest tests/test_phase_b_replay.py`
  - Result: exit 0; `25 passed in 1.43s`.
- `uv run pytest tests/test_projection_artifacts.py`
  - Result: exit 0; `3 passed in 0.12s`.
- `uv run pytest tests/test_bridge_calibration_experiment.py`
  - Result: exit 0; `19 passed in 0.41s`.
- `python -m compileall cps tests scripts`
  - Result: exit 0; compile completed with no errors and compiled `tests\test_diagnostic_threshold_contract.py`.
- `git diff --check`
  - Result: exit 0; no whitespace errors. Git printed LF-to-CRLF warnings for pre-existing tracked dirty files.
- `if (Select-String -Path 'docs/protocols/diagnostic-threshold-contract-v12.md','docs/templates/diagnostic-threshold-contract-template.json','tests/test_diagnostic_threshold_contract.py','docs/reviews/P53-diagnostic-threshold-contract-review.md' -Pattern '[ \t]+$') { exit 1 } else { 'no trailing whitespace in P53 files' }`
  - Result: exit 0; `no trailing whitespace in P53 files`.
- `uv run pytest`
  - Result: exit 0; `530 passed, 4 skipped in 31.53s`.

## Checks not run

- `uv run pytest tests/test_bridge_calibration.py`
  - Reason: `tests/test_bridge_calibration.py` does not exist in this checkout. The closest relevant focused bridge test, `uv run pytest tests/test_bridge_calibration_experiment.py`, was run instead and passed.

## Findings

### Blocking findings

None.

### Non-blocking notes

- `git diff --check` still prints LF-to-CRLF warnings for tracked dirty files that predate this P53 patch.
- Several P51/P52 files remain untracked in the worktree from prior phases; P53 did not modify them.

## Required changes

None.

## Next-phase decision

P54 may proceed after independent review of this P53 phase.
