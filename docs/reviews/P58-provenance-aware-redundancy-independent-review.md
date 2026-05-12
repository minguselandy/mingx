phase: P58
phase_name: provenance-aware redundancy diagnostics scaffold independent review
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
live_api_used: false
human_labels_present: false
human_human_kappa_present: false
contamination_status: not_applicable

## Scope reviewed

- Added files:
  - `docs/experiments/P58-provenance-aware-redundancy-plan.md`
  - `docs/templates/provenance-redundancy-diagnostic-template.json`
  - `docs/reviews/P58-provenance-aware-redundancy-review.md`
  - `tests/test_p58_provenance_aware_redundancy.py`

- Modified files:
  - None for P58.

- Generated artifacts:
  - None. No P58 artifact directory was found under `artifacts/experiments/`.

- Out-of-scope worktree items:
  - `AGENTS.md` remains modified from earlier work.
  - `.codex/automation-state/` remains untracked.
  - `artifacts/experiments/synthetic_regime_v12/events.jsonl` remains untracked.
  - P57 scaffold files and review notes remain untracked from prior phase work.
  - `docs/mingx-v12-p51-p60-followup-dev-experiment-plan.md` remains untracked.
  - `docs/mingx-v12-p51-p60-review-protocol.md` remains untracked.
  - `docs/reviews/P51-P55-v12-commit-package-independent-review.md` remains untracked.
  - `docs/reviews/P55-blocked-rerun-audit-record-commit-independent-review.md` remains untracked from a prior review.
  - This independent review file is created by the present review.

## Summary

P58 adds an operational provenance-aware redundancy diagnostic scaffold with a plan, conservative JSON template, self-review note, and focused tests. It does not execute a new experiment, import data, generate artifacts, run live APIs, create human labels, compute kappa, start P59/P60, or upgrade claims.

## Category review

All required diagnostic categories are present in the plan and template:

- `duplicate_redundancy`
- `independent_corroboration`
- `adversarial_repetition`
- `source_conflict_pair`
- `prerequisite_overlap`
- `paraphrase_near_duplicate`
- `qualifier_mismatch`
- `temporal_scope_mismatch`

The plan and template include description, selector implication, escalation behavior, claim ceiling, and failure modes for each category.

Selector implications and escalation behavior are conservative:

- `duplicate_redundancy` is penalized strongly only when provenance and finding hashes confirm true duplication.
- `independent_corroboration` is preserved when source independence is high and the claim is important.
- `adversarial_repetition` triggers contradiction/provenance audit rather than a simple diversity penalty.
- `source_conflict_pair` requires audit/escalation or adjudication.
- `prerequisite_overlap` is preserve-or-escalate until the prerequisite chain is resolved.
- `paraphrase_near_duplicate` is lower priority unless provenance differs or related risk flags apply.
- `qualifier_mismatch` escalates because qualifier loss can change claim meaning.
- `temporal_scope_mismatch` escalates because time scope can change claim truth.

## Feature/template review

`docs/templates/provenance-redundancy-diagnostic-template.json` parses successfully and includes the required identity, provenance, hash, score, flag, category, implication, escalation/audit, claim ceiling, metric/selector, paper eligibility, measurement validation, and denied-claims fields.

Conservative defaults are present:

- `paper_evidence_eligible: false`
- `measurement_validation_claim: false`
- `metric_claim_level: operational_utility_only`
- `selector_regime_label: ambiguous`
- `escalation_required: true`
- `audit_required: true`

The template does not default to `greedy_supported`, `calibrated_proxy_supported`, `vinfo_proxy_supported`, or `measurement_validated`.

The P58 plan and template have no volatility-scan hits for timestamps, UUIDs, API keys, secrets, absolute Windows paths, `/home/`, or `/mnt/`.

## Policy review

The policy distinguishes independent corroboration from duplicate redundancy. Duplicate redundancy is only strongly penalized under confirmed provenance/finding duplication, while independent corroboration is preserved when source independence is high.

Adversarial repetition and source conflict require audit or escalation. Prerequisite overlap is preserve-or-escalate, not automatic penalty. Qualifier and temporal-scope mismatch also escalate because they can change claim meaning or truth.

P58 states that provenance-aware redundancy diagnostics are operational heuristics unless separately calibrated.

## P55/P56/P57 boundary review

P58 preserves prior phase boundaries:

- P55 remains `failed_closed_no_rows / blocked_operator_required`.
- P55 rows imported/validated remain `0`.
- P55 review ceiling remains `none`.
- P55 paper evidence remains `false`.
- P55 fit metrics remain not computed.
- P56 remains `no_imported_traces`.
- P56 traces imported/validated remain `0`.
- P56 review ceiling remains `none`.
- P56 paper evidence remains `false`.
- P56 measurement validation remains `false`.
- P56 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.
- P57 remains extraction-risk scaffold only.

P58 does not proceed from P55/P56 success and does not convert P57 extraction-risk scaffold into selector validity. P58 does not repair P55/P56 blocked states.

## Claim-boundary review

- No selector validity claim.
- No metric bridge support claim.
- No V-information support claim.
- No measurement validation claim.
- No `calibrated_proxy_supported` claim.
- No `vinfo_proxy_supported` claim.
- No fixture/template paper evidence claim.
- No evidence claim upgrade.

P58 remains operational diagnostic scaffold only.

## Test review

`tests/test_p58_provenance_aware_redundancy.py` is narrow and deterministic. It covers JSON parsing, required feature fields, required categories, conservative defaults, no upgraded default labels, independent-corroboration versus duplicate-redundancy separation, audit/escalation behavior for adversarial/source-conflict/qualifier/temporal cases, preserve-or-escalate behavior for prerequisite overlap, P55/P56/P57 boundary preservation, claim-boundary denials, and machine-neutral plan/template content.

The tests require no live APIs, external services, operator data, human labels, or kappa.

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
?? docs/mingx-v12-p51-p60-followup-dev-experiment-plan.md
?? docs/mingx-v12-p51-p60-review-protocol.md
?? docs/reviews/P51-P55-v12-commit-package-independent-review.md
?? docs/reviews/P55-blocked-rerun-audit-record-commit-independent-review.md
?? docs/reviews/P57-extraction-audit-v2-independent-review.md
?? docs/reviews/P57-extraction-audit-v2-review.md
?? docs/reviews/P58-provenance-aware-redundancy-review.md
?? docs/templates/extraction-audit-v2-record-template.json
?? docs/templates/human-sentinel-extraction-audit-protocol-template.md
?? docs/templates/provenance-redundancy-diagnostic-template.json
?? tests/test_p57_extraction_audit_v2.py
?? tests/test_p58_provenance_aware_redundancy.py
```

```bash
git diff -- docs/experiments/P58-provenance-aware-redundancy-plan.md docs/templates/provenance-redundancy-diagnostic-template.json docs/reviews/P58-provenance-aware-redundancy-review.md tests/test_p58_provenance_aware_redundancy.py
```

Result: exit 0; no output because the P58 files are untracked additions. I inspected the files directly and ran tests/scans over their paths.

```bash
git diff --check
```

Result: exit 0, with warning only for unrelated dirty `AGENTS.md` line-ending normalization.

```text
warning: in the working copy of 'AGENTS.md', LF will be replaced by CRLF the next time Git touches it
```

```bash
python -m json.tool docs/templates/provenance-redundancy-diagnostic-template.json
```

Result: exit 0; JSON parsed and printed. Key checked fields include `record_schema_version`, candidate pair identity fields, source/provenance/hash fields, score and flag fields, `category_definitions`, `metric_claim_level: operational_utility_only`, `selector_regime_label: ambiguous`, `paper_evidence_eligible: false`, `measurement_validation_claim: false`, claim boundaries, prior phase boundaries, and denied claims.

```bash
uv run pytest tests/test_p58_provenance_aware_redundancy.py
```

Result: exit 0.

```text
7 passed in 0.05s
```

```bash
uv run pytest tests/test_revised_framing_guardrails.py
```

Result: exit 0.

```text
13 passed in 0.61s
```

```bash
python -m compileall cps tests scripts
```

Result: exit 0; compileall completed for `cps`, `tests`, and `scripts`.

```bash
uv run pytest -q
```

Result: exit 0.

```text
575 passed, 4 skipped in 33.65s
```

```bash
rg -n "selector validity|metric bridge support|V-information support|measurement validation|paper-grade evidence|calibrated_proxy_supported|vinfo_proxy_supported|measurement_validated|greedy_supported" docs/experiments/P58-provenance-aware-redundancy-plan.md docs/templates/provenance-redundancy-diagnostic-template.json docs/reviews/P58-provenance-aware-redundancy-review.md tests/test_p58_provenance_aware_redundancy.py
```

Result: exit 0; hits are denied, gated, review, or negative-test contexts. Representative hits:

```text
docs/experiments/P58-provenance-aware-redundancy-plan.md:17:P58 does not establish selector validity.
docs/experiments/P58-provenance-aware-redundancy-plan.md:18:P58 does not establish metric bridge support.
docs/experiments/P58-provenance-aware-redundancy-plan.md:19:P58 does not establish V-information support.
docs/experiments/P58-provenance-aware-redundancy-plan.md:20:P58 does not establish measurement validation.
docs/experiments/P58-provenance-aware-redundancy-plan.md:95:The template must not default to `greedy_supported`, `calibrated_proxy_supported`, `vinfo_proxy_supported`, or `measurement_validated`.
docs/templates/provenance-redundancy-diagnostic-template.json:165:    "calibrated_proxy_supported",
docs/templates/provenance-redundancy-diagnostic-template.json:166:    "vinfo_proxy_supported",
docs/templates/provenance-redundancy-diagnostic-template.json:168:    "measurement_validated",
tests/test_p58_provenance_aware_redundancy.py:153:    assert template["selector_regime_label"] != "greedy_supported"
```

```bash
rg -n "duplicate_redundancy|independent_corroboration|adversarial_repetition|source_conflict_pair|prerequisite_overlap|paraphrase_near_duplicate|qualifier_mismatch|temporal_scope_mismatch" docs/experiments/P58-provenance-aware-redundancy-plan.md docs/templates/provenance-redundancy-diagnostic-template.json tests/test_p58_provenance_aware_redundancy.py
```

Result: exit 0; required categories are present in the plan, template, and tests. Representative hits:

```text
docs/experiments/P58-provenance-aware-redundancy-plan.md:33:| `duplicate_redundancy` | Two candidates carry the same finding from the same or effectively identical provenance, confirmed by finding and source-span hashes. | Penalize strongly only when provenance and finding hashes confirm true duplication. | No escalation is needed when identity and provenance agree; otherwise downgrade to ambiguous and audit. | operational diagnostic improvement only | false duplicate from paraphrase, lost source distinction, over-penalized independent corroboration |
docs/experiments/P58-provenance-aware-redundancy-plan.md:34:| `independent_corroboration` | Candidates support the same or compatible claim from independent sources or independently derived evidence. | Preserve when source independence is high and the claim is important. | Escalate only if source independence is uncertain, provenance is missing, or the claim is high-criticality. | operational diagnostic improvement only | mistaken source independence, source laundering, unsupported consensus |
docs/experiments/P58-provenance-aware-redundancy-plan.md:35:| `adversarial_repetition` | A claim is repeated, paraphrased, or amplified in a way that may create artificial salience or false consensus. | Do not apply a simple diversity penalty; trigger contradiction/provenance audit. | Audit required; escalate if repetition source, incentive, or contradiction context is unresolved. | operational diagnostic improvement only | adversarial restatement mistaken for corroboration, spam counted as signal, contradiction hidden by repetition |
```

```bash
rg -n "failed_closed_no_rows|blocked_operator_required|no_imported_traces|P55|P56|P57" docs/experiments/P58-provenance-aware-redundancy-plan.md docs/reviews/P58-provenance-aware-redundancy-review.md
```

Result: exit 0; hits preserve P55/P56/P57 boundary statements. Representative hits:

```text
docs/experiments/P58-provenance-aware-redundancy-plan.md:11:This phase is non-P55/P56/P57-success-dependent. P55 remains failed_closed_no_rows / blocked_operator_required. P56 remains no_imported_traces. P57 remains extraction-risk scaffold only. P58 does not proceed from P55/P56 success. P58 does not convert P57 extraction audit into selector validity. P58 does not repair P55/P56 blocked states.
docs/experiments/P58-provenance-aware-redundancy-plan.md:113:P55 remains failed_closed_no_rows / blocked_operator_required. Rows imported/validated remain 0. P55 review ceiling remains none. P55 paper evidence remains false. P55 fit metrics remain not computed.
docs/experiments/P58-provenance-aware-redundancy-plan.md:115:P56 remains no_imported_traces. Traces imported/validated remain 0. P56 review ceiling remains none. P56 paper evidence remains false. P56 measurement validation remains false. P56 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.
```

```bash
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" docs/templates/provenance-redundancy-diagnostic-template.json docs/experiments/P58-provenance-aware-redundancy-plan.md docs/reviews/P58-provenance-aware-redundancy-review.md
```

Result: exit 0; the only hit is the P58 self-review's recorded scan command.

```bash
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" docs/templates/provenance-redundancy-diagnostic-template.json docs/experiments/P58-provenance-aware-redundancy-plan.md
```

Result: exit 1; no matches.

Additional artifact check:

```powershell
Get-ChildItem artifacts\experiments -Directory | Where-Object { $_.Name -match 'p58|provenance.*redundancy|redundancy' } | Select-Object Name,FullName
```

Result: exit 0; no output, confirming no P58 generated artifact directory was present.

Additional phase-boundary scan:

```bash
rg -n "P59|P60|ReprojectionWitness replay|evidence ledger|may proceed|next_phase_allowed|start P59|start P60" docs/experiments/P58-provenance-aware-redundancy-plan.md docs/templates/provenance-redundancy-diagnostic-template.json docs/reviews/P58-provenance-aware-redundancy-review.md tests/test_p58_provenance_aware_redundancy.py
```

Result: exit 0; only `next_phase_allowed: false` and statements requiring independent review before P59/P60.

## Checks not run

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

- P58 files are untracked additions, so `git diff -- <P58 paths>` has no output until staged. This review inspected the files directly and ran tests/scans over them.
- P58 is a docs/template/test scaffold only; any future execution or calibration remains separately gated.
- Unrelated dirty/untracked worktree items remain outside P58 scope.

## Required changes

None.

## Next-phase decision

Independent review is required before any phase progression.

P59/P60 may not proceed from P58 success unless separately authorized.

P58 does not repair P55/P56 blocked states.
