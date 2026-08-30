# 团队 AI 协作与交付中枢：产品设计终稿

> 状态：`approved`
>
> 日期：2026-08-30
>
> 依据：[`team-ai-collaboration-delivery-hub-product-design-v2.md`](../team-ai-collaboration-delivery-hub-product-design-v2.md)、此前讨论、当前 Agent 能力工作台真实实现、Omni-Brain Blueprint 与 Harness。
>
> 本文是产品与系统边界的唯一批准终稿。源稿保留为讨论依据，不作为实施真相；目标能力不代表已经实现。

## 1. 最终产品判断

这套产品不是“Agent 管理页”，而是团队工作的 AI 协作控制面：

> 让团队把灵感、明确请求和日常工作，经过人和 Agent 的持续协作，转化为可安排、可执行、可验证、可追溯的成果；再把真实任务中的知识、反馈和失败，转化为评测与能力改进候选。

产品必须把以下信息连成一条可理解的工作链：

```text
为什么出现
→ 团队决定做成什么
→ 是否承诺投入
→ 人与 Agent 怎样协作
→ 在什么代码、知识和环境上执行
→ 形成了什么结果与证据
→ 人是否接受
→ 是否沉淀为知识、评测和能力改进
```

对任意一件真实工作，另一名团队成员无需翻聊天记录，就应能回答：

1. 最初为什么提出；
2. 当前是灵感、候选需求、正式需求还是已承诺工作；
3. Agent 做过什么，人纠正、拒绝或批准了什么；
4. 当前正式需求、计划和验收标准是哪一版；
5. 产出了什么代码、报告、验证和知识；
6. 下一步由谁在什么条件下推进。

页面数量、Agent 数量和自动化比例都不能代替上述用户结果。

## 2. 产品边界与现有系统关系

| 层 | 责任 | 明确不负责 |
|---|---|---|
| 团队 AI 协作工作台 | Idea、候选/正式需求、Work、人机讨论、负责人、决定、成果全景 | 不实现模型推理，不复制代码和知识全文 |
| Omni-Brain Harness | 取知、需求/方案形成、开发、验证、审查、知识回写与评测方法 | 不承担团队业务记录和页面运行态 |
| Agent Runtime | 启动能力、维护 Run、捕获规范事件和原始失败 | 不决定需求优先级、业务接受与发布 |
| Codex / OpenCode | S0/S1 的两个 CLI 执行器；Codex 主要用于开发建设，OpenCode 主要用于评测和对照 | 不是协作历史和业务状态的事实源 |
| Worker Runner | 未来负责工作区、进程、资源、租约和产物回传 | 首版不建设远程调度 |
| PostgreSQL / Git / ArtifactStore | 分别保存业务状态、代码/正式知识和大体积运行产物 | 不相互复制形成第二事实源 |

### 2.1 物理宿主

S0/S1 继续使用主线 `apps/quality-platform/` 的 Vue3、FastAPI、PostgreSQL 公共能力和现有 Agent Runtime，不新建另一套 React 前端、SQLite 控制面或微服务系统。

协作能力在代码和数据上作为跨领域模块存在，不能写进 `manual_qc`。质检、知识、研发和其他领域页面可以嵌入协作动作，但共用同一套 Idea、需求、Work 和 Run 事实。

只有跨团队部署、独立伸缩或安全边界真实要求出现后，才讨论从现有模块化单体拆分服务。

### 2.2 用户看到“能力”，平台保留精确版本

普通用户无需区分 Agent、Harness、Skill、Preset 和 CLI。产品统一展示“能力”：能解决什么问题、需要什么输入、产生什么结果、历史任务效果、当前版本和已知边界。

平台内部必须保留：

```text
capability_id / version
prompt / skill / tool / harness version
model provider / model id / config
executor type / version
knowledge context digest
repository / base commit
verification recipe version
```

S0/S1 同时接入 Codex CLI 和 OpenCode CLI。Codex 是开发、方案和后续平台建设的默认执行器；OpenCode 是评测、重放和对照任务的默认执行器。默认值是能力策略，不是硬编码限制：用户可以在能力允许的范围内显式选择执行器和模型。

## 3. 核心业务对象

### 3.1 主链路

```text
Idea（可选）
  ↓ 转为候选需求
Requirement(status=candidate) + Revision
  ↓ 需求评审接纳
Requirement(status=accepted)
  ↓ 承诺 NOW 或 NEXT
Work / 正式工作
  ↓
WorkPlan → Agent/Human Steps → 结果、验证、审查与接受
```

事故、强制事项或明确业务请求可以直接创建 `candidate` Requirement；监控、调查、数据处理等轻量执行也可以直接创建 Work。不是所有对象都必须从 Idea 开始，也不是所有 Work 都必须是软件开发。

### 3.2 三层业务语义

| 对象 | 解决的问题 | 最低内容 | 不代表什么 |
|---|---|---|---|
| Idea | 先不丢掉一个想法、观察或机会 | 原始内容、来源人、时间、可选领域 | 不代表存在正式需求或团队会投入 |
| Requirement | 从候选到接纳始终保存同一需求及其版本 | 问题、用户结果、价值、范围、验收、未知、来源、Revision | `candidate` 不代表已接纳；`accepted` 不代表已排期或已冻结方案 |
| Work | 表示团队已经决定实际执行和验收的一次工作 | Owner、时间盒/窗口、目标、输入、输出、完成证据、计划 | 不一定是开发，也不等同于一次 Agent Run |

Idea 与 Requirement 保留来源关系，不通过覆盖原文“升级”。Requirement 从 `candidate` 到 `accepted` 保持同一业务身份，内容变化使用不可覆盖的 Revision，并记录评审、批准或取代关系。

### 3.3 执行与协作对象

| 对象 | 责任 |
|---|---|
| Thread / Entry | 围绕一个业务对象持续的人机讨论、候选结果和活动时间线 |
| Decision | 接纳、驳回、延期、合并、批准、返工和结果接受等正式决定 |
| WorkPlan / PlanStep | 显式、可编辑、可版本化的工作步骤与输入输出契约 |
| Agent Run | 某个能力的一次原子执行；沿用当前 `t_agent_run` |
| Run Event | Run 中追加写的输入、动作、工具结果、状态和错误 |
| Executor Session | Codex/OpenCode 原生会话句柄，用于恢复或补充查看 |
| Artifact / Evidence | 文件、Diff、Commit、报告、日志和验证结果的引用 |
| Knowledge Proposal | 经接受结果触发的知识变化候选 |
| Candidate EvalCase | 从真实任务抽取、尚待固定输入和评审的评测候选 |

### 3.4 Thread、Run 与 Executor session 必须分开

```text
Thread = 人与 Agent 围绕一件事持续协作的产品上下文
Run = 某个能力的一次不可覆盖的执行尝试
Executor session = Codex/OpenCode 用于定位或继续会话的技术句柄
```

一个 Thread 可以包含补背景、需求梳理和多次修订 Run；一次 Run 可以关联一个执行器 session。即使 Codex/OpenCode 的目录、进程或 API 已不可用，PostgreSQL 中的业务对象、规范事件、人的决定和结果摘要仍必须可读。

## 4. 状态与人工 Gate

不使用一个万能 `status`，但首版也不提前建设置信度、复杂健康度或过多枚举。

### 4.1 Idea

```text
captured → discussing → converted / archived
```

### 4.2 Requirement

需求从候选到正式接纳始终是同一对象，当前状态为：

```text
candidate / accepted / rejected / deferred / merged / superseded / closed
```

- `accepted` 保留原 Requirement 身份并冻结获准 Revision；
- `rejected` 必须记录原因；
- `deferred` 必须记录复审日期或重新打开条件；
- `merged` 必须指向承接 Requirement；
- 被驳回或延期后重新讨论时，新建 Revision 和评审记录，不覆盖历史。

只有 `accepted` Requirement 才进入团队投入承诺：

| commitment | 含义 | 必填信息 |
|---|---|---|
| `NOW` | 当前周期推进 | Owner、时间盒或目标时间、首个 Work |
| `NEXT` | 下一明确窗口推进 | Owner、预计窗口、进入条件 |
| `LATER` | 认可价值但暂不承诺 | 复审日期或触发条件 |

Requirement status 与 commitment 分开：`accepted + LATER` 表示需求成立但暂不承诺；`rejected` 不拥有 commitment。正式需求以后不再适用时，通过 `superseded / closed` 和独立原因记录处理。

### 4.3 Work

首批保持简单：

```text
planned → in_progress → verifying → done / cancelled
```

是否阻塞先通过显式 blocker 和活动记录表达；真实团队使用证明需要聚合后，再增加独立 health 字段。

### 4.4 Run

继续沿用当前排队、运行、成功、失败和取消。只有真正支持 Agent 提问并恢复后，才加入 `waiting_human`。

### 4.5 不可绕过的人工 Gate

1. Candidate Requirement 是否被接纳；
2. Requirement 哪一版可以进入承诺和执行；
3. 高风险方案是否可以施工；
4. 实际结果是否接受、是否 Push、创建 PR/MR 或合并；
5. 真实任务是否晋升为正式 EvalCase 或正式知识变更；
6. 能力候选是否晋升为生产版本。

Agent 可以生成候选、执行验证和总结证据，不能替人作以上决定。

## 5. Work 与工作计划

### 5.1 Work 是统一执行对象

以下事情都可以成为 Work：

- 开发、修复和架构变更；
- 调研与分析；
- 定时或持续观察；
- 数据获取和处理；
- 视频、日志和报告任务；
- 知识摄入与更新；
- 评测、对比和能力优化；
- 事故处置。

每个正式 Work 至少包含：

```text
work_type
source object
goal / expected outcome
owner / reviewer
timebox or target window
inputs / expected outputs
completion evidence
current WorkPlan revision
```

### 5.2 外层确定，步骤内 Agent 自主

工作步骤、输入输出、完成条件、批准点和返工方向由显式 WorkPlan 管理。Agent 可以建议计划，也可以在某一步内部自主查知识、调用工具或分解任务，但不能暗中修改 Gate、删除验证或直接控制执行机和发布权限。

首批 PlanStep 只需要：

```text
step_type              human / agent / external
capability_version     使用的能力版本
input_contract         显式输入及上游产物
output_contract        期望结果
completion_criteria    完成条件
verification           怎样证明完成
approval_policy        是否需要人工批准
retry_policy           失败后怎样处理
context_policy         注入哪些知识和业务上下文
```

### 5.3 工作配方渐进实现

目标产品可以覆盖以下稳定配方：

- Idea 到 candidate/accepted Requirement；
- 快速低风险变更；
- 标准开发；
- 架构与迁移变更；
- 调查分析；
- 监控观察；
- 数据获取处理；
- 报告文档。

S0 只实现 Idea 到 candidate/accepted Requirement 的确定性动作；S1 只实现一个 `standard_development_v1` 固定计划。首版不提供图形化 Workflow DSL，也不同时实现八种模板。第二种真实工作稳定复用后，再抽取可编辑模板和规划能力。

## 6. 三条代表性用户旅程

### 6.1 灵感到正式需求

```text
记录 Idea
→ 在 Idea 中查已有背景和相关工作
→ 人机讨论并保留原始想法
→ 创建 candidate Requirement
→ Agent 梳理问题、用户结果、范围和验收候选
→ 人修订并作需求评审
→ 接纳当前 Requirement Revision，状态改为 accepted
→ 记录 NOW / NEXT / LATER
```

需求评审只回答“为什么做、做成什么、怎样验收”，不冻结表结构、API、目录或最终 Agent 数量。只有会改变接纳决定的关键未知，才触发有界 Research Work。

### 6.2 正式需求到开发交付

```text
Requirement commitment = NOW
→ 创建 Work 与固定 standard_development_v1 WorkPlan
→ 获取最低充分知识上下文
→ 形成并批准方案
→ Codex 开发 Run
→ 真实验证 Run
→ 独立审查 Run
→ 人接受或返工
→ Branch / Commit / PR(MR)
→ Knowledge Proposal
→ Candidate EvalCase
```

低风险小变更以后可以压缩方案文档，但仍必须明确目标、改动、验证和审查摘要。数据库迁移、权限、共享契约或不可逆变化不能走快速通道。

### 6.3 非开发工作

```text
直接创建 Work
→ 明确输入、输出、完成证据和时间盒
→ 选择或生成显式 WorkPlan
→ 人与 Agent 完成分析/监控/数据/报告步骤
→ 人验收结果
→ 可选形成知识、candidate Requirement 或 EvalCase
```

非开发 Work 没有 Branch、Commit 和 MR，但仍具有计划、Run、反馈、Artifact 和验收。

## 7. 产品信息架构

### 7.1 一级导航

```text
AI 协作
├── 工作台       我的待判断、正在执行、失败/阻塞、近期成果
├── 灵感         Idea Inbox、讨论和转候选需求
├── 需求         Candidate/Accepted Requirement、评审和承诺
├── 工作         Work、负责人、计划、成果和验收
├── 能力         团队能力、适用范围、真实任务与评测效果
├── Runs         跨领域运行状态、错误诊断和详细轨迹
└── 管理设置     只显示已经实现的身份、执行和基础设施配置
```

工作站、评测与学习、Workflow 模板和知识提案在形成真实独立工作量前，不占一级导航。它们先分别进入管理设置、能力详情和 Work 详情。

### 7.2 工作台

工作台优先帮助人继续工作：

1. 等我判断：需求评审、承诺、方案 Gate、结果验收；
2. Agent 正在做：当前 Run、动作和进度；
3. 需要处理：失败、缺输入和验证不通过；
4. 近期工作：按时间盒、负责人和风险排序；
5. 最近形成：Requirement、Commit、报告、知识或评测候选。

### 7.3 领域内使用，全局治理

具体 Agent 动作从工作发生的位置触发：

- Idea：查背景、讨论、梳理 candidate Requirement；
- Requirement：形成方案、创建 Work；
- Work：开发、验证、审查、知识回写；
- 质检或知识页面：使用当前领域上下文发起能力。

全局能力与 Runs 页面负责发现、运行治理、历史效果和故障诊断，不成为所有业务任务的唯一入口。

### 7.4 详情页中心

Idea、Requirement 和 Work 详情共用一个交互原则：

- 顶部展示身份、负责人、阶段、当前决定和下一步；
- 主区是人的消息、Agent 候选、Run 摘要、修订和决定组成的协作时间线；
- 侧区展示当前结构化结果、关联对象、来源和证据；
- 具体 trace、stdout、工具调用和 payload 只在 Run 详情按需加载。

## 8. 前端读取与性能边界

必须继续沿用已经验证的渐进读取：

```text
列表 → 只读摘要、状态、负责人、最近活动和少量聚合计数
对象详情 → 才读正文、Thread 和关联对象
Run 详情 → 才读 prompt、结果、错误与增量事件
```

- Agent 目录启动时读取并缓存注册表，显式刷新才重新扫描；
- Idea、需求、Work 和 Run 列表不扫描本地 OpenCode 会话；
- 列表不高频轮询完整对象；
- 只有用户当前选中且仍在运行的 Run 才增量拉取事件，终态后停止；
- 后续可以用 SSE 改善当前详情体验，但 SSE 不是 S0 的前置条件；
- 余额、鉴权、模型不可用、工具和平台错误保持原始信息量，不统一压缩为“环境问题”。

## 9. 运行模型与渐进演进

### 9.1 当前和 S0/S1 的物理模型

```text
Thread
  └── Work / Requirement
        └── WorkPlan + PlanStep（S1）
              └── t_agent_run
                    ├── t_agent_run_event
                    ├── Codex/OpenCode session ref
                    └── Artifact references（S1）
```

当前 `t_agent_run` 继续表示一次原子 Agent 执行。S0 只给它增加明确的业务对象和 Thread 关联；S1 再关联 Work 和 PlanStep。失败后的重新执行新建 Run，不覆盖旧记录。

### 9.2 不立即物理拆分 WorkflowRun / StepRun / Attempt

v2 所区分的“完整计划执行、步骤运行、基础设施尝试”在目标语义上成立，但不应现在一次性拆成三套表：

- 当前没有远程 Worker、Lease 和同一逻辑步骤的基础设施自动重试；
- 已经验证的 `t_agent_run` 足以表达当前原子执行；
- 过早迁移会让 S0/S1 先服务基础设施模型，而不是用户旅程。

当远程 Worker 或自动恢复进入时，再增加：

```text
AgentRun（逻辑步骤执行）
  └── RunAttempt（绑定 Worker、Workspace、环境和 Lease）
```

只有真实出现“整套计划多次重放并需要独立身份”后，才增加 WorkExecution/WorkflowRun。该演进不改变 Idea、Requirement、Work 和 Thread。

### 9.3 规划与调度分离

未来的 Work Planning Capability 只能产出显式、可编辑的计划候选。确定性系统负责状态迁移、权限、最低 Gate、工作区和调度；未来 Dispatcher 根据 Worker 能力、Repo 权限、资源、负载和租约选择执行位置。

不建设拥有平台最高权限的“任务派发 Agent”。

## 10. 执行、工作区和多人边界

### 10.1 S0/S1 已冻结约束

- 同时支持 Codex CLI 和 OpenCode CLI，均通过统一 Executor Adapter 进入 `t_agent_run`；
- Codex 默认服务开发建设类任务，OpenCode 默认服务评测、重放和对照任务；
- 继续使用当前模块化单体和一个 Agent Runtime 服务；
- 使用独立 Git worktree 提供代码与文件隔离；
- 同一代码仓同时只允许一个写入型开发 Work；
- 不使用 Docker；
- 不声称隔离进程、端口、CPU、内存、网络、依赖或凭据；
- Codex/OpenCode CLI 进程与临时端口由各自执行器管理，平台不扫描其他目录或端口；
- 多个执行器工作目录或服务不能共享未显式登记的 session。

### 10.2 worktree 能解决什么，不能解决什么

worktree 能隔离：

- 代码文件；
- Git index；
- 分支和工作成果。

worktree 不能隔离：

- 进程和端口；
- 系统依赖；
- CPU、内存和网络；
- 用户凭据；
- 同名外部服务与共享数据库。

S1 通过“单仓一个写入型 Work、固定 base commit、独立分支和显式环境约束”控制风险。只有并发、依赖冲突或安全边界真实暴露后，才引入 Docker 或远程 Sandbox。

### 10.3 团队 Worker 是后续独立纵切

多人和多工作站阶段采用轻量 Runner 主动注册、心跳、Pull 和 Lease，不由中心平台 SSH 进入员工机器。Runner 负责创建独立 workspace、调用 Executor、捕获事件和上传产物。

Docker 在这一阶段仍是可选环境隔离机制，不替代 worktree/clone；是否成为必选由真实依赖冲突和安全要求决定。

## 11. 事实源与数据切片

### 11.1 事实源

| 内容 | 权威事实源 | 平台保存方式 |
|---|---|---|
| Idea、Requirement、Work、Owner、Decision | PostgreSQL | 完整结构化业务记录 |
| Thread、人的消息、Run 状态和规范事件 | PostgreSQL | 时间线、状态、摘要和必要小型 payload |
| Codex/OpenCode 原生会话 | 各执行器自身 | 保存 executor + session ref，用于恢复和补充查看 |
| Branch、Commit、PR/MR 和代码 | Git / 托管平台 | 保存引用、摘要与同步状态 |
| 正式知识 | Git Markdown 知识仓 | 保存知识版本、候选与审查状态 |
| 大日志、附件和完整运行包 | ArtifactStore | S1 先使用本地文件 URI，团队阶段再按需切 NAS/OBS |
| 密钥 | 本机环境或后续 Secret Provider | 平台只保存 profile 引用，不写进 Prompt、事件或 Artifact |

当前 Run 事件不为了远期 ArtifactStore 立即迁移。S1 只把大日志、附件、Diff 和报告写入统一 `ArtifactStore` 接口；PostgreSQL 保留可查询的关键事件、摘要、URI 和 checksum。

### 11.2 S0 候选数据变化

```text
t_collab_idea
t_collab_requirement
t_collab_requirement_revision
t_collab_thread
t_collab_thread_entry
t_collab_decision
t_agent_run 增加 subject_type / subject_id / thread_id / trigger_action
```

### 11.3 S1 候选数据变化

```text
t_work
t_work_plan
t_work_plan_step
t_agent_artifact
t_knowledge_context_snapshot
t_knowledge_proposal
t_eval_case（先支持 candidate）
```

### 11.4 后续才增加

```text
t_agent_worker
t_run_attempt
t_task_lease
t_executor_registry
t_runtime_profile
t_eval_run / comparison / learning_candidate
```

首版不创建万能 `object` 表、万能 `object_link` 或几十张空表。跨对象关系先使用明确外键；稳定的任意关系需求出现后，再增加受控 link。

## 12. 开发交付与审查包

S1 的标准开发计划固定为：

```text
Requirement Revision
→ Knowledge Context Snapshot
→ Solution Revision + 人工 Gate
→ Development Run
→ Verification Run
→ Review Run
→ Human Acceptance
→ Branch / Commit / PR(MR)
→ Knowledge Proposal
→ Candidate EvalCase
```

交付详情需要自动组合一份 `Delivery Dossier / 交付审查包`：

1. 原始 Idea、candidate Requirement 或直接请求；
2. 需求评审决定和当前 Requirement Revision；
3. 方案、替代方向和人的关键纠正；
4. Base commit、分支、Commit、Diff 和影响范围；
5. 实际验证环境、命令、输入、结果和附件；
6. 独立审查发现、必须修改项和剩余风险；
7. 人工接受、发布与回滚决定；
8. Knowledge Proposal 和 Candidate EvalCase。

Git 托管平台仍是 Commit、PR/MR、Review 和 Merge 的事实源。平台可以生成审查包和链接，但 S1 的 Push/PR 遵循第 15 节冻结边界：必须人工确认；Merge 始终保留人工决定。

## 13. 知识、评测与能力学习

### 13.1 知识进入任务

每个重要 Work 在执行前形成有界 Knowledge Context Snapshot：

```text
knowledge repository / commit
需要回答的问题
选中的正式知识和直接事实源
关键事实、未知、冲突与适用范围
digest 和生成时间
```

任务接受后检查知识影响，只生成候选 Diff，不直接发布正式知识。

### 13.2 第一版只评两个维度

| 维度 | 关注点 |
|---|---|
| 最终结果 | 是否忠实满足目标，结果和验收证据是否成立 |
| 中间轨迹 | 是否使用正确上下文、响应人的纠正、遵守关键边界且没有无依据扩展 |

先由一个明确指定的 Judge 或人工规则完成，不增加置信度路由和多 Judge 仲裁。余额、鉴权、模型、工具和环境失败作为运行事实单独分类，不混入能力质量得分。

### 13.3 真实任务到能力改进

```text
真实 Run 与人的反馈
→ Candidate EvalCase
→ 固定输入、预期结果/rubric 和验证方式
→ 人工批准为正式 EvalCase
→ 回归对比
→ Skill / Prompt / Tool / Harness 修改候选
→ 人工批准、发布和回滚
```

Agent 可以提出和自测候选，不能在线修改生产能力并自行晋升。

## 14. 分阶段落地

### S0：需求治理自举

目标：把“建设团队 AI 协作与交付中枢”本身作为第一条真实 Idea 放进平台，完成一次人机需求治理。

实现：

- 固定服务端身份 `admin`，不实现登录、用户切换和权限；
- Idea、candidate/accepted Requirement 与 Requirement Revision；
- Thread、Entry 和 Decision；
- “查背景”和“梳理需求”两个现有能力动作；
- `CodexCliExecutor` 与现有 OpenCode 执行器统一接入 Run；
- Codex 作为协作与开发建设默认执行器，OpenCode 作为评测/对照默认执行器；
- Run 与业务对象/Thread 关联；
- 列表摘要、详情按需加载和当前 Run 增量事件。

完成证据：

- 一分钟内记录不完整 Idea，原文不被 Agent 覆盖；
- Idea 和直接请求都可以创建 candidate Requirement；
- Requirement 评审只冻结 R1，不要求 R2；
- 人的修订产生新的候选或 Requirement Revision，旧记录仍可见；
- 接纳后保持同一 Requirement 身份、状态变为 accepted；S0 记录 NEXT/LATER，NOW 在 S1 创建首个 Work 时开放；
- Codex 和 OpenCode 各完成至少一次真实 Run，规范事件、session、结果和具体失败均可追溯；
- 使用 `admin` 身份能从页面回答第 1 节六个问题；S0 不声称已验证多人审计。

### S1：第一个由平台管理的真实开发闭环

推荐用例：

> 从已批准 Requirement 创建 Work 和固定 WorkPlan，并在 Work 页面启动、关联开发/验证/审查 Run，回填 worktree、分支、Commit 和接受决定。

S1 本身作为 S0 中的第一个 accepted Requirement 跟进。实现继续使用 Codex/OpenCode CLI、单服务、单仓单写入和 worktree，不使用 Docker；开发步骤默认 Codex，评测和对照步骤默认 OpenCode。

完成证据：

- Work、Owner、Reviewer、时间盒和完成证据明确；
- 固定 `standard_development_v1` 从方案走到人工接受；
- 每个 Run 关联明确步骤、输入版本和上游结果；
- worktree、base commit、分支、Commit、真实验证和审查可追溯；
- 交付审查包从事实对象自动组装；
- 形成 Knowledge Proposal 和 Candidate EvalCase；
- 失败重跑不覆盖旧 Run，原始错误不丢失。

### S2：团队执行可靠性

只有团队实际多人使用后再实现：

- 可信身份认证、多人 Owner/Reviewer 和权限；
- Worker 注册、心跳、Pull、Lease、Drain 和 Lost/Retry；
- AgentRun 下的 RunAttempt；
- 本地 ArtifactStore 向 NAS/OBS 的切换；
- 多工作目录和执行端点的显式登记；
- 按真实需要加入 Docker、固定镜像和更强 Secret/网络策略。

### S3：多类 Work 与计划修订

- 快速变更、调查分析、监控观察等第二类真实配方；
- WorkPlan Revision；
- Step Retry/Fork/Take Over；
- 人工打断与恢复；
- 稳定后才增加规划能力和模板编辑。

### S4：评测与能力治理

- Replay Package；
- 正式 EvalCase、版本对比和失败聚类；
- Learning Candidate；
- 回归、灰度、批准、发布和回滚。

多 Agent Team、图形化 Workflow DSL 和耐久工作流引擎均无当前排期；出现已验证需求后另行立项。

## 15. 已冻结的决定

以下结论来自用户已明确约束、当前真实实现或 v2 已充分论证，可直接作为后续规格边界：

1. 平台是团队 AI 协作与交付控制面，不是 Agent 聊天壳或通用项目管理工具。
2. 业务对象与执行器分离；Codex/OpenCode session 不是业务事实源。
3. 需求评审只冻结“为什么做、做成什么、怎样验收”，详细方案后置。
4. Work 是开发、分析、监控、数据和知识等正式执行的统一对象。
5. Agent 只能建议显式计划；状态、权限、Gate、工作区和未来调度保持确定性。
6. 具体 Agent 能力在领域对象中使用，全局工作台治理跨领域待办、能力和 Run。
7. 首版复用现有 Vue3、FastAPI、PostgreSQL 和模块化单体，不另建技术栈。
8. S0/S1 同时支持 Codex 和 OpenCode；Codex 默认用于开发建设，OpenCode 默认用于评测和对照。
9. S0/S1 使用 worktree 和单仓单写入，不使用 Docker，也不夸大隔离能力。
10. 当前 `t_agent_run` 继续作为原子 Run；不立即拆 WorkflowRun/StepRun/Attempt。
11. PostgreSQL 保存业务状态和规范事件；Git 保存代码和正式知识；大产物通过可替换 ArtifactStore 引用。
12. 列表只查摘要，详情按需加载，只有选中且活跃的 Run 增量刷新。
13. 完整 trace、规范事件和正式 Decision 分离，不依赖模型隐藏思维链。
14. 第一版评测只覆盖最终结果和中间轨迹，不引入置信度路由。
15. Agent 不能自动接受需求、Merge、发布知识或晋升生产能力。
16. 首版用固定纵切，不做通用 Workflow DSL、万能调度 Agent 和多 Agent 集群。
17. Requirement 同时承载候选和正式需求，以 `candidate/accepted` 等状态和 Revision 区分，不保留独立 Proposal 对象。
18. S0 不做身份认证，所有业务动作由服务端固定 `admin` 执行；不声称支持可信多人审计。
19. Agent 可以创建分支、修改、验证并 Commit；Push/创建 PR(MR) 需要人工确认；Merge 始终人工。

## 16. 用户本轮已拍板

2026-08-30，用户明确批准：

1. 合并 Proposal 与 Requirement，以 candidate/accepted 等状态区分需求成熟度和评审结果；
2. S0/S1 同时引入 Codex 与 OpenCode，Codex 主要承接后续开发，OpenCode 主要运行评测；
3. S0 暂不建设身份认证，统一使用 `admin`；
4. Git 采用推荐边界：Agent 可分支、修改、验证、Commit，Push/PR(MR) 人工确认，Merge 人工。

S0 实施前已经没有需要用户继续选择的产品分叉。Codex JSONL 事件映射、取消、session resume、表字段、索引和本地 Artifact 目录属于 R2/PoC 责任；只有本机实际能力与公开契约冲突时，才回到用户决定替代路径。

## 17. 直接行动

不再继续扩写北极星文档，按以下顺序推进：

1. 形成 S0 可施工 R2：页面交互、API、PostgreSQL migration、权限、Run 关联、测试和回滚；
2. 在现有 Vue3/FastAPI/PostgreSQL 宿主实现 S0，并把本文对应想法作为第一条真实 Idea；
3. 用 S0 形成并批准 S1 Requirement；
4. 形成 S1 可施工 R2，用平台管理 Work、开发 Run、验证、审查和交付证据；
5. S1 通过后，再以真实团队使用决定 Worker、Docker、OBS、模板和评测治理的下一步。

用户无需决定 CLI 事件格式、SSE/WebSocket、表索引、Artifact 目录和 Run migration 等技术细节；这些由 S0/S1 R2 提出最低成本方案和回滚路径。
