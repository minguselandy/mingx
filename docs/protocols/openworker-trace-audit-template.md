# openWorker Trace-Field Audit Template

这是当前阶段的 audit 方法包，不是对任何具体 openWorker 代码库的可用性结论。

在 openWorker 代码路径明确之前，这个模板只负责三件事：
- 定义 5 个 trace field 的最小证据
- 统一 `already exported / partially exported / not exported` 判定口径
- 统一 `one-week port / one-month effort / multi-month project` 的工程范围分级

## 1. 审计字段

### candidate pool
- 最小证据：能定位某一 dispatch round 在 selection 前的候选集合，以及每个候选项的稳定 id。
- `already exported`：round 级候选集合和 item id 已直接落盘或可直接 API 读取。
- `partially exported`：只能看到部分候选、或缺少稳定 id / round 绑定。
- `not exported`：运行后无法还原候选集合。

### greedy trace
- 最小证据：至少能恢复每一步 greedy 选择顺序、当步增益或打分、以及已选集合状态。
- `already exported`：step-by-step trace 已存在并可直接映射到具体 round。
- `partially exported`：只能看到最终 selected set，或只有部分 step metadata。
- `not exported`：没有可恢复的 greedy 过程记录。

### selected set
- 最小证据：能恢复最终被选中的 finding / paragraph / proposition 集合，以及 token-budget 结果。
- `already exported`：最终 selected set 与 round 绑定清晰，能直接重建 dispatch snapshot。
- `partially exported`：只保留最终拼接后的 context，没有 item 级 selected set。
- `not exported`：最终选中内容不可恢复。

### materialized context
- 最小证据：能恢复实际发给下游 agent 的上下文内容、顺序和截断结果。
- `already exported`：materialized payload、顺序、截断或裁剪信息完整可见。
- `partially exported`：只看到部分 prompt 或只看到 selected set，看不到最终 materialization。
- `not exported`：实际下游上下文不可恢复。

### extraction alignment
- 最小证据：能把上游自由文本 / tool output / evidence 映射到进入 candidate pool 的结构化项。
- `already exported`：存在稳定 provenance 链，可从 extracted item 追溯回 source evidence。
- `partially exported`：只有部分 provenance 字段，或只能人工拼接。
- `not exported`：structured item 与 source evidence 没有可审计对齐关系。

## 2. 工程范围分级

### one-week port
- 主要是读现有日志、补导出、加 schema 映射。
- 不需要改核心执行路径或存储模型。
- 风险集中在字段命名、路径收口、历史兼容。

### one-month effort
- 需要在多个 runtime 节点补 trace、补事件 schema、补 round-level 关联键。
- 需要少量回放或数据迁移脚本，但不重构系统核心控制流。
- 风险集中在跨模块联动和历史数据不一致。

### multi-month project
- 需要改核心 runtime 架构、事件模型、memory / extraction / dispatch 边界，或新增长期存储层。
- 需要系统性重放、兼容治理、或跨团队协作。
- 风险已经超出“导出 trace”范畴，属于架构级 observability 改造。

## 3. 审计记录模板

每个字段至少记录：
- `field_name`
- `availability_status`
- `minimum_evidence_found`
- `current_export_path_or_api`
- `missing_pieces`
- `round_binding_present`
- `stable_item_id_present`
- `provenance_chain_present`
- `engineering_scope`
- `blocking_dependencies`
- `notes`

## 4. 拿到代码路径后的执行方式

1. 先找 round-level source of truth：event log、dispatch snapshot、selector trace、prompt materialization。
2. 对 5 个字段逐项打勾，只记录“能否恢复”与“恢复成本”，不要先做大改实现。
3. 每项只给一个主结论：`already exported`、`partially exported`、或 `not exported`。
4. 最后汇总一页 availability map，并给出总工程量结论：
   `one-week port`、`one-month effort`、或 `multi-month project`。

## 5. 当前限制

- 当前仓库还没有绑定的 openWorker 代码路径。
- 因此本文件不输出 availability 结论，只提供方法和判定口径。
