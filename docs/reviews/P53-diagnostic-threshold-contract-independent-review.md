phase: P53
phase_name: diagnostic threshold contract and MetricBridgeWitness contract hardening independent review
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

- Added files:
  - `docs/protocols/diagnostic-threshold-contract-v12.md`
  - `docs/templates/diagnostic-threshold-contract-template.json`
  - `tests/test_diagnostic_threshold_contract.py`
  - `docs/reviews/P53-diagnostic-threshold-contract-review.md`

- Modified files:
  - None for P53. The actual tracked dirty files in the worktree are prior-phase or unrelated files.

- Out-of-scope worktree items:
  - `AGENTS.md`
  - `README.md`
  - `docs/README.md`
  - `docs/archive/context_projection_fixed_v12.md`
  - `docs/codex/README.md`
  - `docs/templates/claim-boundary-checklist.md`
  - `tests/test_revised_framing_guardrails.py`
  - `.codex/automation-state/`
  - `artifacts/experiments/synthetic_regime_v12/events.jsonl`
  - pre-existing P51/P52/P51-P60 planning and review documents shown by `git status --short`

## Summary

P53 added a protocol/audit scaffold for a diagnostic threshold contract, a deterministic JSON template, focused tests, and an implementation review note. It did not modify runtime or schema code, did not create bridge evidence, and did not start P54/P55/P56/P57/P58/P59/P60 work.

## Contract field review

Pass. The protocol and JSON template represent the required fields: `contract_id`, `contract_schema_version`, `calibration_epoch`, `active_stratum`, `metric_claim_level_precondition`, `block_size_max`, `signal_threshold`, `ratio_lcb_method`, `ratio_quantile`, `ratio_lcb_threshold`, `pairwise_excess_threshold`, `sag_gap_threshold`, `triple_excess_threshold`, `min_effective_sample_size`, `drift_policy`, `underpowered_policy`, `fixture_policy`, `synthetic_policy`, `decision_logic`, `claim_boundary`, and `paper_evidence_policy`.

The `active_stratum` object includes `task_family`, `model_tier`, `materialization_policy`, `block_size`, `candidate_slice`, `metric`, and `data_source_kind`.

## Decision logic review

Pass. Diagnostic labels are traceable to predeclared thresholds or fail-closed rules. The protocol/template define deterministic precedence from hard claim-boundary failures through metric-bridge downgrades, fixture/synthetic restrictions, signal/ESS gates, higher-order risk, pairwise escalation, greedy support, and ambiguous fallback. Earlier fail-closed conditions block later upgraded labels.

## Threshold and ESS review

Pass. Thresholds, LCB method, ratio quantile, and ESS gates are explicit or inactive with fail-closed behavior. `null` thresholds are allowed only for inactive gates, missing thresholds cannot be inferred post hoc, and the protocol does not claim universal scientific thresholds. Thresholds are stratum-specific unless separately justified.

## MetricBridgeWitness semantics review

Pass. `MetricBridgeWitness` records status and provenance, but presence alone is not bridge support. Missing, stale, mismatched, underpowered, incomplete, or failed witness states downgrade claims and cannot emit `vinfo_proxy_supported` or `calibrated_proxy_supported`.

## Fixture/synthetic/replay boundary review

Pass. Fixture-only, synthetic-only, and replay-completeness-only cases remain claim-limited and paper-ineligible. The contract does not infer metric support from replay completeness, synthetic structural signatures, fixture realistic-task success, extraction audit completeness, `ReprojectionWitness` rows, or model-adjudicated labels.

## Test review

Pass. `tests/test_diagnostic_threshold_contract.py` contains seven narrow deterministic tests. They parse the JSON template, cover required fields, fail-closed policies, threshold policy, deprecated-label exclusion from the template, conservative `MetricBridgeWitness` semantics, and protocol scaffold wording. The tests do not introduce live API dependencies or depend on absolute local paths, timestamps, UUIDs, or nondeterministic output.

## Claim-boundary review

- Metric claim ceiling: `none`
- Selector label ceiling: `none`
- Paper eligibility: `false`
- Measurement validation claim: `false`
- Denied claims remain denied.
- No claim was upgraded.
- P53 remains protocol/audit scaffold only.

Deprecated labels appear only as denied/legacy/archive examples or in tests that assert exclusion from the template. The template does not contain deprecated active labels.

## Checks run

```text
git status --short
Result: exit 0
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
?? docs/protocols/diagnostic-threshold-contract-v12.md
?? docs/reviews/P51-P60-v12-review-claim-gate-protocol.md
?? docs/reviews/P51-followup-doc-entrypoint-cleanup-independent-review.md
?? docs/reviews/P51-followup-doc-entrypoint-cleanup-review.md
?? docs/reviews/P51-v12-state-reconciliation-independent-review.md
?? docs/reviews/P51-v12-state-reconciliation-review.md
?? docs/reviews/P52-manuscript-proof-evidence-integration-independent-review.md
?? docs/reviews/P52-manuscript-proof-evidence-integration-review.md
?? docs/reviews/P53-diagnostic-threshold-contract-review.md
?? docs/templates/diagnostic-threshold-contract-template.json
?? tests/test_diagnostic_threshold_contract.py
```

```text
git diff -- docs/protocols/diagnostic-threshold-contract-v12.md docs/templates/diagnostic-threshold-contract-template.json tests/test_diagnostic_threshold_contract.py docs/reviews/P53-diagnostic-threshold-contract-review.md
Result: exit 0; no output because the P53 files are untracked additions.
```

```text
git diff --check
Result: exit 0; LF-to-CRLF warnings only:
warning: in the working copy of 'AGENTS.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'README.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/README.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/archive/context_projection_fixed_v12.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/codex/README.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/templates/claim-boundary-checklist.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tests/test_revised_framing_guardrails.py', LF will be replaced by CRLF the next time Git touches it
```

```text
python -m json.tool docs/templates/diagnostic-threshold-contract-template.json
Result: exit 0; JSON parsed and pretty-printed successfully.
```

```text
uv run pytest tests/test_diagnostic_threshold_contract.py
Result: exit 0; 7 passed in 0.07s
```

```text
uv run pytest tests/test_revised_framing_guardrails.py
Result: exit 0; 13 passed in 0.88s
```

```text
uv run pytest tests/test_phase_b_replay.py
Result: exit 0; 25 passed in 1.88s
```

```text
uv run pytest tests/test_projection_artifacts.py
Result: exit 0; 3 passed in 0.16s
```

```text
uv run pytest tests/test_bridge_calibration_experiment.py
Result: exit 0; 19 passed in 0.64s
```

```text
python -m compileall cps tests scripts
Result: exit 0; listed cps, tests, and scripts with no compile errors.
```

```text
uv run pytest
Result: exit 0; 530 passed, 4 skipped in 36.76s
```

```text
rg -n "contract_id|contract_schema_version|calibration_epoch|active_stratum|min_effective_sample_size|ratio_lcb_method|underpowered_policy|fixture_policy|synthetic_policy|decision_logic|claim_boundary|paper_evidence_policy" docs/protocols/diagnostic-threshold-contract-v12.md docs/templates/diagnostic-threshold-contract-template.json
Result: exit 0; expected required-field hits in the protocol at lines 54-57, 61, 67, 69-74, 76, 195-196 and in the template at lines 2-5, 37, 51, 56, 79, 96, 108, 119, 121, 168, 188.
```

```text
rg -n "metric_claim_level_precondition|block_size_max|signal_threshold|ratio_quantile|ratio_lcb_threshold|pairwise_excess_threshold|sag_gap_threshold|triple_excess_threshold|task_family|model_tier|materialization_policy|block_size|candidate_slice|metric|data_source_kind" docs/protocols/diagnostic-threshold-contract-v12.md docs/templates/diagnostic-threshold-contract-template.json
Result: exit 0; expected required-field and active-stratum hits in the protocol at lines 58-66 and 78-84, and in the template at lines 6-14, 31-45.
```

```text
rg -n "Vinfo_proxy_certified|greedy_valid|measurement_validated" docs/protocols/diagnostic-threshold-contract-v12.md docs/templates/diagnostic-threshold-contract-template.json tests/test_diagnostic_threshold_contract.py
Result: exit 0; expected denied/legacy/test-only hits at docs/protocols/diagnostic-threshold-contract-v12.md lines 44-46 and tests/test_diagnostic_threshold_contract.py lines 47-49. No template hits.
```

```text
rg -n "validation|validated|paper-grade|deployed V-information verification|theorem-level deployed submodularity verification" docs/protocols/diagnostic-threshold-contract-v12.md docs/templates/diagnostic-threshold-contract-template.json
Result: exit 0; expected denied-boundary hits at protocol lines 11, 46, 207-209, 211, 216 and false claim-boundary booleans in the template at lines 172-176.
```

```text
rg -n "replay completeness|synthetic structural|fixture|extraction audit|ReprojectionWitness|model-adjudicated" docs/protocols/diagnostic-threshold-contract-v12.md docs/templates/diagnostic-threshold-contract-template.json
Result: exit 0; expected boundary-policy hits in the protocol and template. Hits deny metric/paper support from replay completeness, synthetic structural signatures, fixture evidence, extraction audit completeness, ReprojectionWitness rows, and model-adjudicated labels.
```

```text
rg -n "P54|P55|P56|P57|P58|P59|P60|new bridge stratum|bridge pilot|replay substrate|extraction audit v2|provenance-aware|re-projection|evidence ledger" docs/protocols/diagnostic-threshold-contract-v12.md docs/templates/diagnostic-threshold-contract-template.json tests/test_diagnostic_threshold_contract.py docs/reviews/P53-diagnostic-threshold-contract-review.md
Result: exit 0; only docs/reviews/P53-diagnostic-threshold-contract-review.md lines 29 and 116 mention not starting P54/P55 and allowing P54 after independent review.
```

```text
if (Test-Path tests\test_bridge_calibration.py) { 'present' } else { 'missing' }
Result: exit 0; missing
```

```text
Select-String trailing-whitespace check over P53 files
Result: exit 0; no trailing whitespace matches in P53 files.
```

## Checks not run

```text
uv run pytest tests/test_bridge_calibration.py
Reason: file does not exist. Verified with Test-Path returning "missing". Closest relevant existing check run instead: uv run pytest tests/test_bridge_calibration_experiment.py, 19 passed in 0.64s.
```

## Findings

### Blocking findings

None.

### Non-blocking notes

- The worktree still contains unrelated tracked modifications and untracked prior-phase files outside P53 scope.
- The P53 files are untracked additions, so `git diff -- <P53 files>` and `git diff --check` do not display/check their content until staged or otherwise compared. I read the files directly and ran a separate trailing-whitespace check over the P53 files.

## Required changes

None.

## Next-phase decision

P54 may proceed. P53 is accepted with non-blocking worktree hygiene notes, no operator/scientific gate is triggered, no claim-boundary violation remains, and the contract remains protocol/audit scaffold only.
