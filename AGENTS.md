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
- `docs/protocols/` 是当前协议主入口；`docs/archive/final_paper_context_projection_submission_final_v8.md` 是当前论文 framing anchor，其他 `docs/archive/` 草稿仅作为历史参考。
- `api/` 是当前 provider/profile、backend 工厂和 API smoke 工具的统一入口；涉及模型切换或 API 接入时优先从这里收口。
- `artifacts/phase0/`、`configs/runs/`、`reference/files/` 是当前运行输入、run plan 和旧 `files/` 参考材料的主要来源。
- `.env.example` 记录当前推荐的 secret 与 `API_*` 覆盖模板。

优先读取的现有 artifact：
- `docs/protocols/phase0-specification.md`
- `docs/protocols/phase1-protocol.md`
- `docs/protocols/phase2-design.md`
- `docs/protocols/execution-readiness-checklist.md`
- `docs/archive/final_paper_context_projection_submission_final_v8.md`
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
5. `docs/archive/final_paper_context_projection_submission_final_v8.md`

规范约束优先级：
- `docs/protocols/phase0-specification.md` 锁定 domain、granularity、budget、design invariant、known limitation。
- `docs/protocols/phase2-design.md` 提供 downstream 统计和设计边界；不要在 Gate 1-3 前提前把项目推进成完整 Phase 2/4 平台。
- `docs/protocols/phase1-protocol.md` 和 `docs/protocols/execution-readiness-checklist.md` 负责把工作落成可执行步骤，但不能静默覆盖 Phase 0 / Phase 2 已锁定的不变量或边界。
- `docs/archive/final_paper_context_projection_submission_final_v8.md` 控制当前研究 framing、术语和“不该跑偏成什么论文”；旧 paper draft 只作为 historical archive，不再作为 canonical anchor。

### Paper framing vs execution contract
- final v8 论文控制研究边界：conditional theory、formal/proxy/pipeline/runtime 分层、bridge statement、verification / monitoring / escalation，以及 extraction 作为 `M* -> M` bridge risk。
- protocol、run plan、`run_summary.json` 和 `events.jsonl` 控制执行判断：某次 run 是否 complete、green、pilot-only、contamination failed 或 measurement-validated，不由论文措辞直接决定。
- 若论文 runtime interface 和当前代码之间存在差距，默认把 `ProjectionPlan`、`BudgetWitness`、`MaterializedContext` 理解为目标 auditable interface / future alignment target，不要假定当前实现已经完整具备。
- 不要为了贴合论文叙事去改 source question 或 primary answer-serving path；rewrite、replacement、compression、memory formation 都应保持 sidecar / derived-view 语义，并带 lineage。

若动作调度优先级与规范约束发生张力，选择“不违反 invariant 的最近一步可执行动作”，并只指出影响当前执行的冲突。

### Research framing guardrails
论文定位已经锁定，不要把项目推进成：
- system paper
- memory paper
- 泛 context engineering paper
- PID paper

当前论文定位：
- formal object：per-round、per-agent、token-budgeted context/content selection，目标函数为 predictive V-information
- conditional theory：weak-submodular / pairwise-additive complementarity regime，作为 conditional theory + verification protocol，而不是已证明的 deployed-system end-to-end guarantee
- bridge statement：formal objective / proxy measurement / runtime heuristic / runtime artifact 四层分离
- deployment-facing contribution：verification / monitoring / escalation
- extraction：`M* -> M` bridge risk 和 testable bottleneck，不是 weak-submodular theorem 的自动延伸
- runtime / memory：仅为 supporting / bridge-risk layers；memory 可以影响 candidate pool，但不是当前形式化主对象

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
当前主目标是：Phase 1 reduced-scope runtime hardening、contamination triage / follow-up sidecar 收口，以及 final v8 论文 framing 与现有 runtime artifact / protocol 的边界对齐。

### Current execution order
1. 先把当前 live / reduced-scope artifacts 解释清楚：工程链路可运行不等于 scientific pass，contamination-failed 或 partial protocol-full-live artifacts 不得写成 `measurement_validated`。
2. 继续收紧 contamination triage、operator decision、same-hop replacement 和 follow-up package 的 sidecar workflow；不得修改已经完成的 failed source run。
3. 核对 `run_summary.json`、`events.jsonl`、contamination / bridge / annotation exports 是否能表达当前 runtime resolution、gate status、lineage 和 approval state。
4. 将 final v8 的 runtime interface 要求映射到现有 artifact 表面，优先形成最小对齐说明；不要提前重构为完整 `ProjectionPlan` / `BudgetWitness` / `MaterializedContext` 平台。
5. 只有在 reduced-scope follow-up 的人审批准、lineage 和最小安全检查齐备后，才考虑新的 follow-up run。
6. protocol-full live 或 Phase 2/3 解释必须等待对应 gate 条件成立，不从 partial artifact 或 paper framing 越级推出科学结论。

### Current sidecar
- contamination review / rewrite / replacement / follow-up package lane
- compression、memory formation、derived-view 相关的双路语义核对
- openWorker candidate pool / greedy trace / selected set / materialized context / extraction alignment 的可观测性核对

### Current do-not-do-yet
- sidecar 不能阻塞主线程。
- 不要先搭大而全实验平台。
- 不要提前把项目推进成完整 Phase 2/4 full-study 平台。
- 不要把 partial `artifacts/phase1/protocol_full_live/` 或 reduced-scope live run 当作 completed scientific result。
- 不要把论文 runtime interface 直接写成已实现 API。
- 不要为了让回答更容易而修改 primary source question；问题 rewrite / replacement 只能作为带 lineage 的 sidecar / follow-up 工作。

### Current phase and gate boundary interpretation
- `Phase 0 / Gate 1` 的目标是数据锁定、可复现和执行前 provisioning；优先完成 MuSiQue data acquisition / loading、content hash 固定、hop-stratified sample manifest 复现、Phase 0 artifact 校验，以及 Phase 1 所需依赖、接口、预算、存储和最小 smoke test。
- `Phase 1` 的目标是 measurement apparatus / feasibility probe。它验证 measurement chain 的稳定性、bridge 可用性、automated-to-expert substitution fidelity；不要误写成已经完成 extraction-uniformity hypothesis test。当前默认 variance source 仍锁定为 paragraph-order permutation；若引入 composition variation，必须明确说明是在做扩展而非当前默认协议。
- `Phase 2 / Phase 3` 主要用于 downstream design / pilot analytical post-processing。在 Gate 1-3 尚未完成前，不要提前写 retrieval simulation 的正式结论或 full-study 平台。

## Gate completion / definition of done (current Phase 1 reduced-scope / follow-up)

本节同样是 current / time-sensitive；如果当前 gate 目标变化，应优先更新这里。

当前阶段至少在满足以下条件时，才算完成并可进入下一步：
- 当前 reduced-scope / partial live artifacts 已被正确标注：`pipeline_status`、`measurement_status`、contamination gate、annotation state、bridge state 和 `resolved_runtime`（若为新导出）能在 `run_summary.json` / `events.jsonl` / exports 中追踪；旧 artifact 缺字段时必须明确说明是历史导出而非协议变化。
- contamination-failed run 保持 scientific stop：不得自动 rerun、不得自动 restrict、不得自动升级到 `measurement_validated`；review / rewrite / replacement 只能作为 human-in-the-loop sidecar。
- follow-up package 若继续使用，必须具备最小安全闭环：source run 不被改写、same-hop replacement lineage 可审计、operator signoff 状态明确、`execution_ready` 不被误读、失败 source run 的 scientific status 不被 retroactively 修改。
- final v8 论文 framing 已映射到文档入口：formal/proxy/pipeline/runtime 分层、`M* -> M` extraction risk、verification / escalation，以及 `ProjectionPlan` / `BudgetWitness` / `MaterializedContext` 作为目标 runtime interface 的边界被清楚写出。
- protocol-full live 或 Phase 2/3 推进前，必须重新核对 active protocol、run plan、budget、annotation、contamination 和 bridge gate；partial artifact 或 reduced-scope pilot 不能被当作 full scientific completion。
- 当前阶段完成仍只表示 runtime scaffold / triage / follow-up readiness 成立；不能把结果表述成 hypothesis test 已完成，也不能写成 extraction-uniformity 已被验证。
