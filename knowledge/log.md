# knowledge/log.md
# append-only 知识库操作时间线
# 格式：## [YYYY-MM-DD] <操作类型> | <标题>
# 操作类型枚举：init | ingest | query | health | migrate | update | compile
# 用 grep "^## \[" log.md | tail -10 查看最近操作

## [2026-07-06] init | Omni-Brain 知识库初始化

- 创建：knowledge/ 目录结构
- 创建：taxonomy.yaml（v1.0）
- 创建：index.md（空黄页骨架）
- 触发：项目 Phase 0 初始化
## [2026-07-10] ingest | Omni-Brain 产品基调讨论稿 v0.1

- 新增 `raw/conversations/2026-07-10-product-direction-discussion.md`：记录 Omni-Brain 产品基调讨论原料。
- 新增 `synthesis/omni_brain_product_direction_v0_1.md`（draft）：提炼工作、开发与业务知识系统的暂定定位和待验证原则。

## [2026-07-10] update | 补充人的使用模式与知识演进治理

- 新增 `raw/conversations/2026-07-10-product-direction-discussion-02.md`：保存使用模式、变更安全、混沌知识库和元演进问题。
- 重构 `docs/product-direction-discussion.md` 的人类使用与长期维护章节，引入稳定骨架、预设/临时视图、可回滚 change set、brownfield 治理和四层评测。
- 更新 `synthesis/omni_brain_product_direction_v0_1.md`（仍为 draft），补充本轮暂定原则与待验证事项。

## [2026-07-10] update | 重构项目操作契约并澄清知识底座与视图

- 完全重写根级 `AGENTS.md`：改为围绕当前使命、发现阶段、决策成熟度、知识/视图工作模型和安全变更协议的项目操作契约。
- 新增 `raw/conversations/2026-07-10-product-direction-discussion-03.md`：保存知识骨架与视图关系的澄清问题。
- 重构 `docs/product-direction-discussion.md`：将“三层结构”修正为“一个规范底座、两类投影视图、一个横切治理控制面”。
- 更新 `synthesis/omni_brain_product_direction_v0_1.md`（仍为 draft），补充最小骨架发现阶段和视图关系。

## [2026-07-10] ingest | 质检领域首个真实场景

- 新增 `raw/conversations/2026-07-10-quality-domain-real-scenario.md`：保存用户问题和外部质检知识来源范围。
- 新增 `docs/scenarios/quality-domain-knowledge-workbench.md`：梳理真实工作场景、痛点、业务目标、产品形态、候选知识坐标和验证旅程。
- 新增并登记 `synthesis/quality_domain_real_scenario_v0_1.md`（draft），与产品基调卡建立双向关系。
- 更新 `docs/product-direction-discussion.md`：将质检领域登记为首个真实验证场景。

## [2026-07-11] update | 质检知识底座、视图与公共基建候选架构

- 新增 `raw/conversations/2026-07-11-quality-substrate-and-views.md`：保存知识图谱扩展、产品视图和跨域公共基建问题。
- 重构 `docs/scenarios/quality-domain-knowledge-workbench.md`：补充事实源/规范底座/派生结构承载模型、小核心与上下文包、节点关系准入、有界遍历、视图模板和公共基建唯一落点。
- 更新 `docs/product-direction-discussion.md` 与 `synthesis/quality_domain_real_scenario_v0_1.md`（仍为 draft），登记本轮候选原则和待验证事项。

## [2026-07-11] ingest | 建立 Omni-Brain Blueprint 总入口

- 新增 `raw/conversations/2026-07-11-blueprint-convergence.md`：保存项目收束、架构、进展、差距和路线统一入口需求。
- 新增 `docs/blueprint.md`：统一记录项目目标、顶层架构、组件成熟度、设计原则、质检覆盖、当前焦点、路线和开放问题。
- 更新 `AGENTS.md`：将 Blueprint 设为产品定位、当前进度与路线的首要入口。
- 更新 discussion、质检场景和产品方向卡：明确文档职责和下钻关系，避免多个文档同时冒充当前架构总览。

## [2026-07-11] update | 人工质检能力建设的长期牵引与短期产物闭环

- 新增 `raw/conversations/2026-07-11-manual-quality-capability-building-direction.md`：保存人工质检真实痛点、短中长期目标和 Omni-Brain 角色校正。
- 新增 `docs/problems/2026-07-11-manual-quality-capability-construction-gap.md`：将分散知识、手工跟踪和脚本依赖分诊为能力建设闭环问题。
- 更新 Blueprint、产品方向讨论稿和质检场景：明确完整质检平台能力建设闭环作为长期牵引，具体能力产物作为短期实验。
- 更新当前工作台与两张 draft Synthesis 卡：登记双重验收、首个产物候选和待验证的组件边界。
- 保留“验收任务分配闭环”为候选而非最终决定；未新增运行态或动作控制顶层组件。

## [2026-07-11] update | 能力切片证据分级与验收发现入口

- 新增 `raw/conversations/2026-07-11-acceptance-capability-experiment-entry.md`：保存用户对首个切片验证深度的确认和验收任务不同起点问题。
- 新增 `docs/specs/capability-slice-experiment.md`（Provisional）：定义 L1 路径跑通、L2 可信闭环、L3 可复用和 L4 跨场景泛化。
- 明确组件全局成熟度与切片证据分开；首个人工质检切片以 L2 为目标，允许显式人工步骤但不允许不可观察的人肉补偿。
- 更新 Blueprint、产品讨论稿、质检场景、问题案例和当前工作台；将知识发现与需求明确的先后关系保留为首个实验问题。

## [2026-07-11] update | 讨论结论与行动交接规则

- 更新 `AGENTS.md`：重要讨论必须同时给出当前判断、结论收束和可执行行动交接。
- 更新 `docs/specs/conversation-knowledge-lifecycle.md`：定义用户动作、Agent 动作、预期产物、无动作影响和常用互动表达的触发结果。
- 新增 `docs/problems/2026-07-11-discussion-action-handoff-unclear.md`（experimenting）：记录用户无法从开放式总结判断如何继续的问题及五轮验证计划。
- 更新 `docs/now.md`：登记讨论行动交接实验。按用户选择，本轮未保存逐字原始会话。

## [2026-07-12] update | 任务知识准备与长期知识复利边界

- 按用户要求只沉淀结构化结论，未保存逐字原始对话，也未把 provisional 产品判断新建为规范知识卡。
- 修正首个验证主线：人工质检验收先作为测试夹具，优先建设可由基础模型调用和重放的任务知识准备能力；领域工具不是当前首要结果。
- 明确任务知识准备包含目标澄清、存量盘点、缺口分类、补知、编织、验证和决策准备度门禁，检索无结果不等于允许模型自由补写。
- 明确双重产物与门禁：本次任务投影默认短生命周期；稳定新增知识作为变更候选进入规范底座和人类浏览视图，避免一次性碎片与重复准备。
- 更新 Blueprint、产品讨论稿、质检场景、能力切片实验协议和当前工作台；所有新增判断保持 provisional，待验收实例和基础模型重放验证。

## [2026-07-12] update | 渐进式任务路由与任务知识准备 Skill

- 更新 `AGENTS.md`：加入 A 直接执行、B 有界上下文、C 完整知识准备的最低充分路由、动态升降级规则和组件进入默认工作方式的成熟度门槛。
- 重构 `.agents/skills/knowledge-query/SKILL.md`：删除“所有非平凡任务强制检索”，明确其为无状态、有边界的存量知识查询；当前检索脚本为 stub 时必须标记人工降级。
- 新增并注册 `.agents/skills/task-knowledge-prep/SKILL.md`（experimental）：由 Agent 会话驱动，以任务工作区保存可恢复状态，编排查询、补知、编织、双门禁和知识交接。
- 按当前约定未新增任务知识准备 Spec，也未实现 `task_case.py`；文件工作区和人工门禁只能作为可测基线，不能声称组件已验证。

## [2026-07-12] update | 安装写作 Skill 并重写知识工作流 Skills

- 将用户级 `writing-great-skills` 完整安装到项目 `.agents/skills/` 并注册，使 OpenCode/项目 Agent 可直接发现；保留其 `GLOSSARY.md` 渐进披露词汇表。
- 按可预测性、单一事实源、完成标准和防止 sediment/sprawl 的原则重写 `knowledge-query` 与 `task-knowledge-prep`。
- `knowledge-query` 收敛为“定界—查询—收束”三步，不重复 AGENTS 路由或写死当前 stub 状态；每步都有可检查完成标准。
- `task-knowledge-prep` 收敛为可恢复账本上的五步循环，复用查询 Skill 的缺口类型，保留任务投影/长期候选分流和双门禁。

## [2026-07-12] implementation | 最小任务知识准备案账本工具

- 新增 `scripts/task_case.py`：以 PyYAML 和 Python 标准库实现任务案创建、状态恢复、事件/证据追加、机械双门禁、视图重建与受控关闭。
- 新增 `tests/test_task_case.py`：覆盖可恢复目录、门禁前后变化、关键冲突阻断、陈旧门禁复核和明确终止；5 项测试通过。
- 新增 `eval/datasets/task_case/acceptance_exploration.yaml`：把人工质检验收探索定义为首个恢复与阻断夹具，不把领域工具实现作为当前产物。
- 更新 `task-knowledge-prep`、Blueprint 和当前工作台接入脚本；当前状态仅为 `Implemented@mechanical-ledger`，尚未形成真实新会话或基础模型重放证据。

## [2026-07-12] experiment | 首次基础模型任务案恢复重放

- 用户提供 Gemini 新会话的结果与完整执行轨迹：目标、焦点、阻塞和门禁恢复准确，但过程先猜测 Skill、逐层搜索、全量读取、下钻源码，并在 PyYAML 缺失后探索环境和直接安装依赖。
- 将本次证据评定为“结果通过、引导失败”，不能据此声称任务案恢复组件已验证；摘要写入任务案 Evidence，未保存完整原始会话。
- 更新 `AGENTS.md`：显式 case ID 直接读取权威 `case.yaml`，按门禁和引用渐进下钻；仅查看状态不加载 `task-knowledge-prep`，不得为恢复自行安装或切换环境。
- 更新恢复评测夹具，新增零搜索、零无关读取、零环境变更指标及禁止路径；新增 q-004 等待同类基础模型复测。

## [2026-07-12] update | AGENTS 自治理与最小评测策略

- 按用户要求只沉淀结构化结论，未保存本轮逐字原始对话；`knowledge-ingest` 的检索、索引与编译脚本仍为 stub，本轮使用协议化人工分流，不声称完成自动知识摄入。
- 新增 `docs/specs/agents-contract-governance.md`（Provisional）：定义操作契约职责、准入、替换优先、容量触发和行为回归；AGENTS 只保留最小治理内核，并移除动态实验状态。
- 新增 `docs/specs/evaluation-strategy.md`（Provisional）：定义代码、契约、Agent 行为和能力切片四层验证，区分硬门禁与软指标，并采用 E0—E4 隔离阶梯。
- 升级任务案恢复用例并新增 Gemini 两轮结构化 baseline；第二轮核心硬门禁通过，登记为 L1/单用例 route-core 证据，不升级组件整体 Verified。
- 外部调研仅用于校验最小对象边界：Inspect AI 与 Harbor 作为未来适配候选，当前不安装；现阶段优先冻结 fixture 和实现最小评分 runner。

## [2026-07-12] update | Agent 评测方法论校正

- 根据用户反馈修正此前偏基础设施的参考坐标：Anthropic Agent Evals 方法作为对象与生命周期主骨架，LangChain Deep Agents 用于行为 taxonomy、trace 驱动和正确性—效率分层。
- 新增 `docs/research/agent-evaluation-reference-review.md`：区分方法论、模型生成数据集、组件实证、被测能力和执行基础设施；gbrain、CodeGraph、Graphify 等用于 capture/replay、A/B、多 Trial 和能力发现，宣传指标仍待独立反证。
- 重写 `docs/specs/evaluation-strategy.md`：采用 Suite/Task/Trial/Grader/Transcript/Outcome，区分 Agent/Eval Harness、Capability/Regression、参考解、平衡任务、Grader 校准和 pass@k/pass^k。
- 将恢复用例迁移至 schema 0.2，并按 Outcome、范围、安全、质量和效率重新解释两次 Gemini Trial；尚缺冻结 fixture、参考解和 Grader 校准，因此暂停 Runner 实现。
- 未保存外部网页全文或本轮逐字对话；检索/编译 stub 未被当作已执行的自动摄入能力。

## [2026-07-12] experiment | 恢复 Task v2 fixture 与 Grader 校准

- 冻结 `acceptance_knowledge_prep_v1` 最小 fixture，并提供能通过必需 Grader 的参考响应；不复制后续活跃任务状态。
- 新增 `TC_UNKNOWN_CASE_001` 反向任务，检查不存在 ID 时不自动创建、不编造和不加载推进工作流。
- 新增人工校准报告：Outcome、权威范围和安全作为必需 Grader；固定顺序、目录列表和短事件读取只作效率参考。
- q-005 已由结构化证据回答；下一步允许测试先行实现“不调用模型、只评分已提供 Trial”的最小 Runner。

## [2026-07-12] audit | Skill 体系与 Eval 知识生命周期

- 新建可恢复任务案 `skill-system-audit`，审计 `.agents/skills/` 九个项目 Skill 的来源、蓝图归属、实现真实性、触发风险与证据等级。
- 新增 `docs/research/skill-system-audit-2026-07-12.md`：确认七个 Skill 首次出现于 Phase 0，其中 `knowledge-query` 后来已重写，其余六个基本保持初始化契约；`knowledge-ingest`、`eval-runner`、`knowledge-health`、`code-ingest` 等存在 stub 或不存在接口的超前声明。
- 新增 `docs/specs/skill-system-governance.md`（Provisional）：Skill 必须区分操作/编排/参考职责，采用强度与产品成熟度分离，并用正反任务和 change set 决定是否进入默认工作方式。
- 新增并登记 `synthesis/agent_evaluation_methodology_v0_1.md`（draft）：只吸收已形成项目采用边界的 Eval 方法；外部逐项分析继续留在 research，具体对象与门禁留在 spec，运行证据留在 `eval/`。
- 由于现有 `knowledge-ingest` 契约与 stub 状态不一致，本次使用受控人工分流完成摄入，没有保存外部网页全文，也未声称执行了自动检索、冲突检测或索引编译。

## [2026-07-12] implementation | Skill 首轮治理

- 测试先行新增 `tests/test_skill_contracts.py` 和 13 项 `skill_governance_v1.yaml` 路由 fixture，覆盖正触发、反触发、stub、缺失 Runner、任务反思和 Skill 自动固化。
- 重写 `knowledge-ingest`：仅处理明确授权的长期知识变更或已批准候选，强制分流 research/spec/knowledge/eval/task，当前工具不可用时记录 `manual_fallback`。
- `eval-runner`、项目 `skill-creator`、`task-reflector`、`knowledge-health`、`code-ingest` 直接从活动 Skill 目录删除；对应 Runner、健康检查和代码摄入实现存在前不得恢复能力声明。
- 删除无仓库消费者的 `.agents/skills.json`；不把“维护 registry”新增为产品问题，当前以活动目录事实为准。
- 未创建新的 `skill-change-proposal`；长期 Skill 变更继续作为 C 类任务形成 change set，避免在无行为证据时重复扩张。
- 当前结果为 `Implemented@contract`：静态契约和既有任务案测试通过，但尚无独立 Agent Trial，不升级为 verified。

## [2026-07-18] correction | 真实工况与可用结果优先

- 用户指出旧 M1 在未确定知识摄入用户流程、存储结构和真实使用方式前，先扩建了脚本、Schema、控制面与 Eval，导致技术产物很多但没有可用能力。
- 更新 `AGENTS.md`：产品与公共能力工作必须从真实用户、真实输入、可观察结果、实际消费和验收证据反推；支撑性技术物不得冒充里程碑或产品进展。
- 撤回并清理旧 M1 的 Skill、CLI、Schema、合成 fixture/Eval、手工验收知识切片、架构包、任务案和独立 Harness 增量；保留真实原料、外部研究、C1—C10 和无关的任务恢复成果。
- 将路线改为 M1 知识摄入、M2 知识使用、M3 知识驱动真实任务、M4 知识随变化演进、M5 跨模型/领域/规模硬化；可移植性、治理和 Eval 改为横切门禁。
- 当前回到 M1 设计起点：先由用户确认工作流、知识落点、产品视图、人机分工和技术选项，再在独立 Harness 中用真实人工质检验收材料实现并运行最薄纵向切片。

## [2026-07-19] ingest | 登记 ChatGPT 质检项目原始资料集

- 用户将 ChatGPT 质检项目的 25 个文件人工下载到 `raw/quality_check/`；文件后缀为 `.txt`，实际内容为 UTF-8 Markdown，原文件保持不变。
- 新增 `raw/index.md`，登记资料集来源、规模、完整性指纹、内容导航和使用边界，供本次 M1 与后续任务共同复用。
- 原料中的状态与实现声明不自动升级为规范事实；后续按任务定向读取，并结合人工决定、固定代码版本和运行证据做去重与冲突检查。

## [2026-07-25] ingest | 登记 quality_materials 本地受限资料集

- 登记仓库根 `quality_materials/` 的 17 个原始文件：共 5,123 行、204,555 字节，聚合指纹为 `422474ba2d4db4508dd58cb553fa51f1379352655b95904a434b3fbd7d29baf9`。
- 新材料覆盖一站式质检平台、人工质检、验收、ConfigManager、数据库、快照、前端源码和工程导读，是后续知识摄入与本地能力复刻的优先来源。
- 因材料含生产连接和认证信息，原件保持本地受限并加入 `.gitignore`；规范知识和实验代码只消费接口、行为、边界和陷阱，不复制秘密值。
- 逐文件完整性、主题、用途和敏感级别登记到任务案 `quality-materials-knowledge-and-replication`；后续先处理与 `raw/quality_check/` 的重复、补充、冲突和现实形态，再进入规范知识与代码。

## [2026-08-30] publish | 已认证质检知识进入产品主线

- 将用户认证参考 `experiment/reader-first-knowledge-v1@fa8438b` 的 33 篇正式知识与产品视图收编到 `knowledge/published/quality-check/`；内容保持原版本，不以本次目录迁移改写事实。
- 根 `knowledge/index.md` 成为全局入口，显式区分已发布规范知识、不可变原始资料和 `eval/` 中的实验/评分证据。
- Agent 注册表改为从当前主线 `harness.yaml` 读取能力，并以主线 HEAD 建立 Run worktree，使知识、Skills、产品代码和评测资产处于同一可追溯版本。

## 2026-09-13：个人工作台的知识与代码入口

在 index 登记跨领域阅读视图，指向现有金铲铲、正式质检知识、共作、技能和历史实验；规范正文与 raw 原料未改。YYH-7 继续跟踪缺失历史文件，YYH-15 跟踪已验证的子事项委托修复，YYH-16 跟踪 Spider 复用审查。目录只提供导航，不把旧实验或未核实材料晋升为正式知识。变更与回退见 workspaces/reviews/personal-workbench-operating/review.md。
