# Context Projection Selection / Measurement and Runtime-Audit Scaffold

This repository is the companion measurement and runtime-audit scaffold for the
revised Context Projection Selection paper, currently archived at
[docs/archive/context_projection_revised_v10.md](./docs/archive/context_projection_revised_v10.md).
`cps/` is the canonical code package.

The revised paper separates six layers:

1. Formal layer: conditional V-information theory for per-round, per-agent,
   token-budgeted content selection
2. Proxy layer: CI, replay, log-loss, or utility finite-difference measurements
   under explicit bridge conditions
3. Pipeline layer: retrieval, reranking, MMR, packing, and other heuristics
4. Runtime layer: auditable artifacts and replay/monitoring interfaces
5. Metric bridge: claim-level gates between V-information proxy claims,
   calibrated proxy claims, operational-utility-only claims, and ambiguity
6. Extraction layer: a separate `M* -> M` bridge-risk audit, not an extension of
   the weak-submodular guarantee

This repository implements measurement scaffolds, proxy diagnostics, replay
artifacts, synthetic structural tests, bridge-calibration scaffolds, and
extraction-audit infrastructure. It does not certify deployed V-information weak
submodularity, and it does not provide theorem inheritance for heuristic
pipelines.

It currently covers:

1. Phase 0 artifact validation and smoke checks
2. Phase 1 manifest loading, ordering, log-prob scoring, and `delta_loo`
3. Append-only measurement storage with `events.jsonl` as source of truth
4. Cohort runner support for mock and live API-profile-backed runs
5. Bridge and export scaffolds for calibration batches
6. Synthetic structural diagnostics and replayable projection artifacts

Project entrypoints:

- [docs/README.md](./docs/README.md)
- [docs/paper-alignment-v10.md](./docs/paper-alignment-v10.md)
- [docs/architecture.md](./docs/architecture.md)
- [docs/protocols/execution-readiness-checklist.md](./docs/protocols/execution-readiness-checklist.md)
- [configs/runs/README.md](./configs/runs/README.md)
- [api/README.md](./api/README.md)

## Paper Context

The current research framing is the revised conditional-theory,
metric-bridge, and proxy-regime framing in
[docs/archive/context_projection_revised_v10.md](./docs/archive/context_projection_revised_v10.md).
For the repository-to-paper map, start with
[docs/paper-alignment-v10.md](./docs/paper-alignment-v10.md).

This repository is not a full paper implementation. Protocol docs, run plans,
`run_summary.json`, and `events.jsonl` decide current execution status.
`artifacts/` are time-sensitive run outputs; reduced-scope, partial, or
contamination-failed live artifacts must not be described as completed
scientific validation.

The `phase0/` and `phase1/` directories now act as compatibility shims.
New imports and new runtime entrypoints should prefer `cps.*`.

## Runtime

- Protocol lock remains:
  DashScope OpenAI-compatible Chat API
  `frontier = qwen3.6-plus`
  `small = qwen3.6-flash`
  `coding = qwen3-coder-plus`
- Runtime provider/model resolution now lives under `api/`:
  `api/settings.py` owns active API profiles and role-model mapping
  `api/backends.py` owns live/mock backend construction
  `cps/runtime` consumes role models and does not branch on provider names directly
- Current API profiles:
  `dashscope-qwen-phase1` is the default Phase 1 profile
- Use `.env.example` as the template for secrets and generic `API_*` overrides

Secrets stay in local `.env` and are not committed.

## Suggested Commands

### Windows PowerShell
```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv sync
uv run pytest
uv run python -m api --show-profiles
uv run python -m api --export-phase1-env --profile dashscope-qwen-phase1
uv run python -m cps.runtime.phase1_smoke --backend mock --run-plan configs/runs/smoke.json --env .env
uv run python -m cps.runtime.cohort --plan configs/runs/live-calibration-p3.json --backend live --env .env
```

### WSL / Bash
```bash
uv venv
source .venv/bin/activate
uv sync
uv run pytest
uv run python -m api --show-profiles
uv run python -m api --export-phase1-env --profile dashscope-qwen-phase1
uv run python -m cps.runtime.phase1_smoke --backend mock --run-plan configs/runs/smoke.json --env .env
uv run python -m cps.runtime.cohort --plan configs/runs/live-calibration-p3.json --backend live --env .env
```

Legacy compatibility commands remain available:

- `uv run python -m phase1.smoke --backend mock --run-plan configs/runs/smoke.json --env .env`
- `uv run python -m phase1.run --plan configs/runs/live-calibration-p3.json --backend live --env .env`
