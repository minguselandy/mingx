# Project Agent Contract

This file is a long-term collaboration contract for Codex and other agents.

* Put long-term rules in `Stable working contract`.
* Put current-stage and time-sensitive content in `Current run brief` and
  `Gate completion / definition of done`.
* If the project state changes, update the time-sensitive sections before
  changing stable collaboration rules.
* If tensions arise: current execution order is determined by the current run
  brief and checklist; long-term boundaries, design invariants, and safety
  baselines are governed by the stable contract and locked protocols.

## Stable Working Contract

### Collaboration Mode

* Default to implementation-first collaboration for implementation requests.
  If the user explicitly asks for review, pure analysis, brainstorming, status,
  or Q&A, follow that intent and do not make code or artifact changes unless
  asked.

### Execution Posture

* Prioritize the smallest runnable closed loop; do not start with large,
  comprehensive abstractions.
* Move according to gates and dependency graph: upstream before downstream;
  runnable before elegant.
* Prefer reusing existing protocols, scripts, run plans, and artifacts in the
  repo rather than reinventing interfaces or re-entering specs.
* Each implementation step should, where possible, produce reusable artifacts
  such as `json`, `csv`, `parquet`, `md`, or `script`.
* After completing each module, prioritize adding a smoke test or minimal
  validation script.

### Working Surface And Reuse

* Current working directory `.` is the repo root and the entry point for
  implementation, configuration, and execution.
* `docs/protocols/` is the current primary protocol entry point.
* `docs/archive/context_projection_revised_v10.md` is the current revised paper
  framing anchor. Older drafts in `docs/archive/`, including
  `final_paper_context_projection_submission_final_v8.md`, are historical
  references only.
* `docs/paper-alignment-v10.md` is the repository-facing map from the revised
  paper layers to current modules, artifacts, and claim-level reporting rules.
* `api/` is the unified entry point for current provider/profile settings,
  backend factory, and API smoke tools. For model switching or API integration,
  consolidate changes here first.
* `artifacts/phase0/`, `configs/runs/`, and `reference/files/` are the main
  sources for current run inputs, run plans, and old `files/` reference
  material.
* `.env.example` records the current recommended secret and `API_*` override
  template.

Task-scoped read sets:

* Paper/research framing: `docs/paper-alignment-v10.md`,
  `docs/archive/context_projection_revised_v10.md`.
* Protocol/gate work: `docs/protocols/execution-readiness-checklist.md`,
  `docs/protocols/phase1-protocol.md`,
  `docs/protocols/phase0-specification.md`,
  `docs/protocols/phase2-design.md`.
* Runtime/API work: `api/README.md`, `api/settings.py`, `api/backends.py`,
  `phase1.yaml`, `configs/runs/README.md`.
* Artifact audit: `artifacts/phase0/sample_manifest_v1.json`,
  `artifacts/phase0/content_hashes.json`, relevant `run_summary.json`,
  `events.jsonl`, bridge, annotation, and contamination exports.
* Data-prep work: `data_prep.py`, `reference/files/data_prep.py`,
  `reference/files/data_prep.json`.

### Document Precedence And Conflict Handling

Split priority into two layers to avoid misreading execution checklists as
allowed to override design invariants.

Execution-action scheduling priority:

1. `docs/protocols/execution-readiness-checklist.md`
2. `docs/protocols/phase1-protocol.md`
3. `docs/protocols/phase0-specification.md`
4. `docs/protocols/phase2-design.md`
5. `docs/paper-alignment-v10.md`
6. `docs/archive/context_projection_revised_v10.md`

Normative constraint priority:

* `docs/archive/context_projection_revised_v10.md` controls the current paper
  framing: conditional V-information theory, proxy measurement, heuristic
  pipeline diagnostics, auditable runtime artifacts, metric-bridge claim levels,
  and extraction as a separate `M* -> M` bridge risk.
* `docs/paper-alignment-v10.md` controls how current repository modules and
  artifacts should be described relative to that revised paper.
* `docs/protocols/phase0-specification.md` locks domain, granularity, budget,
  design invariants, and known limitations for the current MuSiQue cycle.
* `docs/protocols/phase2-design.md` provides downstream statistics and design
  boundaries; do not prematurely turn the project into a full Phase 2/4
  platform before gates are met.
* `docs/protocols/phase1-protocol.md` and
  `docs/protocols/execution-readiness-checklist.md` turn the work into
  executable steps, but cannot silently override invariants or boundaries
  already locked by Phase 0 / Phase 2 or the revised paper framing.

If execution-action priority and normative constraints conflict, choose the
nearest executable action that does not violate invariants, and only point out
conflicts that affect current execution.

### Paper Framing Vs Execution Contract

* The revised paper controls the research boundary, not run completion status.
* Protocols, run plans, `run_summary.json`, and `events.jsonl` control
  execution judgments: whether a run is complete, green, pilot-only,
  contamination failed, or measurement-validated is not determined directly by
  paper wording.
* Formal layer: conditional V-information theory over per-round, per-agent,
  token-budgeted content selection.
* Proxy layer: CI, replay, log-loss, or utility finite-difference measurements
  under explicit bridge conditions.
* Pipeline layer: retrieval, reranking, MMR, packing, and related heuristics;
  these are not theorem-level optimizers.
* Runtime layer: auditable artifacts and replay/monitoring interfaces.
* Metric bridge: claim-level gates between V-information proxy claims,
  calibrated proxy claims, operational-utility-only claims, and ambiguity.
* Extraction layer: separate `M* -> M` bridge-risk audit; do not treat it as an
  extension of the weak-submodular guarantee.
* If there is a gap between paper artifacts and current code, treat
  `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, and
  `MetricBridgeWitness` as target auditable interfaces or partially implemented
  artifact surfaces until verified locally.
* `CandidatePool` is a replay support artifact, not one of the four core paper
  runtime artifacts.
* Do not modify the source question or primary answer-serving path just to fit
  the paper narrative. Rewrite, replacement, compression, and memory formation
  remain sidecar / derived-view semantics with lineage.

### Research Framing Guardrails

The paper positioning is locked. Do not push the project into becoming:

* a system paper
* a memory paper
* a generic context-engineering paper
* a scheduler theory paper
* a PID paper

Current paper positioning:

* formal object: per-round, per-agent, token-budgeted content selection, with
  predictive V-information as the objective function
* conditional theory: weak-submodular / pairwise-additive complementarity
  regime, framed as conditional theory plus verification protocol, not as a
  proven deployed-system end-to-end guarantee
* bridge statement: separation of formal, proxy, pipeline, runtime,
  metric-bridge, and extraction layers
* deployment-facing contribution: verification, monitoring, escalation, replay,
  and claim-level reporting discipline
* extraction: `M* -> M` bridge risk and testable bottleneck, not an automatic
  extension of the weak-submodular theorem
* runtime / memory: supporting and bridge-risk layers only; memory may affect
  the candidate pool, but it is not the current formalized main object

### File And Code Strategy

* Prefer small-step edits.
* Prefer modifying files most relevant to the current gate; avoid unrelated
  refactors.
* Do not expand the directory tree without clear benefit.
* For provider/model or API switching, prioritize modifying `api/settings.py`,
  `api/backends.py`, and `api/README.md`; do not scatter provider branches into
  `cps/runtime`.
* Prefer reusing existing scripts and artifacts in the repo, especially material
  under `docs/protocols/`, `docs/archive/`, `artifacts/phase0/`,
  `configs/runs/`, and `reference/files/`, before deciding whether to migrate
  or simplify them.
* Measurement/event store should follow an append-only approach.
* Deterministic derived artifacts may be overwritten, or explicitly saved as
  versioned snapshots; do not make every intermediate file append-only.
* Checkpoints are only for recovery assistance; the event log is the source of
  truth.

### Multi-Agent / Delegation Policy

Borrow ECC-style management ideas, but only use minimal role-based management in
Codex.

* Prioritize completing main-thread blocking tasks locally; do not delegate
  first.
* Only delegate clearly bounded, non-critical-path tasks to sidecar roles.
* `explorer`: read-only exploration
* `reviewer`: read-only review
* `docs_researcher`: read-only documentation / spec checking

Do not over-split tasks just to look more agentic. Sidecars must not block the
main thread.

### Output Preference

For implementation requests, default response format:

1. Very brief restatement of the current state
2. A 3-6 step minimal development plan
3. Clear next artifact
4. Directly proceed with code, scripts, directory structure, and data-flow work

For review, status, explanation, or Q&A requests, lead with findings, current
state, and concrete recommendations. Do not perform implementation work unless
the user asks for it or clearly authorizes it.

### Git And Delivery Baseline

* By default, after completing code or documentation changes and validation,
  organize local changes for review and report the diff scope.
* Create a commit only when the user explicitly asks, or when the current task
  has an already-agreed commit expectation.
* Push only with explicit user authorization.
* Before any commit or push, check that `.env`, API keys, caches, checkpoints,
  temporary files, or other local secrets are not included.
* If `git` is not in PATH on the current machine, use the installed absolute
  path for `git`; do not stop delivery because of a PATH issue.
* If push fails after authorization, keep the completed local commit and
  prioritize reporting the blocking reason.

## Current Run Brief (time-sensitive)

Status anchor:

* Last verified: 2026-04-25
* Active lane: Phase 1 reduced-scope runtime hardening and follow-up readiness
* Paper alignment target: revised conditional-theory / metric-bridge /
  proxy-regime framing in `context_projection_revised_v10.md`
* Source artifacts to inspect before advancing: relevant `run_summary.json`,
  `events.jsonl`, contamination diagnostics, bridge exports, annotation exports,
  follow-up lineage, and operator approval state
* Stale when: a new protocol-full live run, follow-up live run, revised paper
  draft, or gate decision supersedes these artifacts

This section is current / time-sensitive. If the current gate target changes in
the future, update this section first rather than changing `Stable working
contract`.

### Current Main Target

The current main target is: Phase 1 reduced-scope runtime hardening, closing out
contamination triage / follow-up sidecar, and aligning the revised paper framing
with the existing runtime artifacts / protocol boundaries.

### Current Execution Order

1. First clarify the current live / reduced-scope artifacts: an engineering
   chain being runnable does not equal scientific pass; contamination-failed or
   partial protocol-full-live artifacts must not be described as
   `measurement_validated`.
2. Continue tightening the sidecar workflow for contamination triage, operator
   decision, same-hop replacement, and follow-up package; do not modify the
   already completed failed source run.
3. Check whether `run_summary.json`, `events.jsonl`, contamination / bridge /
   annotation exports can express the current runtime resolution, gate status,
   lineage, and approval state.
4. Map revised-paper runtime interface requirements to the existing artifact
   surface, prioritizing minimal alignment notes; do not prematurely refactor
   into a full `ProjectionPlan` / `BudgetWitness` / `MaterializedContext` /
   `MetricBridgeWitness` platform.
5. Only consider a new follow-up run after reduced-scope follow-up human review
   approval, lineage, and minimal safety checks are in place.
6. Any protocol-full live or Phase 2/3 interpretation must wait until the
   corresponding gate conditions are met; do not infer scientific conclusions
   from partial artifacts or paper framing.

### Current Sidecar

* contamination review / rewrite / replacement / follow-up package lane
* dual semantics check for compression, memory formation, and derived-view
  related work
* observability check for openWorker candidate pool / greedy trace / selected
  set / materialized context / extraction alignment
* metric-bridge qualification for proxy diagnostics and operational-utility
  claims

### Current Do-Not-Do-Yet

* Sidecars must not block the main thread.
* Do not build a large, comprehensive experimental platform first.
* Do not prematurely push the project into a full Phase 2/4 full-study platform.
* Do not treat partial `artifacts/phase1/protocol_full_live/` or reduced-scope
  live run as a completed scientific result.
* Do not write the paper runtime interface directly as an already implemented
  API.
* Do not modify the primary source question just to make the answer easier;
  question rewrite / replacement may only be sidecar / follow-up work with
  lineage.

### Current Phase And Gate Boundary Interpretation

The active lane is Phase 1 follow-up/readiness. The following points are
boundary references, not instructions to restart Gate 1 unless a run or artifact
audit shows the prerequisite is missing.

* `Phase 0 / Gate 1` concerns data locking, reproducibility, and pre-execution
  provisioning.
* `Phase 1` is a measurement apparatus / feasibility probe. It validates the
  stability of the measurement chain, bridge usability, contamination handling,
  and automated-to-expert substitution fidelity; do not misdescribe it as a
  completed extraction-uniformity hypothesis test or selector-regime proof. The
  current default variance source remains locked to paragraph-order permutation;
  if composition variation is introduced, explicitly state that it is an
  extension rather than the current default protocol.
* `Phase 2 / Phase 3` mainly support downstream design / pilot analytical
  post-processing. Before gates are complete, do not write formal conclusions
  for retrieval simulation or a full-study platform.

## Gate Completion / Definition Of Done (current Phase 1 reduced-scope / follow-up)

This section is also current / time-sensitive; if the current gate target
changes, update this section first.

The current stage counts as complete and ready to move forward only when at
least the following conditions are met:

* Current reduced-scope / partial live artifacts are correctly labeled:
  `pipeline_status`, `measurement_status`, contamination gate, annotation state,
  bridge state, and `resolved_runtime` if newly exported, are traceable in
  `run_summary.json` / `events.jsonl` / exports; when old artifacts lack fields,
  explicitly state that they are historical exports, not a protocol change.
* The contamination-failed run remains a scientific stop: do not automatically
  rerun, automatically restrict, or automatically upgrade it to
  `measurement_validated`; review / rewrite / replacement may only be a
  human-in-the-loop sidecar.
* If the follow-up package continues to be used, it must have a minimal safety
  loop: the source run is not rewritten, same-hop replacement lineage is
  auditable, operator signoff state is explicit, `execution_ready` is not
  misread, and the failed source run's scientific status is not retroactively
  modified.
* Revised paper framing has been mapped to the documentation entry point:
  formal/proxy/pipeline/runtime/metric-bridge/extraction layering,
  `M* -> M` extraction risk, claim-level reporting, verification / escalation,
  and the boundary around `ProjectionPlan`, `BudgetWitness`,
  `MaterializedContext`, and `MetricBridgeWitness` as target runtime interfaces.
* Before protocol-full live or Phase 2/3 advancement, re-check the active
  protocol, run plan, budget, annotation, contamination, bridge gate, and
  metric-bridge claim level; partial artifacts or reduced-scope pilot cannot be
  treated as full scientific completion.
* Completion of the current stage still only means runtime scaffold / triage /
  follow-up readiness is in place; it must not be described as a completed
  hypothesis test, extraction-uniformity validation, or selector-regime proof.
