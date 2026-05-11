# P37-P44 Development and Experiment Roadmap

**Project:** Context Projection Selection / Measurement and Runtime-Audit Scaffold  
**Repository:** `minguselandy/mingx`  
**Primary package:** `cps/`  
**Paper source:** `docs/archive/context_projection_revised_v10.md`  
**Roadmap status:** planning document  
**Live API authorization:** not granted by this roadmap

Current status note: this P37-P44 roadmap is preserved as the v10-era
development-cycle record. The current v12 paper direction is anchored at
`docs/archive/context_projection_fixed_v12.md` and mapped in
`docs/paper-alignment-v12.md`. For the next active development cycle, start
with `docs/roadmaps/mingx-followup-dev-experiment-plan-v0-2.md`; it keeps v10
documents as legacy/archive material and makes one-stratum metric bridge
calibration the highest-priority missing experiment. No measurement validation
is claimed by either roadmap.


## Source Basis

This document is aligned to:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`
- `docs/experiment-design-overview.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/phase-tree-crosswalk.md`
- `docs/current-work-summary.md`
- `configs/runs/README.md`

Local execution status must always be verified from `git status`, run plans, `run_summary.json`, `events.jsonl`, and concrete artifacts. Paper text and roadmap documents are not run-completion evidence.


## 1. Strategic Objective

The next development cycle should turn the current runtime-audit scaffold into an evidence ladder that is replayable, claim-gated, and manuscript-ready.

The target evidence ladder is:

```text
repo-state lock
  -> synthetic structural validity
  -> artifact schema stability
  -> offline replay and diagnostic recomputation
  -> Route B model-adjudicated operational evaluation
  -> fresh contamination-aware reduced-scope live follow-up, if explicitly approved
  -> realistic-task context-projection benchmark
  -> manuscript evidence integration
```

The roadmap does not attempt to prove deployed V-information weak submodularity. It operationalizes the paper's bridge statement by keeping formal theory, proxy measurement, heuristic pipeline behavior, runtime artifacts, and metric-claim levels separate.


## Claim Boundary Lock

This milestone is part of the Context Projection Selection measurement and runtime-audit scaffold. It must not be reported as deployed V-information certification, theorem inheritance for a heuristic pipeline, scheduler correctness, full system validation, or `measurement_validated` evidence.

Conservative claim rules:

- contamination failure => `pilot_only` and scientific-stop for measurement interpretation
- missing human labels => not `measurement_validated`
- missing human-human kappa => not `measurement_validated`
- stale or missing metric bridge => `operational_utility_only` or `ambiguous`
- synthetic-only evidence => `vinfo_proxy_supported`, not deployed V-information certification
- replay package completeness => replay/observability evidence only, not scientific validation
- model-adjudicated labels => not human labels
- Codex/model audit => not human review
- live API success alone => operational evidence only, not measurement validation


## 2. Milestone Overview

| Milestone | Name | Primary goal | Live API? | Maximum claim |
|---|---|---|---|---|
| P37 | Repo-state and claim-boundary lock | Reconcile GitHub main, local repos, paper framing, and current evidence status | No | engineering status lock |
| P38 | Synthetic structural benchmark hardening | Strengthen Phase A synthetic diagnostics and reports | No | `vinfo_proxy_supported` |
| P39 | Artifact schema freeze | Freeze replay-critical artifact schema and hash behavior | No | replay readiness |
| P40 | Phase B offline replay implementation | Recompute diagnostics from recorded traces and cached utility records | No | replay / observability evidence |
| P41 | Route B model-adjudicated evaluation | Build fully automated prelabel/audit/adjudication route | Maybe, but not required initially | `model_adjudicated_pilot_only` or `operational_utility_only` |
| P42 | Fresh reduced-scope follow-up batch | Use prepared replacement questions for a fresh contamination-aware pilot | Yes, only after explicit approval | `pilot_only` unless stronger evidence exists; never `measurement_validated` alone |
| P43 | Phase C realistic-task benchmark | Test context-projection behavior on realistic tasks | Optional, design-dependent | bridge-qualified operational evidence |
| P44 | Manuscript evidence integration | Integrate results into the v10 manuscript without claim inflation | No | no claim upgrade by itself |

Sidecars:

| Sidecar | Purpose | Depends on |
|---|---|---|
| openWorker trace audit | Determine whether concrete deployment traces export required replay fields | concrete openWorker code path |
| extraction-uniformity sidecar | Measure `M* -> M` extraction bridge risk using `c_high`, `c_low`, and `Delta_hat` | contamination-safe and annotation-reliable substrate |

## 3. Required Ordering

P37 must come first because stale project assumptions are a major risk. P38 and P39 can then proceed in parallel if the repository is clean. P40 should precede P43 because realistic-task results are weak manuscript evidence unless they are replayable and claim-gated.

Recommended order:

```text
P37 -> P38 -> P39 -> P40 -> P41 -> P42 -> P43 -> P44
```

P42 must not be run until there is explicit operator approval for live API use. The current contamination-failed mini-batch must not be rerun and described as measurement validation. Fresh replacement questions must preserve lineage and contamination triage records.

## 4. Development Principles

### 4.1 Artifact-first development

Every experiment must write machine-readable artifacts before writing human-facing summaries. Reports are derived views; `events.jsonl`, explicit artifact files, and stable hashes are the source of truth.

Minimum artifact family:

- `events.jsonl`
- `CandidatePool`
- `ProjectionPlan`
- `BudgetWitness`
- `MaterializedContext`
- `MetricBridgeWitness`
- diagnostic records
- claim-gate report
- run summary

### 4.2 Claim-gated reporting

Every output report must carry:

- `metric_claim_level`
- `selector_regime_label`
- `selector_action`
- contamination status, if applicable
- human-label status, if applicable
- kappa status, if applicable
- metric-bridge status
- artifact completeness status

### 4.3 No implicit theorem inheritance

A heuristic pipeline can be useful without inheriting the formal theorem. A synthetic benchmark can pass without certifying deployed V-information. A model-adjudicated label can guide operational work without becoming a human label.

## 5. Success Criteria Across the Cycle

The P37-P44 cycle is successful if it produces:

1. a clean project-state lock;
2. a synthetic diagnostic report with pre-registered structural gate status;
3. frozen and tested artifact schema;
4. an offline replay runner with per-dispatch replay status;
5. a Route B model-adjudicated package with explicit non-human-label semantics;
6. an optional fresh follow-up pilot that preserves contamination boundary;
7. a realistic-task benchmark plan or execution report with explicit metric bridge scope;
8. a manuscript update package that does not claim `measurement_validated` unless the full claim gate is satisfied.

## 6. Branching Recommendation

Use one review branch per milestone unless the milestone is purely documentary and low-risk.

Suggested branches:

```text
codex/p37-repo-state-claim-boundary-lock
codex/p38-synthetic-structural-benchmark-hardening
codex/p39-artifact-schema-freeze
codex/p40-phase-b-offline-replay
codex/p41-route-b-model-adjudicated-evaluation
codex/p42-fresh-followup-replacement-batch
codex/p43-phase-c-realistic-task-benchmark
codex/p44-manuscript-evidence-integration
```

Do not push `main` directly. Do not merge review branches without a review document.

## 7. Validation Matrix

| Milestone | Required validation |
|---|---|
| P37 | `uv run pytest -q` if available; otherwise report skipped validation |
| P38 | synthetic benchmark CLI; synthetic tests; report diff audit |
| P39 | schema stability tests; hash stability tests; compileall |
| P40 | replay tests; missing-field downgrade tests; diagnostic recomputation tests |
| P41 | Route B claim-gate tests; model-label-not-human-label tests; manifest validation |
| P42 | non-live request-builder and backend tests; live tests only under explicit env gates |
| P43 | benchmark dry-run; metric-bridge assignment tests; artifact completeness tests |
| P44 | grep over unsafe claims; manuscript review checklist; no claim-boundary regression |

## 8. Final Deliverable Shape

The end of this cycle should produce a manuscript-facing evidence bundle:

```text
evidence_ladder_summary.md
synthetic_structural_report.md
phase_b_replay_report.md
route_b_model_adjudicated_report.md
fresh_followup_batch_report.md, if executed
phase_c_benchmark_report.md, if executed
claim_gate_report.md
manuscript_patch.md
```
