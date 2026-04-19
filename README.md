# MuSiQue Gate 1 Project

This repository now contains the local implementation scaffold for MuSiQue
Gate 1 as a runnable project, covering:

1. Phase 0 artifact validation and smoke checks
2. Phase 1 manifest loading, ordering, log-prob scoring, and `delta_loo`
3. Append-only measurement storage with `events.jsonl` as source of truth
4. Cohort runner support for mock and live DashScope / Qwen runs
5. Bridge and export scaffolds for calibration batches

Documentation entrypoints:

- [docs/README.md](./docs/README.md)
- [docs/architecture.md](./docs/architecture.md)
- [docs/protocols/execution-readiness-checklist.md](./docs/protocols/execution-readiness-checklist.md)
- [configs/runs/README.md](./configs/runs/README.md)

The current `phase0/` and `phase1/` directories are compatibility-oriented
runtime packages. They no longer represent the preferred long-term project
architecture.

## Runtime

- Provider: DashScope OpenAI-compatible Chat API
- Frontier model: `qwen3-32b`
- Small model: `qwen3-14b`
- Coding model: `qwen3-coder-plus`

Secrets stay in local `.env` and are not committed. Use `.env.example` as the
template.

## Suggested commands

### Windows PowerShell
```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv sync
uv run pytest
uv run python -m phase1.smoke --backend mock --run-plan configs/runs/smoke.json --env .env
uv run python -m phase1.run --plan configs/runs/live-calibration-p3.json --backend live --env .env
```

### WSL / bash
```bash
uv venv
source .venv/bin/activate
uv sync
uv run pytest
uv run python -m phase1.smoke --backend mock --run-plan configs/runs/smoke.json --env .env
uv run python -m phase1.run --plan configs/runs/live-calibration-p3.json --backend live --env .env
```
