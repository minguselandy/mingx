# P45-P50 v12 Phase Summary

## Executive Summary

The P45-P50 package adds a v12-aligned Proxy-Regime Diagnosis evidence/audit scaffold across bridge calibration, synthetic diagnostics, realistic-task fixtures, Phase B replay hardening, extraction audit, and optional re-projection witness recording.

This package is claim-gated engineering and audit infrastructure. It does not introduce a new empirical claim tier, does not establish measurement validation, and does not promote fixture or synthetic artifacts to paper evidence. The current P45 `bio_attribute` stratum remains non-calibrated: no calibrated proxy support and no V-information proxy support are claimed.

## Changed Areas

- Bridge calibration: P45 bridge lane is implemented, operator/API scaffolds are available, live canaries were preserved, and closure records the current stratum as not calibrated.
- Synthetic structural diagnostics: P46 refreshes deterministic v12 synthetic artifacts with v12 selector labels and cost-aware comparison outputs.
- Realistic-task fixture benchmark: P47 adds fixture-only model-adjudicated realistic-task artifacts and isolates `full_context` as a non-budget-comparable reference baseline.
- Phase B replay hardening: P48 separates replay usability from metric claims and paper eligibility, binds replay identity by full dispatch identity, and fails closed on candidate-pool hash mismatch.
- Extraction audit: P49 adds a fixture-only audit lane for the M* → M boundary, including source spans, provenance references, support status, defects, and deterministic candidate-pool hashes.
- ReprojectionWitness scaffold: P50 adds a fixture-only optional witness for dynamic re-projection decisions, including triggers, actions, context diffs, budget status, dispatch identity, and candidate-pool provenance.
- Documentation and roadmap updates: active v12 docs, summaries, and roadmaps now describe P45-P50 as evidence/audit scaffolding with conservative claim gates.
- Tests and guardrails: focused tests cover deterministic artifacts, claim boundaries, replay identity, candidate-pool provenance, budget comparability, extraction defects, and re-projection witness behavior.

## Phase-by-Phase Summary

### P45

Purpose: implement and close the one-stratum bridge calibration lane.

Changed files and artifacts: bridge calibration/data-generation code, configs, runbooks, closure docs, live canary artifacts, positive-control artifacts, and bridge failure reports.

Evidence scope: operator/API-ready bridge lane plus diagnostic live-smoke artifacts.

Claim ceiling: operational or ambiguous diagnostics only for the current `bio_attribute` stratum.

Review verdict: completed and closed.

Remaining notes: the fixed-logloss positive control passed, but P45d/P45e did not establish utility-to-logloss calibration. This stratum should not be expanded to 20-30 rows without a new scientific rationale.

### P46

Purpose: refresh synthetic benchmark artifacts under v12 labels and add cost-aware comparison outputs.

Changed files and artifacts: synthetic benchmark/regime/diagnostic code, tests, `artifacts/experiments/synthetic_regime_v12/`, and `docs/experiments/synthetic-regime-v12.md`.

Evidence scope: `synthetic_structural_only`.

Claim ceiling: `ambiguous_metric`.

Review verdict: accepted with metric naming cleanup.

Remaining notes: synthetic structural signatures are useful diagnostics, but they are not bridge evidence or paper-grade validation.

### P47

Purpose: add a deterministic fixture realistic-task benchmark for model-adjudicated labels.

Changed files and artifacts: `cps/experiments/realistic_tasks.py`, tests, run config, `artifacts/experiments/realistic_task_model_adjudicated_v12/`, and experiment docs.

Evidence scope: fixture-only realistic-task engineering scaffold.

Claim ceiling: `operational_utility_only`.

Review verdict: accepted after budget-comparability fix.

Remaining notes: `full_context` is retained as an always-large-context reference baseline and excluded from budget-fair aggregate conclusions.

### P48

Purpose: harden Phase B replay artifacts and replay classification under v12 claim boundaries.

Changed files and artifacts: `cps/experiments/phase_b_replay.py`, Phase B replay tests, and Phase B replay protocol docs.

Evidence scope: replay auditability and deterministic classification hardening.

Claim ceiling: replay usability only unless a valid external bridge exists.

Review verdict: accepted with notes.

Remaining notes: a future stricter guard may downgrade metric level when CandidatePool or ProjectionPlan substrate is absent, even if a bridge witness exists.

### P49

Purpose: implement a fixture-only extraction audit pilot for the M* → M boundary.

Changed files and artifacts: `cps/experiments/extraction_audit.py`, focused tests, run config, `artifacts/experiments/extraction_audit_pilot_v12/`, and experiment docs.

Evidence scope: `fixture_extraction_audit_only`.

Claim ceiling: `operational_utility_only`.

Review verdict: accepted with notes.

Remaining notes: the actual claim-gate filename is `extraction_claim_gate_report.json`. Future cleanup may rename `c_effective` / `c_s` to avoid visual collision with metric-bridge notation.

### P50

Purpose: add an optional fixture-only `ReprojectionWitness` scaffold for recording dynamic re-projection decisions.

Changed files and artifacts: `cps/experiments/reprojection_witness.py`, focused tests, run config, `artifacts/experiments/reprojection_witness_pilot_v12/`, and experiment docs.

Evidence scope: `fixture_reprojection_witness_only`.

Claim ceiling: `operational_utility_only` for ordinary audit rows and `ambiguous_metric` for fail-closed rows.

Review verdict: accepted with notes.

Remaining notes: the clean no-reprojection fixture uses `operator_requested` plus `abstain_no_safe_reprojection`; this is claim-safe but semantically closer to a no-op witness than a true re-projection trigger.

## Evidence Posture

- P45: bridge lane implemented, but the current stratum did not calibrate.
- P46: synthetic structural only.
- P47: fixture realistic-task benchmark only.
- P48: replay hardening and auditability only.
- P49: extraction audit pilot only.
- P50: optional re-projection audit witness only.

This package does not claim `measurement_validated`, human-label validation, human-human kappa, deployed V-information verification, calibrated proxy support, V-information proxy support, paper-grade model-adjudicated evidence, or deployed runtime improvement.

## Claim Boundary Table

| Phase | Artifact / Lane | Evidence Scope | Allowed Claim | Forbidden Claim | Review Status |
| --- | --- | --- | --- | --- | --- |
| P45 | Bridge calibration lane | operator/API-ready diagnostics for current non-calibrated stratum | `operational_utility_only` or `ambiguous_metric` | `calibrated_proxy_supported`, `vinfo_proxy_supported`, `measurement_validated` | completed and closed |
| P46 | Synthetic structural diagnostics | `synthetic_structural_only` | `ambiguous_metric` | bridge evidence, measurement validation, paper-grade evidence | accepted |
| P47 | Realistic-task fixture benchmark | fixture-only model-adjudicated scaffold | `operational_utility_only` | paper-grade model-adjudicated evidence, calibrated proxy support | accepted |
| P48 | Phase B replay hardening | replay auditability and deterministic classification | replay usability with conservative metric claims | replay usability as metric support, fixture replay as paper evidence | accepted with notes |
| P49 | Extraction audit pilot | `fixture_extraction_audit_only` | extraction audit defects and provenance diagnostics | selector-regime validation, bridge validation, measurement validation | accepted with notes |
| P50 | ReprojectionWitness scaffold | `fixture_reprojection_witness_only` | optional audit witness records | runtime improvement, selector correctness, V-information support | accepted with notes |

## Validation Summary

- Full test suite: `519 passed, 4 skipped`.
- Focused P50 test: `8 passed`.
- P49 test: `6 passed`.
- P48 test: `25 passed`.
- P47 test: `6 passed`.
- Framing guardrails: `9 passed`.
- `python -m compileall cps scripts`: passed.
- `git diff --check`: passed with LF/CRLF warnings only.

The line-ending warnings are non-blocking repository hygiene warnings, not whitespace errors.

## Remaining Non-Blocking Notes

- P48: future stricter guard may downgrade metric level when CandidatePool or ProjectionPlan substrate is absent.
- P49: future naming cleanup may rename `c_effective` / `c_s`.
- P50: no-op witness wording can be clarified later.
- The worktree may contain prior P46/P47/P48/P49/P50 changes and untracked artifacts until this package is committed.
- No live API was run for P46-P50.
- No secrets were touched.
- No staging, commit, or push is implied by this summary document alone.

## Recommended Next Action

Stop feature work after P50, prepare the PR/sync package, review diff boundaries, and commit P45-P50 as a v12 evidence/audit scaffold package. Do not start new experimental claims until this package is cleanly summarized and synced.

## PR Summary Draft

### Summary

Adds the P45-P50 v12 evidence/audit scaffold package for Proxy-Regime Diagnosis alignment.

### What Changed

- Closed P45 for the current non-calibrated bridge stratum.
- Refreshed P46 synthetic structural artifacts with v12 labels and cost-aware outputs.
- Added P47 fixture realistic-task benchmark artifacts and budget-comparability fields.
- Hardened P48 Phase B replay identity, provenance, determinism, and claim gates.
- Added P49 fixture extraction audit for the M* → M boundary.
- Added P50 fixture ReprojectionWitness scaffold.

### Claim Boundaries

No measurement validation, human-label validation, human-human kappa, deployed V-information verification, calibrated proxy support, V-information proxy support from fixture/synthetic artifacts, fixture/synthetic paper evidence, or deployed runtime improvement is claimed.

### Validation

Latest known validation passed: compileall, focused P47-P50 tests, framing guardrails, `git diff --check`, and full `uv run pytest -q` with `519 passed, 4 skipped`.

### Review Status

P45-P50 have completed review. P48/P49/P50 carry only non-blocking notes documented above.

### Follow-Up Notes

Future work can tighten absent-substrate replay guards, rename P49 `c_effective` / `c_s`, and clarify P50 no-op witness wording. These are cleanup items, not claim upgrades.
