phase: P57
phase_name: extraction audit v2 and human-sentinel protocol scaffold independent review
reviewer: codex-independent-review
date: 2026-05-12
verdict: ACCEPT_WITH_NOTES
blocked: false
requires_operator: false
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
  - `docs/experiments/P57-extraction-audit-v2-plan.md`
  - `docs/templates/extraction-audit-v2-record-template.json`
  - `docs/templates/human-sentinel-extraction-audit-protocol-template.md`
  - `docs/reviews/P57-extraction-audit-v2-review.md`
  - `tests/test_p57_extraction_audit_v2.py`

- Modified files:
  - None for P57.

- Generated artifacts:
  - None. No P57 artifact directory was found under `artifacts/experiments/`.

- Out-of-scope worktree items:
  - `AGENTS.md` remains modified from earlier work.
  - `.codex/automation-state/` remains untracked.
  - `artifacts/experiments/synthetic_regime_v12/events.jsonl` remains untracked.
  - `docs/mingx-v12-p51-p60-followup-dev-experiment-plan.md` remains untracked.
  - `docs/mingx-v12-p51-p60-review-protocol.md` remains untracked.
  - `docs/reviews/P51-P55-v12-commit-package-independent-review.md` remains untracked.
  - `docs/reviews/P55-blocked-rerun-audit-record-commit-independent-review.md` remains untracked from a prior review.
  - This independent review file is created by the present review.

## Summary

P57 adds an extraction-risk audit v2 plan, a conservative JSON record template, a future human-sentinel protocol template, a self-review note, and focused tests. It does not execute extraction audits, import data, generate artifacts, create human labels, compute kappa, or upgrade claims.

## Strata and label review

All required strata are present in the plan and record template:

- `simple_factual`
- `complex_conditional`
- `qualifier_heavy`
- `temporal_scope`
- `cross_chunk`
- `long_tail_entity`
- `high_provenance_value`
- `prerequisite`
- `contradictory`
- `adversarial_repetition_sensitive`

The plan gives each stratum a description, context-projection relevance, expected failure modes, minimum record fields, and claim ceiling.

All required labels are present:

- `captured_exact`
- `captured_core_preserved`
- `captured_core_changed`
- `missing`
- `unsupported_added`
- `duplicate_or_overmerged`
- `contradiction_lost`
- `qualifier_lost`
- `temporal_scope_error`
- `provenance_lost`
- `selector_impact_estimate`

`selector_impact_estimate` is explicitly risk-only, not selector validity and not metric support.

## Metric review

The plan and record template define extraction-specific metrics:

- `extraction_completeness_by_stratum`
- `effective_extraction_completeness`
- `value_weighted_extraction_loss`
- `critical_finding_miss_rate`
- `unsupported_finding_rate`
- `provenance_loss_rate`

These are not presented as bridge metrics. The plan explicitly says not to use `c_s` or `zeta_s` for extraction audit metrics and keeps those names reserved for bridge calibration.

## Record template review

`docs/templates/extraction-audit-v2-record-template.json` parses successfully. It includes schema/version, source document identity and hash fields, source span hash, extracted item identity and hash fields, candidate pool hash, stratum, ground-truth and extracted finding fields, label and rationale, provenance expected/observed, qualifier expected/observed, temporal scope expected/observed, contradiction and prerequisite context, value weight, criticality, selector impact estimate, data source kind, label source kind, annotator count, adjudication status, agreement statistic, `human_human_kappa_present`, `model_adjudicated`, `paper_evidence_eligible`, `measurement_validation_claim`, and `denied_claims`.

Defaults are conservative:

- `paper_evidence_eligible: false`
- `measurement_validation_claim: false`
- `human_human_kappa_present: false`
- `model_adjudicated: false`

The plan plus templates have no volatility-scan hits for timestamps, UUIDs, API keys, secrets, absolute Windows paths, `/home/`, or `/mnt/`.

## Human-sentinel protocol review

The human-sentinel protocol is operator-gated and unexecuted. It defines purpose, operator gate, annotator requirements, label instructions, adjudication procedure, agreement statistic requirements, kappa handling, contamination review, sentinel-only conditions, measurement-validation candidate gate, and explicit model-adjudication non-substitution rules.

It states that missing human labels or missing kappa must not be filled by model adjudication, model-adjudicated labels are not human labels, human sentinel evidence is not automatically measurement validation, extraction audit results do not prove selector validity, and extraction audit results do not establish metric bridge support.

## P55/P56 boundary review

P57 preserves the blocked prior-state boundaries:

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

P57 does not proceed from P55/P56 success and does not repair P55/P56 blocked states.

## Claim-boundary review

- No selector validity claim.
- No metric bridge support claim.
- No V-information support claim.
- No measurement validation claim.
- No human labels or kappa.
- No model-adjudicated-as-human-label claim.
- No fixture-only paper evidence claim.
- No evidence claim upgrade.

P57 remains extraction-risk scaffold only.

## Test review

`tests/test_p57_extraction_audit_v2.py` is narrow and deterministic. It covers JSON parsing, required record fields, required strata, required labels, selector-impact risk-only semantics, extraction metrics, `c_s` / `zeta_s` separation, human-sentinel non-substitution language, claim-boundary language, conservative defaults, denied claims, and machine-neutral template content. It does not require live APIs, human labels, operator data, or external services.

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
?? docs/mingx-v12-p51-p60-followup-dev-experiment-plan.md
?? docs/mingx-v12-p51-p60-review-protocol.md
?? docs/reviews/P51-P55-v12-commit-package-independent-review.md
?? docs/reviews/P55-blocked-rerun-audit-record-commit-independent-review.md
?? docs/reviews/P57-extraction-audit-v2-review.md
?? docs/templates/extraction-audit-v2-record-template.json
?? docs/templates/human-sentinel-extraction-audit-protocol-template.md
?? tests/test_p57_extraction_audit_v2.py
```

```bash
git diff -- docs/experiments/P57-extraction-audit-v2-plan.md docs/templates/extraction-audit-v2-record-template.json docs/templates/human-sentinel-extraction-audit-protocol-template.md docs/reviews/P57-extraction-audit-v2-review.md tests/test_p57_extraction_audit_v2.py
```

Result: exit 0; no output because the P57 files are untracked additions. I inspected the files directly and ran tests/scans over their paths.

```bash
git diff --check
```

Result: exit 0, with warning only for unrelated dirty `AGENTS.md` line-ending normalization.

```text
warning: in the working copy of 'AGENTS.md', LF will be replaced by CRLF the next time Git touches it
```

```bash
python -m json.tool docs/templates/extraction-audit-v2-record-template.json
```

Result: exit 0; JSON parsed and printed. Key checked fields include `record_schema_version`, source/extracted item identity and hash fields, `selector_impact_estimate`, `human_human_kappa_present: false`, `model_adjudicated: false`, `paper_evidence_eligible: false`, `measurement_validation_claim: false`, required strata, required labels, extraction metrics, claim boundaries, and denied claims.

```bash
uv run pytest tests/test_p57_extraction_audit_v2.py
```

Result: exit 0.

```text
7 passed in 0.06s
```

```bash
uv run pytest tests/test_revised_framing_guardrails.py
```

Result: exit 0.

```text
13 passed in 0.73s
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
568 passed, 4 skipped in 35.82s
```

```bash
rg -n "selector validity|metric bridge support|V-information support|measurement validation|human-human kappa|human label|model-adjudicated|paper-grade evidence|c_s|zeta_s" docs/experiments/P57-extraction-audit-v2-plan.md docs/templates/extraction-audit-v2-record-template.json docs/templates/human-sentinel-extraction-audit-protocol-template.md docs/reviews/P57-extraction-audit-v2-review.md tests/test_p57_extraction_audit_v2.py
```

Result: exit 0; hits are denied, gated, protocol, review, or test assertions. Representative hits:

```text
docs/experiments/P57-extraction-audit-v2-plan.md:25:- extraction audit is not selector validity
docs/experiments/P57-extraction-audit-v2-plan.md:26:- extraction audit is not metric bridge support
docs/experiments/P57-extraction-audit-v2-plan.md:27:- extraction audit is not V-information support
docs/experiments/P57-extraction-audit-v2-plan.md:28:- extraction audit is not measurement validation
docs/experiments/P57-extraction-audit-v2-plan.md:91:Do not use `c_s` or `zeta_s` for extraction audit metrics. Those names are bridge-calibration quantities and remain separate from extraction-risk reporting.
docs/templates/human-sentinel-extraction-audit-protocol-template.md:83:Missing human labels or missing kappa must not be filled by model adjudication.
docs/templates/human-sentinel-extraction-audit-protocol-template.md:85:Model-adjudicated labels are not human labels.
```

```bash
rg -n "failed_closed_no_rows|blocked_operator_required|no_imported_traces|P55|P56" docs/experiments/P57-extraction-audit-v2-plan.md docs/reviews/P57-extraction-audit-v2-review.md
```

Result: exit 0; hits preserve P55/P56 blocked state. Representative hits:

```text
docs/experiments/P57-extraction-audit-v2-plan.md:17:P57 is non-P55/P56-success-dependent. P55 remains failed_closed_no_rows / blocked_operator_required. P56 remains no_imported_traces. P57 does not proceed from P55/P56 success. P57 does not repair P55/P56 blocked states.
docs/experiments/P57-extraction-audit-v2-plan.md:126:P55 remains failed_closed_no_rows / blocked_operator_required. Rows imported/validated remain 0. P55 review ceiling remains none. P55 paper evidence remains false. P55 fit metrics remain not computed.
docs/experiments/P57-extraction-audit-v2-plan.md:128:P56 remains no_imported_traces. Traces imported/validated remain 0. P56 review ceiling remains none. P56 paper evidence remains false. P56 measurement validation remains false. P56 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.
```

```bash
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" docs/templates/extraction-audit-v2-record-template.json docs/templates/human-sentinel-extraction-audit-protocol-template.md docs/experiments/P57-extraction-audit-v2-plan.md docs/reviews/P57-extraction-audit-v2-review.md
```

Result: exit 0; the only hit is the P57 self-review's recorded scan command.

```bash
rg -n "timestamp|uuid|api_key|secret|C:\\\\|/home/|/mnt/" docs/templates/extraction-audit-v2-record-template.json docs/templates/human-sentinel-extraction-audit-protocol-template.md docs/experiments/P57-extraction-audit-v2-plan.md
```

Result: exit 1; no matches.

Additional artifact check:

```powershell
Get-ChildItem artifacts\experiments -Directory | Where-Object { $_.Name -match 'p57|extraction_audit_v2|extraction-audit-v2' } | Select-Object Name,FullName
```

Result: exit 0; no output, confirming no P57 generated artifact directory was present.

## Checks not run

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

- P57 files are untracked additions, so `git diff -- <P57 paths>` has no output until staged. This review inspected the files directly and ran tests/scans over them.
- Human-sentinel execution remains future operator-gated work and was not performed in P57.
- Unrelated dirty/untracked worktree items remain outside P57 scope.

## Required changes

None.

## Next-phase decision

Independent review is required before any phase progression.

P58/P59/P60 may not proceed from P57 success unless separately authorized.

P57 does not repair P55/P56 blocked states.
