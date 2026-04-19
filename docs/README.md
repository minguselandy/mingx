# Project Docs

这个仓库现在按“完整项目”来组织文档，而不是把 `phase0` / `phase1`
当作长期主目录语义。

## 先看哪里

- [architecture.md](./architecture.md)
  说明当前代码布局、artifact 布局，以及后续迁移方向。
- [../configs/runs/README.md](../configs/runs/README.md)
  当前推荐的运行计划入口。
- [protocols/execution-readiness-checklist.md](./protocols/execution-readiness-checklist.md)
  当前执行顺序和 gate 判断的最高优先级文档。
- [protocols/phase1-protocol.md](./protocols/phase1-protocol.md)
  Phase 1 的 measurement chain、bridge、annotation 约束。

## 文档分层

- `protocols/`
  当前仍然有效、直接指导实现和执行的协议文档。
- `archive/`
  研究草稿和历史参考文档，不作为当前实现入口。

## 当前代码语义

目前代码仍保留 `phase0/`、`phase1/` 目录，目的是保持现有运行链路、
测试和 artifact 兼容。它们现在更接近“阶段兼容层”，而不是这个项目的
长期模块边界。

当前运行计划已经抽到 `configs/runs/`，`artifacts/phase1/*.json`
保留为兼容副本和历史入口。

后续如果继续演进，推荐把代码逐步迁到按能力划分的包，例如：

- `data/`
- `providers/`
- `scoring/`
- `store/`
- `analysis/`
- `runtime/`

在这一步之前，先保证：

- 现有 Gate 1 / Phase 1 闭环不被打断
- `events.jsonl` 继续作为 source of truth
- live plans 和已有 artifact 不被破坏
