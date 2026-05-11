# Current Work Summary

This document summarizes the currently completed work after the recent Phase 1
live mini-batch, contamination triage, and runtime-default updates.

## Paper Framing Update

The current paper framing is now the fixed v12 framing:

- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper-alignment-v12.md`

Use it for the research boundary: conditional V-information theory, the
formal/proxy/pipeline/runtime/metric-bridge/extraction layering, proxy-regime
diagnosis and escalation, extraction as an `M* -> M` bridge risk, and the
target auditable runtime interfaces `ProjectionPlan`, `BudgetWitness`,
`MaterializedContext`, and `MetricBridgeWitness`.

The v10 files remain preserved as legacy/archive material:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`

P45 bridge calibration is now implemented but not calibrated for the current
`bio_attribute` stratum. The lane is operator/API-ready and its fixed-logloss
positive control verified the measured-logprob path, but later canaries did not
establish a utility-to-logloss bridge. The repository does not claim
`measurement_validated` evidence, scientific validation, deployed
V-information verification, fabricated human labels, fabricated kappa,
fabricated bridge calibration, or `calibrated_proxy_supported` for the failed
stratum.

Do not use the paper to infer run completion status. Current execution status
still comes from protocol docs, run plans, `run_summary.json`, `events.jsonl`,
and exported diagnostics. The current implementation should be read as a Phase
1 runtime / measurement scaffold, not as a completed full-paper runtime.

The paper's runtime interfaces are alignment targets. Current Phase A synthetic
smoke runs materialize `ProjectionPlan`, `BudgetWitness`,
`MaterializedContext`, and `MetricBridgeWitness` artifacts and pass the
pre-registered structural gate when tests are run, but broader runtime or
deployed-interface claims still require code and artifact verification in the
relevant lane.

## Current Stable Runtime Defaults

The repository default Phase 1 live model pair is now:

- `frontier = qwen3.6-plus`
- `small = qwen3.6-flash`

These defaults are aligned across:

- `api/settings.py`
- `phase1.yaml`
- active protocol docs
- runtime/config tests

Newer `run_summary.json` exports now include a `resolved_runtime` block so the
active profile, backend ids, and role-level model ids can be read without
scanning the full event log.
Historical artifacts generated before that export change may not carry the
field until they are rerun or explicitly regenerated.

## Completed Runtime And Protocol Work

The following implementation work is already complete:

- live model probing and logprob guardrails
- bridge escalation scaffold
- real annotation package materialization
- contamination escalation bundle export
- AI-assisted contamination review packet export
- single-question question-only reprobe helper
- approved replacement -> follow-up package helper

Relevant code and scripts:

- `cps/runtime/cohort.py`
- `cps/analysis/contamination_review.py`
- `cps/analysis/reprobe.py`
- `cps/runtime/followup.py`
- `scripts/export_contamination_review_packet.py`
- `scripts/run_question_only_reprobe.py`
- `scripts/build_followup_package.py`

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
- question rewrite and replacement do not modify the primary source-question
  answer path; they prepare lineage-preserved follow-up or derived-view work
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

## Next Planning Documents

The P45-P50 phase-doc package is now the controlling Codex
development/reference package for v12 follow-up work:

- [P45-P50 v12 Phase Docs](./codex/v12-phase-docs/README.md)
- [P45 One-Stratum Bridge Calibration Plan](./codex/v12-phase-docs/P45-one-stratum-bridge-calibration-plan.md)
- [P45 Bridge Calibration Closure](./experiments/P45-bridge-calibration-closure.md)
- [P46 Synthetic v12 Artifact Refresh Plan](./codex/v12-phase-docs/P46-synthetic-v12-artifact-refresh-plan.md)
- [Common Guardrails](./codex/v12-phase-docs/COMMON-GUARDRAILS.md)

P45 is closed for the current `bio_attribute` stratum as implemented but
non-calibrated. The next active phase is P46 synthetic v12 artifact refresh.
P50 is optional and must not precede P46-P49 unless explicitly deferred. These
phase docs do not claim `measurement_validated` evidence and do not supply
bridge calibration results by themselves.

The P37-P44 planning package adds follow-up planning and review artifacts for
the next development cycle:

- [P37-P44 Development and Experiment Roadmap](./roadmaps/P37-P44-development-and-experiment-roadmap.md)
- [P37 Repo State and Claim Boundary Lock Protocol](./protocols/P37-repo-state-claim-boundary-lock-protocol.md)
- [P40 Phase B Offline Replay Implementation Plan](./experiments/P40-phase-b-offline-replay-implementation-plan.md)
- [P41 Route B Model-Adjudicated Evaluation Plan](./experiments/P41-route-b-model-adjudicated-evaluation-plan.md)

These planning documents do not change the current run status: the reduced-scope
live run remains `pilot_only`, contamination failed, and measurement validation
still awaits real labels, kappa, contamination closure, fresh bridge evidence,
and claim-gate review.
