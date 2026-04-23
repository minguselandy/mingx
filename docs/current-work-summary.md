# Current Work Summary

This document summarizes the currently completed work after the recent Phase 1
live mini-batch, contamination triage, and runtime-default updates.

## Current Stable Runtime Defaults

The repository default Phase 1 live model pair is now:

- `frontier = qwen3.6-plus`
- `small = qwen3.6-flash`

These defaults are aligned across:

- `api/settings.py`
- `phase1.yaml`
- active protocol docs
- runtime/config tests

`run_summary.json` export logic also now includes a `resolved_runtime` block so
the active profile, backend ids, and role-level model ids can be read without
scanning the full event log.

## Completed Runtime And Protocol Work

The following implementation work is already complete:

- live model probing and logprob guardrails
- bridge escalation scaffold
- real annotation package materialization
- contamination escalation bundle export
- AI-assisted contamination review packet export
- single-question question-only reprobe helper

Relevant code and scripts:

- `cps/runtime/cohort.py`
- `cps/analysis/contamination_review.py`
- `cps/analysis/reprobe.py`
- `scripts/export_contamination_review_packet.py`
- `scripts/run_question_only_reprobe.py`

## Live Mini-Batch Status

The reduced-scope live run at:

- `artifacts/phase1/live_mini_batch/`

completed as an engineering run, but not as a scientific pass.

Stable conclusions:

- runtime plumbing completed
- bridge diagnostics computed
- annotation package materialized
- contamination gate failed
- run remains `pilot_only`

This run must not be described as `measurement_validated`.

## Contamination Triage Outcome

The contamination review and operator artifacts now exist under:

- `artifacts/phase1/live_mini_batch/exports/contamination_review_packet.*`
- `artifacts/phase1/live_mini_batch/exports/contamination_triage_memo.md`
- `artifacts/phase1/live_mini_batch/exports/contamination_operator_decision_sheet.md`

The current triage result is now conservative and final for this batch:

- `2hop__86458_20273 -> drop_and_replace`
- `3hop1__222979_40769_64047 -> drop_and_replace`
- `4hop1__76111_624859_355213_203322 -> drop_and_replace`

The reason all three now land on `drop_and_replace` is that the only retained
rewrite candidate was reprobed live and still failed the contamination
threshold.

Live reprobe artifact:

- `artifacts/phase1/live_mini_batch/exports/rewrite_reprobe_result_3hop1__222979_40769_64047.json`

## Replacement Preparation

Because the final operator path for this batch is now `replace_only`, the next
same-hop replacements were prepared using the repository's existing
`same_hop_next_rank_on_resume_v1` selection policy.

Artifacts:

- `artifacts/phase1/live_mini_batch/replacement_manifest.json`
- `artifacts/phase1/live_mini_batch/exports/replacement_plan.md`

Selected replacements:

- `2hop__132929_684936`
- `3hop1__409517_547811_80702`
- `4hop3__373866_5189_38229_86687`

These are selection candidates only. They are not scientific approvals and do
not change the status of the already completed failed run.

## Current Project Interpretation

The current best framing is:

- main line: answer-serving / fixed-question execution
- sidecar line: compression, memory formation, contamination triage, rewrite,
  replacement, and other derived views

This means:

- source questions should be treated as immutable for primary serving
- derived rewrites/replacements may still exist, but as sidecar artifacts
- contamination has different semantics by lane:
  - scientific stop for measurement interpretation
  - interpretation limit for serving
  - representation signal for memory/compression sidecars

## Recommended Immediate Next Step

Do not rerun the failed reduced-scope batch directly.

If continuing the current lane, the most reasonable next action is:

1. treat the current run as finalized at `stop_and_escalate`
2. preserve its triage and replacement artifacts
3. decide whether future work should prioritize:
   - framework improvements for fixed-question answering, or
   - sidecar logic for compression/memory formation, or
   - a fresh reduced-scope follow-up batch using the prepared replacements
