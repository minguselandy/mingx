# Recent Change Handoff Prompt

Use the prompt below when you want another AI agent to understand the recent
repo changes before continuing work.

```text
You are taking over an active repository after a recent implementation pass.
Read this as a change handoff, not as a blank-slate codebase exploration.

First, assume these recent changes are already intentional:

1. `cps/` is the canonical implementation package.
2. `api/` owns runtime profile/model/backend resolution.
3. `events.jsonl` is the append-only source of truth for run state.
4. `artifacts/` contains time-sensitive run outputs, not stable rules.
5. `docs/archive/context_projection_revised_v10.md` is the current paper-framing anchor. Read it with `docs/paper-alignment-v10.md` for research boundaries, metric-bridge claim levels, runtime artifacts, and extraction bridge-risk semantics.
6. The current default live model pair is:
   - `frontier = qwen3.6-plus`
   - `small = qwen3.6-flash`
7. The repository now includes an AI-assisted contamination triage workflow.
8. Newer `run_summary.json` exports include a `resolved_runtime` block so runtime overrides are visible without digging through event logs. Older historical artifacts may predate this field.

What was recently changed:

- Default Phase 1 runtime model resolution was switched from older Qwen3 defaults to `qwen3.6-plus / qwen3.6-flash`.
- Active protocol docs and README files were updated to match that default.
- A contamination triage workflow was added:
  - `docs/protocols/phase1-contamination-triage-and-question-rewrite.md`
  - `scripts/export_contamination_review_packet.py`
  - `cps/analysis/contamination_review.py`
- A reusable AI onboarding prompt was added:
  - `docs/project-reading-prompt.md`
- The revised v10 paper framing is now the canonical research framing:
  - `docs/archive/context_projection_revised_v10.md`
  - `docs/paper-alignment-v10.md`
- A recent reduced-scope live run produced review artifacts:
  - `artifacts/phase1/live_mini_batch/exports/contamination_review_packet.json`
  - `artifacts/phase1/live_mini_batch/exports/contamination_review_packet.md`

How to read the current state:

1. Read `docs/README.md`
2. Read `AGENTS.md`
3. Read `docs/paper-alignment-v10.md`
4. Read `docs/archive/context_projection_revised_v10.md`
5. Read `docs/project-reading-prompt.md`
6. Read `docs/protocols/execution-readiness-checklist.md`
7. Read `docs/protocols/phase1-protocol.md`
8. Read `docs/protocols/phase1-contamination-triage-and-question-rewrite.md`
9. Read `api/README.md`
10. Read `cps/runtime/cohort.py`

Critical semantic guardrails:

- Do not treat a reduced-scope live run as `measurement_validated`.
- A contamination gate fail is a scientific blocker, not an engineering retry signal.
- AI-generated rewrite advice is advisory only; it does not clear the gate automatically.
- Do not silently revert the default model pair back to `qwen3-32b / qwen3-14b`.
- If you see those older model names in historical artifacts or old reports, interpret them as historical state unless current runtime/config files still point to them.
- The paper controls research framing; protocol docs, run plans, `run_summary.json`, and `events.jsonl` control execution status.
- Treat `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, and `MetricBridgeWitness` as paper-specified target runtime interfaces, not as current-code guarantees unless the implementation is verified.
- Treat legacy `gamma_hat` fields as trace-decay or compatibility signals unless a current report reconstructs block-ratio LCB and assigns a metric-bridge claim level.
- Rewrite, replacement, compression, and memory-formation work remains sidecar / derived-view work and must not mutate the primary source-question answer path.

What to inspect first if continuing runtime work:

- `artifacts/.../exports/run_summary.json`
- `resolved_runtime` inside `run_summary.json`
- `exports/contamination_diagnostics.json`
- `exports/contamination_escalation_bundle.json`
- `exports/bridge_diagnostics.json`
- annotation exports under `exports/annotations/`

What to inspect first if continuing implementation work:

- `api/settings.py`
- `phase1.yaml`
- `cps/runtime/cohort.py`
- `cps/analysis/contamination_review.py`
- `scripts/export_contamination_review_packet.py`

What not to do:

- Do not assume unfinished `artifacts/phase1/protocol_full_live/` is commit-ready.
- Do not add a new annotation platform unless explicitly requested.
- Do not treat protocol docs as paper prose; they are execution contracts.

Expected output:

- Start with a short conclusion.
- Separate engineering status, scientific status, and documentation gaps.
- Anchor recommendations to concrete files and current protocol semantics.
```
