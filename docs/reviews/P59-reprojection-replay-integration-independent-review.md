phase: P59
phase_name: ReprojectionWitness replay integration scaffold independent review
reviewer: codex-independent-review
date: 2026-05-12
verdict: ACCEPT_WITH_NOTES
blocked: false
requires_operator: false
next_phase_allowed: false
metric_claim_level_max: operational_utility_only
selector_regime_label_max: ambiguous
paper_evidence_eligible: false
measurement_validation_claim: false
deployed_runtime_improvement_claim: false
live_api_used: false
human_labels_present: false
human_human_kappa_present: false
contamination_status: not_applicable

## Scope reviewed

- Added files:
  - `docs/experiments/P59-reprojection-replay-integration-plan.md`
  - `docs/templates/reprojection-witness-replay-template.json`
  - `docs/reviews/P59-reprojection-replay-integration-review.md`
  - `tests/test_p59_reprojection_replay_integration.py`

- Modified files:
  - None for P59.

- Generated artifacts:
  - None. No P59 experiment artifact directory was present under `artifacts/experiments`.

- Out-of-scope worktree items:
  - `AGENTS.md`
  - `.codex/automation-state/`
  - `artifacts/experiments/synthetic_regime_v12/events.jsonl`
  - `docs/experiments/P57-extraction-audit-v2-plan.md`
  - `docs/experiments/P58-provenance-aware-redundancy-plan.md`
  - `docs/mingx-v12-p51-p60-followup-dev-experiment-plan.md`
  - `docs/mingx-v12-p51-p60-review-protocol.md`
  - `docs/reviews/P51-P55-v12-commit-package-independent-review.md`
  - `docs/reviews/P55-blocked-rerun-audit-record-commit-independent-review.md`
  - `docs/reviews/P57-extraction-audit-v2-independent-review.md`
  - `docs/reviews/P57-extraction-audit-v2-review.md`
  - `docs/reviews/P58-provenance-aware-redundancy-independent-review.md`
  - `docs/reviews/P58-provenance-aware-redundancy-review.md`
  - `docs/templates/extraction-audit-v2-record-template.json`
  - `docs/templates/human-sentinel-extraction-audit-protocol-template.md`
  - `docs/templates/provenance-redundancy-diagnostic-template.json`
  - `tests/test_p57_extraction_audit_v2.py`
  - `tests/test_p58_provenance_aware_redundancy.py`

## Summary

P59 adds a ReprojectionWitness replay-integration audit scaffold, including a protocol plan, JSON record template, self-review, and deterministic tests. It does not execute replay interventions, import data, change runtime code, create generated artifacts, or upgrade any evidence claim.

## Witness field review

The plan and JSON template include the required witness identity, source replay record, trigger/rationale, budget before/after, selector before/after, candidate-pool hashes, materialized-context hashes, selected/excluded context before/after, context diff, output hashes, evaluator policy, uncertainty label, bridge status, claim gate, paper/measurement/deployed-improvement booleans, and denied-claims fields.

## Trigger and decision-rule review

The required trigger types are present: `unknown_due_to_missing_context`, `hallucination_risk`, `wrong_despite_context`, `ambiguous`, `operator_review_requested`, `budget_overflow`, and `candidate_pool_mismatch`.

The fail-closed decision rules are conservative:

- identity mismatch is `not_comparable`, paper-ineligible, and cannot upgrade metric claims;
- candidate-pool mismatch without documented expansion is `fail_closed_candidate_pool_mismatch`;
- over-budget revised context is an operational violation;
- missing, stale, mismatched, underpowered, ambiguous, or failed bridge status remains `ambiguous_metric` or `operational_utility_only` and denies `calibrated_proxy_supported` / `vinfo_proxy_supported`;
- fixture-only before/after improvement remains operational audit only, not deployed runtime improvement, not paper evidence, and not measurement validation.

## Template-default review

`docs/templates/reprojection-witness-replay-template.json` parses successfully. Defaults are conservative: `paper_evidence_eligible: false`, `measurement_validation_claim: false`, `deployed_runtime_improvement_claim: false`, `metric_bridge_status: missing`, and `claim_gate_result: audit_only_or_not_comparable`. The template does not default to `calibrated_proxy_supported`, `vinfo_proxy_supported`, `measurement_validated`, or `deployed_runtime_improvement`.

The P59 plan/template volatility scan found no timestamps, UUIDs, API keys, secrets, absolute local paths, or machine-specific paths. The broader scan only matched the P59 self-review's recorded scan command.

## P55/P56/P57/P58 boundary review

P59 preserves prior phase boundaries. It states that P55 remains `failed_closed_no_rows` / `blocked_operator_required`, P56 remains `no_imported_traces`, P57 remains extraction-risk scaffold only, and P58 remains operational diagnostic scaffold only. P59 does not proceed from P55/P56 success, does not convert P57/P58 scaffolds into evidence claims, and does not repair P55/P56 blocked states.

## Claim-boundary review

Confirmed:

- no deployed runtime improvement claim;
- no selector validity claim;
- no metric bridge support claim;
- no V-information support claim;
- no measurement validation claim;
- no `calibrated_proxy_supported` claim;
- no `vinfo_proxy_supported` claim;
- no fixture/template paper evidence;
- no evidence claim upgrade.

## Test review

`tests/test_p59_reprojection_replay_integration.py` is narrow and deterministic. It covers JSON parsing, required witness fields, trigger types, conservative defaults, identity mismatch, candidate-pool mismatch, over-budget revised context, missing/stale bridge denial of upgraded claims, fixture improvement as operational audit only, claim-boundary denials, prior-phase boundary preservation, and volatility-free templates. It does not require live APIs, external services, operator data, human labels, or kappa.

## Checks run

```bash
git status --short
```

Result: exit 0.

```text
 M AGENTS.md
?? .codex/automation-state/
?? artifacts/experiments/synthetic_regime_v12/events.jsonl
?? docs/experiments/P57-extraction-audit-v2-plan.md
?? docs/experiments/P58-provenance-aware-redundancy-plan.md
?? docs/experiments/P59-reprojection-replay-integration-plan.md
?? docs/mingx-v12-p51-p60-followup-dev-experiment-plan.md
?? docs/mingx-v12-p51-p60-review-protocol.md
?? docs/reviews/P51-P55-v12-commit-package-independent-review.md
?? docs/reviews/P55-blocked-rerun-audit-record-commit-independent-review.md
?? docs/reviews/P57-extraction-audit-v2-independent-review.md
?? docs/reviews/P57-extraction-audit-v2-review.md
?? docs/reviews/P58-provenance-aware-redundancy-independent-review.md
?? docs/reviews/P58-provenance-aware-redundancy-review.md
?? docs/reviews/P59-reprojection-replay-integration-review.md
?? docs/templates/extraction-audit-v2-record-template.json
?? docs/templates/human-sentinel-extraction-audit-protocol-template.md
?? docs/templates/provenance-redundancy-diagnostic-template.json
?? docs/templates/reprojection-witness-replay-template.json
?? tests/test_p57_extraction_audit_v2.py
?? tests/test_p58_provenance_aware_redundancy.py
?? tests/test_p59_reprojection_replay_integration.py
```

```bash
git diff -- docs/experiments/P59-reprojection-replay-integration-plan.md docs/templates/reprojection-witness-replay-template.json docs/reviews/P59-reprojection-replay-integration-review.md tests/test_p59_reprojection_replay_integration.py
```

Result: exit 0, no output because the P59 files are untracked additions in this worktree.

```bash
git diff --check
```

Result: exit 0, warning only:

```text
warning: in the working copy of 'AGENTS.md', LF will be replaced by CRLF the next time Git touches it
```

```bash
python -m json.tool docs/templates/reprojection-witness-replay-template.json
```

Result: exit 0.

```bash
uv run pytest tests/test_p59_reprojection_replay_integration.py
```

Result: exit 0.

```text
8 passed in 0.05s
```

```bash
uv run pytest tests/test_revised_framing_guardrails.py
```

Result: exit 0.

```text
13 passed in 0.58s
```

```bash
python -m compileall cps tests scripts
```

Result: exit 0.

```bash
uv run pytest -q
```

Result: exit 0.

```text
583 passed, 4 skipped in 32.87s
```

```bash
rg -n "deployed runtime improvement|selector validity|metric bridge support|V-information support|measurement validation|paper-grade evidence|calibrated_proxy_supported|vinfo_proxy_supported|measurement_validated" docs/experiments/P59-reprojection-replay-integration-plan.md docs/templates/reprojection-witness-replay-template.json docs/reviews/P59-reprojection-replay-integration-review.md tests/test_p59_reprojection_replay_integration.py
```

Result: exit 0. Hits were denied-claim, gated, template-denied, self-review command, or test-only mentions.

```bash
rg -n "unknown_due_to_missing_context|hallucination_risk|wrong_despite_context|ambiguous|operator_review_requested|budget_overflow|candidate_pool_mismatch" docs/experiments/P59-reprojection-replay-integration-plan.md docs/templates/reprojection-witness-replay-template.json tests/test_p59_reprojection_replay_integration.py
```

Result: exit 0. Required trigger and conservative classification terms were present.

```bash
rg -n "failed_closed_no_rows|blocked_operator_required|no_imported_traces|P55|P56|P57|P58" docs/experiments/P59-reprojection-replay-integration-plan.md docs/reviews/P59-reprojection-replay-integration-review.md
```

Result: exit 0. Hits preserved P55/P56/P57/P58 boundary statements only.

```bash
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" docs/templates/reprojection-witness-replay-template.json docs/experiments/P59-reprojection-replay-integration-plan.md docs/reviews/P59-reprojection-replay-integration-review.md
```

Result: exit 0. The only hit was the P59 self-review's recorded scan command.

```bash
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" docs/templates/reprojection-witness-replay-template.json docs/experiments/P59-reprojection-replay-integration-plan.md
```

Result: exit 1, no matches. The P59 template and plan are volatility-clean.

```bash
Get-ChildItem artifacts\experiments -Directory | Where-Object { $_.Name -match 'p59|reprojection.*replay|reprojection-replay' } | Select-Object Name,FullName
```

Result: exit 0, no output. No generated P59 artifact directory was present.

## Checks not run

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

- The P59 scaffold files are untracked additions in the current worktree, so `git diff -- <P59 paths>` produced no patch output. The files were inspected directly from the worktree.
- Unrelated dirty/untracked items remain outside P59 scope, including `AGENTS.md`, `.codex/automation-state/`, prior P57/P58 scaffold files, and other review/navigation files listed under scope.

## Required changes

None.

## Next-phase decision

Independent review is required before any phase progression. P60 may not proceed from P59 success unless separately authorized. P59 does not repair P55/P56 blocked states.
