# P42 Fresh Reduced-Scope Follow-Up Batch Plan

**Milestone:** P42
**Status:** no-git DEV execution pass completed with live API skipped
**Live API:** prohibited unless explicitly approved by operator
**Maximum claim:** `pilot_only` unless stronger gates are separately satisfied; live success alone is not measurement validation


## Source Basis

This document is aligned to:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`
- `docs/experiment-design-overview.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/phase-tree-crosswalk.md`
- `docs/current-work-summary.md`
- `configs/runs/README.md`

Local execution status must be verified from the no-git automation state files, run plans, validation output, `run_summary.json`, `events.jsonl`, and concrete artifacts when such artifacts are produced. Paper text and roadmap documents are not run-completion evidence. During no-git direct development automation, do not run Git commands to determine status.


## 1. Purpose

P42 defines a fresh reduced-scope follow-up pilot using replacement questions. It must not rerun the contamination-failed mini-batch and relabel it as successful. The existing failed run remains finalized at `stop_and_escalate` / `pilot_only` for measurement interpretation.


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


## 2. Current Failed-Batch Boundary

The prior reduced-scope live mini-batch:

- completed runtime plumbing;
- computed bridge diagnostics;
- materialized annotation package;
- failed contamination gate;
- remains `pilot_only`;
- must not be described as `measurement_validated`.

The prepared replacement questions are selection candidates only. They are not scientific approvals.

## 3. Replacement Candidates

Current prepared same-hop replacements:

```text
2hop__132929_684936
3hop1__409517_547811_80702
4hop3__373866_5189_38229_86687
```

These must preserve lineage to the replacement manifest and triage artifacts.

## 4. Preconditions

Before live execution:

1. P37 state lock is complete;
2. failed mini-batch is preserved, not modified;
3. replacement manifest exists;
4. API profile is confirmed;
5. non-live request-builder and backend tests pass;
6. operator explicitly approves live API calls;
7. output root is unique and does not overwrite previous artifacts.

## 5. Non-Live Readiness Commands

```bash
uv run python -m api --show-profiles
uv run python -m api --export-phase1-env --profile dashscope-qwen-phase1
uv run pytest -q tests/test_phase1_request_builder.py tests/test_phase1_backend_runtime.py
```

Automation execution for P42 uses the non-live path first. The focused offline
readiness target is:

```bash
uv run pytest -q tests/test_phase1_request_builder.py tests/test_phase1_backend_runtime.py tests/test_controlled_live_pilot.py
```

## 6. Live Test Gate

Only after explicit operator approval and all live-smoke gates are true:

- mock/offline path passed;
- `.env` exists;
- credentials resolve locally;
- `CPS_ALLOW_LIVE_API=1`;
- `P42_ALLOW_LIVE_SMOKE=1`;
- run plan has `operator_approval=true`;
- CLI explicitly uses `--backend live`;
- `max_cases <= 3`;
- `max_repeats = 1`.

If any gate is missing, live execution is skipped and the exact skip reason is recorded. Only after those gates are satisfied:

```bash
PHASE1_ENABLE_LIVE_TESTS=1 uv run pytest -q   tests/test_phase1_live_api.py   tests/test_phase1_live_run.py
```

A live cohort command must use a fresh output directory and a replacement-specific run plan.

## 7. Required Outputs

```text
run_plan.json
resolved_runtime block
run_summary.json
events.jsonl
contamination_report.json
bridge_report.json
annotation_package, if generated
replacement_lineage_report.md
pilot_summary.md
claim_gate_report.md
```

## 8. Stop Conditions

Stop immediately if:

- contamination gate fails;
- API profile resolves to unexpected models;
- output root points to existing artifacts;
- selected questions differ from replacement manifest without operator approval;
- run summary omits claim-level status;
- live budget exceeds approved scope.

## 9. Acceptance Criteria

P42 is accepted when:

- the run is fresh and lineage-preserving;
- live execution, if any, was explicitly approved;
- contamination status is recorded;
- no failed or replacement run is described as measurement validation;
- output can feed observability or Route B evidence only under claim gate limits.

## 10. P42 No-Git Automation Result

- Execution time: `2026-05-05T01:17:58.5416162+08:00`
- Mode: no-git direct development in `mingx-dev`
- Offline/mock path: executed through focused request-builder, backend-runtime, and controlled-live-pilot tests
- Live API: skipped before any provider call because `CPS_ALLOW_LIVE_API` and `P42_ALLOW_LIVE_SMOKE` were unset
- `.env`: present, but no secret values were read into this document
- Raw provider responses: none written
- Output interpretation: `pilot_only` / `operational_utility_only`; no `measurement_validated` claim
