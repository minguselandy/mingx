# Context Projection Selection / Measurement and Runtime-Audit Scaffold

This repository is the companion measurement and runtime-audit scaffold for the
current v12 Context Projection Selection paper direction, currently archived at
[docs/archive/context_projection_fixed_v12.md](./docs/archive/context_projection_fixed_v12.md).
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
- [docs/paper-alignment-v12.md](./docs/paper-alignment-v12.md)
- [docs/architecture.md](./docs/architecture.md)
- [docs/protocols/execution-readiness-checklist.md](./docs/protocols/execution-readiness-checklist.md)
- [configs/runs/README.md](./configs/runs/README.md)
- [api/README.md](./api/README.md)

## Current development planning

The current Codex development/reference package for v12 follow-up work is:

- [P45-P50 v12 Phase Docs](docs/codex/v12-phase-docs/README.md)

This package controls the next bounded Codex tasks. P45, one-stratum metric
bridge calibration, is the next priority. P50 is optional and must not precede
P45-P49. The package contains plans and reviews only; it does not claim
`measurement_validated` evidence and does not supply bridge calibration results
by itself.

The earlier P37-P44 development and experiment planning package is indexed at:

- [Mingx Follow-up Development and Experiment Plan v0.2](docs/roadmaps/mingx-followup-dev-experiment-plan-v0-2.md)
- [P37-P44 Development and Experiment Roadmap](docs/roadmaps/P37-P44-development-and-experiment-roadmap.md)
- [Documentation Index](docs/README.md)
- [Claim Boundary Checklist](docs/templates/claim-boundary-checklist.md)

These documents are planning and review artifacts. They do not claim
measurement validation, scientific validation, or deployed V-information
certification.

## Paper Context

The current research framing is the v12 conditional-theory, metric-bridge, and
proxy-regime diagnosis framing in
[docs/archive/context_projection_fixed_v12.md](./docs/archive/context_projection_fixed_v12.md).
For the repository-to-paper map, start with
[docs/paper-alignment-v12.md](./docs/paper-alignment-v12.md).
The v10 manuscript and alignment files remain preserved as legacy/archive
material:
[docs/archive/context_projection_revised_v10.md](./docs/archive/context_projection_revised_v10.md)
and [docs/paper-alignment-v10.md](./docs/paper-alignment-v10.md).
Bridge calibration remains the highest-priority missing experiment; the
repository does not claim `measurement_validated` evidence.

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
