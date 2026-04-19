# MuSiQue Gate 1 / Phase 1 Scaffold

This repository now contains the local implementation scaffold for MuSiQue
Gate 1, covering:

1. Phase 0 artifact validation and smoke checks
2. Phase 1 manifest loading, ordering, log-prob scoring, and `delta_loo`
3. Append-only measurement storage with `events.jsonl` as source of truth
4. Cohort runner support for mock and live DashScope / Qwen runs
5. Bridge and export scaffolds for calibration batches

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
uv run python -m phase1.smoke --backend mock --run-plan artifacts/phase1/run_plan.json --env .env
uv run python -m phase1.run --plan artifacts/phase1/live_calibration_p3_plan.json --backend live --env .env
```

### WSL / bash
```bash
uv venv
source .venv/bin/activate
uv sync
uv run pytest
uv run python -m phase1.smoke --backend mock --run-plan artifacts/phase1/run_plan.json --env .env
uv run python -m phase1.run --plan artifacts/phase1/live_calibration_p3_plan.json --backend live --env .env
```
