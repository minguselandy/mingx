# Project Working Contract

## Language and collaboration mode
- 默认使用中文交流。
- 默认进入 implementation-first / vibe coding 协作模式，但若用户明确要求 review、纯分析、brainstorming 或问答，则以用户意图为准。
- 优先给出最小可运行闭环，不先做大而全抽象。
- 顺着 gate 和依赖图推进：先上游、后下游；先可运行、后优雅。
- 每一步尽量产出可复用 artifact，例如 `json`、`csv`、`parquet`、`md`、`script`。

## Working surface
- 当前工作目录 `phase0-config-starter/` 是干净的实现和配置落点。
- 工作区级 `files/` 目录是当前规格和现有 artifact 的主要来源。
- 优先复用 `files/` 中已有内容，而不是重新发明接口或重新录入规格。

优先读取的现有 artifact：
- `C:\Users\Mingx\Documents\mx-codex\files\phase0-specification.md`
- `C:\Users\Mingx\Documents\mx-codex\files\phase1-protocol.md`
- `C:\Users\Mingx\Documents\mx-codex\files\phase2-design.md`
- `C:\Users\Mingx\Documents\mx-codex\files\execution-readiness-checklist.md`
- `C:\Users\Mingx\Documents\mx-codex\files\data_prep.py`
- `C:\Users\Mingx\Documents\mx-codex\files\data_prep.json`
- `C:\Users\Mingx\Documents\mx-codex\files\sample_manifest_v1.json`
- `C:\Users\Mingx\Documents\mx-codex\files\content_hashes.json`

## Document precedence
当规格文档之间存在张力时，按下面顺序解释，只指出影响当前执行的问题：

1. `execution-readiness-checklist.md`
   负责 gate 顺序、下一可执行动作、并行 sidecar 的阻塞关系。
2. `phase1-protocol.md`
   负责可执行测量流程、数据准备、log-prob、bridge、annotation 的实施细节。
3. `phase0-specification.md`
   负责锁定 domain、granularity、budget、design invariant、known limitation。
4. `phase2-design.md`
   负责后续 pilot/full-study 的统计和设计约束，但不要提前把项目推进成完整 Phase 2/4 实验平台。
5. paper draft
   只用于研究 framing、术语和“不该跑偏成什么论文”。

## Current project priority
当前主目标是：MuSiQue Gate 1 pre-execution provisioning 和 Phase 0/1 scaffold alignment。

当前执行顺序：
1. 锁定并验证 Phase 0 / Gate 1 上游 artifact
   `content_hashes.json`、`sample_manifest_v1.json`、最小 smoke validation。
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
- 优先复用 `files/` 下现有脚本和 artifact，再决定是否迁移或精简到 starter。
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
- 当用户明确要求“做完后提交到 GitHub”时，默认在本轮完成代码与验证后直接执行本地 commit 和远端 push，不额外停下来重复确认。
- push 前仍需保持最小安全检查：不要提交 `.env`、API key、cache、checkpoint、临时文件或其他本地 secret。
- 若当前机器上的 `git` 不在 PATH 中，可以使用已安装的 `git.exe` 绝对路径继续完成提交与 push；不要因为 PATH 问题中断交付。
- 若 push 失败，优先报告阻塞原因并保留已完成的本地提交状态。
