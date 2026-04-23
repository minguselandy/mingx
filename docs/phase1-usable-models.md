# Phase 1 Usable Models

- Generated at UTC: `2026-04-23T03:09:56.604209+00:00`
- Profile: `dashscope-qwen-phase1`
- Provider: `dashscope`
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Visible model count: `233`
- Usable model count: `82`

## Regenerate

```bash
python scripts/list_phase1_usable_models.py --env .env --timeout 15 --json-out artifacts/phase1/model_probe/usable_models.json --markdown-out docs/phase1-usable-models.md
```

## Full Report

- JSON report: `artifacts/phase1/model_probe/usable_models.json`

## Usable Models

- `glm-4.7`
- `glm-5`
- `kimi-k2.5`
- `kimi/kimi-k2.5`
- `qwen-flash`
- `qwen-math-plus`
- `qwen-math-plus-0919`
- `qwen-math-plus-latest`
- `qwen-max`
- `qwen-max-0919`
- `qwen-max-2025-01-25`
- `qwen-max-latest`
- `qwen-max-longcontext`
- `qwen-plus`
- `qwen-plus-2025-01-25`
- `qwen-plus-2025-04-28`
- `qwen-plus-2025-07-14`
- `qwen-plus-2025-09-11`
- `qwen-plus-2025-11-05`
- `qwen-plus-2025-12-01`
- `qwen-plus-latest`
- `qwen-turbo`
- `qwen-turbo-2024-11-01`
- `qwen-turbo-2025-04-28`
- `qwen-turbo-2025-07-15`
- `qwen-turbo-latest`
- `qwen-vl-max`
- `qwen-vl-max-latest`
- `qwen-vl-plus`
- `qwen-vl-plus-2025-08-15`
- `qwen-vl-plus-latest`
- `qwen2.5-14b-instruct`
- `qwen2.5-14b-instruct-1m`
- `qwen2.5-32b-instruct`
- `qwen2.5-7b-instruct-1m`
- `qwen2.5-coder-32b-instruct`
- `qwen2.5-math-72b-instruct`
- `qwen3-0.6b`
- `qwen3-1.7b`
- `qwen3-14b`
- `qwen3-235b-a22b`
- `qwen3-235b-a22b-instruct-2507`
- `qwen3-30b-a3b`
- `qwen3-30b-a3b-instruct-2507`
- `qwen3-32b`
- `qwen3-4b`
- `qwen3-8b`
- `qwen3-coder-480b-a35b-instruct`
- `qwen3-coder-flash`
- `qwen3-coder-plus`
- `qwen3-coder-plus-2025-07-22`
- `qwen3-coder-plus-2025-09-23`
- `qwen3-max`
- `qwen3-max-2025-09-23`
- `qwen3-max-2026-01-23`
- `qwen3-max-preview`
- `qwen3-next-80b-a3b-instruct`
- `qwen3-omni-flash`
- `qwen3-omni-flash-2025-09-15`
- `qwen3-omni-flash-2025-12-01`
- `qwen3-vl-flash`
- `qwen3-vl-flash-2025-10-15`
- `qwen3-vl-flash-2026-01-22`
- `qwen3-vl-plus-2025-09-23`
- `qwen3.5-122b-a10b`
- `qwen3.5-27b`
- `qwen3.5-35b-a3b`
- `qwen3.5-397b-a17b`
- `qwen3.5-flash`
- `qwen3.5-flash-2026-02-23`
- `qwen3.5-omni-flash`
- `qwen3.5-omni-flash-2026-03-15`
- `qwen3.5-omni-plus`
- `qwen3.5-omni-plus-2026-03-15`
- `qwen3.5-plus`
- `qwen3.5-plus-2026-02-15`
- `qwen3.6-35b-a3b`
- `qwen3.6-flash`
- `qwen3.6-flash-2026-04-16`
- `qwen3.6-max-preview`
- `qwen3.6-plus`
- `qwen3.6-plus-2026-04-02`

## Notes

- This document only lists models that passed the current Phase 1 probe contract.
- The probe requires `logprobs=true`, `top_logprobs=0`, `stream=false`, `n=1`, and `enable_thinking=false`.
- Models that are visible in `/models` but fail the probe are excluded from the usable list.
