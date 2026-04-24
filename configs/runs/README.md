# Run Plans

This directory stores canonical project-level run plans.

These files define:

- input manifest and hash sources
- backend role and scoring scope
- calibration scope
- output storage roots
- but not provider secrets, concrete base URLs, or hardcoded live model ids

They are not run outputs themselves. Real outputs still land under
`artifacts/`.

Canonical runtime package:

- `python -m cps.runtime.phase1_smoke`
- `python -m cps.runtime.cohort`

Provider/model resolution:

- Run plans intentionally stay at the `mock` / `live` backend level.
- The active live provider and role-model mapping are resolved through
  `api/settings.py`, typically via `API_PROFILE` plus optional `API_*`
  overrides from `.env`.
- Default profile: `dashscope-qwen-phase1`

Current recommended run plans:

- Protocol-full targets:
  [cohort.json](./cohort.json),
  [protocol-full-mock.json](./protocol-full-mock.json),
  [protocol-full-live.json](./protocol-full-live.json)
- Reduced-scope pilot configs:
  [smoke.json](./smoke.json),
  [live-pilot.json](./live-pilot.json),
  [live-mini-batch.json](./live-mini-batch.json),
  [live-calibration-p2.json](./live-calibration-p2.json),
  [live-calibration-p3.json](./live-calibration-p3.json)
- Experimental sidecar configs:
  [synthetic-regime-smoke.json](./synthetic-regime-smoke.json)

Interpretation rules:

- `scope_mode = protocol_full` means the config is intended to satisfy the scientific Phase 1 scope.
- `scope_mode = pilot_reduced_scope` means the config is engineering/pilot only and must not be used as a Phase 2 statistical input.
- Current `live-*` configs use reduced scope, including `question_paragraph_limit = 5` and calibration `per_hop_count` values of `1`, `2`, or `3`.
- To switch live provider/model bundles, prefer
  `python -m api --export-phase1-env --profile <profile>`
  rather than editing run plans directly.

Protocol-full execution notes:

- `protocol-full-mock.json` is intentionally a two-stage pre-flight.
  The first `python -m cps.runtime.cohort --plan configs/runs/protocol-full-mock.json --backend mock`
  run will usually stop at `status = awaiting_annotation`.
- For the cheapest synthetic completion path, fill the generated label package with:
  `python -m cps.runtime.annotation --annotation-manifest <.../exports/annotations/annotation_manifest.json> --fill-synthetic-passthrough`
  then rerun the same cohort command.
- Treat the CLI report as the run-level status source of truth.
  In `exports/run_summary.json`, check `pipeline_status` and `measurement_status`
  rather than expecting a top-level `status` field.
- `exports/run_summary.json` now also carries a `budget` block.
  This records the current-plan equivalent forward-pass estimate, the current
  runner API-call estimate, and a 1.3x recommended provisioning target.
- Live readiness is a separate step:
  1. `python -m api --export-phase1-env --profile dashscope-qwen-phase1`
  2. `pytest -q tests/test_phase1_request_builder.py tests/test_phase1_backend_runtime.py`
  3. `PHASE1_ENABLE_LIVE_TESTS=1 pytest -q tests/test_phase1_live_api.py tests/test_phase1_live_run.py`
- A contamination `gate_decision = fail` is a scientific stop, not an engineering retry signal.
  Do not auto-restrict to a subset or auto-rerun and still call the run `measurement_validated`.
- When contamination fails, inspect `exports/contamination_escalation_bundle.json`.
  It is a manual-decision packet, not an automatic remediation trigger.

Synthetic regime benchmark:

- The synthetic benchmark is a sidecar diagnostic scaffold for controlled set
  functions. It does not run a scheduler, memory system, openWorker port, or
  live model benchmark.
- Canonical smoke command:
  `python -m cps.experiments.synthetic_benchmark --config configs/runs/synthetic-regime-smoke.json --output-dir artifacts/experiments/synthetic_regime_smoke`
- Expected outputs are `events.jsonl`, `candidate_pools.jsonl`,
  `projection_plans.jsonl`, `budget_witnesses.jsonl`,
  `materialized_contexts.jsonl`, `diagnostics.jsonl`, `summary.json`, and
  `report.md`.
- Interpret `gamma_hat`, synergy fraction, and greedy-vs-augmented gap as
  provisional proxy-layer diagnostics only. They are not theorem inheritance
  and not a system-level performance claim.
