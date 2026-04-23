# API Utilities

这个目录是仓库里 API 抽象的唯一入口，负责三件事：

- 管理 provider/profile 和角色模型映射
- 构造运行时 backend
- 提供 Phase 1 运行时配置导出 CLI

它的目标是把“具体用哪家 API、哪组模型”封装在 `api/` 里，让
`cps/runtime` 只关心 `frontier` / `small` / `coding` 这些角色模型。

## 当前职责分工

- [settings.py](./settings.py)
  维护 API profile 注册表，解析 active profile 和泛化的 `API_*` 覆盖项。
- [backends.py](./backends.py)
  根据解析结果构造 live/mock backend。
- [openai_compatible.py](./openai_compatible.py)
  提供基础 OpenAI-compatible client。

## 协议锁定与实现抽象

这个目录不会覆盖当前 Phase 1 的协议锁定。

仓库当前默认的正式 Phase 1 仍然是：

- `API_PROFILE=dashscope-qwen-phase1`
- `frontier = qwen3-32b`
- `small = qwen3-14b`
- `coding = qwen3-coder-plus`

这些协议锁定值来自 [phase1.yaml](../phase1.yaml) 和
[api/settings.py](./settings.py)。

可选 profile：

- `dashscope-qwen-phase1`
  当前正式默认值，Phase 1 logprob-ready。

## 运行时数据流

1. `.env` 和进程环境提供 secret 与覆盖项
2. `api/settings.py` 解析 `API_PROFILE`、`API_BASE_URL`、`API_*_MODEL`
3. `api/backends.py` 根据 profile 构造 live/mock backend
4. `cps/runtime` 只消费角色模型，不再直接判断具体 provider 分支
5. 具体 OpenAI-compatible transport 落在 `cps/providers/openai_compatible.py`

## 环境变量优先级

当前推荐优先级如下：

1. `API_PROFILE`
2. `API_BASE_URL`、`API_KEY`、`API_FRONTIER_MODEL`、`API_SMALL_MODEL`、`API_CODING_MODEL`
3. 当前 profile 对应的 provider-specific secret
   `DASHSCOPE_*`
4. 兼容兜底的旧变量
   `PHASE1_PROVIDER_PROFILE`、`PHASE1_FRONTIER_MODEL`、`PHASE1_SMALL_MODEL`、`CODING_MODEL`

也就是说，新的主路径已经是通用 `API_*`，旧 `PHASE1_*` 变量只保留兼容。

## 常用命令

```bash
python -m api --show-profiles
python -m api --export-phase1-env --profile dashscope-qwen-phase1
python -m api --probe-phase1-logprobs --env .env --model-role small
python scripts/list_phase1_usable_models.py --env .env
```

`--probe-phase1-logprobs` 会执行一次真实 live 请求，用当前 `.env` / 运行时配置检查：

- 请求是否仍按 Phase 1 contract 打开 `logprobs=true`
- provider 是否真的返回 token-level logprobs
- 是否出现“token logprobs 全 0”的退化响应

如果 probe 失败，优先处理 provider/profile 兼容性，不要直接启动 `protocol-full-live`。

如果需要盘点当前账号下“哪些模型真的可用于当前 Phase 1 合约”，可以运行：

```bash
python scripts/list_phase1_usable_models.py \
  --env .env \
  --timeout 15 \
  --json-out artifacts/phase1/model_probe/usable_models.json \
  --markdown-out docs/phase1-usable-models.md
```

这个脚本会：

- 调用 `/models` 列出当前账号可见模型
- 用当前 Phase 1 request contract 逐个探测
- 打印 `usable_models` 和每个不可用模型的错误原因
- 可选把完整 JSON 和 Markdown 摘要直接写入仓库

## 当前限制

- `cps/providers/dashscope.py` 和 `phase1/*` 仍然保留兼容 shim，
  但新的 provider/model 切换应优先改 `api/`
