# Codex task: Phase B B1/B2 replay artifact binding and missing-field classification

## Goal

Implement Phase B B1/B2 replay artifact binding and missing-field classification.

Add:

- `cps/experiments/phase_b_replay.py`
- `tests/test_phase_b_replay.py`

Add CLI:

```bash
uv run python -m cps.experiments.phase_b_replay \
  --input-dir artifacts/<source-run> \
  --output-dir artifacts/experiments/phase_b_replay_smoke
```

## Source-of-truth docs

Read before editing:

- `AGENTS.md`
- `docs/codex/phase-development-guidance.md`
- `docs/codex/phases/phase-b-replay-readiness.md`
- `docs/paper-alignment-v10.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/protocols/phase-b-readiness-and-first-replay-plan.md`

## Required input support

Support these files:

- `events.jsonl`
- `candidate_pools.jsonl`
- `projection_plans.jsonl`
- `budget_witnesses.jsonl`
- `materialized_contexts.jsonl`
- `metric_bridge_witnesses.jsonl`
- `diagnostics.jsonl`
- `utility_records.jsonl`

Equivalent cached utility/log-loss records may be supported only if an existing repo convention already exists.

## Required outputs

Write:

- `replay_manifest.jsonl`
- `missing_fields.json`
- `replay_summary.json`

Do not write `replay_diagnostics.jsonl` yet unless explicitly empty/placeholder and marked not recomputed.

## Required data structures

Implement dataclasses or equivalent typed structures for:

- `ReplayArtifactBundle`
- `ReplayManifestRow`
- `MissingFieldRecord`
- `ReplaySummary`

Use the fields specified in `docs/codex/phases/phase-b-replay-readiness.md`.

## Required behavior

- Offline replay only.
- No live inference.
- No diagnostic recomputation.
- No block-ratio recomputation.
- Conservative dispatch binding using `run_id`, `dispatch_id`, `agent_id`, `round_id`.
- Deterministic output ordering by `run_id`, `dispatch_id`, `agent_id`, `round_id`.
- No timestamps, UUIDs, absolute paths, or environment-specific values in canonical outputs.

## Replay status precedence

Apply in this exact order. First matching class wins:

1. `replay_unusable`
2. `pilot_degraded`
3. `replay_partial`
4. `replay_usable`

Use the detailed definitions in `docs/codex/phases/phase-b-replay-readiness.md`.

## Metric-bridge rules

- Missing bridge usually means `replay_partial`, unless earlier structural/materialization defects apply.
- Stale bridge usually means `replay_partial` plus conservative scope.
- Synthetic bridge claim level must remain `structural_synthetic_only`.
- Operational bridge claim level must remain `operational_utility_only`.
- Do not emit `Vinfo_proxy_certified` without fresh matching `MetricBridgeWitness`.

## CandidatePool rule

`CandidatePool` is replay substrate only.

It must not be counted as one of the four core paper artifacts.

## Required tests

Implement tests for:

1. complete dispatch bundle -> `replay_usable`
2. missing `MetricBridgeWitness` -> `replay_partial`; no bridge-qualified claim
3. missing materialization order -> not `replay_usable`; replay defect recorded
4. missing excluded candidates -> not `replay_usable`; replay defect recorded
5. missing candidate pool -> `replay_unusable`
6. operational-only bridge -> `metric_claim_level == operational_utility_only`
7. structural synthetic bridge -> `metric_claim_level == structural_synthetic_only`
8. stale bridge -> conservative/recalibration-required scope; no `Vinfo_proxy_certified`
9. CLI writes required output files
10. `CandidatePool` is substrate, not core paper artifact

## Validation commands

Run:

```bash
uv run pytest tests/test_phase_b_replay.py
```

Then:

```bash
uv run pytest tests/test_projection_artifacts.py tests/test_synthetic_regime_benchmark.py tests/test_revised_framing_guardrails.py
```

Then:

```bash
uv run pytest
```

## Non-goals

Do not:

- implement diagnostic recomputation
- implement live inference
- implement Phase C
- change synthetic benchmark behavior
- change `gamma_hat` semantics
- change `block_ratio_lcb_star` semantics
- infer missing materialization order
- infer excluded candidates without explicit complete considered set
- emit theorem-level deployment verification
- emit `Vinfo_proxy_certified` without fresh matching bridge evidence

## Required final response

Report:

- changed files
- implementation summary
- classification logic summary
- tests run and exact results
- assumptions
- limitations
- whether `replay_diagnostics.jsonl` was not written or was only an empty placeholder
- whether paper-boundary guardrails were touched
