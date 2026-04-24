# Project Agent Contract

This file is a long-term collaboration contract for Codex / agents.

* Put long-term rules in `Stable working contract`.
* Put current-stage and time-sensitive content in `Current run brief` and `Gate completion / definition of done`.
* If the project state changes in the future, prioritize updating the time-sensitive sections rather than changing the stable collaboration rules.
* If tensions arise: the current execution order is determined by the current run brief and checklist; long-term boundaries, design invariants, and safety baselines are governed by the stable contract and locked protocols.

## Stable working contract

### Collaboration mode

* Default to implementation-first / vibe coding collaboration mode, but if the user explicitly asks for review, pure analysis, brainstorming, or Q&A, follow the user’s intent.

### Execution posture

* Prioritize the smallest runnable closed loop; do not start with large, comprehensive abstractions.
* Move according to gates and dependency graph: upstream before downstream; runnable before elegant.
* Prefer reusing existing protocols, scripts, run plans, and artifacts in the repo rather than reinventing interfaces or re-entering specs.
* Each step should, where possible, produce reusable artifacts such as `json`, `csv`, `parquet`, `md`, or `script`.
* After completing each module, prioritize adding a smoke test or minimal validation script.

### Working surface and reuse

* Current working directory `.` is the repo root and the entry point for implementation, configuration, and execution.
* `docs/protocols/` is the current primary protocol entry point; `docs/archive/final_paper_context_projection_submission_final_v8.md` is the current paper framing anchor. Other drafts in `docs/archive/` are historical references only.
* `api/` is the unified entry point for current provider/profile settings, backend factory, and API smoke tools. For model switching or API integration, consolidate changes here first.
* `artifacts/phase0/`, `configs/runs/`, and `reference/files/` are the main sources for current run inputs, run plans, and old `files/` reference material.
* `.env.example` records the current recommended secret and `API_*` override template.

Existing artifacts to read first:

* `docs/protocols/phase0-specification.md`
* `docs/protocols/phase1-protocol.md`
* `docs/protocols/phase2-design.md`
* `docs/protocols/execution-readiness-checklist.md`
* `docs/archive/final_paper_context_projection_submission_final_v8.md`
* `data_prep.py`
* `reference/files/data_prep.py`
* `reference/files/data_prep.json`
* `artifacts/phase0/sample_manifest_v1.json`
* `artifacts/phase0/content_hashes.json`

### Document precedence and conflict handling

Split priority into two layers to avoid misreading execution checklists as allowed to override design invariants.

Execution-action scheduling priority:

1. `docs/protocols/execution-readiness-checklist.md`
2. `docs/protocols/phase1-protocol.md`
3. `docs/protocols/phase0-specification.md`
4. `docs/protocols/phase2-design.md`
5. `docs/archive/final_paper_context_projection_submission_final_v8.md`

Normative constraint priority:

* `docs/protocols/phase0-specification.md` locks domain, granularity, budget, design invariants, and known limitations.
* `docs/protocols/phase2-design.md` provides downstream statistics and design boundaries; do not prematurely turn the project into a full Phase 2/4 platform before Gates 1–3.
* `docs/protocols/phase1-protocol.md` and `docs/protocols/execution-readiness-checklist.md` turn the work into executable steps, but cannot silently override invariants or boundaries already locked by Phase 0 / Phase 2.
* `docs/archive/final_paper_context_projection_submission_final_v8.md` controls the current research framing, terminology, and “what this paper should not drift into”; old paper drafts are only historical archives and are no longer canonical anchors.

### Paper framing vs execution contract

* final v8 paper controls the research boundary: conditional theory, formal/proxy/pipeline/runtime layering, bridge statement, verification / monitoring / escalation, and extraction as an `M* -> M` bridge risk.
* Protocols, run plans, `run_summary.json`, and `events.jsonl` control execution judgments: whether a run is complete, green, pilot-only, contamination failed, or measurement-validated is not determined directly by paper wording.
* If there is a gap between the paper runtime interface and the current code, treat `ProjectionPlan`, `BudgetWitness`, and `MaterializedContext` by default as target auditable interfaces / future alignment targets; do not assume the current implementation already fully supports them.
* Do not modify the source question or primary answer-serving path just to fit the paper narrative; rewrite, replacement, compression, and memory formation should all remain sidecar / derived-view semantics with lineage.

If execution-action priority and normative constraints conflict, choose the nearest executable action that does not violate invariants, and only point out conflicts that affect current execution.

### Research framing guardrails

The paper positioning is locked. Do not push the project into becoming:

* a system paper
* a memory paper
* a generic context engineering paper
* a PID paper

Current paper positioning:

* formal object: per-round, per-agent, token-budgeted context/content selection, with predictive V-information as the objective function
* conditional theory: weak-submodular / pairwise-additive complementarity regime, framed as conditional theory + verification protocol, not as a proven deployed-system end-to-end guarantee
* bridge statement: separation of four layers — formal objective / proxy measurement / runtime heuristic / runtime artifact
* deployment-facing contribution: verification / monitoring / escalation
* extraction: `M* -> M` bridge risk and testable bottleneck, not an automatic extension of the weak-submodular theorem
* runtime / memory: only supporting / bridge-risk layers; memory may affect the candidate pool, but it is not the current formalized main object

### File and code strategy

* Prefer small-step edits.
* Prefer modifying files most relevant to the current gate; avoid unrelated refactors.
* Do not expand the directory tree without clear benefit.
* For provider/model or API switching, prioritize modifying `api/settings.py`, `api/backends.py`, and `api/README.md`; do not scatter provider branches into `cps/runtime`.
* Prefer reusing existing scripts and artifacts in the repo, especially material under `docs/protocols/`, `docs/archive/`, `artifacts/phase0/`, `configs/runs/`, and `reference/files/`, before deciding whether to migrate or simplify them.
* Measurement/event store should follow an append-only approach.
* Deterministic derived artifacts may be overwritten, or explicitly saved as versioned snapshots; do not make every intermediate file append-only.
* Checkpoints are only for recovery assistance; the event log is the source of truth.

### Multi-agent / delegation policy

Borrow ECC-style management ideas, but only use minimal role-based management in Codex.

* Prioritize completing main-thread blocking tasks locally; do not delegate first.
* Only delegate clearly bounded, non-critical-path tasks to sidecar roles.
* `explorer`: read-only exploration
* `reviewer`: read-only review
* `docs_researcher`: read-only documentation / spec checking

Do not over-split tasks just to “look more agentic.” Sidecars must not block the main thread.

### Output preference

Default response format:

1. Very brief restatement of the current state
2. A 3–6 step minimal development plan
3. Clear next artifact
4. Directly proceed with code, scripts, directory structure, and data-flow work

Unless the user asks otherwise, do not start with a long analysis.

### Git and delivery baseline

* By default, after completing code and validation in the current round, organize local changes for review; if appropriate, prepare a local commit directly.
* Only push if the user has not forbidden it, minimal safety checks pass, and the remote policy allows it.
* Before pushing, still check: do not commit `.env`, API keys, caches, checkpoints, temporary files, or other local secrets.
* If `git` is not in PATH on the current machine, use the installed absolute path for `git` to continue completing the local commit; do not stop delivery because of a PATH issue.
* If push fails, keep the completed local commit and prioritize reporting the blocking reason.

## Current run brief (time-sensitive)

This section is current / time-sensitive. If the current gate target changes in the future, update this section first rather than changing `Stable working contract`.

### Current main target

The current main target is: Phase 1 reduced-scope runtime hardening, closing out contamination triage / follow-up sidecar, and aligning final v8 paper framing with the existing runtime artifacts / protocol boundaries.

### Current execution order

1. First clarify the current live / reduced-scope artifacts: an engineering chain being runnable does not equal scientific pass; contamination-failed or partial protocol-full-live artifacts must not be described as `measurement_validated`.
2. Continue tightening the sidecar workflow for contamination triage, operator decision, same-hop replacement, and follow-up package; do not modify the already completed failed source run.
3. Check whether `run_summary.json`, `events.jsonl`, contamination / bridge / annotation exports can express the current runtime resolution, gate status, lineage, and approval state.
4. Map final v8’s runtime interface requirements to the existing artifact surface, prioritizing a minimal alignment note; do not prematurely refactor into a full `ProjectionPlan` / `BudgetWitness` / `MaterializedContext` platform.
5. Only consider a new follow-up run after reduced-scope follow-up human review approval, lineage, and minimal safety checks are in place.
6. Any protocol-full live or Phase 2/3 interpretation must wait until the corresponding gate conditions are met; do not infer scientific conclusions from partial artifacts or paper framing.

### Current sidecar

* contamination review / rewrite / replacement / follow-up package lane
* dual semantics check for compression, memory formation, and derived-view related work
* observability check for openWorker candidate pool / greedy trace / selected set / materialized context / extraction alignment

### Current do-not-do-yet

* Sidecars must not block the main thread.
* Do not build a large, comprehensive experimental platform first.
* Do not prematurely push the project into a full Phase 2/4 full-study platform.
* Do not treat partial `artifacts/phase1/protocol_full_live/` or reduced-scope live run as a completed scientific result.
* Do not write the paper runtime interface directly as an already implemented API.
* Do not modify the primary source question just to make the answer easier; question rewrite / replacement may only be sidecar / follow-up work with lineage.

### Current phase and gate boundary interpretation

* The goal of `Phase 0 / Gate 1` is data locking, reproducibility, and pre-execution provisioning; prioritize completing MuSiQue data acquisition / loading, fixed content hashes, reproducible hop-stratified sample manifest, Phase 0 artifact validation, and Phase 1 dependencies, interfaces, budget, storage, and minimal smoke tests.
* The goal of `Phase 1` is measurement apparatus / feasibility probe. It validates the stability of the measurement chain, bridge usability, and automated-to-expert substitution fidelity; do not misdescribe it as a completed extraction-uniformity hypothesis test. The current default variance source remains locked to paragraph-order permutation; if composition variation is introduced, explicitly state that it is an extension rather than the current default protocol.
* `Phase 2 / Phase 3` mainly support downstream design / pilot analytical post-processing. Before Gates 1–3 are complete, do not prematurely write formal conclusions for retrieval simulation or a full-study platform.

## Gate completion / definition of done (current Phase 1 reduced-scope / follow-up)

This section is also current / time-sensitive; if the current gate target changes, update this section first.

The current stage counts as complete and ready to move forward only when at least the following conditions are met:

* Current reduced-scope / partial live artifacts are correctly labeled: `pipeline_status`, `measurement_status`, contamination gate, annotation state, bridge state, and `resolved_runtime` if newly exported, are traceable in `run_summary.json` / `events.jsonl` / exports; when old artifacts lack fields, explicitly state that they are historical exports, not a protocol change.
* The contamination-failed run remains a scientific stop: do not automatically rerun, automatically restrict, or automatically upgrade it to `measurement_validated`; review / rewrite / replacement may only be a human-in-the-loop sidecar.
* If the follow-up package continues to be used, it must have a minimal safety loop: the source run is not rewritten, same-hop replacement lineage is auditable, operator signoff state is explicit, `execution_ready` is not misread, and the failed source run’s scientific status is not retroactively modified.
* final v8 paper framing has been mapped to the documentation entry point: formal/proxy/pipeline/runtime layering, `M* -> M` extraction risk, verification / escalation, and the boundary around `ProjectionPlan` / `BudgetWitness` / `MaterializedContext` as target runtime interfaces are clearly written out.
* Before protocol-full live or Phase 2/3 advancement, re-check the active protocol, run plan, budget, annotation, contamination, and bridge gate; partial artifacts or reduced-scope pilot cannot be treated as full scientific completion.
* Completion of the current stage still only means runtime scaffold / triage / follow-up readiness is in place; it must not be described as a completed hypothesis test or as extraction-uniformity having been validated.
