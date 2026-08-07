# Omni-Brain 当前工作台

> **用途：** 新会话用本页恢复“现在做什么、做到哪里、下一步是什么”。
> **更新时间：** 2026-08-07。
> **实验真值：** 用例、版本、分数和证据统一查[实验与评测总账](../eval/STATUS.md)。

## 当前判断

Omni-Brain 要形成一套可移植、Codex/OpenCode 兼容、换模型后仍能工作的知识与任务 Harness。

M1“知识整理与摄入”已经完成首个真实闭环：混乱材料经过候选整理、用户审查、正式发布、干净会话消费和跨模型重放，成为**人能浏览、AI 能回答、来源可追溯并可继续演进**的正式知识。当前成熟度是 `Verified@quality-check-incremental-slice`，不能外推为跨领域或所有宿主均已验证。

开发优先路线已经取得三个真实质检开发切片。M2“可信查询与任务上下文”也已形成第一个限定范围闭环：10 条真实问题的确定性知识入口路由全部命中，两条未见过的人员/权限与交付状态问题由较弱模型实际调用路由器后取得 `10/10`，且没有宽泛搜索和文件修改。当前成熟度为 `Verified@quality-check-trusted-query-slices`，只适用于当前中文 Markdown、单一质检领域和最多三篇规范页。

M4“代码变化到知识回写”已完成第二个相邻代码切片，但仍未验证：快照导入回写由 `17/24` 提升到 `20/24`，同时暴露旧版本句子未清理、可运行命令缺失、公共能力漏更新和固定夹具边界丢失。当前主线因此不再分别追加问答题或回写题，而是进入一个**开发复合工况**：可信任务上下文 → 真实代码工作 → 项目运行验证 → 知识变化候选。

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

## 当前可信查询切片

[可信知识问答薄切片](specs/m2-trusted-query-thin-slice.md)已经完成四类基础问答、两轮停止规则回归、10 条确定性路由评测和两条路由集成盲测。

- 第一组学习、现状/未知、版本冲突、开发上下文问题为 `22/24`，证明答案内容可用，也暴露复杂开发问题会无界阅读；
- 路由器 `knowledge_route.py` 只遍历正式导航可达知识，为问题返回一个主入口和有差异的候补，在固定 10 条质检路线中为 `10/10`；
- 集成盲测中，人员历史/权限与交付四状态问题均为 `5/5`，只读两篇页面、无宽泛搜索、无失败命令、零文件修改；
- 路由器达到 `Verified@quality-knowledge-ten-route-slice`，Skill 与路由组合达到 `Verified@quality-check-personnel-and-delivery-pair`；尚未验证第二领域、OpenCode、英文/混合语言、大知识库、精确源码联查和关系型多跳。

详细证据见[知识入口路由评测](../eval/reports/real_work/knowledge-route-quality-v1-2026-08-07.md)和[路由集成盲测](../eval/trials/real_work/TRUSTED_KNOWLEDGE_ANSWER_ROUTER_CODEX_LUNA_HARNESS_001/audit.md)。

## 当前代码回写切片

[代码变化到知识回写](../eval/fixtures/real_work/code_to_knowledge_writeback_v1/README.md)已经完成强参考与四轮 Luna 盲测。第四轮候选 `3a6c5da` 能发现固定验证报告、完整列出 18 个快照字段和 13 个嵌套指标字段、保留源码与报告冲突、区分独立系统，并原位更新数据、采样、软件结构、根入口和两种产品视图；正式知识和代码来源均未修改。

独立内容审计为 `22/24`，关键题未全过：前端 API 行到任务树行的转换责任没有写透，固定报告的代表性运行结果只概括了覆盖面。Trial 后的修正已在相邻的“本地快照导入”变化上重放：第二轮由 `17/24` 提升为 `20/24`，提交祖先、外部契约、软件职责和代表性运行结果的通用修正均生效，但仍有四项关键语义缺口。Harness `a54abcd` 已只收束跨用例成立的完成标准并通过当时的完整回归；当前 `3a9715d` 的 103 项回归通过。完整代码回写仍是**已实现、需要人工审查、尚未 verified**。证据见[首切片第四轮审计](../eval/trials/real_work/CODE_TO_KNOWLEDGE_WRITEBACK_CODEX_LUNA_HARNESS_004/audit.md)和[相邻切片第二轮审计](../eval/trials/real_work/CODE_TO_KNOWLEDGE_WRITEBACK_SNAPSHOT_IMPORT_CODEX_LUNA_HARNESS_002/audit.md)。

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
- 普通知识问答已通过根规则、问答 Skill 和确定性入口路由把读取收束到主入口及必要候补；这是当前质检切片内证据，不外推到源码联查和大规模知识。
- 根 `AGENTS.md` 不写入单次实验细节；摄入步骤留在 Harness Skill，动态证据留在 Eval。
- 近期优先级是开发先产生可用收益；知识摄入、查询、验证和回写随开发切片进入，不扩建平行阶段。
- 质检全部材料、正式知识、当前前后端、架构和历史原型由用例组合覆盖；单个任务只读最低充分来源。

## 下一步

1. 冻结当前 M2 质检问答路线，不为省掉一篇仍相关的候补继续调排序或提示词。
2. 设计并运行一个新的开发复合工况，固定自然语言需求、正式知识、真实代码、项目环境和知识回写边界，验证 M2 → M3 → M4 能否在同一任务中闭环。
3. 若复合工况失败，只修复跨阶段交接中可复现的通用问题；不为单题新增业务专属字段、门禁或检查器。
4. 复合工况可用后，再选择第二领域或 OpenCode 反证可移植性；M4 发布批准与回滚在内容关键题全过后演练。

用户当前无需维护状态或批准每一轮实验；后续只需审视最终业务效果与 Harness 是否具有泛化性。

## 稳定入口

- 长期目标与 C1—C10：[Blueprint](blueprint.md)
- 完整阶段计划：[Master Roadmap](harness-roadmap.md)
- 用例、参考和 Trial：[实验与评测总账](../eval/STATUS.md)
- M1 实现方案：[增量知识摄入方案](specs/m1-incremental-knowledge-ingestion-proposal.md)
