# Project Agent Contract

本文件是供 Codex / agent 长期遵循的协作契约。
- `Stable working contract` 放长期有效规则。
- `Current run brief` 与 `Gate completion / definition of done` 放当前阶段、time-sensitive 内容。
- 若未来项目状态变化，优先更新 time-sensitive 小节，而不是改动稳定协作规则。
- 发生张力时：当前执行顺序以 current run brief 和 checklist 决定；长期边界、设计不变量和安全基线以 stable contract 与锁定协议为准。

## Stable working contract

### Language and collaboration mode
- 默认使用中文交流。
- 默认进入 implementation-first / vibe coding 协作模式，但若用户明确要求 review、纯分析、brainstorming 或问答，则以用户意图为准。

### Execution posture
- 优先给出最小可运行闭环，不先做大而全抽象。
- 顺着 gate 和依赖图推进：先上游、后下游；先可运行、后优雅。
- 优先复用仓库内已有 protocol、script、run plan 和 artifact，而不是重新发明接口或重新录入规格。
- 每一步尽量产出可复用 artifact，例如 `json`、`csv`、`parquet`、`md`、`script`。
- 每完成一个模块，优先补 smoke test 或最小验证脚本。

### Working surface and reuse
- 当前工作目录 `.`（仓库根目录）是实现、配置和运行入口。
- `docs/protocols/` 是当前协议主入口；`docs/archive/` 仅作为历史草稿、framing 和归档材料。
- `api/` 是当前 provider/profile、backend 工厂和 API smoke 工具的统一入口；涉及模型切换或 API 接入时优先从这里收口。
- `artifacts/phase0/`、`configs/runs/`、`reference/files/` 是当前运行输入、run plan 和旧 `files/` 参考材料的主要来源。
- `.env.example` 记录当前推荐的 secret 与 `API_*` 覆盖模板。

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

### Document precedence and conflict handling
把优先级拆成两层，避免把执行清单误读成可以覆盖设计不变量。

执行动作调度优先级：
1. `docs/protocols/execution-readiness-checklist.md`
2. `docs/protocols/phase1-protocol.md`
3. `docs/protocols/phase0-specification.md`
4. `docs/protocols/phase2-design.md`
5. `docs/archive/paper-draft-v5.5-taskB-final-gemini-minimal-q7revised-polish2.md`

规范约束优先级：
- `docs/protocols/phase0-specification.md` 锁定 domain、granularity、budget、design invariant、known limitation。
- `docs/protocols/phase2-design.md` 提供 downstream 统计和设计边界；不要在 Gate 1-3 前提前把项目推进成完整 Phase 2/4 平台。
- `docs/protocols/phase1-protocol.md` 和 `docs/protocols/execution-readiness-checklist.md` 负责把工作落成可执行步骤，但不能静默覆盖 Phase 0 / Phase 2 已锁定的不变量或边界。
- `docs/archive/paper-draft-v5.5-taskB-final-gemini-minimal-q7revised-polish2.md` 只用于研究 framing、术语和“不该跑偏成什么论文”。

若动作调度优先级与规范约束发生张力，选择“不违反 invariant 的最近一步可执行动作”，并只指出影响当前执行的冲突。

### Research framing guardrails
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

### File and code strategy
- 优先小步修改。
- 优先改当前 gate 最相关文件，不做无关重构。
- 不要在没有明确收益时扩目录树。
- 涉及 provider/model 或 API 切换时，优先修改 `api/settings.py`、`api/backends.py`、`api/README.md`，不要把 provider 分支散落到 `cps/runtime`。
- 优先复用仓库内现有脚本和 artifact，尤其是 `docs/protocols/`、`docs/archive/`、`artifacts/phase0/`、`configs/runs/`、`reference/files/` 下的内容，再决定是否迁移或精简。
- measurement/event store 使用 append-only 思路。
- 确定性派生产物可以 overwrite，或明确做 versioned snapshot；不要把所有中间文件都做成追加式。
- checkpoint 只做恢复辅助，event log 才是 source of truth。

### Multi-agent / delegation policy
借鉴 ECC 的管理思想，但在 Codex 中只做最小角色化管理。
- 主线程阻塞任务优先本地直接完成，不先委派。
- 只把明确、边界清晰、非关键路径任务交给 sidecar role。
- `explorer`：只读探索
- `reviewer`：只读审查
- `docs_researcher`：只读文档 / 规格核对

不要为了“看起来更 agentic”而过度拆任务。sidecar 不能阻塞主线程。

### Output preference
默认响应格式：
1. 极简复述当前状态
2. 给出 3-6 步最小开发计划
3. 明确下一步 artifact
4. 直接进入代码、脚本、目录结构、数据流推进

除非用户要求，否则不要先写长篇分析。

### Git and delivery baseline
- 默认在本轮完成代码与验证后整理出可审阅的本地改动；如合适，可以直接准备本地 commit。
- 只有在用户未禁止、最小安全检查通过、且远端策略允许时才执行 push。
- push 前仍需检查：不要提交 `.env`、API key、cache、checkpoint、临时文件或其他本地 secret。
- 若当前机器上的 `git` 不在 PATH 中，可以使用已安装的 `git` 绝对路径继续完成本地提交；不要因为 PATH 问题中断交付。
- 若 push 失败，保留已完成的本地 commit，并优先汇报阻塞原因。

## Current run brief (time-sensitive)

本节是 current / time-sensitive 内容。若未来项目状态变化，优先更新这一节，而不是改动 `Stable working contract`。

### Current main target
当前主目标是：MuSiQue Gate 1 pre-execution provisioning 和 Phase 0/1 scaffold alignment。

### Current execution order
1. 锁定并验证 Phase 0 / Gate 1 上游 artifact：
   `artifacts/phase0/content_hashes.json`、`artifacts/phase0/sample_manifest_v1.json`、最小 smoke validation。
2. 建立 sample manifest loader 和基础 schema 对齐。
3. 建立 forced-decode answer log-prob scoring interface。
4. 建立 paragraph-order permutation 下的 `delta_loo` / LCB aggregation。
5. 建立 bridge regression、tertile stratification、tolerance band 流水线。
6. 仅在 Gate 1-3 条件满足后，再推进 retrieval simulation 和 Phase 3 analytical post-processing。

### Current sidecar
- openWorker infrastructure audit
- candidate pool / greedy trace / selected set / materialized context / extraction alignment 的可观测性核对

### Current do-not-do-yet
- sidecar 不能阻塞主线程。
- 不要先搭大而全实验平台。
- 不要提前把项目推进成完整 Phase 2/4 full-study 平台。
- 不要把大量时间花在论文措辞打磨上，除非用户明确要求。

### Current phase and gate boundary interpretation
- `Phase 0 / Gate 1` 的目标是数据锁定、可复现和执行前 provisioning；优先完成 MuSiQue data acquisition / loading、content hash 固定、hop-stratified sample manifest 复现、Phase 0 artifact 校验，以及 Phase 1 所需依赖、接口、预算、存储和最小 smoke test。
- `Phase 1` 的目标是 measurement apparatus / feasibility probe。它验证 measurement chain 的稳定性、bridge 可用性、automated-to-expert substitution fidelity；不要误写成已经完成 extraction-uniformity hypothesis test。当前默认 variance source 仍锁定为 paragraph-order permutation；若引入 composition variation，必须明确说明是在做扩展而非当前默认协议。
- `Phase 2 / Phase 3` 主要用于 downstream design / pilot analytical post-processing。在 Gate 1-3 尚未完成前，不要提前写 retrieval simulation 的正式结论或 full-study 平台。

## Gate completion / definition of done (current Gate 1)

本节同样是 current / time-sensitive；如果当前 gate 目标变化，应优先更新这里。

当前 `Gate 1` 至少在满足以下条件时，才算完成并可进入下一步：
- `artifacts/phase0/content_hashes.json` 可校验：仓库内加载的 MuSiQue working split、`phase0.yaml` 的 `split` / `seed` 配置、以及 `content_hashes.json` 中记录的 dataset hash / manifest version / sampling seed 之间没有未解释的不一致。
- `artifacts/phase0/sample_manifest_v1.json` 可加载且 schema 对齐：至少可以被仓库现有 loader / validator（如 `phase0.load_manifest`、`phase0.validate_manifest`）读取，并与当前 `phase1.v1` manifest 结构、hop-stratified 计数、paragraph pool range、以及基础 question / paragraph 字段保持一致。
- 最小 smoke validation 可运行：仓库现有 smoke 入口能够在不改协议假设的前提下完成一次最小闭环，验证 manifest、hash、基础 measurement / export 路径与事件存储可以贯通。
- Phase 1 所需依赖 / 接口 / 预算 / 存储具备最小可执行闭环：至少已经打通 provider/profile 解析、forced-decode log-prob 接口、append-only measurement/event store、基础 run plan wiring、以及最小恢复 / 重跑路径；可以进入真正的 Phase 1 scaffold implementation，而不是停留在静态规格阶段。
- Gate 1 的完成仍只表示 provisioning 和 execution-readiness 成立；不能把当前结果表述成 hypothesis test 已完成，也不能写成 extraction-uniformity 已被验证。
