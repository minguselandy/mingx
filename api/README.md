# API Utilities

这个目录单独管理仓库里的 OpenAI-compatible API 工具，先以 EVAS 为主。

它不会覆盖当前 Phase 1 的既有模型锁定。仓库里原来的 Phase 1 仍然是：

- `frontier`: `qwen3-32b`
- `small`: `qwen3-14b`
- `coding`: `qwen3-coder-plus`

这些值来自 [phase1.yaml](../phase1.yaml)。

当前可直接使用：

```bash
python -m api --list-models --show-recommendations
python -m api --chat-smoke --role small
python -m api --env-file .env --chat-smoke --model openai/gpt-5.4-mini
```

默认推荐模型：

- `frontier`: `openai/gpt-5.4`
- `small`: `openai/gpt-5.4-mini`
- `coding`: `openai/gpt-5.3-codex`

注意：

- 当前 CLI 会同时显示两套信息：
  Phase 1 已锁定的 Qwen 模型
  EVAS 下可选的候选模型
- 这套目录适合做模型探测、聊天 smoke test 和后续统一 API 管理。
- 当前 EVAS 已探测模型还不能直接替换 Phase 1 的 `delta_loo` scorer，因为返回里没有稳定可用的 token `logprobs`。
