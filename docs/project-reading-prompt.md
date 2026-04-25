# AI Project Reading Prompt

Use the prompt below when onboarding another AI agent to this repository.

```text
You are entering an active research-engineering repository. Read it as an execution system, not as a paper draft.

Your job:
1. Build a correct mental model of the current Phase 1 runtime and protocol constraints.
2. Distinguish stable implementation contracts from current run-state artifacts.
3. Avoid proposing work that violates the repository's gate-driven, implementation-first workflow.

Reading order:
1. docs/README.md
2. AGENTS.md
3. docs/paper-alignment-v10.md
4. docs/archive/context_projection_revised_v10.md
   - Focus on the abstract, bridge statement, metric bridge, runtime artifacts, and extraction bridge-risk sections.
5. docs/protocols/execution-readiness-checklist.md
6. docs/protocols/phase1-protocol.md
7. docs/protocols/phase1-contamination-triage-and-question-rewrite.md
8. configs/runs/README.md
9. api/README.md
10. docs/architecture.md
11. cps/runtime/cohort.py
12. cps/analysis/bridge.py
13. cps/analysis/contamination.py
14. cps/runtime/annotation.py

How to interpret the repo:
- `cps/` is the canonical implementation package.
- `api/` owns provider/model profiles, backend factories, and live probe helpers.
- `docs/protocols/` contains active execution contracts.
- `docs/archive/context_projection_revised_v10.md` is the current paper-framing anchor.
- `docs/paper-alignment-v10.md` maps revised paper layers to repository modules and claim rules.
- `artifacts/` contains run outputs. Treat these as time-sensitive state, not stable rules.
- `events.jsonl` is the runtime source of truth for a run.

Non-negotiable constraints:
- Default collaboration language is Chinese unless the user asks otherwise.
- Preserve the implementation-first / minimal runnable loop posture.
- Follow gates and dependency order; do not jump ahead to a larger platform build.
- Reuse existing artifacts, manifests, scripts, and protocol documents before adding new abstractions.
- Do not silently reinterpret a run as hypothesis validation when the protocol says it is only measurement validation or pilot-only.
- A contamination gate fail is a scientific stop, not an engineering retry signal.
- The revised paper controls research framing, not run completion status.
- `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, and `MetricBridgeWitness` are target auditable runtime interfaces from the paper; do not assume the current code fully implements them unless you verify it locally.
- Legacy `gamma_hat` fields should be read as `trace_decay_proxy` or `legacy_trace_ratio`, not as headline weak-submodularity diagnostics.

Document precedence:
- Execution scheduling follows the checklist / active run-plan documents.
- Design invariants and boundary constraints still come from the protocol/spec documents and must not be overwritten by a convenience implementation detail.

Current project semantics to keep in mind:
- The repo already supports live model probing, bridge diagnostics, annotation package export, and contamination escalation bundles.
- Reduced-scope live runs may be engineering-successful while still being scientifically blocked by contamination.
- AI-assisted contamination review is advisory only; it cannot clear the gate automatically.
- Rewrite, replacement, compression, and memory-formation work belongs to a sidecar / derived-view lane and must preserve source-run lineage.

What to inspect in run outputs:
- Start from `exports/run_summary.json`.
- Then inspect `exports/contamination_diagnostics.json`, `exports/bridge_diagnostics.json`, and annotation exports.
- If a run failed contamination, inspect `exports/contamination_escalation_bundle.json`.
- If an AI rewrite workflow is needed, inspect `exports/contamination_review_packet.md` or regenerate it with `scripts/export_contamination_review_packet.py`.

What not to do:
- Do not assume unfinished `artifacts/phase1/protocol_full_live/` directories are commit-ready or scientifically valid.
- Do not auto-upgrade any run to `measurement_validated`.
- Do not auto-rerun from rewritten questions without human approval and lineage tracking.
- Do not add a new external annotation system unless the user explicitly asks for it.
- Do not modify primary source questions to make the answer-serving path easier; question rewrite/replacement is sidecar follow-up work only.

Expected output style:
- Summarize findings in terms of gates, artifacts, and executable next steps.
- When recommending changes, anchor them to specific files and current protocol semantics.
- When uncertainty exists, say whether it is an engineering blocker, a scientific blocker, or a documentation gap.
```
