# Context Projection Selection / MuSiQue Gate 1 Runtime Scaffold

This repository contains the runnable Phase 0/1 measurement and runtime
scaffold for the Context Projection Selection project, using MuSiQue as the
current Gate 1 / Phase 1 domain. `cps/` is the canonical code package.

It currently covers:

1. Phase 0 artifact validation and smoke checks
2. Phase 1 manifest loading, ordering, log-prob scoring, and `delta_loo`
3. Append-only measurement storage with `events.jsonl` as source of truth
4. Cohort runner support for mock and live API-profile-backed runs
5. Bridge and export scaffolds for calibration batches

Project entrypoints:

- [docs/README.md](./docs/README.md)
- [docs/architecture.md](./docs/architecture.md)
- [docs/protocols/execution-readiness-checklist.md](./docs/protocols/execution-readiness-checklist.md)
- [configs/runs/README.md](./configs/runs/README.md)
- [api/README.md](./api/README.md)

## Paper Context

The current canonical paper framing is
[docs/archive/final_paper_context_projection_submission_final_v8.md](./docs/archive/final_paper_context_projection_submission_final_v8.md).
That paper defines the research object and boundary: conditional theory,
the formal/proxy/pipeline/runtime bridge, verification and escalation, and
extraction as a separate bridge risk.

This repository is not a full paper implementation. It implements and records
the Phase 0/1 measurement/runtime scaffold needed to exercise that framing.
Protocol docs, run plans, `run_summary.json`, and `events.jsonl` decide current
execution status. `artifacts/` are time-sensitive run outputs; reduced-scope,
partial, or contamination-failed live artifacts must not be described as
completed scientific validation.

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

## Suggested commands

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

### WSL / bash
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
