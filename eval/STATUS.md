# Omni-Brain 实验与评测总账

> **作用**：这是“有哪些用例、输入是什么、参考成果在哪里、跑过哪些模型、结果如何、下一步做什么”的唯一状态入口。
> **更新时间**：2026-08-14。
> **边界**：Blueprint 说明系统由什么组件构成；路线图说明能力怎样递进；本页只管理实际用例、参考成果和 Trial 状态。

> **历史工作区**：2026-08-09 起，已完成 Trial 的顶层候选/参考目录不再长期保留。历史 manifest 中的绝对执行路径可能已经清理；对应 Git 树统一归档在本设计仓 `refs/eval/workspaces/<原工作区目录名>`，Prompt、轨迹、最终回答和审计仍保存在 `eval/trials/`。新的现场统一创建在 `/home/yyh/project/.omni-brain-runs/` 并在封存后回收。

## 1. 当前结论

- M1“知识整理与摄入”已经完成首个质检增量文档切片闭环：内容通过、用户批准、正式发布、干净消费、86 项回归和跨模型重放均有证据。成熟度为 **Verified@quality-check-incremental-slice**，不是跨领域或全宿主 Verified。
- 当前独立 Harness Release 位于 `/home/yyh/project/omni-brain-harness`，远端为 `github.com/pokemonAndCodeMaster/omni-brain` 的 `release/m1-ingestion-harness-v1@7e3034c`，标签为 `harness-m1-ingestion-v1`；公开单分支重克隆后的空知识检查和 86 项回归通过，不预装质检答案。
- 质检知识集成版位于 `/home/yyh/project/omni-brain-harness-quality-check-v1` 的 `release/m1-quality-knowledge-v1` 分支，提交 `900cf85`；包含 33 个 Markdown、24 个概念和两种产品视图，是 M1 产物与 M2 查询输入，不是通用 Harness 本体。
- Luna Trial 002 是获批正式内容：25 个材料组、90 项发现、15 个主题、内容 `24/24`。Terra Trial 003 在同一 Harness 与输入上通过 6 个可恢复会话形成另一份 `24/24` 候选，证明结果不只依赖 Luna 单次长会话。
- 固定 Luna 内容 Trial 的模型提交 `ed93abe` 为 `20/24`、无核心题为 0，首次达到当前基础文档内容线。审计发现模型手写来源索引存在路径错误，未直接发布；通用修复后可审阅候选为 `0225003`，候选领域地图下的知识检查通过。
- 同一 Batch 1 和 Batch 2 不再继续做 Prompt、Skill 或后台字段微调。M1 进入维护状态；近期改为开发优先的组合切片，在真实开发中同步验证 M2 查询、M3 实现和 M4 知识变化候选。
- 首个开发用例“验收配额可见性”已收敛到首个 Harness 验证切片。修订参考为 `a1aa7a9`；Luna 无专项 Skill 基线 `ab5d448` 为 `16/20`。开发 Skill 两版因跳过最大组合分别得到 `15/20`、`14/20`；加入实现前快照的 `acffe26` 让同一模型自主得到候选 `e5d734a`（`18/20`），14/15 实际 API、五个固定选项与 Edge 页面通过。该能力为 `Verified@manual-qc-allocation-slice`，下一步换排障用例反证。
- “页面/API范围差异排障”已完成无专项 Skill 基线：Luna 在 165 秒内用 Service、HTTP 与 PostgreSQL 日行复现 `2629/2575` 和 `516/499`，正确证明差异来自空 Scope 与页面日期 Scope，保持零文件修改，结果 `18/20`。该工况不新增排障 Skill；它被保留为“没有 Bug 时不制造改动”的回归用例。
- “本地 CSV 安全写入快照”已完成强参考和两轮同题弱模型 Trial。首轮为 `16/20`，暴露动态 `seed` 破坏夹具身份及显式 `null` 被覆盖；15 行通用副作用规则使第二轮达到 `17/20`，停止重建数据、补充聚焦测试，独立真实库确认空/非空状态、旧选项、整批拒绝、失效确认与幂等写入均通过。解析器仍接受不完整 JSONB 指标，因此只记为数据写入正向证据，不升级开发 Skill 的采用级别。
- “问题选项 Facet 性能优化”已完成强参考与 Luna 重放。弱模型沿真实页面请求、Repository 和执行计划找到无关 JSONB 标签展开，只改一条 SQL，在 151200 行固定负载上把交错测量中位数从 `86.825 ms` 降到 `69.680 ms`，改善 `19.8%`；独立评测在性能负载与正常 3024 行现场均确认结果等价和回归通过。Trial 为 `18/20`，使开发 Skill 升级为验收配额页面与只读 SQL 两类切片内已验证。
- “验收分配缺口”跨层实验用例已完成修订参考与 Luna 盲测。弱模型沿 Catalog、Repository、HTTP、Vue 映射和任务表完成纵切，自主发现 `10 + 5` 最大组合并取得 `18/20`；独立数据库、API 和 Edge 证明四级结果 `173 → 26 → 12 → 3`、筛选、排序和下钻可用。候选还用正式知识和运行事实反证了首轮专家参考的类别互抵口径，参考已从 `d5a5fa6` 修正为 `35948ae`。这些结果证明冻结实验题内的执行能力，不代表它是用户“完整人工质检统计与详情”诉求的合理拆分。
- “验收分配缺口详情”完成 OpenCode + DeepSeek V4 Flash 的 Harness 前后盲测。首轮业务内容、数据库/API/页面和回归可用，但完整键盘焦点闭环失败且最终声明超过证据，为 `18/20`；通用 Skill 只收紧来源追踪、短运行探针、键盘证据和交付映射后，第二轮自主处理行重渲染后的焦点恢复，固定 PostgreSQL、HTTP、四级页面、零分母、完整键盘和回归全部通过，为 `20/20`。该题停止调参；开发 Harness 新增 OpenCode/DeepSeek 交互切片证据，但仍限于同一质检系统。
- “代码变化到知识回写”首题形成 `24/24` 强参考，第四轮 Luna 为 `22/24`；随后在“验收未完成量”相邻增量上继续盲测，最终候选 `a8ea723` 达到 `24/24` 且全部关键题通过。来源身份、父知识原位融合、业务公式、前后端责任、旧列配置兼容、公共能力和产品视图均可从候选直接回答。能力升级为 `Verified@manual-qc-same-system-adjacent-writeback-slice`，仍须人工审查，不自动发布。
- “本地快照导入代码回写”作为不同变化类型的保留集完成第三轮。结果由 `17/24 → 20/24 → 21/24`，数据库公共能力、当前态和可运行入口已修复；精确校验边界、代表性人工状态值与固定日期夹具边界仍遗漏，三个关键题失败。该保留集不接受，说明外部契约和数据库状态密集型回写仍是 `implemented / human review required`；不再通过追加 Skill 文案拟合同题。
- M2“可信查询与任务上下文”已完成首个限定范围闭环。四类基础问答为 `22/24`；确定性知识入口路由器在 10 条真实质检问法上为 `10/10`；路由集成后的人员权限与交付多状态两条盲问答均为 `5/5`，实际只读主入口和一个候补，无宽泛搜索、失败命令或文件修改。M2 当前为 `Verified@quality-check-trusted-query-slices`，只覆盖中文 Markdown、单一质检领域和最多三篇规范页。
- 干净 Harness 候选已发布到远端 `release/development-writeback-harness-v1@a5104ec`，标签 `harness-development-writeback-v1-rc1`。它汇集 M1 摄入、M3 开发和 M4 回写能力，不预装领域答案；M4 明确标为已实现并真实试用、尚未 verified。
- 当前实验 Harness 位于 `experiment/development-harness-v1@ab902c6`。它保留 M3/M4 已有切片，并新增已验证的软件开发本地审查能力；该提交尚未推送远端，也不等同于已有正式 Release。
- 质检知识阅读体验用例已收口：用户审查后的认证参考为 `experiment/reader-first-knowledge-v1@fa8438b`。OpenCode + DeepSeek V4 Flash 的 007 Trial 在隔离仓库中审视 27 个用户页面，修改 22 页、保留 5 页，7 个读者问题均完成，内容 `93/100`且无关键失败。具有三种模式入口、单一页面规划源和小批页面任务包的 Harness 已发布到 `release/reader-first-ingestion-harness-v1@ab0c7a3`，标签 `harness-reader-first-ingestion-v1`。该验证只覆盖质检整库阅读整改，未外推到跨领域或任意规模。
- “人工质检统计与详情”开发准备已经完成现状审计：`quality-platform-lab@89e48d9` 已覆盖原计划中的只读总览、图表、任务汇总、四级下钻、指标详情和公共表格主体，不应从零重做。本轮 PostgreSQL 自检、真实 HTTP、Python `16/16`、Vue `29/29`、类型检查和生产构建通过；新鲜浏览器操作仍待人工完成。该场景尚未升级为正式 Trial，下一步先由用户认证现有工作台，再确认“验收覆盖与配额缺口”等真正未满足的业务结果。
- 质检材料、正式知识、当前实验平台、历史前端原型和认证参考均已纳入资产覆盖目录。用例组合覆盖全部家族，单个任务仍只读最低充分来源。
- 本地 AI 工作审查已完成 OpenCode DeepSeek 三类闭环。正向 004 对照用户审定真值独立评分 `17/18`；任务错位 006 只读任务身份包后停止，没有访问产品实现；简单状态 002 不生成审查单。能力成熟度为 `Verified@deepseek-software-review-positive-mismatch-no-trigger-slice`。发布提交的两次正向补跑因模型服务长时间无响应没有成品，不计通过；完整失败证据已封存，不覆盖 004 的内容结论。

## 2. 名称只表示一件事

| 名称 | 含义 | 是否用于表示实验结果 |
|---|---|---|
| `C1—C10` | Blueprint 架构组件，例如来源、规范知识、摄入、查询、产品视图和评测 | 否 |
| `M1—M5` | 能力阶段，例如知识摄入、知识使用、真实任务和知识回写 | 否 |
| `B1/B2` | 两批冻结原始材料 | 否 |
| `K0/K1` | 旧的知识快照编号：摄入 B1 后、再增量摄入 B2 后 | 只作为历史 ID |
| `E1—E7` | 旧的真实工作场景编号 | 只作为历史 ID |
| `RC1` | Harness 发布候选版本 | 否 |
| `Trial` | 一个模型在固定输入和 Harness 上实际运行一次 | 是 |

从本页开始，面向用户优先使用完整名称；历史目录、分支和 manifest 中的旧编号不迁移，只在括号中保留以便追溯。

## 3. 已准备好的用例

| 用例 | 固定输入 | 认证参考成果 | 已有 Trial | 当前状态 | 下一步 |
|---|---|---|---|---|---|
| **基础文档摄入**（旧 `M1/K0/B1`） | 66 份人工质检验收材料及 `SHA256SUMS` | 已认证，31 个结果文件 | 多模型历史最好 `21/24`；当前 Luna 路线由 `19→18` 失败对照推进到 `20/24` | 内容达到接受线；来源视图已修复，候选未发布 | 人工审查 `0225003`，决定采纳、部分拒绝或退回 |
| **增量文档摄入**（旧 `M1/K1/B2`） | 认证基础知识 + 25 份新增材料 | 已认证，41 个结果文件 | Luna Trial 002 与 Terra Trial 003 均为 `24/24` | 已发布并完成跨模型可恢复重放 | 作为 M1 回归保留；不再针对同批调优 |
| **代码全链路摄入**（旧 `E1`） | `quality-platform-lab@203c785`、任务分析表、两个指标和日期锚定的私有运行 fixture | 已认证，含 12 个内容问题与可重建 PostgreSQL 输入 | GLM `13/24`、旧 Luna `14/24`、V2 Luna `16/24`、两轮 `17/24`、最新 `20/24` | 已达到当前用例接受线；候选未发布 | 暂停代码补丁；与基础候选一起进入发布审查，不单独复跑 |
| **已有知识整库阅读整改** | 质检集成版已有正式知识；不重新读项目外原料 | 用户审查的 `fa8438b`，评分规则见 `quality_reader_redesign_v1` | DeepSeek 005 内容 `90/100` 但流程失败；006 过读后中止；007 为 `93/100` 且流程完整 | `Verified@quality-check-reader-refactor-slice`，Harness 已发布 | 停止同题调优；换开发知识准备和第二领域反证 |
| **验收配额可见性** | `quality-platform-lab@203c785`、正式质检知识 `900cf85`、按需可读原料/原型、本地数据库 | 修订参考 `a1aa7a9`，待用户认证 | 基线 `16/20`；两次失败重放 `15/20`、`14/20`；实现前快照版 `18/20` | 开发 Skill 在本切片验证；14/15 API、五个固定选项和 Edge 通过 | 不再复跑本题；换数据写入工况验证泛化 |
| **页面/API范围差异排障** | `quality-platform-lab@a1aa7a9`、正式质检知识 `900cf85`、固定 PostgreSQL 种子 | 参考诊断已形成，待用户认证 | Luna 基线 `18/20` | 真实复现通过、零代码修改；不需要新 Skill | 保留为零修改回归；进入本地表格安全写库 |
| **本地 CSV 安全写入快照** | `quality-platform-lab@a1aa7a9`、两份固定 CSV、私有 PostgreSQL、正式质检知识 `900cf85` | 参考实现 `12a9c5d`，待用户认证 | Luna 首轮 `16/20`；副作用修订版 `17/20` | 主要用户路径和状态保护可用；不完整指标输入仍可通过 | 停止同题调优；进入只读 SQL 性能优化 |
| **问题选项 Facet 性能优化** | `quality-platform-lab@a1aa7a9`、151200 行性能负载、正常 3024 行夹具、正式质检知识 `900cf85` | 参考实现 `bb5bfc3`，待用户认证 | Luna Harness `18/20` | 结果等价、约 20% 中位数改善、正常回归通过；缺聚焦测试与明确知识落点 | 停止同题调优；进入跨前后端契约功能 |
| **验收分配缺口** | `quality-platform-lab@a1aa7a9`、3024 行固定数据库、正式质检知识 `900cf85` | 修订参考 `35948ae`，待用户认证 | Luna Harness `18/20` | 数据库、API、Edge 四级定位通过；盲测纠正首轮参考口径 | 停止增加同类开发题；进入代码变化知识回写 |
| **验收分配缺口详情实验题** | `quality-platform-lab@35948ae`、3024 行固定数据库、正式质检知识 `900cf85` | 实验参考工作树 `1b1b4b8`；原始需求参考资格已被用户否定 | OpenCode/DeepSeek `18/20 → 20/20` | 冻结实验题内的详情、四级 Scope、零分母、数据库/API/页面、完整键盘和全量回归通过 | 保留为独立 Harness 回归；不得再表述为原始多维结果分析需求的切片 |
| **代码变化到知识回写** | 已发布质检知识 + `qpl-gap-ref@35948ae` + 固定验证报告 | 强参考 `28b0951`，`24/24` | Luna 四轮；最新候选 `3a6c5da` 为 `22/24` | 隔离、身份、完整数据契约、证据发现、原位融合和视图同步通过；内容深度仍有两项缺口 | 用 Trial 后修正版在相邻真实代码变化重放，不继续拟合本题 |
| **验收未完成量代码回写** | 父知识 `28b0951` + `qpl-pending-ref@26db0e1` + 固定验证报告 | 强参考 `760a86d`，`24/24` | Luna 五轮；最终候选 `a8ea723` 为 `24/24` | 同系统相邻增量的内容、融合、安全和视图全部通过；候选未发布 | 冻结为回写成功回归，不再同题调优 |
| **本地快照导入代码回写** | 已发布质检知识 + 快照导入实现/固定报告 | 强参考与 24 项冻结问题 | Luna 三轮；`17/24 → 20/24 → 21/24` | 主链路和公共能力改善；精确校验、代表状态、日期夹具三个关键项仍缺 | 保留为 holdout；先设计通用契约/运行证据提取，再换新题验证 |
| **可信知识问答与入口路由** | 正式质检知识 `900cf85` + 学习/现状/冲突/开发/人员/交付等真实问法 | 10 个参考答案、24 项基础内容题、10 条路由真值 | 基础包 `22/24`；路由 `10/10`；集成盲测 `10/10` | `Verified@quality-check-trusted-query-slices`，范围限定 | 冻结同领域调优；嵌入新的开发复合工况 |
| **本地 AI 工作审查** | 已完成任务的原始输入、Diff、运行证据与边界 | v0.2 任务错位负例 + 用户审定的 v0.3 验收未完成量正向真值 | 正向 004 `17/18`；错位 006、不触发 002 通过 | 软件开发本地审查三类切片已验证 | 停止同题调优；进入模糊需求到可审方案能力 |
| **任务案恢复**（旧 `TC_*`） | 冻结任务账本 fixture | 只有历史校准材料，缺新鲜参考执行 | 历史 Gemini 等记录 | 暂停，不是当前主线 | 不创建新 Trial |

### 3.1 基础文档摄入

**用户结果：** 从空知识库开始，把一批质量不一、结构混乱的人工质检验收材料整理成可浏览、可查询、可追溯并可继续用于工作的规范知识。

**输入：** [`m1_brownfield_v1` 材料说明](fixtures/knowledge_ingestion/m1_brownfield_v1/README.md)中的 Batch 1。实际包位于 `/home/yyh/project/omni-brain-m1-brownfield-input-v1/batch-1`。

**当前参考：** [基础文档摄入参考审查](reference/m1-knowledge-ingestion-brownfield-v1/k0/review.md)，状态为 `certified`。参考成果是当前最佳可用结果，不要求候选复制相同文件布局。

**候选最终应交给用户：**

1. 规范知识页；
2. 领域视图和学习/工作旅程视图；
3. 一份发布前审查页，明确可靠内容、冲突和外部缺口。

**当前通过条件：** 内容至少 `20/24`、没有核心问题为 `0`；质检位置、人工质检全貌、需求到交付生命周期、验收三阶段、数据状态、采样规则、软件结构和公共能力不能因问题规划过窄而消失；来源和正式知识保持不变；过程成本不能回到逐文件机械登记。

### 3.2 增量文档摄入

**用户结果：** 在已有规范知识上吸收后来到达的材料，正确处理新增、修改、合并、冲突、过时声明和产品视图变化，而不是重新生成一套平行知识。

**输入：** 冻结的基础参考成果，加上 Batch 2 的 25 份原料。

**当前参考：** [增量文档摄入参考审查](reference/m1-knowledge-ingestion-brownfield-v1/k1/review.md)，状态为 `certified`。

**当前结果：** 第一次运行内容可回答，但把更新写成批次化章节；第二次运行经过通用 Harness 修复后，正确保留父知识、原位融合新增内容、同步入口和产品视图，内容复核达到 `24/24`，并经用户批准发布。Terra medium 随后从同一输入独立形成另一份 `24/24` 候选；它需要多个会话，但能依靠工作台逐段恢复并最终达到 `publish_ready`。

### 3.3 代码全链路摄入

**用户结果：** 从页面上的“标注提交量”和“验收完成率”出发，理解 PostgreSQL、SQL、后端分层、HTTP、Vue、表格交互与样式，并能按知识完成真实 API、同范围 SQL 和页面核对。

**输入与参考：** [代码全链路参考说明](reference/e1-code-knowledge-ingestion-v1/README.md)，固定来源提交为 `203c785`。

**当前通过条件：** `20/24` 才算通过；达到 `18/24` 且实际改善关键材料时只允许进入一次定向修订。必须取得中央转换、字段映射、共享表格、默认日期范围和一次新鲜 API/SQL/页面对账，不能只复述综合文档或历史验证报告。

### 3.4 验收配额可见性

**用户结果：** 任务分析表直接展示预期验收分配量、实际验收分配量和分配达成率；预期量为零时为空，不制造风险阈值。

**用例：** [生产等价需求与工况](fixtures/real_work/manual_qc_allocation_visibility_v1/README.md)。候选只看到自然语言需求、固定项目和公开来源，不看到参考实现或评审依据。

**参考候选：** [实现与运行证据](reference/real_work/manual_qc_allocation_visibility_v1/README.md)，代码为 `quality-platform-lab` 的 `reference/manual-qc-allocation-visibility-v1@a1aa7a9`。参考复用既有指标、SQL 和表格，只接通前端消费链，并把任务表 9 个基础指标叠加 5 个固定问题选项所需的查询上限从 12 最小调整到 14。

**当前验证：** 17 项 Python、30 项 Vue、类型和生产构建通过；14 项查询成功、15 项被拒绝；真实 API 对 24 个任务返回正常和零分母结果；Edge 实际渲染出现新列和 `—`；旧版已保存列顺序不会隐藏新增列。列排序、筛选和保存复用既有 DataWorkbench 契约，尚待用户可见浏览器人工操作确认。

**Luna 基线：** [完整审计](trials/real_work/MANUAL_QC_ALLOCATION_CODEX_LUNA_BASELINE_001/audit.md)。候选功能和独立真实链可用，且主动发现参考遗漏；不足是未读取正式知识、生产会话没有自行跑通 PostgreSQL/API/Edge、把上限放宽到 16 而非最低 14，知识变化只给出笼统口径复核。该结果用于批准通用 Harness 修订，不直接晋升代码。

**Harness 重放：** [首版审计](trials/real_work/MANUAL_QC_ALLOCATION_CODEX_LUNA_HARNESS_002/audit.md)和[最大状态说明版审计](trials/real_work/MANUAL_QC_ALLOCATION_CODEX_LUNA_HARNESS_003/audit.md)都证明“把正确清单写进 Skill”仍会被模型跳过。加入[实现前快照](trials/real_work/MANUAL_QC_ALLOCATION_CODEX_LUNA_HARNESS_004/audit.md)后，模型首次在编辑前公开组合构成、自主发现 14、用五个真实选项运行并准确保留浏览器缺口。独立评测补做 15 拒绝和 Edge 最大配置。候选仍有 HTTP/Service 上限未共享定义、知识落点不够具体两项差距。

**候选通过判断：** 页面和数据真实可用；没有重造后端或阈值；正常/超额/零分母与下钻语义正确；使用项目环境完成实际验证；知识变化候选准确；过程没有无界翻库。文件拓扑不要求复制参考。

### 3.5 页面/API范围差异排障

**用户结果：** 面对页面 `516 / 499 / 96.7%` 与空 Scope API `2629 / 2575 / 97.946%` 的差异，能迅速判断是范围、数据版本还是公式问题；给出同范围真实对账，有 Bug 才修，没有 Bug 保持零代码修改。

**用例与参考：** [固定工况](fixtures/real_work/manual_qc_scope_discrepancy_v1/README.md)把源码路径和 commit 分开表达；[参考诊断](reference/real_work/manual_qc_scope_discrepancy_v1/README.md)沿页面日期、请求 Scope、Schema 和 Repository 闭区间条件证明两组结果来自不同日期范围，并把动态默认日期与固定种子老化列为独立候选问题。

**当前结果：** [Luna 无专项 Skill 基线](trials/real_work/MANUAL_QC_SCOPE_DISCREPANCY_CODEX_LUNA_BASELINE_001/audit.md)为 `18/20`。模型在 165 秒内沿页面状态、Schema、Service、Repository 和 PostgreSQL 日行完成控制变量，再通过真实 HTTP 复现两组数值；它正确判断不是 Bug，保持零代码、零文档和零测试修改。

**Harness 判断：** 不新增查询/排障 Skill。目标明确、直接事实源完整、风险低的排障继续走 A/B 类直接执行；正式知识未被读取的问题留给 M2 最低充分上下文，固定种子随动态日期窗口老化的问题留给 Eval fixture。该用例成为“预期零修改”的代表性回归。

### 3.6 本地 CSV 安全写入快照

**用户结果：** 在项目根先预览本地 CSV 的文件身份和逐行新增/修改/不变，再用该次预览的确认令牌在单事务中写入；脏批零写入，文件或相关数据库行变化后旧确认失效，重复导入不刷新时间，人工确认/执行状态不被覆盖。

**用例与参考：** [固定工况](fixtures/real_work/manual_qc_snapshot_csv_import_v1/README.md)提供一份 `1 insert + 1 update + 1 unchanged` 的有效文件和后部含脏行的失败文件；[参考实现](reference/real_work/manual_qc_snapshot_csv_import_v1/README.md)位于 `reference/manual-qc-snapshot-import-v1@12a9c5d`。当前单用户、本地、小批量、同步确认条件下直接写现有快照表；网页上传、多人审批、异步、持久审计或按批回滚才触发 staging/批次表。

**两轮结果：** [首轮审计](trials/real_work/MANUAL_QC_SNAPSHOT_IMPORT_CODEX_LUNA_HARNESS_001/audit.md)为 `16/20`；[副作用规则重放](trials/real_work/MANUAL_QC_SNAPSHOT_IMPORT_CODEX_LUNA_HARNESS_002/audit.md)为 `17/20`。第二轮候选真实跑通首次写入、脏批、状态变化、重复执行和恢复，并经独立评测确认顶层、Good、Bad、匹配选项、旧选项的空/非空状态均保持；Python 20、Vue 30、类型和构建通过。

**未通过边界：** 第二轮解析器允许缺少 11 个数值键的指标对象进入预览，可能把不完整 JSONB 落库；模型取得全表指纹的命令失败后仍开始写入，最终还声明了未亲自观察的问题选项状态。开发 Skill 已增加“基线失败阻断写入”和“只报告真实输出”规则，但不再用本题复跑验证，避免过拟合。

### 3.7 问题选项 Facet 性能优化

**用户结果：** 在分析页选择问题标签后，更快获得该标签下的问题选项；接口、Scope、排序和 200 条上限不变，`驾驶行为分类` 仍返回有序的 `CUT_IN / FOLLOW_TOO_CLOSE / MERGE / YIELD`。

**用例与参考：** [固定工况](fixtures/real_work/manual_qc_question_option_facet_performance_v1/README.md)把原始 3024 行快照固定放大为 151200 行，只改变数据量；[参考实现](reference/real_work/manual_qc_question_option_facet_performance_v1/README.md)位于 `reference/manual-qc-question-option-facet-performance-v1@bb5bfc3`，用直接读取选中标签替代展开全部 JSONB 标签后过滤。

**当前结果：** [Luna Harness 审计](trials/real_work/MANUAL_QC_QUESTION_OPTION_FACET_PERF_CODEX_LUNA_HARNESS_001/audit.md)为 `18/20`。模型在 270 秒内完成真实 API 基线、执行计划、暖缓存交错各 12 轮、最小 SQL 修改与重复测量，中位数改善 `19.8%`；独立评测复现 `20.2%` 改善，并在正常 3024 行现场确认 `verify`、API、Python 17、Vue 30、类型和构建通过。

**剩余边界：** 候选没有新增聚焦的持久回归测试，知识变化候选没有明确规范文件和保持边界。这些要求已经在通用 Skill 中，不继续追加 SQL 专属提示。该切片与后续跨层用例共同构成当前开发能力证据。

### 3.8 验收分配缺口

**用户结果：** 任务分析表直接显示按最终 Good/Bad 分类计划计算的验收分配缺口，并能沿任务、日期、组和标注员定位缺口来源；缺口为零时保持中性，不生成阈值或责任判断。

**用例与参考：** [固定工况](fixtures/real_work/manual_qc_allocation_shortfall_v1/README.md)从 `quality-platform-lab@a1aa7a9` 开始；[修订参考](reference/real_work/manual_qc_allocation_shortfall_v1/README.md)位于 `reference/manual-qc-allocation-shortfall-v1@35948ae`。首轮参考把 Good/Bad 执行结果再次互抵，盲测候选指出最终分类计划必须分别保留正缺口；正式知识、快照结构和独立 SQL 均支持候选，参考因此被修正。

**当前结果：** [Luna Harness 审计](trials/real_work/MANUAL_QC_ALLOCATION_SHORTFALL_CODEX_LUNA_HARNESS_001/audit.md)为 `18/20`。候选在 334 秒内完成跨层纵切，17 项 Python、30 项 Vue、类型和构建通过；最大 15 项 API 返回 200，第 16 项返回 422；独立 Edge 证明排序、`173～173` 数值筛选和 `173 → 26 → 12 → 3` 四级下钻。

**Harness 判断：** 同一通用开发 Skill 已覆盖页面/契约、只读 SQL 性能和跨层业务算法三类真实切片。模型最终把仅渲染过的页面写成已完成交互，并漏掉知识变化候选，因此 Harness 只做了通用交付收敛和共享 worktree 源码隔离提醒，没有写入指标名、公式或固定数字。当前采用级别为 `Verified@three-manual-qc-development-slices`，不外推到跨领域、写入安全或任意宿主。

### 3.8.1 验收分配缺口详情实验题

**适用边界：** 这是 Harness 实验设计者后来构造的冻结开发题，不是用户原始“完整人工质检统计与详情”诉求的需求分解。用户在本地审查单 R0 明确否定了两者的对应关系；因此以下 `20/20` 只评价实验题执行，不能用于证明原始需求理解、任务拆分或方案形成能力。

**用户结果：** 用户点击任务、日期、组或标注员的缺口数字，可以直接看到整体、Good、Bad 的预期、实际、缺口、达成率和三条按日趋势，并理解局部超额为何不抵消其他位置缺口；零分母显示为未知值，不生成问题选项配额或自动判断。

**固定输入：** [生产任务与评分](fixtures/real_work/manual_qc_allocation_gap_detail_v1/README.md)从修订后的产品 `35948ae` 开始，使用同一 3024 行 PostgreSQL 和正式质检知识 `900cf85`。参考工作树为 `qpl-allocation-gap-detail-reference-v1@1b1b4b8`；候选看不到参考、评分项或历史 Trial。

**前后对照：** [第一轮审计](trials/real_work/MANUAL_QC_ALLOCATION_GAP_DETAIL_OPENCODE_DEEPSEEK_001/audit.md)为 `18/20`：业务内容与真实数据成立，但焦点进入、Tab 环绕和关闭后恢复没有实现，最终说明仍概括为键盘已完成。[第二轮审计](trials/real_work/MANUAL_QC_ALLOCATION_GAP_DETAIL_OPENCODE_DEEPSEEK_002/audit.md)为 `20/20`：相同模型在修订后的通用 Skill 下自主发现表格行重渲染会替换原触发节点，改用稳定标签恢复焦点；独立 SQL、HTTP、四级页面、零分母、Enter、正反向 Tab、Escape、焦点恢复和全量回归均通过。

**Harness 判断：** 有效修改只有四类通用规则：沿用户动作追到 handler/owner/验证入口；运行探针保持单一目的并在重复失败时停止；交互证据拆成触发、进入、环绕、关闭和恢复；最终声明逐项映射实际证据。公式、指标名、固定数字和页面路径没有进入 Skill。本题已经收敛，不再追加 Prompt；第二轮仍有较多临时浏览器脚本，只有在新交互题复现后才考虑建设确定性浏览器证据组件。

### 3.9 代码变化到知识回写

**用户结果：** 固定代码、Schema、规则和运行证据变化后，把新事实原位融入正式知识与产品视图，保留历史、冲突和生产未知，并停在可拒绝、可回滚的候选，而不是生成一份更新摘要。

**输入与参考：** [固定工况](fixtures/real_work/code_to_knowledge_writeback_v1/README.md)使用已发布质检知识和 `qpl-gap-ref@35948aebf41b8772b77df18bd68ce9ff2d295344`；[强参考](reference/real_work/code_to_knowledge_writeback_v1/README.md)为 `28b0951`，固定内容题 `24/24`。

**第四轮结果：** [完整审计](trials/real_work/CODE_TO_KNOWLEDGE_WRITEBACK_CODEX_LUNA_HARNESS_004/audit.md)记录候选 `3a6c5da`。模型没有看到参考，能够发现固定验证报告、完整冻结 18 个顶层字段和 13 个嵌套字段、保留 9+5/10+5 证据差异、建立独立来源/系统/软件页并原位更新父知识和视图。结构达到 `publish_ready`，但内容为 `22/24`：API 行到任务树行的转换入口没有写透，固定报告的代表性运行结果没有充分内化。

**Harness 判断：** 代码回写已经是可试用的真实能力，但尚未 verified。Trial 后只做两项通用修正：关闭软件候选前核对 types/utils/mapper/adapter 等直接转换入口；采用固定报告时内化决定判断的具体结果。修正已经换相邻代码变化反证，结果见下一节。

### 3.10 验收未完成量代码回写

**用户结果：** 把“验收未完成量”跨层开发变化原位更新进已有知识，使业务读者能区分它与分配缺口，开发者能定位后端既有能力、前端消费链、组合上限、兼容机制和固定运行证据。

**用例与参考：** [固定工况](fixtures/real_work/manual_qc_pending_visibility_writeback_v1/README.md)使用父知识 `28b0951`、`qpl-pending-ref@26db0e1` 和固定验证报告；[强参考](reference/real_work/manual_qc_pending_visibility_writeback_v1/README.md)为 `760a86d`，冻结内容为 `24/24`。

**最终结果：** [第五轮独立审计](trials/real_work/MANUAL_QC_PENDING_VISIBILITY_WRITEBACK_CODEX_LUNA_HARNESS_005/audit.md)为 `24/24`，全部关键问题通过。候选准确固定 root、branch、HEAD 与 parent；保留 `max(sum(actual_alloc)-sum(actual_complete),0)` 的聚合语义；区分验收未完成量与分类原子分配缺口；解释后端已有、前端新增消费；冻结 11+5/第 17 项拒绝、`1737 → 144 → 51 → 20` 和完整回归；并把旧列配置恢复机制落到公共数据工作台。

**Harness 判断：** 代码回写升级为 `Verified@manual-qc-same-system-adjacent-writeback-slice`。这个结论只覆盖已有完整父知识、固定 Git 来源和验证报告的同一质检系统相邻增量；候选仍停在人工审查前，不能自动发布或外推到跨系统、删除退役、缺少报告和第二领域。

### 3.11 本地快照导入代码回写

**用户结果：** 把新加入的本地 CSV 快照导入能力，连同外部契约、校验/转换、事务与竞态、人工状态保护、可运行命令和固定验证边界，原位融入既有质检知识，而不是另建一份功能摘要。

**用例与参考：** [固定工况](fixtures/real_work/code_to_knowledge_writeback_snapshot_import_v1/README.md)使用同一正式质检知识和快照导入实现/报告；[参考成果](reference/real_work/code_to_knowledge_writeback_snapshot_import_v1/README.md)冻结 24 项内容问题。

**当前结果：** [第三轮保留集审计](trials/real_work/CODE_TO_KNOWLEDGE_WRITEBACK_SNAPSHOT_IMPORT_CODEX_LUNA_HARNESS_003/audit.md)为 `21/24`，延续首轮 `17/24`、第二轮 `20/24` 的改善。弱模型正确判断提交祖先关系，完整吸收 11 列 CSV、18 列快照返回、13 键指标状态、导入模型、锁/事务和公共数据库能力，并原位更新 11 个长期 owner。

**未通过边界：** 精确校验仍缺 `2_147_483_647` 上界、布尔拒绝和状态字段类型；固定报告中的 `reference-reviewer`、`MANUAL_DONE` 等代表性状态被压成“状态保护通过”；`2026-07-13..2026-07-26` 日期平移及其非产品属性遗漏。三个关键题失败，保留集不接受。下一步不是继续加提示词；先在新的开发纵切观察精确契约与运行状态缺口是否复现，复现后才升级为通用提取组件。

### 3.12 可信知识问答与入口路由

**用户结果：** 用户从项目根直接提问，先得到正确且最低充分的正式知识答案；答案能列清已知、未知、冲突和适用范围，并能把开发问题交给后续真实源码与运行验证，不需要理解账本、YAML 或摄入流程。

**基础问答：** [四类问答包](fixtures/real_work/trusted_knowledge_answer_pack_v1/README.md)覆盖学习、现状/未知、版本冲突和开发上下文，首轮盲测为 `22/24`。简单问题内容稳定，复杂开发问题仍出现宽泛搜索和多读页面。

**确定性路由：** [10 条真实路线](fixtures/real_work/knowledge_route_quality_v1/README.md)促成只读、无状态的 `knowledge_route.py`。它只遍历根入口可达的正式 Markdown，返回一个主入口和按问题子句差异化的候补；固定评测为 `10/10`，见[路由报告](reports/real_work/knowledge-route-quality-v1-2026-08-07.md)。

**集成盲测：** [人员权限与交付状态审计](trials/real_work/TRUSTED_KNOWLEDGE_ANSWER_ROUTER_CODEX_LUNA_HARNESS_001/audit.md)为 `10/10`。两次会话都真实调用路由器，只读主入口和一个候补，没有宽泛搜索、失败命令、源码探测或文件修改。组件成熟度为 `Verified@quality-check-trusted-query-slices`；尚未证明第二领域、OpenCode、跨语言、大知识库、精确源码联查或关系型多跳。

## 4. 已保留的知识摄入 Trial

| 用例 | Trial | 模型/宿主 | 内容结果 | 结论 |
|---|---|---|---:|---|
| 历史综合摄入 | [`M1_LUNA_001`](trials/knowledge_ingestion/M1_LUNA_001/pre-review-analysis.md) | Luna | `10/24` | 早期失败基线；输入组织与当前基础用例不同，不参与当前横向排序 |
| 基础文档摄入 | [`M1_K0_OPENCODE_GO_MINIMAX27_001`](trials/knowledge_ingestion/M1_K0_OPENCODE_GO_MINIMAX27_001/pre-review-analysis.md) | MiniMax / OpenCode | `12/24` | 下界样本 |
| 基础文档摄入 | [`M1_K0_OPENCODE_GO_KIMI_001`](trials/knowledge_ingestion/M1_K0_OPENCODE_GO_KIMI_001/pre-review-analysis.md) | Kimi / OpenCode | `19/24` | 内容较强，仍未通过 |
| 基础文档摄入 | [`M1_K0_OPENCODE_GO_GLM51_001`](trials/knowledge_ingestion/M1_K0_OPENCODE_GO_GLM51_001/pre-review-analysis.md) | GLM 5.1 / OpenCode | `19/24` | 中等模型基线 |
| 基础文档摄入 | [`M1_K0_OPENCODE_GO_GLM51_V13_6_003`](trials/knowledge_ingestion/M1_K0_OPENCODE_GO_GLM51_V13_6_003/pre-review-analysis.md) | GLM 5.1 / OpenCode | `21/24` | 历史内容最好；存在来源状态和候选边界问题，不能发布 |
| 基础文档摄入 | [`M1_K0_CODEX_LUNA_RC1_001`](trials/knowledge_ingestion/M1_K0_CODEX_LUNA_RC1_001/pre-review-analysis.md) | Luna / Codex | `13/24` | RC1 导航有效，但关键候选被筛掉 |
| 基础文档摄入 | [`M1_V2_K0_CODEX_LUNA_001`](trials/knowledge_ingestion/M1_V2_K0_CODEX_LUNA_001/pre-review-analysis.md) | Luna / Codex | `10/24` | 过程成本下降，但两个局部问题替代了完整目标 |
| 代码全链路摄入 | [`E1_CODE_OPENCODE_GO_GLM51_001`](trials/knowledge_ingestion/E1_CODE_OPENCODE_GO_GLM51_001/pre-review-analysis.md) | GLM 5.1 / OpenCode | `13/24` | 有静态代码链，缺产品视图和真实运行 |
| 代码全链路摄入 | [`E1_CODE_CODEX_CLI_LUNA_001`](trials/knowledge_ingestion/E1_CODE_CODEX_CLI_LUNA_001/pre-review-analysis.md) | Luna / Codex | `14/24` | 视图改善，仍漏中央源码、默认范围和真实对账 |
| 代码全链路摄入 | [`CODE_INGEST_CODEX_LUNA_V2_001`](trials/knowledge_ingestion/CODE_INGEST_CODEX_LUNA_V2_001/pre-review-analysis.md) | Luna / Codex | `16/24` | 中央代码与正常 SQL/API 对账改善；零分母、固定日期、页面和知识状态同步仍缺 |
| 代码全链路摄入 | [`CODE_INGEST_CODEX_LUNA_V2_002`](trials/knowledge_ingestion/CODE_INGEST_CODEX_LUNA_V2_002/pre-review-analysis.md) | Luna / Codex | `17/24` | 并发状态和证据写回修复生效；精确字段链改善，但非 Git 运行数据、SQL 和页面不可重放 |
| 代码全链路摄入 | [`CODE_INGEST_CODEX_LUNA_V2_003`](trials/knowledge_ingestion/CODE_INGEST_CODEX_LUNA_V2_003/pre-review-analysis.md) | Luna / Codex | `17/24` | 固定日期、SQL/API 与四级下钻改善；后到前端证据、最终字段、正常/零分母任务和来源提交仍缺 |
| 代码全链路摄入 | [`CODE_INGEST_CODEX_LUNA_V2_004`](trials/knowledge_ingestion/CODE_INGEST_CODEX_LUNA_V2_004/pre-review-analysis.md) | Luna / Codex | `20/24` | 来源身份、后到证据和正常/边界对象进入正文；达到接受线，转基础文档回归 |
| 基础文档摄入 | [`M1_V2_K0_CODEX_LUNA_002`](trials/knowledge_ingestion/M1_V2_K0_CODEX_LUNA_002/pre-review-analysis.md) | Luna / Codex | `15/24` | 局部流程、数据状态与来源改善，但完整领域、软件结构、公共能力和完整算法仍缺；只允许一次共享工作流修订 |
| 基础文档摄入 | [`M1_V2_K0_CODEX_LUNA_003`](trials/knowledge_ingestion/M1_V2_K0_CODEX_LUNA_003/pre-review-analysis.md) | Luna / Codex | `16/24` | 目标覆盖修订改变了问题规划与软件内容，但业务/目标/历史证据仍被当前代码吞没；停止 Skill 文案补丁 |
| 基础文档摄入 | [`M1_V2_K0_CODEX_LUNA_004`](trials/knowledge_ingestion/M1_V2_K0_CODEX_LUNA_004/pre-review-analysis.md) | Luna / Codex | `13/24` | 目标规划切片改善现实边界但造成虚假依据完成和内容覆盖回退；低于否定线，停止同类复跑 |
| 基础文档摄入 | [`M1_MAP_PLAN_CODEX_LUNA_001`](trials/knowledge_ingestion/M1_MAP_PLAN_CODEX_LUNA_001/pre-review-analysis.md) | Luna / Codex | `19/24` | 客观材料地图和二次目录复核恢复 Ratio、数据库公共边界、软件纵切和现实形态；仍缺上位领域、完整生命周期、平台全貌和数据状态 |
| 基础文档摄入 | [`M1_READER_OUTCOME_CODEX_LUNA_001`](trials/knowledge_ingestion/M1_READER_OUTCOME_CODEX_LUNA_001/pre-review-analysis.md) | Luna / Codex | `18/24` | 唯一定向修订改善字段冲突，但丢失类函数细节和补知责任；已撤回，不再复跑同类方案 |
| 基础文档摄入 | [`M1_DETAIL_PRESERVATION_CODEX_LUNA_001`](trials/knowledge_ingestion/M1_DETAIL_PRESERVATION_CODEX_LUNA_001/pre-review-analysis.md) | Luna / Codex | `20/24` | 独立叙述文档、原子发现和发现到正文映射补回平台模块与数据状态；模型手写来源索引有误，已由通用确定性修复重建，候选待人工审查 |
| 增量文档摄入 | [`M1_INCREMENTAL_CODEX_LUNA_001`](trials/knowledge_ingestion/M1_INCREMENTAL_CODEX_LUNA_001/pre-review-analysis.md) | Luna / Codex | `24/24` | 内容可回答，但规范页和产品视图追加批次章节，长期结构不通过；触发通用语义融合修订 |
| 增量文档摄入 | [`M1_INCREMENTAL_CODEX_LUNA_002`](trials/knowledge_ingestion/M1_INCREMENTAL_CODEX_LUNA_002/pre-review-analysis.md) | Luna / Codex | `24/24` | 父知识保留、原位融合、入口语义和产品视图同步通过；已获用户批准并发布为正式知识 |
| 增量文档摄入 | [`M1_INCREMENTAL_CODEX_TERRA_003`](trials/knowledge_ingestion/M1_INCREMENTAL_CODEX_TERRA_003/cross-model-analysis.md) | Terra / Codex | `24/24` | 通过 6 个可恢复会话完成同一用例；结构有合理差异，内容、安全与父知识保留均通过 |

`eval/trials/knowledge_ingestion/` 保存代表性现场。每个目录包含 Prompt、候选身份、过程证据与审计；Trial 数量本身不算进度。

## 5. 参考成果的权威关系

| 参考目录 | 当前角色 |
|---|---|
| `reference/m1-knowledge-ingestion-brownfield-v1/k0` | 基础文档摄入的当前认证参考 |
| `reference/m1-knowledge-ingestion-brownfield-v1/k1` | 增量文档摄入的当前认证参考 |
| `reference/e1-code-knowledge-ingestion-v1` | 代码全链路摄入的当前认证参考 |
| `reference/real_work/manual_qc_allocation_visibility_v1` | 验收配额可见性的参考候选；待用户确认后才能标为认证参考 |
| `reference/real_work/manual_qc_allocation_shortfall_v1` | 验收分配缺口的修订参考候选；首轮口径已被盲测和运行证据纠正，待用户确认 |
| `reference/m1-knowledge-ingestion-v1` | 早期综合参考；认证历史仍有效，但因混合两类来源且不能验证增量演进，不再作为新 Trial 的主评分参考 |

`certified` 只表示专家成果经过人工审查，并在声明的材料和代码版本内可作为比较基准；它不表示被测 Harness 已经能产生同等质量，也不表示其中的目标设计已经成为生产事实。

## 6. 未来真实工作场景

以下内容只有用户结果和初步轮廓，尚无完整 fixture、认证参考和可运行 Trial，因此不列入“已准备用例”：

| 候选场景 | 当前输入准备度 | 升级为正式用例前还缺什么 | 优先级 |
|---|---|---|---|
| 已发布质检知识的学习/查询/开发体验审视 | 正式知识和历史查询已就绪 | 固定三条用户旅程、人工阅读意见和问题分层 | 0 |
| 人工质检统计与详情的复杂前后端开发 | 现有工作台主体已实现；源码、正式知识、本地数据库和现状审计就绪 | 新鲜浏览器认证；选择并确认一个真正未满足的业务结果及口径 | 1 |
| 质检前端架构与运行调试知识摄入 | 当前代码和多份历史/目标材料已就绪 | 冻结当前/历史/目标来源身份，加入新鲜启动与调试结果 | 1 |
| 授权数据库资产、表结构和消费者关系整合 | 本地 PostgreSQL、migration 和代码入口已就绪 | 明确授权数据库范围、安全连接方式和动态事实快照方法 | 1 |
| 人工质检完整现状规整 | 正式知识、原料和实验代码已就绪 | 当前生产事实、人力责任和真实数据源需人工或直接证据确认 | 2 |
| 数据库优化实践与成果增量整合 | 已有 Facet 性能 Trial 和部分规范 | 用户个人实践、讨论与成果的权威来源路径 | 2 |
| 金铲铲第二领域知识摄入 | 未定位正式材料 | 材料路径、主要用途、当前版本和读者问题 | 2 |
| Harness 工程论文/源码/项目讨论摄入 | 研究包和 7 个源码 checkout 已就绪 | 固定读者问题，分离外部证据、本项目决定和开放假设 | 3 |
| 当前架构局限与优化方案 | 现有代码与部分架构知识可用 | 先取得优先级 1 的真实开发、运行和知识缺口证据 | 3 |
| Harness 安装/组合与真实工作 Trial 编排 | 工作流和证据目录已明确 | 用户工作流、安装冲突策略、命令设计和代表 Trial | 4 |
| 跨模型、助手和邻近领域迁移（旧 `E7`） | 已有 Codex 切片和一次 OpenCode 使用历史 | 代表用例稳定、OpenCode 模型可用、第二领域正式输入 | 4 |

近期事项的简单顺序、责任人和用户入口见 [`docs/now.md`](../docs/now.md)。只有固定公开输入、私有参考/问题、隔离方式和真实验收动作都准备好后，候选场景才移动到第 3 节。场景设计可保存在 [`docs/experiments/knowledge-driven-work-experiments.md`](../docs/experiments/knowledge-driven-work-experiments.md)，但动态执行状态必须回到本页。

## 7. 当前实现与下一动作

| Harness | 角色 | 状态 |
|---|---|---|
| `6d740db` / `release/m1-knowledge-ingestion-rc1` | 当前发布候选 | 本地回归通过，真实内容失败，不发布 |
| `9cb03bc` / `experiment/m1-simplified-ingestion-v2` | 精简工作流首版 | 首次基础文档 Trial `10/24`，保留为失败证据 |
| `97f1448` / `experiment/m1-simplified-ingestion-v2` | 针对目标覆盖与状态碰壁的修正版 | 63 项测试通过；代码 Trial `16/24`，证明部分真实能力但未达到发布线 |
| `0b00dcf` / `experiment/m1-simplified-ingestion-v2` | 针对代码 Trial 真实阻塞的通用修正版 | 67 项测试通过；已由 `ec73902` 基线上的代码重跑验证 |
| `ec73902` / `experiment/m1-simplified-ingestion-v2` | `0b00dcf` 功能修正及启动文档同步 | 代码重跑 `17/24`；状态和证据写回生效，运行输入不可重放 |
| `4a68795` / `experiment/m1-simplified-ingestion-v2` | 非 Git 运行输入最薄切片 | `--mount` 现场引用、`--copy-mount` 私有可写副本、绝对路径和环境边界已实现；70 项回归及真实 health/Vitest 烟测通过，待新 Trial |
| `dcd982a` / `experiment/m1-simplified-ingestion-v2` | 启动状态同步 | Harness 入口已改为先固定评测运行输入再重跑；不新增功能或内容证据 |
| `16b8d1e` / `experiment/m1-simplified-ingestion-v2` | 后到证据与代表性例子修订 | `start/status` 公开 Git 身份；Skill 要求新证据先入正文、真实例子覆盖正常/边界对象；代码 Trial 已验证内容收益 |
| `a782637` / `experiment/m1-simplified-ingestion-v2` | 当前模型实验基线 | 代码用例 `20/24`；基础文档回归 `15/24`，共享目标覆盖仍不足 |
| `fc3436d` / `experiment/m1-simplified-ingestion-v2` | 共享目标覆盖修订 | 基础文档复跑 `16/24`；问题规划改善但知识与证据角色仍未整体规划，停止继续改 Skill 文案 |
| `25b1455` / `experiment/m1-simplified-ingestion-v2` | 失败状态同步 | Harness 启动入口已指向组件设计；不包含新的功能或内容证据 |
| `f4809dc` / `experiment/m1-simplified-ingestion-v2` | 目标建模与知识规划最薄切片 | 75 项回归通过，但同批内容 Trial 只有 `13/24`；启发式现实标签、单来源 supported、四主题规划和单活动小批共同失败，当前表示已否定 |
| `b91c8b3` / `experiment/m1-material-map-plan-review` | 材料地图与知识目录复核替代路线 | 固定 Luna Trial `19/24`，无核心题为 0；材料覆盖明显恢复，但仍未通过 |
| `5f14a53` / `experiment/m1-material-map-plan-review` | 读者结果规划定向修订 | 同批 Trial `18/24`，发生内容细节回退，已否定 |
| `d48ac72` / `experiment/m1-material-map-plan-review` | 失败修订撤回点 | 能力等价回到 `b91c8b3`；保留 `19/24` 基线 |
| `6b330e1` / `experiment/m1-material-map-plan-review` | 细节保真内化切片 | 80 项回归通过；同批模型候选 `ed93abe` 内容 `20/24`，首次达到基础文档接受线 |
| `d5901b1` / `experiment/m1-material-map-plan-review` | 来源追溯修复 | 单来源定位输入收缩，来源视图从已校验发现与正文落点机械重建；修复模型候选的手抄路径错误 |
| `17ff40a` / `experiment/m1-material-map-plan-review` | 稳定语义融合首版 | 禁止按摄入批次追加章节，要求新知识进入长期语义结构 |
| `b5efe63`—`ddeca58` / `experiment/m1-material-map-plan-review` | 增量父知识与入口收敛 | 保守局部合并、缩减防护、入口/日志同步、消费任务直接走知识入口和父级当前态复核 |
| `3e53be8`—`4d8b596` / `experiment/m1-material-map-plan-review` | 最终审查恢复与语义同步 | 发布准备阶段可重新规划漏项、父级语义同步无需伪造发现，主题视图关联改为按需 |
| `9956ba5` / `experiment/m1-material-map-plan-review` | M1 最终实验 Harness | 86 项回归通过；支持空知识实验与已发布知识包，测试夹具不再继承正式业务知识 |
| `7e3034c` / `release/m1-ingestion-harness-v1` / `harness-m1-ingestion-v1` | 当前独立 Harness Release | 已推送公开远端；从远端全新浅克隆后，空知识骨架、知识检查和 86 项回归通过 |
| `900cf85` / `release/m1-quality-knowledge-v1` | 质检知识集成版 | 已发布 33 个 Markdown、24 个概念及两种产品视图；知识检查、正式消费和跨模型重放通过 |
| `338f670`—`1d74b99` / `experiment/development-harness-v1` | 开发 Skill 前两版 | 正式知识与真实运行部分改善，但最大组合在两次同题重放中仍被跳过；保留为失败证据 |
| `acffe26` / `experiment/development-harness-v1` | 实现前快照版开发 Skill | 同一弱模型自主发现 9 + 5、真实跑通 14；首个开发切片验证通过 |
| `54cba78` / `experiment/development-harness-v1` | 首个开发切片状态 | 87 项 Harness 回归通过；成熟度到 `Verified@manual-qc-allocation-slice` |
| `2e72fb7`—`958448e` / `experiment/development-harness-v1` | 数据写入副作用修订 | 精确基线、冲突状态、失败阻断与证据声明规则；CSV 同题由 `16/20` 提升到 `17/20`，只记正向证据，采用级别不变 |
| `52653dd` / `experiment/development-harness-v1` | 两类开发切片状态 | SQL 性能 Trial `18/20`，真实中位数改善约 20%；开发 Skill 升级为验收配额页面与只读 SQL 两类切片内已验证 |
| `c7aadc1` / `experiment/development-harness-v1` | 三类开发切片收敛版 | 分配缺口 Trial `18/20` 并纠正首轮参考；87 项回归通过，交付声明和共享 worktree 源码边界已收敛，下一步进入知识回写 |
| `c9bca1a` / `experiment/development-harness-v1` | 代码回写第四轮基线 | 固定验证报告优先、Python 契约冻结、证据复用和低成本语义检查；第四轮内容 `22/24` |
| `ebd696c` / `experiment/development-harness-v1` | 第四轮后的内容深度修正 | 转换入口与固定验证结果必须进入正文；95 项回归、Skill 和知识检查通过，待相邻切片反证 |
| `f29328b`—`a54abcd` / `experiment/development-harness-v1` | 相邻快照导入回写与通用完成标准 | 第二轮由 `17/24` 提升到 `20/24`；当时的完整回归通过 |
| `3cf55a9`—`fc7651d` / `experiment/development-harness-v1` | 可信问答与渐进阅读 | 基础问答 `22/24`；有限集合、绝对链接、一页起读和按缺口下钻规则在回归中收敛 |
| `0da62f3` / `experiment/development-harness-v1` | 确定性知识入口路由 | 10 条真实质检路线 `10/10`，人员/交付集成盲测 `10/10` |
| `3a9715d` / `experiment/development-harness-v1` | M2 限定范围成熟度同步 | 103 项回归、Skill 与知识检查通过；M2 为 `Verified@quality-check-trusted-query-slices` |
| `6deafb9`—`183fc6d` / `experiment/development-harness-v1` | 来源身份、兼容机制与相邻代码回写收敛 | 验收未完成量第五轮 `24/24`；108 项回归通过；回写在声明切片升级为 verified |
| `a5104ec` / `release/development-writeback-harness-v1` / `harness-development-writeback-v1-rc1` | 当前干净 Harness 候选发布 | 已推送远端；M1/M3 按切片验证，M4 为已实现并真实试用但尚未 verified |
| `a2f790e` / `experiment/development-harness-v1` | 今晚验证后的实验 Harness | 已推送远端；108 项回归通过，M4 在同系统相邻增量切片 verified，并保留精确契约 holdout 限制 |
| `3c87fca` / `experiment/development-harness-v1` | 组件地图基线 | 组件实体与实际使用方式已整理，109 项回归通过；作为后续开发交互实验的起点 |
| `3595182`—`ae54c8a` / `experiment/development-harness-v1` | OpenCode 缺口详情交互收敛版 | 同题由 `18/20` 提升到 `20/20`；完整焦点闭环和证据声明通过，109 项回归与知识检查通过，已推送远端 |
| `36d266e`—`ab902c6` / `experiment/development-harness-v1` | 本地软件工作审查收敛版 | 正向报告 `17/18`；错位身份阻断和简单任务不触发通过；110 项 Harness 回归与知识检查通过，尚未推送 |
| `fa8438b` / `experiment/reader-first-knowledge-v1` | 质检知识阅读体验认证参考 | 22 个用户可见页面经用户多轮审视后形成最佳当前结果；用于 Trial 后审计，不进入盲测输入 |
| `3b98c89`—`ab0c7a3` / `release/reader-first-ingestion-harness-v1` / `harness-reader-first-ingestion-v1` | 整库阅读整改 Harness Release | 007 中 OpenCode 弱模型用小批页面完成 27 页审视，内容 `93/100`；99 项发布回归与知识结构检查通过，已推送远程 |

M1 同批优化和发布已经收口。M2 已在质检中文知识问答切片内验证，M3 已在页面、SQL 和跨层算法三类质检开发切片验证。M4 在同系统相邻增量首次达到冻结内容接受线，但快照导入 holdout 仍证明精确契约和运行状态会遗漏。

当前不继续调试“验收分配缺口详情”或同一审查用例。下一主线是“模糊开发需求到可审方案”：使用已保留的人工质检多维结果分析诉求，形成需求理解、系统上下文、影响范围、方案选项、人工决定点、验证计划和开发交接，再复用已验证的 `review-work` 审查。候选实验优先使用 OpenCode + DeepSeek V4 Flash；供应或额度失败后切 Codex + GPT-5.6 Luna high，供应失败不计内容 Trial，同模型续接不冒充跨模型证据。

## 8. 每次 Trial 必须冻结什么

一次有效 Trial 至少留下：

1. 固定 Harness、模型、宿主、输入与自然语言 Prompt；
2. 候选规范知识、产品视图和唯一审查页；
3. 来源与正式知识是否被修改的证据；
4. 实际过程、失败动作、运行结果与人工介入；
5. 对认证参考和内容问题的人工比较；
6. 明确结论：晋升、修订、停止或否定当前方案。

只有本地测试而没有真实候选内容，状态是 `implemented`；只有一次高分但不能稳定复现，不能升级为 `verified`。
