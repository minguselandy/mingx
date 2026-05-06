# P40 Phase B Offline Replay Implementation Plan

**Milestone:** P40  
**Experiment stack:** Phase B offline replay and artifact sufficiency  
**Status:** implemented replay contract
**Live API:** prohibited  
**Maximum claim:** replay / observability evidence


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

P40 implements the offline replay runner. Phase B consumes recorded traces and cached utility or log-loss records. It must not re-run live inference to fill missing replay fields.

The goal is to determine whether dispatch-time context projection traces can reconstruct:

- candidate pool `M`;
- selected subset `S_i`;
- token budget `B_i`;
- materialized context order;
- metric bridge witness;
- diagnostic values;
- pipeline-vs-proxy alignment.


## Claim Boundary Lock

This milestone is part of the Context Projection Selection measurement and runtime-audit scaffold. It must not be reported as deployed V-information certification, theorem inheritance for a heuristic pipeline, scheduler correctness, full system validation, or `measurement_validated` evidence.

Conservative claim rules:

- contamination failure => `pilot_only` and scientific-stop for measurement interpretation
- missing human labels => not `measurement_validated`
- missing human-human kappa => not `measurement_validated`
- stale or missing metric bridge => `operational_utility_only` or `ambiguous`
- synthetic-only evidence => `structural_synthetic_only`, not deployed V-information certification
- replay package completeness => replay/observability evidence only, not scientific validation
- model-adjudicated labels => not human labels
- Codex/model audit => not human review
- live API success alone => operational evidence only, not measurement validation


## 2. Replay Inputs

Each replayable dispatch must bind:

```text
run_id
dispatch_id
agent_id
round_id
events.jsonl
CandidatePool
ProjectionPlan
BudgetWitness
MaterializedContext
MetricBridgeWitness
cached utility/log-loss records
task metadata
prior diagnostics, if available
```

## 3. Replay Status Labels

Every replay attempt must receive exactly one status:

| Status | Definition | Allowed use |
|---|---|---|
| `replay_usable` | `M`, `S_i`, `B_i`, excluded ids, materialization order, realized token counts, replay diagnostics, metric bridge witness, and proxy utility records are present | Full Phase B diagnostic report |
| `pilot_degraded` | Structural diagnostics can be recomputed, but materialized context, realized token counts, or task metadata are incomplete | Exploratory pilot only |
| `replay_partial` | Dispatch identity, candidate pool, and selected set are recoverable, but one or more core diagnostics cannot be recomputed | Observability gap report only |
| `replay_unusable` | Candidate pool, selected set, or dispatch binding cannot be reconstructed | Exclude from diagnostic aggregation |

Headline diagnostic claims must use only `replay_usable` records.

Replay status and claim level are separate fields. A row can remain
`replay_usable` while claim-level gates exclude it from headline diagnostics.
Every per-dispatch row records:

```text
replay_status
metric_claim_level
selector_regime_label
diagnostic_recompute_status
headline_eligible
headline_exclusion_reason
```

Conservative precedence:

1. missing `run_id`, `dispatch_id`, `agent_id`, or `round_id` => `replay_unusable`;
2. missing candidate pool => `replay_unusable`;
3. missing selected set => `replay_unusable`;
4. missing materialized context/order or realized budget => `pilot_degraded` or `replay_partial`;
5. complete artifacts but insufficient cached utility/log-loss records => `replay_usable` with `diagnostic_recompute_status=insufficient_utility_records` and `headline_eligible=false`;
6. contamination failure => preserve the underlying `replay_status`, set `metric_claim_level=pilot_only`, and set `headline_eligible=false`;
7. missing/stale metric bridge => `metric_claim_level=operational_utility_only` or `ambiguous`;
8. only `replay_usable` rows with sufficient utility records, safe bridge, and no contamination enter headline diagnostics.

## 4. Diagnostic Recompute Steps

For each dispatch:

1. group events by dispatch identity;
2. verify stable hashes across artifact family;
3. rebuild `M` from `CandidatePool`;
4. rebuild `S_i` from `ProjectionPlan`;
5. rebuild `B_i` from `BudgetWitness`;
6. rebuild materialization order from `MaterializedContext`;
7. assign claim scope from `MetricBridgeWitness`;
8. recompute `block_ratio_lcb_b2` where utility records support it;
9. recompute `block_ratio_lcb_star` where configured;
10. recompute `block_ratio_lcb_b3` or triple-excess where records support it;
11. recompute pairwise interaction mass from the configured top-L slice;
12. recompute greedy-vs-seeded-augmented gap;
13. compare observed pipeline selection against diagnostic-guided alternatives;
14. derive `metric_claim_level`, `selector_regime_label`, and `selector_action`;
15. record missing-field downgrades.

Utility-record recomputation fails closed. Missing cached utility/log-loss
fields produce `diagnostic_recompute_status=insufficient_utility_records`.
Uninformative denominator evidence produces
`diagnostic_recompute_status=uninformative_denominator` and is not interpreted
as a low block-ratio failure.

## 5. Pipeline-vs-Proxy Alignment Metrics

Report at least:

```text
selected_set_overlap
selected_token_cost
budget_utilization
observed_proxy_value
greedy_proxy_value
seeded_augmented_proxy_value
local_search_proxy_value, if configured
observed_matches_selector_action
metric_claim_level
selector_regime_label
selector_action
missing_fields
```

## 6. Recommended Implementation Targets

```text
cps/experiments/phase_b_replay.py
tests/test_phase_b_replay.py
```

## 7. CLI Shape

Recommended command:

```bash
uv run python -m cps.experiments.phase_b_replay   --input artifacts/experiments/synthetic_regime_smoke   --output-dir artifacts/experiments/phase_b_replay_synthetic_smoke
```

Optional later command for live-mini-batch observability only:

```bash
uv run python -m cps.experiments.phase_b_replay   --input artifacts/phase1/live_mini_batch   --output-dir artifacts/experiments/phase_b_replay_live_mini_batch_observability
```

The latter must preserve contamination-failed `pilot_only` interpretation.

## 8. Required Outputs

```text
replay_manifest.json
replay_manifest.jsonl
per_dispatch_diagnostics.jsonl
missing_field_report.json
missing_fields.json
pipeline_proxy_alignment.json
metric_claim_level_summary.json
selector_regime_summary.json
replay_status_counts.json
replay_summary.json
report.md
```

Headline summaries must count excluded rows separately and must not mix
contaminated, partial, unusable, stale-bridge, insufficient-utility, or
denominator-uninformative rows into headline diagnostic denominators.

## 9. Validation

```bash
uv run python -m compileall cps scripts
uv run pytest tests/test_phase_b_replay.py -q
uv run pytest -q
```

## 10. Acceptance Criteria

P40 is accepted when:

- the replay runner works on Phase A synthetic artifacts;
- every dispatch receives exactly one replay status;
- missing fields downgrade claims conservatively;
- replay status and claim level remain separate;
- headline diagnostics use only eligible rows;
- stale/missing bridge, contamination failure, insufficient utility records, and uninformative denominators are excluded from headline denominators;
- `TraceDecay` is not reported as headline gamma;
- contaminated or reduced-scope live artifacts cannot enter headline claims unless replay protocol and claim gates allow it;
- report tables are derived from machine-readable outputs.
