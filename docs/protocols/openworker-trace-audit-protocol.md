# openWorker Trace Audit Protocol

**Status:** sidecar protocol  
**Live API:** prohibited  
**Purpose:** determine whether concrete openWorker traces can support Phase B replay


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


## 1. Purpose

This sidecar audits concrete openWorker code paths for trace-field availability. It does not port openWorker, redesign memory, or claim runtime validation.

If no concrete openWorker code path is available, the report must say `no_concrete_code_path_available` rather than inferring trace availability from templates.


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


## 2. Required Trace Fields

Audit these five fields:

```text
candidate_pool
greedy_or_selection_trace
selected_set
materialized_context
extraction_alignment
```

For Phase B replay compatibility, also check:

```text
excluded_candidates
token_budget
realized_token_counts
materialization_order
content_hashes
metric_bridge_metadata
cached utility or scoring records
dispatch identity binding
```

## 3. Availability Labels

Use exactly one label per field:

| Label | Meaning |
|---|---|
| `already_exported` | field is exported in machine-readable artifacts |
| `partially_exported` | field exists but is incomplete or not replay-stable |
| `not_exported` | field is not exported |
| `no_concrete_code_path_available` | code path unavailable for audit |

## 4. Effort Labels

Use exactly one effort estimate per missing or partial field:

| Label | Meaning |
|---|---|
| `one_week_port` | small export or wrapper change |
| `one_month_effort` | moderate instrumentation and schema work |
| `multi_month_project` | substantial runtime redesign or missing substrate |
| `blocked_unknown` | insufficient code access to estimate |

## 5. Output

```text
docs/reviews/openworker-trace-field-availability-map.md
```

Required report table:

| Field | Availability | Evidence path | Missing pieces | Effort | Phase B implication |
|---|---|---|---|---|---|

## 6. Acceptance Criteria

The audit is accepted when it provides a conservative field-by-field map and does not convert templates into evidence.
