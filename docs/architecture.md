# Architecture Notes

## 当前状态

这个仓库已经不是单纯的 `phase0` starter 了，而是一个围绕 MuSiQue Gate 1
/ Phase 1 的可执行项目。当前已经包含：

- Phase 0 artifact 校验与 smoke
- Phase 1 live / mock scoring
- append-only measurement store
- cohort runner
- bridge / export scaffold
- 研究规格和参考文档

## 为什么不该继续把 `phase0/phase1` 当主骨架

`phase0/phase1` 更适合表达执行阶段、gate 和协议语义，但不适合长期承担项目
模块边界。长期继续这样扩展，会把下面三件事混在一起：

- 研究阶段
- 代码能力
- artifact 产物

这会让项目越来越难找入口，也不利于后面继续加运行计划、分析模块和下游消费层。

## 当前建议的项目语义

建议把项目拆成三层语义：

### 1. `docs/`

负责协议、架构、决策和归档。

### 2. 代码目录

当前先保留 `phase0/`、`phase1/` 作为兼容层，后续逐步迁成按能力划分的目录。

推荐目标：

- `data/`
- `providers/`
- `scoring/`
- `store/`
- `analysis/`
- `runtime/`

### 3. `artifacts/`

负责真实运行结果与复现材料。

这里的 `phase0/`、`phase1/`、`live_calibration_p2/`、`live_calibration_p3/`
是合理的，因为它们表达的是运行阶段和具体 run，而不是代码模块。

## 当前最小迁移策略

这一步只做低风险整理，不打断已有运行链：

1. 文档改成“项目入口 / 协议 / 归档”
2. README 指向文档入口
3. 代码目录先不大规模迁移
4. 继续把 phase 名称留在 protocol 和 artifact 上，而不是作为长期代码架构

## 当前项目入口

- 文档入口：`docs/README.md`
- 运行计划入口：`configs/runs/*.json`
- 运行结果入口：`artifacts/phase0/`、`artifacts/phase1/`

这让项目至少在入口层面区分了：

- 配置
- 代码
- 产物

## 不在这一步做的事

- 不重写 `phase0/phase1` 包
- 不迁移现有 live runner 路径
- 不重做 Phase 0 artifact
- 不把 retrieval / bridge 扩成 full-study platform

## 备份

开始这轮整理前，已经生成本地备份：

- `backups/repo-backup-20260419-225647.zip`
