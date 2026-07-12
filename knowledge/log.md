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
