# SUB Stage Global Constraints

This package is for the **SUB / paper synthesis phase** after the completed POST-LAPI candidate operational evidence package.

## Current baseline

- Branch: `codex/integrated-validation-workbench`
- Latest pushed commit: `ce1f7fa307bcacf794befc49eb34beb8f4e4c1e8`
- Recent commit: `POST-LAPI add pilot audit outputs`
- Remote branch aligned: yes
- Index: clean
- Unrelated untracked leftovers: present, must remain isolated
- Current claim: `operational_utility_only/no_claim_upgrade`
- Route 5: `locked`
- Route 8: `locked`
- Raw API responses stored: `false`

## Completed evidence package

- EPF / PAPER-RS / LAPI completed and merged.
- POST-LAPI goal pack installed and committed.
- POST-0 through POST-8-CONFIG completed.
- POST-3 through POST-7 pilots completed.
- Latest evidence commit: `ce1f7fa307bcacf794befc49eb34beb8f4e4c1e8`.

## Evidence summary

### POST-3 Judge stability

- Live API calls: 240
- Examples: 30
- Normalized rows: 240
- Duplicate agreement: 0.9833
- Order-swap agreement: 0.9833
- Rubric paraphrase agreement: 0.9667
- Gate: `weak_evidence_candidate_ready`

### POST-4 Sufficiency / abstention

- Final artifact run calls: 50
- Total turn calls: 100
- Gate: `sufficiency_abstention_candidate_ready`
- Diagnostic label: `sufficiency_abstention_diagnostic_only`

### POST-5 Reprojection witness

- Live API calls: 26
- Gate: `reprojection_witness_candidate_ready`
- Repair candidate rate: 0.576923
- Label change rate: 0.576923
- Unsupported-to-supported rate: 0.576923
- Parse failed rate: 0.0

### POST-6 Operational replay expansion

- Live API calls: 0
- Normalized replay records: 2,000
- HotpotQA candidate pools: 200
- Budgets: 512, 1024
- Oracle: `non_deployable_upper_bound`

### POST-7 Extraction quality audit

- Live API calls: 100
- Normalized extraction audit records: 100
- Records per stratum: 10
- Final gate: `post7_extraction_quality_audit_completed`
- Value-weighted loss proxy: 0.197403

## Validation summary

- Focused POST-3 to POST-7 tests + guardrails: 59 passed
- JSON validation: 27 JSON files
- JSONL validation: 5 JSONL files / 2,416 JSONL rows
- Secret scan: passed
- Raw-response-storage scan: passed
- Forbidden-path scan: passed
- Compileall: passed

## Hard constraints for every SUB goal

Do not:

- Run live API calls.
- Start new experiments.
- Scale silver labels.
- Unlock Route 5 or Route 8.
- Compute or claim teacher-forced NLL.
- Claim fixed-target continuation scoring.
- Claim metric bridge support.
- Claim `calibrated_proxy_supported`.
- Claim `vinfo_proxy_supported`.
- Claim measurement validation.
- Claim human/external gold validation.
- Claim paper-grade evidence.
- Claim selector superiority or global selector superiority.
- Store raw API responses.
- Use `git add -A`.
- Stage unrelated untracked leftovers.
- Delete unrelated historical leftovers.

## Allowed claim classes

- `operational replay evidence`
- `candidate operational evidence`
- `model-adjudicated weak evidence`
- `sufficiency / abstention diagnostic`
- `replayable artifact evidence`
- `fail-closed bridge audit`
- `scoped operational improvement under matched budgets`
- `model-adjudicated extraction-risk evidence`
- `operational reprojection witness`

## Denied claim classes

- `fixed-target NLL support`
- `teacher-forced scoring support`
- `fixed-target continuation scoring support`
- `metric bridge support`
- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- `measurement validation`
- `human/external gold validation`
- `paper-grade evidence`
- `selector superiority`
- `global selector superiority`
- `Route 5 unlock`
- `Route 8 unlock`

## Default report format for Codex

Every SUB goal must end with:

```text
Goal ID:
Changed files:
Files staged:
Checks run:
Results:
Live API calls run during this goal: 0
New experiments started: no
Raw API responses stored: no
Claim level: operational_utility_only/no_claim_upgrade
Claim upgrade introduced: no
Route 5 locked: yes
Route 8 locked: yes
Unrelated leftovers staged: no
Commit recommended: yes/no
Next recommended goal:
```
