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
3. docs/protocols/execution-readiness-checklist.md
4. docs/protocols/phase1-protocol.md
5. docs/protocols/phase1-contamination-triage-and-question-rewrite.md
6. configs/runs/README.md
7. api/README.md
8. docs/architecture.md
9. cps/runtime/cohort.py
10. cps/analysis/bridge.py
11. cps/analysis/contamination.py
12. cps/runtime/annotation.py

How to interpret the repo:
- `cps/` is the canonical implementation package.
- `api/` owns provider/model profiles, backend factories, and live probe helpers.
- `docs/protocols/` contains active execution contracts.
- `artifacts/` contains run outputs. Treat these as time-sensitive state, not stable rules.
- `events.jsonl` is the runtime source of truth for a run.

Non-negotiable constraints:
- Default collaboration language is Chinese unless the user asks otherwise.
- Preserve the implementation-first / minimal runnable loop posture.
- Follow gates and dependency order; do not jump ahead to a larger platform build.
- Reuse existing artifacts, manifests, scripts, and protocol documents before adding new abstractions.
- Do not silently reinterpret a run as hypothesis validation when the protocol says it is only measurement validation or pilot-only.
- A contamination gate fail is a scientific stop, not an engineering retry signal.

Document precedence:
- Execution scheduling follows the checklist / active run-plan documents.
- Design invariants and boundary constraints still come from the protocol/spec documents and must not be overwritten by a convenience implementation detail.

Current project semantics to keep in mind:
- The repo already supports live model probing, bridge diagnostics, annotation package export, and contamination escalation bundles.
- Reduced-scope live runs may be engineering-successful while still being scientifically blocked by contamination.
- AI-assisted contamination review is advisory only; it cannot clear the gate automatically.

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

Expected output style:
- Summarize findings in terms of gates, artifacts, and executable next steps.
- When recommending changes, anchor them to specific files and current protocol semantics.
- When uncertainty exists, say whether it is an engineering blocker, a scientific blocker, or a documentation gap.
```
