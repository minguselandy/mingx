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

P46 has refreshed the synthetic benchmark under v12 labels at:

- `artifacts/experiments/synthetic_regime_v12/`
- `docs/experiments/synthetic-regime-v12.md`

The refreshed artifacts add four-family structural coverage and cost-aware
baseline comparisons while retaining `metric_claim_level = ambiguous_metric`
and `diagnostic_scope = synthetic_structural_only`.

P47 has added an offline fixture model-adjudicated realistic-task benchmark at:

- `artifacts/experiments/realistic_task_model_adjudicated_v12/`
- `docs/experiments/realistic-task-model-adjudicated-v12.md`

The P47 fixture lane covers three realistic-task families, writes
model-adjudicated schema artifacts, compares minimal/full/top-k/MMR/always-SAG
and v12 cost-aware policies, and keeps `paper_evidence_eligible = false`.
It does not create human labels, kappa, measurement validation, deployed
V-information verification, or calibrated bridge support.

P48 has hardened Phase B replay under v12 semantics. The replay lane now keeps
replay usability separate from metric claim level, requires complete dispatch
identity, checks candidate-pool provenance through `candidate_pool_hash`, records explicit `paper_evidence_eligible` and
`measurement_validation_claim` fields, and treats fixture-only or synthetic-only
replay as non-paper evidence. Missing, stale, or incomplete bridge witnesses
fail closed, and identity or candidate-pool hash mismatches cannot produce
headline or paper evidence.

P49 has added a deterministic fixture extraction audit pilot at:

- `artifacts/experiments/extraction_audit_pilot_v12/`
- `docs/experiments/extraction-audit-pilot-v12.md`

The P49 lane audits raw/source records into structured findings and candidate
pool `M`, including source-span traceability, provenance handles, missing
critical findings, unsupported findings, duplicate or over-merged findings, and
contradictory sources. It remains fixture-only audit substrate:
`paper_evidence_eligible = false`, `measurement_validation_claim = false`, and
no selector-regime claim is upgraded.

P50 has added an optional deterministic fixture ReprojectionWitness scaffold at:

- `artifacts/experiments/reprojection_witness_pilot_v12/`
- `docs/experiments/reprojection-witness-pilot-v12.md`

The P50 lane records why re-projection was triggered, what changed between
initial and revised context, whether budget status stayed comparable, and
whether dispatch identity and candidate-pool provenance stayed consistent. It
remains fixture-only operational audit substrate and does not upgrade P47/P48/P49
claims.

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
- [Synthetic Regime v12 Artifact Refresh](./experiments/synthetic-regime-v12.md)
- [P47 Model-Adjudicated Realistic-Task Plan](./codex/v12-phase-docs/P47-model-adjudicated-realistic-benchmark-plan.md)
- [P47 Model-Adjudicated Realistic-Task Benchmark](./experiments/realistic-task-model-adjudicated-v12.md)
- [P48 Phase B Replay v12 Hardening Plan](./codex/v12-phase-docs/P48-phase-b-replay-v12-hardening-plan.md)
- [Phase B Replay Protocol](./protocols/phase-b-replay-protocol.md)
- [P49 Extraction Audit Pilot Plan](./codex/v12-phase-docs/P49-extraction-audit-pilot-plan.md)
- [P49 Extraction Audit Pilot](./experiments/extraction-audit-pilot-v12.md)
- [P50 Optional ReprojectionWitness Plan](./codex/v12-phase-docs/P50-optional-reprojection-witness-plan.md)
- [P50 ReprojectionWitness Pilot](./experiments/reprojection-witness-pilot-v12.md)
- [Common Guardrails](./codex/v12-phase-docs/COMMON-GUARDRAILS.md)

P45 is closed for the current `bio_attribute` stratum as implemented but
non-calibrated. P46 synthetic v12 artifacts have been refreshed, P47 has added
an offline fixture realistic-task benchmark, P48 has hardened Phase B replay,
P49 has added the fixture extraction audit pilot, and P50 has added the optional
fixture ReprojectionWitness scaffold. These phase docs do not claim
`measurement_validated` evidence and do not supply bridge calibration results
by themselves.

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
