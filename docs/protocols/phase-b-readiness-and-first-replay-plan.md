# Phase B Readiness and First Replay Plan

**Document status:** proposed execution plan for the next development stage.  
**Recommended repo path:** `docs/protocols/phase-b-readiness-and-first-replay-plan.md`  
**Baseline:** v10-aligned measurement and runtime-audit scaffold after the synthetic benchmark follow-up.

---

## 1. Purpose

Phase B turns the v10-aligned scaffold from synthetic structural validation into offline replay readiness.

The central question is:

> Given recorded dispatch traces and cached utility or log-loss records, can the repo reconstruct candidate pools, selections, budgets, materialized contexts, metric-bridge claim levels, and selector diagnostics without live inference?

A successful Phase B does **not** prove Condition A, does **not** certify deployed V-information weak submodularity, and does **not** validate scheduler correctness. It validates whether the repo can audit and replay dispatch-time context projection decisions at the correct claim level.

---

## 2. Baseline Assumptions

Phase A is treated as complete for scaffold purposes only:

- synthetic benchmark artifacts can materialize `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, and `MetricBridgeWitness`;
- synthetic reports use the pre-registered structural validity gate;
- synthetic labels are `structural_synthetic_only`;
- ambiguity is counted separately and not treated as success;
- `gamma_hat` remains legacy compatibility only;
- `TraceDecay` is path-local marginal decay only;
- `block_ratio_lcb_star` is currently a conservative placeholder, not a paper-grade degree-adaptive star-block estimator.

Existing reduced-scope live artifacts remain pilot or observability artifacts unless they satisfy the Phase B replay protocol directly.

---

## 3. Scope

Phase B consumes recorded traces and cached evaluation records. It may read:

- `events.jsonl`
- `CandidatePool`
- `ProjectionPlan`
- `BudgetWitness`
- `MaterializedContext`
- `MetricBridgeWitness`
- cached singleton, marginal, pairwise, block, triple, utility, or log-loss records
- task metadata
- prior diagnostics, if present

Phase B produces:

- `replay_manifest.jsonl`
- `replay_diagnostics.jsonl`
- `missing_fields.json`
- `pipeline_vs_proxy_alignment.json`
- `replay_summary.json`
- `report.md`

---

## 4. Non-Goals

Phase B must not:

- run live model inference to fill missing fields;
- mutate the scheduler or runtime control flow;
- redesign memory;
- treat synthetic success as deployment validation;
- treat extraction audit as selector-regime proof;
- emit `Vinfo_proxy_certified` without a fresh and matching `MetricBridgeWitness`;
- treat `CandidatePool` as one of the four core paper artifacts;
- report legacy `gamma_hat` compatibility output as a current headline weak-submodularity diagnostic.

If traces are missing required data, Phase B reports a replay defect rather than inventing a value.

---

## 5. Replay Status Labels

Every dispatch replay attempt receives exactly one status.

| Status | Meaning | Allowed interpretation |
|---|---|---|
| `replay_usable` | Candidate pool, selected and excluded ids, budget, materialization order, metric bridge witness, and cached proxy utility records are all available. | Full Phase B diagnostic replay. |
| `pilot_degraded` | Structural replay is possible, but materialization, task metadata, or realized budget fields are incomplete. | Exploratory pilot only. |
| `replay_partial` | Dispatch identity, candidate pool, and selected set are recoverable, but one or more diagnostics cannot be recomputed. | Observability-gap report only. |
| `replay_unusable` | Candidate pool, selected set, or dispatch binding cannot be reconstructed. | Exclude from aggregate diagnostics. |

---

## 6. Claim-Level Downgrade Rules

| Condition | Required outcome |
|---|---|
| Missing `MetricBridgeWitness` | `ambiguous` or observability-only; no bridge-qualified claim. |
| Stale bridge | `ambiguous`; recalibration required. |
| Operational-only utility | `operational_utility_only`, not `Vinfo_proxy_certified`. |
| Missing materialization order | replay defect; do not infer order from selected ids. |
| Missing excluded candidates | replay defect; candidate-pool completeness cannot be audited. |
| Low denominator signal | ambiguous/uninformative, not automatic low-ratio failure. |
| Missing triple evidence under higher-order risk | ambiguous; no high-confidence `greedy_valid`. |
| Contamination-failed or extraction-incomplete source run | pilot/observability only unless separately remediated and requalified. |

---

## 7. Phase B Work Packages

### B0 - Document and schema freeze

**Goal:** freeze the replay document and machine-readable output names before implementation.

Deliverables:

- this phase document committed under `docs/protocols/`;
- schema sketch for replay manifest rows;
- schema sketch for missing-field records;
- schema sketch for replay diagnostics;
- explicit compatibility rules for old artifacts.

Exit criteria:

- docs state Phase B is offline replay only;
- output filenames are fixed;
- status labels and downgrade rules are testable.

---

### B1 - Replay input loader

**Goal:** load event logs and sidecar artifacts into a normalized dispatch record.

Minimum implementation:

- group records by `run_id`, `dispatch_id`, `agent_id`, and `round_id`;
- bind `CandidatePool`, `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, and `MetricBridgeWitness`;
- verify candidate-pool hash consistency where available;
- preserve raw missing-field information.

Exit criteria:

- controlled fixture with all artifacts loads as one replayable dispatch;
- missing `MetricBridgeWitness` is detected, not silently ignored;
- missing excluded candidates and missing materialization order are flagged.

---

### B2 - Missing-field classifier

**Goal:** classify each dispatch as `replay_usable`, `pilot_degraded`, `replay_partial`, or `replay_unusable`.

Minimum implementation:

- deterministic rule table;
- per-dispatch missing-field record;
- aggregate status counts;
- tests for each status.

Exit criteria:

- no dispatch can enter headline diagnostic aggregation unless `replay_usable`;
- `pilot_degraded` and `replay_partial` records remain visible but separate.

---

### B3 - Diagnostic recomputation

**Goal:** recompute revised diagnostics from cached values.

Recompute where supported:

- `block_ratio_lcb_b2`;
- `block_ratio_lcb_star`, with current placeholder semantics explicitly preserved unless a true star-block estimator is implemented;
- `block_ratio_lcb_b3`;
- `TraceDecay` as path-local `marginal_gain / singleton_gain`;
- pairwise interaction mass;
- triple-excess diagnostics;
- higher-order ambiguity flags;
- greedy-vs-augmented gap;
- `metric_claim_level`;
- `selector_regime_label`;
- `selector_action`.

Exit criteria:

- diagnostics are recomputed from cached utility/log-loss records rather than copied from summaries;
- missing records produce ambiguity or replay defects;
- legacy `gamma_hat` is compatibility only.

---

### B4 - Pipeline-vs-proxy comparison

**Goal:** compare observed pipeline selections against diagnostic-guided alternatives.

Report at minimum:

- selected-set overlap;
- observed selected value under cached proxy utility;
- alternative greedy / seeded augmented / local-search value where available;
- budget utilization;
- action agreement or mismatch;
- whether the mismatch is claim-qualified or operational-only.

Exit criteria:

- comparison does not imply theorem inheritance;
- alternative selector results are reported as replay diagnostics, not automatic runtime replacements.

---

### B5 - Report generator

**Goal:** produce a Phase B report from replay records.

Report sections:

1. run identity and source artifacts;
2. replay status counts;
3. artifact completeness table;
4. metric-bridge claim-level summary;
5. block-ratio diagnostics;
6. interaction and higher-order diagnostics;
7. greedy-vs-augmented gap;
8. pipeline-vs-proxy alignment;
9. missing-field blockers;
10. claim boundaries and non-claims.

Exit criteria:

- `replay_usable` dispatches are separated from all other statuses;
- no bridge-qualified claim appears without a fresh matching `MetricBridgeWitness`;
- report states whether diagnostics are V-information proxy, calibrated proxy, operational-only, structural synthetic only, or ambiguous.

---

### B6 - First controlled replay run

**Goal:** validate the end-to-end replay path before touching realistic or contaminated artifacts.

Recommended sequence:

1. Generate or reuse a tiny controlled synthetic trace with complete artifacts.
2. Replay it and confirm `replay_usable`.
3. Remove `MetricBridgeWitness` in a fixture and confirm downgrade.
4. Remove materialization order in a fixture and confirm replay defect.
5. Add a fixture with missing triple evidence under higher-order risk and confirm ambiguity.
6. Only after this, attempt an observability-only audit of existing Phase 1 / live-mini-batch artifacts.

Exit criteria:

- controlled fixture produces expected diagnostics;
- negative fixtures produce expected downgrades;
- existing reduced-scope live artifacts are classified by replay status, not by narrative intent.

---

## 8. First Experimental Decision

After B6, make one of three decisions.

| Result | Next action |
|---|---|
| Controlled replay works and existing traces are replayable | Run small Phase B replay report on eligible traces. |
| Controlled replay works but existing traces are incomplete | Open an observability-engineering lane to emit missing artifacts. |
| Controlled replay fails | Fix schema/replay implementation before any Phase C or fresh live batch. |

Do not begin Phase C until controlled Phase B replay works.

---

## 9. Suggested Codex Step Sequence

1. Add this Phase B readiness document.
2. Implement replay manifest and dispatch-binding schemas.
3. Implement artifact/event loader.
4. Implement missing-field classifier and status labels.
5. Implement diagnostic recomputation from cached values.
6. Implement pipeline-vs-proxy comparison.
7. Implement Phase B report generator.
8. Add controlled replay fixtures and downgrade fixtures.
9. Run first controlled replay smoke.
10. Audit existing Phase 1/live-mini-batch artifacts for Phase B eligibility.

Each step should include tests and should be reviewable independently.

---

## 10. Validation Commands

Targeted tests should be added as implementation progresses. The final Phase B implementation should pass:

```bash
uv run pytest
uv run pytest tests/test_phase_b_replay.py
uv run pytest tests/test_projection_artifacts.py tests/test_experiment_diagnostics.py tests/test_revised_framing_guardrails.py
```

A future replay CLI should support a command shaped like:

```bash
uv run python -m cps.experiments.phase_b_replay \
  --input-dir artifacts/<source-run> \
  --output-dir artifacts/experiments/phase_b_replay_smoke
```

The exact module name may differ, but the command must preserve the principle that Phase B reads recorded traces and cached values rather than running live inference.

---

## 11. Known Risks

1. Existing realistic traces may not include excluded candidates or materialization order.
2. Existing utility records may be insufficient for block-ratio or triple-excess recomputation.
3. `MetricBridgeWitness` may not be reconstructable for older runs.
4. Existing reduced-scope live runs may remain contamination-failed and pilot-only.
5. `block_ratio_lcb_star` is currently a placeholder, so the report must not call it a degree-adaptive star-block estimator.
6. Phase B may reveal that an observability-engineering lane is needed before Phase C.

---

## 12. Recommended Immediate Next Step

Commit this document first, then implement only B1 and B2.

That creates a hard separation between:

- whether the repo can bind dispatch artifacts;
- whether traces are complete enough for replay;
- whether diagnostics can be recomputed;
- whether any metric-bridge-qualified claim is allowed.

This is the safest next move because it prevents realistic-task experimentation from outrunning the audit surface required by the revised paper.
