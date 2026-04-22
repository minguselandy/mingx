# Project Working Contract

## Language and collaboration mode
- 默认使用中文交流。
- 默认进入 implementation-first / vibe coding 协作模式，但若用户明确要求 review、纯分析、brainstorming 或问答，则以用户意图为准。
- 优先给出最小可运行闭环，不先做大而全抽象。
- 顺着 gate 和依赖图推进：先上游、后下游；先可运行、后优雅。
- 每一步尽量产出可复用 artifact，例如 `json`、`csv`、`parquet`、`md`、`script`。

## Working surface
- 当前工作目录 `.`（仓库根目录）是实现、配置和运行入口。
- `docs/` 下的文档当前分为两个子目录：`docs/protocols/`（当前生效协议）和 `docs/archive/`（历史草稿/归档材料）。
- `artifacts/phase0/`、`configs/runs/`、`reference/files/` 是当前运行输入、run plan 和旧 `files/` 参考材料的主要来源。
- 优先复用仓库内已有协议文档、run plan、脚本和 artifact，而不是重新发明接口或重新录入规格。

优先读取的现有 artifact：
- `docs/protocols/phase0-specification.md`
- `docs/protocols/phase1-protocol.md`
- `docs/protocols/phase2-design.md`
- `docs/protocols/execution-readiness-checklist.md`
- `docs/archive/paper-draft-v5.5-taskB-final-gemini-minimal-q7revised-polish2.md`
- `data_prep.py`
- `reference/files/data_prep.py`
- `reference/files/data_prep.json`
- `artifacts/phase0/sample_manifest_v1.json`
- `artifacts/phase0/content_hashes.json`

## Document precedence
当规格文档之间存在张力时，按下面顺序解释，只指出影响当前执行的问题：

1. `docs/protocols/execution-readiness-checklist.md`
   负责 gate 顺序、下一可执行动作、并行 sidecar 的阻塞关系。
2. `docs/protocols/phase1-protocol.md`
   负责可执行测量流程、数据准备、log-prob、bridge、annotation 的实施细节。
3. `docs/protocols/phase0-specification.md`
   负责锁定 domain、granularity、budget、design invariant、known limitation。
4. `docs/protocols/phase2-design.md`
   负责后续 pilot/full-study 的统计和设计约束，但不要提前把项目推进成完整 Phase 2/4 实验平台。
5. `docs/archive/paper-draft-v5.5-taskB-final-gemini-minimal-q7revised-polish2.md`
   只用于研究 framing、术语和“不该跑偏成什么论文”。

## Current project priority
当前主目标是：MuSiQue Gate 1 pre-execution provisioning 和 Phase 0/1 scaffold alignment。

当前执行顺序：
1. 锁定并验证 Phase 0 / Gate 1 上游 artifact
   `artifacts/phase0/content_hashes.json`、`artifacts/phase0/sample_manifest_v1.json`、最小 smoke validation。
2. 建立 sample manifest loader 和基础 schema 对齐。
3. 建立 forced-decode answer log-prob scoring interface。
4. 建立 paragraph-order permutation 下的 `delta_loo` / LCB aggregation。
5. 建立 bridge regression、tertile stratification、tolerance band 流水线。
6. 在 Gate 1-3 条件满足后，再推进 retrieval simulation 和 Phase 3 analytical post-processing。

sidecar：
- openWorker infrastructure audit
- candidate pool / greedy trace / selected set / materialized context / extraction alignment 的可观测性核对

注意：
- sidecar 不能阻塞主线程。
- 不要先搭大而全实验平台。
- 不要把大量时间花在论文措辞打磨上，除非用户明确要求。

## Phase and gate boundaries
### Phase 0 / Gate 1
- 目标是数据锁定、可复现和执行前 provisioning。
- 优先完成：
  - MuSiQue data acquisition / loading
  - content hash 固定
  - hop-stratified sample manifest 复现
  - Phase 0 artifact 校验
  - Phase 1 所需依赖、接口、预算、存储和最小 smoke test
- 不要把 Phase 0 的结果写成已经完成了 hypothesis test。

### Phase 1
- 目标是 measurement apparatus / feasibility probe。
- 它验证的是 measurement chain 的稳定性、bridge 可用性、automated-to-expert substitution fidelity。
- 不要误写成已经完成 extraction-uniformity hypothesis test。
- 当前 variance source 锁定为 paragraph-order permutation；如要引入 composition variation，必须明确说明是在做扩展而非当前默认协议。

### Phase 2 / Phase 3
- 主要用于 downstream design / pilot analytical post-processing。
- 不要在 Gate 1-3 尚未完成时提前写 full-study 平台。

## Research framing constraints
论文定位已经锁定，不要把项目推进成：
- system paper
- memory paper
- 泛 context engineering paper
- PID paper

当前论文定位：
- formal object：per-round、per-agent、token-budgeted context/content selection，目标函数为 predictive V-information
- conditional theory：weak-submodular / pairwise-additive complementarity regime
- bridge statement：formal objective / proxy measurement / runtime heuristic 三层分离
- deployment-facing contribution：verification / monitoring / escalation
- extraction / runtime / memory：仅为 supporting / bridge-risk layers

## File and code strategy
- 优先小步修改。
- 优先改当前 gate 最相关文件，不做无关重构。
- 不要在没有明确收益时扩目录树。
- 优先复用仓库内现有脚本和 artifact，尤其是 `docs/protocols/`、`docs/archive/`、`artifacts/phase0/`、`configs/runs/`、`reference/files/` 下的内容，再决定是否迁移或精简。
- measurement/event store 使用 append-only 思路。
- 确定性派生产物可以 overwrite，或明确做 versioned snapshot；不要把所有中间文件都做成追加式。
- checkpoint 只做恢复辅助，event log 才是 source of truth。
- 每完成一个模块，优先补 smoke test 或最小验证脚本。

## Multi-agent / delegation policy
借鉴 ECC 的管理思想，但在 Codex 中只做最小角色化管理。
- 主线程阻塞任务优先本地直接完成，不先委派。
- 只把明确、边界清晰、非关键路径任务交给 sidecar role。
- `explorer`：只读探索
- `reviewer`：只读审查
- `docs_researcher`：只读文档/规格核对

不要为了“看起来更 agentic”而过度拆任务。

## Output preference
默认响应格式：
1. 极简复述当前状态
2. 给出 3–6 步最小开发计划
3. 明确下一步 artifact
4. 直接进入代码、脚本、目录结构、数据流推进

除非用户要求，否则不要先写长篇分析。

## Git and delivery
- 默认在本轮完成代码与验证后直接执行本地 commit 和远端 push，除非用户明确要求不要提交或不要 push。
- push 前仍需保持最小安全检查：不要提交 `.env`、API key、cache、checkpoint、临时文件或其他本地 secret。
- 若当前机器上的 `git` 不在 PATH 中，可以使用已安装的 `git` 绝对路径继续完成提交与 push；不要因为 PATH 问题中断交付。
- 若 push 失败，优先报告阻塞原因并保留已完成的本地提交状态。
