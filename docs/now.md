# Omni-Brain 当前工作台

> **用途：** 新会话用本页恢复“现在做什么、做到哪里、下一步是什么”。
> **更新时间：** 2026-08-07。
> **实验真值：** 用例、版本、分数和证据统一查[实验与评测总账](../eval/STATUS.md)。

## 当前判断

Omni-Brain 要形成一套可移植、Codex/OpenCode 兼容、换模型后仍能工作的知识与任务 Harness。

M1“知识整理与摄入”已经完成首个真实闭环：混乱材料经过候选整理、用户审查、正式发布、干净会话消费和跨模型重放，成为**人能浏览、AI 能回答、来源可追溯并可继续演进**的正式知识。当前成熟度是 `Verified@quality-check-incremental-slice`，不能外推为跨领域或所有宿主均已验证。

开发优先路线已经取得三个真实质检开发切片；当前主线进入 **M4 代码变化到知识回写**。目标不是再造一套更新文档，而是让固定代码事实、运行证据、既有规范知识和产品视图形成隔离、可审查、可拒绝的演进候选。

## 当前可直接使用的发布物

| 发布物 | 路径与版本 | 包含什么 | 用途 |
|---|---|---|---|
| **M1 Harness Release** | `/home/yyh/project/omni-brain-harness`；[`release/m1-ingestion-harness-v1@7e3034c`](https://github.com/pokemonAndCodeMaster/omni-brain/tree/release/m1-ingestion-harness-v1)；标签 `harness-m1-ingestion-v1` | 根规则、Skills、工具、模板、状态工作区、测试和空 OKF 知识骨架 | 已推送公开远端；可单分支克隆到新项目，或直接指定新材料使用 Harness 本体 |
| **开发与回写 Harness RC1** | `/home/yyh/project/omni-brain-harness-release-v1`；[`release/development-writeback-harness-v1@a5104ec`](https://github.com/pokemonAndCodeMaster/omni-brain/tree/release/development-writeback-harness-v1)；标签 `harness-development-writeback-v1-rc1` | M1 摄入、M3 带知识开发、M4 代码回写和空 OKF 骨架 | 已推送；M1/M3 只在声明切片内验证，M4 已真实试用但尚未通过全部内容题 |
| **质检知识集成版** | `/home/yyh/project/omni-brain-harness-quality-check-v1`；`release/m1-quality-knowledge-v1@900cf85` | 同一 Harness 加上用户批准的 33 个 Markdown、24 个概念和两种产品视图 | 浏览首个正式知识成果，并作为 M2 的真实查询输入 |

独立 Harness 已从公开远端重新克隆验证；知识入口仍是 9 个导航页、0 个领域概念，这证明领域答案没有被硬编码。用户从其项目根目录提出自然语言知识摄入请求后，Harness 才会把授权材料整理到隔离候选，产出规范知识、产品视图和 `review.md`，经批准后进入正式知识。

质检集成版的[正式知识入口](../../omni-brain-harness-quality-check-v1/knowledge/index.md)、[领域视图](../../omni-brain-harness-quality-check-v1/knowledge/views/by-domain/quality.md)和[学习/工作旅程](../../omni-brain-harness-quality-check-v1/knowledge/views/by-journey/manual-qc-acceptance.md)用于消费，不再承担“通用 Harness Release”的身份。

## 当前真实开发切片

首个用例是[验收配额可见性](../eval/fixtures/real_work/manual_qc_allocation_visibility_v1/README.md)：让任务分析表同时展示预期分配量、实际分配量和分配达成率，零分母为空，不制造风险阈值。

- 固定基线：`quality-platform-lab@203c785`；
- 参考代码：`/home/yyh/project/quality-platform-lab-reference-allocation-v1` 的 `reference/manual-qc-allocation-visibility-v1@a1aa7a9`；
- 参考说明：[实现、技术取舍与新鲜证据](../eval/reference/real_work/manual_qc_allocation_visibility_v1/README.md)；
- 已通过：17 项 Python、30 项 Vue、14/15 指标边界、类型、生产构建、真实 PostgreSQL/API 与 Edge 渲染；
- 知识处理：只形成[知识变化候选](../eval/reference/real_work/manual_qc_allocation_visibility_v1/knowledge-change-candidate.md)，尚未修改正式知识；
- 基线 Trial：[Luna 审计](../eval/trials/real_work/MANUAL_QC_ALLOCATION_CODEX_LUNA_BASELINE_001/audit.md)；功能与真实页面可用，`16/20`，但正式知识未消费、生产会话未自行跑通数据链、查询上限扩到 16 而非最低 14；
- 开发 Harness：独立仓库 `experiment/development-harness-v1@c7aadc1`；`develop-with-knowledge` 经过三类真实开发切片收敛了最低充分取知、实现前快照、最大组合、真实路径与证据交接；
- 成功 Trial：[`MANUAL_QC_ALLOCATION_CODEX_LUNA_HARNESS_004`](../eval/trials/real_work/MANUAL_QC_ALLOCATION_CODEX_LUNA_HARNESS_004/audit.md)，候选 `e5d734a` 为 `18/20`；14 个不同指标返回 200、15 个返回 422，保存五个问题选项后的 Edge 页面加载 24 个任务；
- 当前状态：参考仍是 `reference_candidate`；开发 Skill 已在同一质检领域三类切片验证，尚未证明跨领域、任意模型或数据写入安全泛化。

这个切片验证的重点不是“两列代码”，而是 Harness 能否让较弱模型发现后端已有能力、只改必要层、用正确环境实际跑通，并准确说明知识影响。

第二个副作用用例[本地 CSV 安全写入快照](../eval/fixtures/real_work/manual_qc_snapshot_csv_import_v1/README.md)也已完成参考和两轮弱模型重放。首轮 `16/20`；加入精确副作用基线和冲突状态验证后为 `17/20`。主要写库路径可用，独立评测确认空/非空人工状态、旧选项、脏批、旧确认和幂等均通过；不完整 JSONB 指标仍会被接受，因此只形成正向证据。完整对照见[第二轮审计](../eval/trials/real_work/MANUAL_QC_SNAPSHOT_IMPORT_CODEX_LUNA_HARNESS_002/audit.md)。

第三个只读性能用例[问题选项 Facet 优化](../eval/fixtures/real_work/manual_qc_question_option_facet_performance_v1/README.md)已完成参考和 Luna 重放。模型在 270 秒内从真实入口与执行计划定位到无关 JSONB 标签展开，只修改一条 Repository SQL；151200 行负载上中位数改善 `19.8%`，独立评测复现约 `20.2%`，正常 3024 行夹具、API、Python、Vue、类型和构建全部通过。Trial 为 `18/20`，缺口是没有聚焦测试和明确知识落点。完整证据见[审计](../eval/trials/real_work/MANUAL_QC_QUESTION_OPTION_FACET_PERF_CODEX_LUNA_HARNESS_001/audit.md)。开发 Skill 因此达到 `Verified@manual-qc-allocation-and-readonly-sql-slices`。

第四个跨层用例[验收分配缺口](../eval/fixtures/real_work/manual_qc_allocation_shortfall_v1/README.md)已完成修订参考和 Luna 盲测。候选用 334 秒打通 Catalog、Repository、HTTP、Vue 和任务表，自主发现 `10 + 5` 最大组合；独立数据库、API 与 Edge 证明 `173 → 26 → 12 → 3` 四级定位、排序和筛选可用。候选还用正式知识和运行事实纠正了首轮专家参考的类别互抵口径。完整证据见[审计](../eval/trials/real_work/MANUAL_QC_ALLOCATION_SHORTFALL_CODEX_LUNA_HARNESS_001/audit.md)。开发 Harness 现为 `Verified@three-manual-qc-development-slices`；下一主线是让这些真实代码变化安全回写正式知识，而不是继续增加开发题。

## 当前代码回写切片

[代码变化到知识回写](../eval/fixtures/real_work/code_to_knowledge_writeback_v1/README.md)已经完成强参考与四轮 Luna 盲测。第四轮候选 `3a6c5da` 能发现固定验证报告、完整列出 18 个快照字段和 13 个嵌套指标字段、保留源码与报告冲突、区分独立系统，并原位更新数据、采样、软件结构、根入口和两种产品视图；正式知识和代码来源均未修改。

独立内容审计为 `22/24`，关键题未全过：前端 API 行到任务树行的转换责任没有写透，固定报告的代表性运行结果只概括了覆盖面。Trial 后的 Harness `ebd696c` 已把这两项改为通用内容要求，95 项回归通过；由于尚未用下一真实切片重放，M4 当前是**已实现、真实试用、尚未 verified**。完整过程与结论见[第四轮审计](../eval/trials/real_work/CODE_TO_KNOWLEDGE_WRITEBACK_CODEX_LUNA_HARNESS_004/audit.md)。

## M1 最终证据

### 正式内容

Luna Trial `M1_INCREMENTAL_CODEX_LUNA_002` 从认证基础知识和固定的 25 份新增材料形成正式内容：

- 25 个材料组、90 项带定位发现、15 个知识主题；
- 相对父知识新增 3 页、原位修改 16 页、删除 0 页；
- 固定内容问题 `24/24`；
- 用户批准后已发布，正式知识可被全新会话直接消费。

### 跨模型重放

Terra Trial `M1_INCREMENTAL_CODEX_TERRA_003` 不读取 Luna 结果或参考答案：

- 通过 6 个可恢复会话完成 25 个材料组和 12 个主题；
- 形成 89 项发现，候选新增 6 页、修改 11 页、删除 0 页；
- 固定内容问题同样为 `24/24`，知识检查通过；
- 文件拓扑不同，但需求交付、人力权限、验收、快照、外部执行、软件分层和公共工作台语义等价可达。

完整比较见[Terra 跨模型审计](../eval/trials/knowledge_ingestion/M1_INCREMENTAL_CODEX_TERRA_003/cross-model-analysis.md)。

## 已经决定

- 同一 Batch 1 和 Batch 2 不再继续调 M1 Prompt、Skill 或后台字段；M1 进入回归维护。
- 已批准的 Luna 结果是正式知识；Terra 的不同拓扑只保留为跨模型证据，不覆盖正式版本。
- 独立 Harness Release 与质检知识集成版分别版本化；知识产物是效果证据和领域资产，不是 Harness 本体。
- 工作台的跨会话游标是必要能力：较弱模型可以分段完成长摄入，不必依赖单次超长上下文。
- 消费会话仍会读取过多知识页和项目状态文件；这是 M2 查询与上下文问题，不继续扩建 M1。
- 根 `AGENTS.md` 不写入单次实验细节；摄入步骤留在 Harness Skill，动态证据留在 Eval。
- 近期优先级是开发先产生可用收益；知识摄入、查询、验证和回写随开发切片进入，不扩建平行阶段。
- 质检全部材料、正式知识、当前前后端、架构和历史原型由用例组合覆盖；单个任务只读最低充分来源。

## 下一步

1. 不再对 `qpl-gap-ref@35948ae` 同题追加提示词或专用检查器；保留第四轮为 `22/24` 的真实边界。
2. 选择一个相邻但不同的代码变化，验证 `ebd696c` 能否让弱模型写清数据转换并充分内化固定运行结果。
3. 若相邻切片内容全过，再把 M4 升级为限定范围 verified，并演练人工批准、正式发布与回滚；否则只修复新切片复现的通用失败。
4. 随后进入 M2 可信查询/最低充分上下文，或用第二领域、第二宿主验证 M5 可移植性。

用户当前无需维护状态或批准每一轮实验；后续只需审视最终业务效果与 Harness 是否具有泛化性。

## 稳定入口

- 长期目标与 C1—C10：[Blueprint](blueprint.md)
- 完整阶段计划：[Master Roadmap](harness-roadmap.md)
- 用例、参考和 Trial：[实验与评测总账](../eval/STATUS.md)
- M1 实现方案：[增量知识摄入方案](specs/m1-incremental-knowledge-ingestion-proposal.md)
