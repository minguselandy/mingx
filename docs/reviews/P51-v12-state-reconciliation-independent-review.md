phase: P51
phase_name: v12 state reconciliation and guardrail cleanup
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

- Changed files:
  - `README.md`
  - `docs/README.md`
  - `docs/templates/claim-boundary-checklist.md`
  - `tests/test_revised_framing_guardrails.py`
  - `docs/reviews/P51-v12-state-reconciliation-review.md`

- Out-of-scope worktree items:
  - `AGENTS.md` remains modified from a prior task and was read as required context.
  - Pre-existing untracked worktree items remain present: `.codex/automation-state/`, `artifacts/experiments/synthetic_regime_v12/events.jsonl`, P51-P60 planning/protocol files, and mirror docs under `docs/mingx-v12-*`.
  - This independent review file is newly added for the review task.

## Summary

P51 updates the root README, docs README, claim-boundary checklist, focused guardrail tests, and implementation review note so the repository entrypoints no longer direct workers to retry closed P45 as the next active priority. P45-P50 are now described as completed evidence/audit scaffold phases; the current P45 `bio_attribute` stratum is recorded as non-calibrated; and P51/P52/P53 are identified as the immediate next phases. The checklist now maps synthetic-only evidence conservatively and denies fixture/synthetic/replay/extraction/reprojection overclaims.

## Claim-boundary review

- Metric claim ceiling: `none`
- Selector label ceiling: `none`
- Paper eligibility: `false`
- Measurement validation claim: `false`
- Denied claims remain denied: deployed V-information verification, theorem-level deployed submodularity verification, synthetic evidence as bridge evidence, fixture evidence as paper-grade evidence, replay usability as metric support, extraction audit as selector validity, and `ReprojectionWitness` as deployed runtime improvement.
- P45 `bio_attribute` remains non-calibrated, with no `calibrated_proxy_supported`, `vinfo_proxy_supported`, or `measurement_validated` claim.

## P51 checklist result

- PASS: root README state. `README.md` no longer says P45 is the next active priority, records P45-P50 as completed scaffold phases, records current P45 `bio_attribute` as non-calibrated, identifies P51/P52/P53 as immediate next work, and links the P51-P60 plan/protocol.
- PASS: docs README state. `docs/README.md` no longer says P45 is the next active priority, treats P45-P50 as completed scaffold/reference phases, links `docs/reviews/P45-P50-v12-phase-summary.md`, and points to the P51-P60 plan/protocol.
- PASS: claim-boundary checklist. The unsafe table mapping was replaced with `synthetic_structural_only` / `ambiguous_metric`, fixture-only evidence is explicitly barred from `vinfo_proxy_supported` and `calibrated_proxy_supported`, and the requested boundary distinctions are present.
- PASS: guardrail tests. Two narrow checks were added: one for the unsafe synthetic-only table row and one for active deprecated labels outside denied/legacy/archive contexts. They introduce no live API dependency and no nondeterministic local path, timestamp, or UUID dependency.
- PASS: P51 implementation review file. `docs/reviews/P51-v12-state-reconciliation-review.md` exists, includes protocol-compatible metadata, records scope, checks, skipped checks, limitations/notes, and states P51 changed documentation/guardrails only with no evidence claim upgrade.
- PASS: no claim upgrade. P51 does not upgrade empirical, metric, selector, or paper-evidence claims.
- PASS: no out-of-scope phase start. No runtime source file or generated experiment artifact was modified by the P51 tracked diff; P52-P60 appear only as planning/review references.

## Checks run

```text
git status --short
Result: exit 0.
 M AGENTS.md
 M README.md
 M docs/README.md
 M docs/templates/claim-boundary-checklist.md
 M tests/test_revised_framing_guardrails.py
?? .codex/automation-state/
?? artifacts/experiments/synthetic_regime_v12/events.jsonl
?? docs/experiments/P51-P60-v12-followup-dev-experiment-plan.md
?? docs/mingx-v12-p51-p60-followup-dev-experiment-plan.md
?? docs/mingx-v12-p51-p60-review-protocol.md
?? docs/reviews/P51-P60-v12-review-claim-gate-protocol.md
?? docs/reviews/P51-v12-state-reconciliation-review.md

git diff -- README.md docs/README.md docs/templates/claim-boundary-checklist.md tests/test_revised_framing_guardrails.py docs/reviews/P51-v12-state-reconciliation-review.md
Result: exit 0. Non-empty tracked diff only for README.md, docs/README.md, docs/templates/claim-boundary-checklist.md, and tests/test_revised_framing_guardrails.py. The untracked P51 implementation review file was inspected separately because plain git diff does not show untracked file contents. Output ended with LF-to-CRLF warnings for the four tracked P51 files.

git diff --check
Result: exit 0. Output contained only LF-to-CRLF warnings for AGENTS.md, README.md, docs/README.md, docs/templates/claim-boundary-checklist.md, and tests/test_revised_framing_guardrails.py.

uv run pytest tests/test_revised_framing_guardrails.py
Result: exit 0. 11 passed in 0.61s.

uv run pytest tests/test_projection_artifacts.py tests/test_synthetic_regime_benchmark.py
Result: exit 0. 24 passed in 7.52s.

python -m compileall cps tests scripts
Result: exit 0. Listed cps, tests, tests\\.tmp subdirectories, and scripts with no compile errors.

uv run pytest
Result: exit 0. 521 passed, 4 skipped in 32.11s.

rg -n -F "synthetic-only evidence | vinfo_proxy_supported" README.md docs tests
Result: exit 0. 4 matches, all in instructional P51-P60 plan text telling implementers to replace or guard against that unsafe row; no active checklist/table mapping remains. A focused exclusion check over non-instructional files returned NO_ACTIVE_MAPPING_MATCH_EXCLUDING_INSTRUCTIONAL_PLAN_EXAMPLES.

rg -n -F "P45 is the next priority" README.md docs
Result: exit 0. 7 matches. Six are P51-P60 plan/protocol checklist or replacement instructions. One match remains in docs/codex/README.md, outside the declared P51 changed-file scope and outside root README/docs README.

rg -n "measurement_validated" README.md docs tests
Result: exit 0. 745 matches. Interpreted matches are denied-claim text, legacy/archive references, claim-gate fields, or tests asserting measurement validation is denied; no P51 target file uses it as an active claim.

rg -n "Vinfo_proxy_certified|greedy_valid" README.md docs tests
Result: exit 0. 58 matches. Interpreted matches are denied, legacy, compatibility, review-protocol, archive, or negative-test contexts; no P51 target file uses either as an active label.

rg -n "P52|P53|P54|P55|P56|P57|P58|P59|P60" cps scripts artifacts configs tests
Result: exit 0. Matches only in tests/test_revised_framing_guardrails.py path constants for the P51-P60 plan/protocol docs. No runtime implementation of P52-P60 was found.
```

## Checks not run

None.

## Findings

### Blocking findings

None.

### Non-blocking notes

- `docs/codex/README.md` still says "P45 is the next priority"; this is stale guidance outside the declared P51 target files. It is not a root README or docs README violation, but it should be cleaned up in a later documentation hygiene pass.
- `git diff --check` still emits LF-to-CRLF warnings for dirty files. These are line-ending hygiene warnings, not whitespace errors.
- The broad literal search finds the unsafe synthetic-only mapping only in P51-P60 instructional text that says to remove or test against that mapping.

## Required changes

None.

## Next-phase decision

P52 may proceed. The P51 verdict is `ACCEPT_WITH_NOTES`, no operator/scientific gate is triggered, no claim-boundary violation remains in the P51 target files, and P51 did not start P52 or any later implementation phase.
