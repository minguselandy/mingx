phase: P55
phase_name: new-stratum bridge calibration pilot
reviewer: codex
date: 2026-05-11
verdict: BLOCKED_OPERATOR_REQUIRED
blocked: true
requires_operator: true
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

- Changed files:
  - `cps/experiments/bridge_calibration_pilot.py`
  - `configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-p55.json`
  - `docs/experiments/P55-new-stratum-bridge-calibration-pilot.md`
  - `tests/test_p55_bridge_calibration_pilot.py`
- Added files:
  - `docs/reviews/P55-new-stratum-bridge-calibration-pilot-review.md`
- Generated artifacts:
  - `artifacts/experiments/p55_bridge_calibration_pilot/manifest.json`
  - `artifacts/experiments/p55_bridge_calibration_pilot/claim_gate_report.json`
  - `artifacts/experiments/p55_bridge_calibration_pilot/report.md`

## Summary

P55 added a deterministic importer, validator, fit/report path, claim gate, P55 run config, focused tests, experiment note, and review note for the P54-approved `evidence_packet_selection_microtask_v1` stratum. No operator-imported row file was present at the configured input path, so the run produced a blocked fail-closed report instead of fabricating pilot data.

## Operator approval review

Route A approval is interpreted narrowly: operator-imported rows are allowed if present and contract-compliant. The approval does not cover live API execution, credentials, human labels, human-human kappa, measurement validation, deployed V-information verification, or broader claim upgrades.

## Row validation review

Configured input path:

`artifacts/operator_inputs/p55_evidence_packet_selection_microtask_v1_rows.jsonl`

No file was present at that path. The generated report records `input_rows_present: false`, `row_count: 0`, `candidate_pool_hash_status: missing`, and `schema_valid: false`. This is a blocked data-source state, not a pilot success.

## Active-stratum review

No rows were evaluated, so no active-stratum match was established. The importer requires exact match to `evidence_packet_selection_microtask_v1`, the P54 materialization/model/decoding/candidate-slice policies, and the P53 contract id before any claim inheritance.

## Fit/report review

- `c_s`: not fit because no operator-imported rows were present.
- `zeta_s`: not reported because no held-out split exists.
- sign agreement: not reported.
- rank correlation: not reported.
- residual stability: `unavailable`.
- ESS: `0.0`, below the P55 gate.
- drift status: `missing`.
- contamination status: `not_applicable`.

## Claim-gate review

- Final metric claim level: `ambiguous_metric` in the artifact report, with review ceiling `none` because no evidence rows were present.
- Selector label ceiling: `none`.
- Paper eligibility: `false`.
- Denied claims: measurement validation, human-label validation, human-human kappa, deployed V-information verification, theorem-level deployed submodularity verification, synthetic evidence as bridge evidence, fixture evidence as paper-grade evidence, replay usability as metric support, extraction audit as selector validity, `ReprojectionWitness` as deployed runtime improvement, current P45 `bio_attribute` as `calibrated_proxy_supported`, P55 fixture/test rows as `calibrated_proxy_supported`, and `vinfo_proxy_supported` without separate formal bridge review.
- Failure reasons: `no_operator_imported_rows`, `operator_rows_required`.

## Artifact determinism review

Canonical P55 outputs are deterministic JSON/Markdown files with stable key ordering and no dates, UUID-like identifiers, absolute local paths, API keys, credentials, or machine-specific fields in the generated artifact contents.

## Checks run

- `python -m cps.experiments.bridge_calibration_pilot --config configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-p55.json`
  - Result: exit 0; wrote blocked fail-closed artifacts; printed `claim_gate_status: failed_closed_no_rows`, `metric_claim_level: ambiguous_metric`, `paper_evidence_eligible: false`, `pilot_status: blocked_operator_required`, reasons `no_operator_imported_rows` and `operator_rows_required`.
- `uv run pytest tests/test_p55_bridge_calibration_pilot.py`
  - Initial result: exit 1; 10 passed, 1 failed. Failure was in `test_c_s_uses_dev_rows_and_zeta_uses_heldout_rows_only` because the test fixture's residual-stability groups had a gap above the configured threshold.
- `uv run pytest tests/test_p55_bridge_calibration_pilot.py`
  - Final result: exit 0; 11 passed in 0.43s.
- `python -m json.tool configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-p55.json`
  - Result: exit 0; JSON parsed successfully.
- `python -m json.tool artifacts/experiments/p55_bridge_calibration_pilot/manifest.json`
  - Result: exit 0; JSON parsed successfully.
- `python -m json.tool artifacts/experiments/p55_bridge_calibration_pilot/claim_gate_report.json`
  - Result: exit 0; JSON parsed successfully.
- `uv run pytest tests/test_p54_bridge_stratum_design.py`
  - Result: exit 0; 5 passed in 0.05s.
- `uv run pytest tests/test_diagnostic_threshold_contract.py`
  - Result: exit 0; 7 passed in 0.05s.
- `uv run pytest tests/test_revised_framing_guardrails.py`
  - Result: exit 0; 13 passed in 0.62s.
- `uv run pytest tests/test_phase_b_replay.py`
  - Result: exit 0; 25 passed in 1.45s.
- `python -m compileall cps tests scripts`
  - Result: exit 0; completed compile listing for `cps`, `tests`, and `scripts`.
- `git diff --check`
  - Result: exit 0; reported line-ending warnings for pre-existing modified files (`AGENTS.md`, `README.md`, `docs/README.md`, `docs/archive/context_projection_fixed_v12.md`, `docs/codex/README.md`, `docs/templates/claim-boundary-checklist.md`, `tests/test_revised_framing_guardrails.py`) but no whitespace errors.
- `uv run pytest -q`
  - Result: exit 0; 546 passed, 4 skipped in 32.50s.
- `rg -n "measurement_validated|human-human kappa|deployed V-information verification|theorem-level deployed submodularity verification" docs/reviews/P55-new-stratum-bridge-calibration-pilot-review.md docs/experiments/P55-new-stratum-bridge-calibration-pilot.md cps/experiments/bridge_calibration_pilot.py tests/test_p55_bridge_calibration_pilot.py configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-p55.json artifacts/experiments/p55_bridge_calibration_pilot`
  - Result: exit 0; hits are denied/boundary statements only. No active measurement-validation, kappa, deployed V-information verification, or theorem-level deployed submodularity verification claim was found.
- `rg -n "calibrated_proxy_supported|vinfo_proxy_supported|ambiguous_metric|operational_utility_only" docs/reviews/P55-new-stratum-bridge-calibration-pilot-review.md docs/experiments/P55-new-stratum-bridge-calibration-pilot.md cps/experiments/bridge_calibration_pilot.py tests/test_p55_bridge_calibration_pilot.py configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-p55.json artifacts/experiments/p55_bridge_calibration_pilot`
  - Result: exit 0; `calibrated_proxy_supported` appears only in the conditional P55 gate, unit-test positive path, or denied fixture/P45/vinfo boundaries. The generated artifacts remain `ambiguous_metric` and do not allow `calibrated_proxy_supported` or `vinfo_proxy_supported`.
- `rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" artifacts/experiments/p55_bridge_calibration_pilot configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-p55.json tests/test_p55_bridge_calibration_pilot.py docs/reviews/P55-new-stratum-bridge-calibration-pilot-review.md`
  - Result: exit 0; hits were only the P55 test's negative assertions for `/home/` and `/mnt/`. No generated artifact, config, or review content contained volatile identifiers, API-key fields, credentials, or absolute local paths.

## Checks not run

None.

## Findings

### Blocking findings

Operator-imported P55 rows are absent. P55 remains blocked for actual bridge-pilot execution until the operator supplies contract-compliant rows for the approved stratum.

### Non-blocking notes

The importer and unit tests include a calibrated positive path only in temporary test data to verify deterministic gate behavior. No such rows are committed as evidence, and the generated P55 artifacts remain blocked and paper-ineligible.

## Required changes

None for the blocked fail-closed report state. To run a real P55 pilot, provide contract-compliant operator-imported rows at the configured input path or an explicitly reviewed override.

## Next-phase decision

P56 should not proceed from P55 as a completed bridge pilot. Independent review may review the blocked P55 report, but actual P55 execution remains blocked until operator-imported rows are supplied and pass the contract gates.
