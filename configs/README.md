# Configs

这个目录保存项目级配置，而不是运行后产物。

当前约定：

- 根目录的 [phase0.yaml](../phase0.yaml) 和 [phase1.yaml](../phase1.yaml)
  仍然是主要协议配置入口。
- `phase1.yaml` 负责锁定当前正式的 Phase 1 provider/model family；
  真正的运行时 provider/profile 解析和 backend 选择由
  [api/settings.py](../api/settings.py) 与 [api/backends.py](../api/backends.py)
  负责。
- `runs/` 保存可执行 run plan 的规范入口。
- `.env.example` 提供默认 secret 和 `API_*` 覆盖模板；
  [api/README.md](../api/README.md) 说明如何导出 profile 覆盖。

`artifacts/phase1/*.json` 中仍然保留历史计划文件，用于兼容已有脚本和已落地
artifact；但推荐今后优先从 `configs/runs/` 读取运行计划。
