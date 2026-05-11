phase: P54
phase_name: materially new bridge-calibration stratum design independent review
reviewer: codex-independent-review
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

- Added files:
  - `docs/experiments/P54-new-bridge-stratum-design-v12.md`
  - `configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json`
  - `tests/test_p54_bridge_stratum_design.py`
  - `docs/reviews/P54-new-bridge-stratum-design-review.md`

- Modified files:
  - None for P54. The actual tracked dirty files in the worktree are prior-phase or unrelated files.

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
  - pre-existing P51/P52/P53/P51-P60 planning and review documents shown by `git status --short`

## Summary

P54 added a design-only bridge-calibration stratum proposal, a dry-run config, focused tests, and an implementation review note. The selected stratum is `evidence_packet_selection_microtask_v1`. P54 did not execute P55, import or generate pilot rows, run live APIs, create bridge evidence, modify runtime/schema code, or upgrade claims.

The design itself is accepted as claim-safe. P55 execution is blocked until the operator explicitly approves the selected data source.

## Stratum design review

- Selected stratum: `evidence_packet_selection_microtask_v1`
- Exactly one stratum selected: yes.
- Materially distinct from P45: yes. P54 changes task family, target type, candidate-pool structure, utility metric, and logloss measurement path.
- Target type: `forced_choice_or_exact_field`.
- Logloss measurement path: `fixed_model_target_logloss_for_declared_answer`, with explicit target evidence and tokenization or forced-choice likelihood.
- Utility metric: `decomposable_answer_correctness_v1`.
- Candidate slice / block size: fixed top-8 candidate packet slice; block size 1 or 2.
- Model/materialization/decoding policy: fixed evaluated model tier, `fixed_order_evidence_packet_v1`, and `deterministic_logloss_scoring_no_generation`.

The design frames the task as dispatch-time worker projection over fixed evidence packets, not generic single-agent RAG. Candidate-pool hash, selected block identity, materialization policy, and dispatch identity are required for P55.

## P45 distinction review

Pass. The design states that the current P45 `bio_attribute` lane was implemented but failed to establish stable utility-to-logloss support. P45 remains non-calibrated, fail-closed, not bridge support, and not `calibrated_proxy_supported`. P54 explicitly avoids retrying or scaling the same `bio_attribute` lane by inertia.

## Dry-run config review

Pass for design review. The dry-run config is valid JSON, deterministic, and machine-neutral. It contains no timestamps, UUIDs, absolute local paths, secrets, API keys, input rows, output artifacts, or live API enablement. It includes the required phase, stratum, task, target, model, materialization, decoding, candidate-slice, block-size, utility, logloss, data-source, contamination, claim-gate, P53 contract, operator-gate, negative-control, expected-output, and claim-boundary fields.

The config is blocked from execution without independent review acceptance and operator approval for the selected data source.

## Negative controls review

Pass. The design/config include all required controls:

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

## Operator gate review

Pass as a gate, with execution blocked. Imported rows, live API use, and human-labeled rows are all disabled in the dry-run config and require explicit later operator approval. P55 is also blocked until P54 independent review accepts the design. Human labels and human-human kappa are not claimed.

Because the selected data source is `operator_imported_rows_pending_approval`, P55 execution is operator-blocked as of this review.

## Test review

Pass. `tests/test_p54_bridge_stratum_design.py` contains five narrow deterministic tests. They parse the dry-run JSON config, check required fields, verify `stratum_id` is not `bio_attribute`, enforce block size `<= 2`, check live/import/human execution gates, verify claim gates block measurement validation and P54 `calibrated_proxy_supported` / `vinfo_proxy_supported`, cover negative controls, and require P53 contract references. The tests do not introduce live API dependencies or depend on absolute paths, timestamps, UUIDs, or nondeterministic output.

## Claim-boundary review

- Metric claim ceiling: `none`
- Selector label ceiling: `none`
- Paper eligibility: `false`
- Measurement validation claim: `false`
- Denied claims remain denied.
- No claim was upgraded.
- P54 remains design review only.

P54 does not claim measurement validation, human-label validation, human-human kappa, deployed V-information verification, theorem-level deployed submodularity verification, bridge support, `calibrated_proxy_supported`, or `vinfo_proxy_supported`.

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
?? configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json
?? docs/experiments/P51-P60-v12-followup-dev-experiment-plan.md
?? docs/experiments/P54-new-bridge-stratum-design-v12.md
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
?? docs/reviews/P53-diagnostic-threshold-contract-independent-review.md
?? docs/reviews/P53-diagnostic-threshold-contract-review.md
?? docs/reviews/P54-new-bridge-stratum-design-review.md
?? docs/templates/diagnostic-threshold-contract-template.json
?? tests/test_diagnostic_threshold_contract.py
?? tests/test_p54_bridge_stratum_design.py
```

```text
git diff -- docs/experiments/P54-new-bridge-stratum-design-v12.md configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json tests/test_p54_bridge_stratum_design.py docs/reviews/P54-new-bridge-stratum-design-review.md
Result: exit 0; no output because the P54 files are untracked additions.
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
python -m json.tool configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json
Result: exit 0; JSON parsed successfully.
```

```text
uv run pytest tests/test_p54_bridge_stratum_design.py
Result: exit 0; 5 passed in 0.05s
```

```text
uv run pytest tests/test_revised_framing_guardrails.py
Result: exit 0; 13 passed in 0.74s
```

```text
python -m compileall cps tests scripts
Result: exit 0; listed cps, tests, and scripts with no compile errors.
```

```text
uv run pytest
Result: exit 0; 535 passed, 4 skipped in 32.81s
```

```text
rg -n "evidence_packet_selection_microtask_v1|bio_attribute|task_family|target_type|logloss|negative_controls|operator_gates|measurement_validated|calibrated_proxy_supported|vinfo_proxy_supported" docs/experiments/P54-new-bridge-stratum-design-v12.md configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json docs/reviews/P54-new-bridge-stratum-design-review.md tests/test_p54_bridge_stratum_design.py
Result: exit 0; expected hits only. Hits include selected stratum, P45 distinction, required config/test fields, explicit logloss path, negative controls, operator gates, and blocked/denied claim-boundary mentions.
```

```text
rg -n "live API|operator-approved|human labels|kappa|paper-grade|deployed V-information verification|theorem-level deployed submodularity verification" docs/experiments/P54-new-bridge-stratum-design-v12.md configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json docs/reviews/P54-new-bridge-stratum-design-review.md tests/test_p54_bridge_stratum_design.py
Result: exit 0; expected hits only. Hits are metadata-false, blocked, denied, or operator-gated boundary statements.
```

```text
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json
Result: exit 1; no matches.
```

```text
rg -n "P55|P56|P57|P58|P59|P60|bridge pilot execution|replay substrate expansion|extraction audit v2|provenance-aware redundancy|re-projection replay integration|evidence ledger package|P54 does not execute|P55 remains blocked|blocked until" docs/experiments/P54-new-bridge-stratum-design-v12.md configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json docs/reviews/P54-new-bridge-stratum-design-review.md tests/test_p54_bridge_stratum_design.py
Result: exit 0; expected P55 design/gate references only. No P56-P60 execution start was found.
```

```text
Select-String trailing-whitespace check over P54 files
Result: exit 0; no trailing whitespace matches in P54 files.
```

## Checks not run

None.

## Findings

### Blocking findings

None for the P54 design itself. P55 execution is operator-blocked by design until the operator approves the selected data source.

### Non-blocking notes

- The worktree still contains unrelated tracked modifications and untracked prior-phase files outside P54 scope.
- The P54 files are untracked additions, so `git diff -- <P54 files>` and `git diff --check` do not display/check their content until staged or otherwise compared. I read the files directly and ran a separate trailing-whitespace check over the P54 files.
- `git diff --check` continues to print LF-to-CRLF warnings for unrelated tracked dirty files.

## Required changes

None.

## Next-phase decision

P55 may not execute from this review alone. The P54 design is accepted as claim-safe, but P55 remains blocked until the operator explicitly approves the selected data source. Imported rows, live API use, and human-labeled rows remain blocked unless separately operator-approved in a later phase.
