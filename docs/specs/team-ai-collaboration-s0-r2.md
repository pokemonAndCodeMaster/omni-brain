# 团队 AI 协作与交付中枢 S0：需求治理与双执行器 R2

> 状态：`verified@local-s0`（本地 API/数据库/CLI 与新增页面浏览器验收通过；长进程取消仍未端到端验证）
>
> 日期：2026-08-30
>
> 产品依据：[`team-ai-collaboration-delivery-hub-product-design.md`](../team-ai-collaboration-delivery-hub-product-design.md)
>
> 实施宿主：`/home/yyh/project/quality-platform-lab@feature/agent-workbench-opencode-v1`
>
> 本规格只覆盖 S0。S1 的 Work、WorkPlan、Commit/Push/PR、交付审查包、知识提案和 EvalCase 只保留接口边界，不在本轮实现。

## 1. 本轮用户结果

用户以固定 `admin` 身份打开现有 Vue3 平台，可以：

1. 快速保存一条不完整 Idea，原文不被后续 Agent 覆盖；
2. 在 Idea 中调用 Codex/OpenCode 能力补背景或梳理需求；
3. 查看人的消息、Agent Run、修订和决定组成的统一时间线；
4. 把 Idea 转成 `candidate` Requirement，或者直接创建 candidate Requirement；
5. 编辑不可覆盖的 Requirement Revision；
6. 对当前 Revision 作接纳、驳回、延期或合并决定；
7. 接纳后保持同一 Requirement 身份，将状态改为 `accepted`，并记录 `NEXT` 或 `LATER`；
8. 在能力目录中显式选择 Codex 或 OpenCode，查看各自健康、模型、session、事件、结果和具体失败；
9. 列表只读取摘要，只有进入对象或 Run 后才加载正文、时间线和 trace。

S0 的可用结果不是“建好了几张表”，而是把“建设团队 AI 协作与交付中枢”这件事保存为第一条真实 Idea，并形成一份经人接受的 Requirement Revision。

## 2. 本轮明确不做

- 登录、SSO、用户切换、角色和权限；
- Work、WorkPlan 和开发交付阶段；
- Git Commit、Push、PR/MR 和 Merge 自动化；
- Docker、远程 Worker、Lease、OBS/NAS；
- WorkflowRun、StepRun、RunAttempt；
- Agent 在线等待人的输入和原进程恢复；
- 自动优先级、自动接纳需求和自动生成排期；
- 正式 EvalCase、Judge、进化 Loop；
- 通用 Workflow DSL、万能对象表和万能关系表；
- 为列表扫描 Codex/OpenCode 本地 session。

## 3. 已批准业务语义

### 3.1 Idea

Idea 保存未经整理也值得保留的原始想法：

```text
captured → discussing → converted / archived
```

`converted` 只表示已经创建来源 Requirement。Idea 原始标题和正文仍然保留。

### 3.2 Requirement

候选和正式需求是同一对象：

```text
candidate / accepted / rejected / deferred / merged / superseded / closed
```

- 内容变更始终新建 Requirement Revision；
- `accepted` 冻结被接受的 Revision，不新建另一条 Requirement；
- `rejected` 必须说明原因；
- `deferred` 必须说明原因和复审时间或触发条件；
- `merged` 必须指向承接 Requirement；
- 重新讨论 rejected/deferred Requirement 时新建 Revision 和 Decision，旧历史不变。

### 3.3 Commitment 的 S0 边界

S0 还没有 Work，因此只允许：

- `NEXT`：填写 Owner=`admin`、预计窗口和进入条件；
- `LATER`：填写复审时间或触发条件。

`NOW` 会在 S1 与“事务内创建首个 Work”同时开放。S0 的请求 Schema 不接受 `NOW`，返回 `422` 和明确字段错误，不制造“已承诺但没有 Work”的假状态。

### 3.4 Thread、Run 与 Session

```text
Thread = 一个 Idea 或 Requirement 的持续协作上下文
Run = 某个能力的一次原子执行
Executor Session = Codex/OpenCode 原生会话句柄
```

一个 Thread 可以关联多次 Run；失败或修订创建新 Run。平台不覆盖旧 Run，也不把执行器内部 session 当正式业务记录。

## 4. 页面与交互

### 4.1 路由

| 路由 | 页面 | 首次加载 |
|---|---|---|
| `/ai/ideas` | Idea Inbox | Idea 摘要分页 |
| `/ai/ideas/:ideaId` | Idea 详情 | Idea 详情、时间线首屏、关联 Run 摘要 |
| `/ai/requirements` | Requirement 列表 | Requirement 摘要分页 |
| `/ai/requirements/:requirementId` | Requirement 详情 | Requirement 详情、当前 Revision、时间线首屏 |
| `/ai/agents` | 能力目录 | 能力摘要与双执行器健康 |
| `/ai/runs/:runId?` | Run 中心 | Run 摘要；选中后才读详情与事件 |

S0 不创建空的“工作台”和“工作”页面。导航只有真实可用入口。

### 4.2 Idea Inbox

用户操作：

- 快速录入：标题、原始想法、可选领域；
- 按状态筛选；
- 查看提出时间、最近活动、关联 Run 数和是否已转需求；
- 点击进入详情。

列表不返回 raw content、Thread、Run 结果或 trace。

### 4.3 Idea 详情

页面结构：

```text
Header：标题、状态、领域、actor=admin、下一步
Main：派生协作时间线
Side：原始想法、关联 Requirement、Agent 动作
```

Agent 动作：

| 动作 | Agent | 默认执行器 | 输出 |
|---|---|---|---|
| 查背景 | `knowledge-assistant` | Codex | 已知、未知、冲突、相关知识与入口 |
| 梳理需求 | `solution-agent` 的 R1 路径 | Codex | 结构化 Requirement Revision 候选 |

用户可以显式改用 OpenCode。Agent 输出先以 Run 候选出现在时间线，不自动修改 Idea 或 Requirement。

“转为候选需求”弹出可编辑预览：

- 若来源 Run 有结构化 R1 payload，预填表单；
- 否则只使用 Idea 原文和用户填写内容；
- 提交后在一个事务内创建 Requirement、Revision、Requirement Thread 和两侧 System Entry，并把 Idea 标为 `converted`；需求评审发生前不伪造 Decision；
- 重复提交返回已存在的关联 Requirement，不重复创建。

### 4.4 Requirement 列表

摘要字段：

```text
id / title / status / commitment
owner / source_type / source_idea_id
current_revision_no / run_counts
created_at / updated_at
```

支持 status、commitment 和标题搜索；不返回 Revision content 和 timeline。

### 4.5 Requirement 详情

页面结构：

```text
Header：状态、commitment、Owner、当前 Revision、下一步
Main：当前 R1 + 派生协作时间线
Side：Revision 历史、Agent 动作、评审决定
```

R1 编辑器字段：

```text
背景与来源
目标用户 / 业务对象
当前问题
为什么值得做
期望用户结果
范围内 / 范围外
关键业务动作
输入与输出
验收标准
约束和依赖
仍未解决的问题
```

candidate 可以不完整；`accepted` 至少要求当前问题、期望结果、范围和一条可执行验收标准。

Decision 操作：

- 接纳：选择当前 Revision，填写 `NEXT` 或 `LATER` 所需信息；
- 驳回：原因必填；
- 延期：原因及复审时间/触发条件必填；
- 合并：目标 Requirement 和原因必填；
- 重新打开：从 rejected/deferred 创建新 Revision，恢复为 candidate。

### 4.6 时间线投影

时间线不是新的事实表。后端按发生时间合并：

- `t_collab_thread_entry` 中人的消息和系统活动；
- 关联 `t_agent_run` 的摘要、状态和结果摘要；
- Requirement Revision 元数据；
- `t_collab_decision`。

Run 卡只显示能力、执行器、状态、模型、摘要和时间。点击后跳到 Run 详情，才读取 prompt、failure reason 和规范事件。

## 5. Vue 组件边界

继续使用 Vue3、Composition API、`<script setup lang="ts">` 和现有设计 token。

```text
src/frontend/src/features/collaboration/
├── api/collaboration.ts
├── types.ts
├── pages/
│   ├── IdeaInboxPage.vue
│   ├── IdeaDetailPage.vue
│   ├── RequirementListPage.vue
│   └── RequirementDetailPage.vue
├── components/
│   ├── IdeaCaptureForm.vue
│   ├── IdeaSummaryList.vue
│   ├── CollaborationTimeline.vue
│   ├── AgentActionPanel.vue
│   ├── RequirementEditor.vue
│   ├── RequirementRevisionList.vue
│   └── RequirementDecisionPanel.vue
└── composables/
    ├── useIdeaInbox.ts
    ├── useIdeaDetail.ts
    ├── useRequirementList.ts
    └── useRequirementDetail.ts
```

| 组件 | 单一职责 | 契约 |
|---|---|---|
| Route Page | 组合功能组件和路由参数 | 不直接拼 API、不承载大段表单 |
| `IdeaCaptureForm` | 编辑并提交一条 Idea | typed `submit`；不自己写 API |
| `IdeaSummaryList` | 展示摘要并选择对象 | props down，emit `select` |
| `CollaborationTimeline` | 呈现已排序的统一 timeline items | 不请求 Run 详情、不解析原始事件 |
| `AgentActionPanel` | 选择动作、执行器、模型和补充说明 | emit typed launch payload |
| `RequirementEditor` | 编辑结构化 R1 Draft | `defineModel` 或 typed update，不保存状态到全局 |
| `RequirementDecisionPanel` | 校验并提交评审决定 | 不直接改变父级 Requirement |
| composable | 管理当前路由对象的 API、加载、错误和显式动作 | 返回 readonly state 与方法 |

不引入 Pinia。S0 状态属于单一路由功能；跨页面只通过 URL 和后端事实恢复。原始 Agent payload 不使用 `v-html` 渲染。

## 6. API 契约

### 6.1 Actor

S0 所有写接口拒绝客户端传入 `actor_id`；相关 Pydantic request model 统一配置 `extra="forbid"`，避免把额外身份字段静默忽略。FastAPI dependency 提供服务端常量：

```text
actor_id = admin
```

历史 Run 的旧 actor 值不改写；新记录统一为 `admin`。

### 6.2 Idea

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/api/ideas` | 摘要分页和状态筛选 |
| `POST` | `/api/ideas` | 创建 Idea |
| `GET` | `/api/ideas/{id}` | 读取单 Idea 正文和关系 |
| `POST` | `/api/ideas/{id}/messages` | 追加人的消息 |
| `GET` | `/api/ideas/{id}/timeline` | 按 cursor 读取派生时间线 |
| `POST` | `/api/ideas/{id}/agent-actions` | 启动查背景或梳理需求 Run |
| `POST` | `/api/ideas/{id}/convert-to-requirement` | 创建 candidate Requirement 与首个 Revision |
| `POST` | `/api/ideas/{id}/archive` | 归档未转需求 Idea |

### 6.3 Requirement

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/api/requirements` | 摘要分页、状态/commitment/标题筛选 |
| `POST` | `/api/requirements` | 直接创建 candidate Requirement 和首个 Revision |
| `GET` | `/api/requirements/{id}` | 读取当前详情与当前 Revision |
| `GET` | `/api/requirements/{id}/revisions` | 读取 Revision 元数据和按需正文 |
| `POST` | `/api/requirements/{id}/revisions` | 创建不可覆盖的新 Revision |
| `POST` | `/api/requirements/{id}/messages` | 追加人的消息 |
| `GET` | `/api/requirements/{id}/timeline` | 按 cursor 读取派生时间线 |
| `POST` | `/api/requirements/{id}/agent-actions` | 启动补背景或需求修订 Run |
| `POST` | `/api/requirements/{id}/decisions` | 接纳、驳回、延期、合并或重开 |

### 6.4 Agent Runtime 演进

| 方法 | 路径 | 变化 |
|---|---|---|
| `GET` | `/api/agents` | 返回 `default_executor`、`supported_executors` 和聚合 Run 计数 |
| `GET` | `/api/agent-runtime/health` | 返回 Codex/OpenCode 两个 Executor 健康，不再只返回 OpenCode |
| `POST` | `/api/agent-runs` | 接受 `executor`、subject/thread/action；不接受 actor_id |
| `GET` | `/api/agent-runs` | 新增 executor、subject 过滤，仍只返回摘要 |
| `GET` | `/api/agent-runs/{id}` | 返回 executor、executor_session_id 和 subject 信息 |
| `GET` | `/api/agent-runs/{id}/events` | 保持 `after_sequence` 增量契约 |
| `POST` | `/api/agent-runs/{id}/cancel` | 取消当前 Codex/OpenCode 子进程组 |

`AgentActionRequest`：

```json
{
  "action": "knowledge_context",
  "executor": "codex",
  "model": null,
  "instruction": "重点核对当前已实现边界"
}
```

Action 只能来自白名单：

```text
knowledge_context → knowledge-assistant
shape_requirement → solution-agent / R1 contract
```

前端不能自定义 agent_id 绕过业务动作映射；能力目录的通用启动入口仍可以显式选择已登记 Agent。

## 7. PostgreSQL Migration

新增 `006_create_collaboration_s0.sql`，使用当前配置 schema（本地默认 `manual_qc_lab`）。

### 7.1 `t_collab_idea`

```text
id varchar(64) PK
title varchar(256)
raw_content text
domain_key varchar(128) nullable
status varchar(32)
created_by varchar(128) default 'admin'
owner_id varchar(128) default 'admin'
created_at / updated_at timestamptz
```

约束：title/raw_content 非空；status 只允许 `captured/discussing/converted/archived`。

### 7.2 `t_collab_requirement`

```text
id varchar(64) PK
source_type varchar(32)
source_idea_id varchar(64) nullable FK
title varchar(256)
status varchar(32)
current_revision_id varchar(64) nullable
accepted_revision_id varchar(64) nullable
commitment varchar(16) nullable
owner_id varchar(128) default 'admin'
target_window varchar(256) nullable
entry_condition text nullable
review_at timestamptz nullable
merged_into_id varchar(64) nullable self FK
created_by varchar(128) default 'admin'
created_at / updated_at timestamptz
```

约束：

- status 白名单；
- candidate 不允许 commitment；
- accepted 必须有 accepted_revision_id 和 `NEXT/LATER`；
- `NEXT` 必须有 target_window 或 entry_condition；
- `LATER` 必须有 review_at 或 entry_condition；
- merged 必须有 merged_into_id，且不能指向自身。

为保证 Idea 转 Requirement 在并发请求下仍幂等，增加 `source_idea_id IS NOT NULL AND source_type = 'idea'` 的唯一部分索引。

### 7.3 `t_collab_requirement_revision`

```text
id varchar(64) PK
requirement_id varchar(64) FK ON DELETE CASCADE
revision_no integer
content jsonb
source_run_id varchar(64) nullable FK
created_by varchar(128) default 'admin'
created_at timestamptz
UNIQUE(requirement_id, revision_no)
```

`content` 由 Pydantic 校验为版本化 R1 对象；数据库至少约束为 JSON object。current/accepted Revision 外键在 revision 表创建后补充。

### 7.4 `t_collab_thread`

```text
id varchar(64) PK
subject_type varchar(32)       # idea / requirement
subject_id varchar(64)
created_at timestamptz
UNIQUE(subject_type, subject_id)
```

这是受控 subject 关联，不是万能对象表。Repository 在事务内验证 subject 存在。

### 7.5 `t_collab_thread_entry`

```text
id bigint identity PK
thread_id varchar(64) FK ON DELETE CASCADE
entry_type varchar(32)        # human_message / system
actor_type varchar(32)        # admin / system
actor_id varchar(128)
body text
payload jsonb
created_at timestamptz
```

Agent Run、Revision 和 Decision 不复制进该表；时间线查询从各事实表组合。

### 7.6 `t_collab_decision`

```text
id varchar(64) PK
requirement_id varchar(64) FK ON DELETE CASCADE
revision_id varchar(64) nullable FK
decision_type varchar(32)
reason text nullable
commitment varchar(16) nullable
target_window varchar(256) nullable
entry_condition text nullable
review_at timestamptz nullable
merged_into_id varchar(64) nullable FK
actor_id varchar(128) default 'admin'
created_at timestamptz
```

Decision 追加写；Requirement 保存当前投影。两者在同一事务更新。

### 7.7 `t_agent_run` 增量

```text
executor varchar(32) default 'opencode'   # codex / opencode
executor_session_id varchar(128) nullable
subject_type varchar(32) nullable         # idea / requirement / work
subject_id varchar(64) nullable
thread_id varchar(64) nullable FK
trigger_action varchar(64) nullable
result_payload jsonb nullable
```

已有 `opencode_session_id` 不在 S0 立即删除：

1. 新列回填旧 session；
2. 新代码只写/read `executor_session_id`，API 暂时保留旧字段为 deprecated alias；
3. S1 验证稳定后再通过独立 migration 删除旧列。

已有历史 Run 的 executor 回填 `opencode`，actor 不改写。新增索引：

```text
(subject_type, subject_id, created_at DESC)
(executor, status, updated_at DESC)
```

## 8. 后端模块与依赖

```text
src/collaboration/
├── models.py
├── repository.py
├── service.py
└── timeline.py

src/agent_runtime/
├── executor.py             # Protocol / request / result
├── codex_executor.py
├── opencode_executor.py
├── registry.py
├── repository.py
├── service.py
└── worktrees.py

src/api/routers/
├── collaboration.py
└── agent_runtime.py
```

依赖：

```text
Collaboration Router
  → Collaboration Service
      → Collaboration Repository
      → AgentRunService.start(subject context)

Agent Runtime Router
  → AgentRunService
      → AgentRunRepository
      → WorktreeManager
      → ExecutorRegistry
          → CodexCliExecutor / OpenCodeExecutor
```

SQL 只在 Repository；Executor 不访问 PostgreSQL；Collaboration 不解析 CLI 事件。两个执行器共用一个 `asyncio.Semaphore(1)`，S0 不出现 Codex 和 OpenCode 同时写同一仓库。

## 9. 双执行器契约

### 9.1 公共协议

```python
class AgentExecutor(Protocol):
    name: str
    def health(self) -> ExecutorHealth: ...
    async def run(self, request: ExecutorRequest, on_event, on_process) -> ExecutorResult: ...
```

`ExecutorResult` 统一返回：

```text
executor
exit_code
session_id
final_message
final_payload
failure_code
failure_reason
```

### 9.2 Codex CLI

基线命令：

```text
codex exec
  --json
  --color never
  --sandbox <read-only|workspace-write>
  -C <worktree>
  [-m <model>]
  [-o <artifact/final>]
  [--output-schema <schema.json>]
  <prompt>
```

官方 OpenAI 文档已经明确：`codex exec` 可非交互执行，`--json` 输出 JSONL 事件，支持 `--output-schema`、最终消息文件和按 session ID resume。[官方说明](https://learn.chatgpt.com/docs/non-interactive-mode)

S0 实际使用：

- 知识和需求动作使用 `read-only`；
- 需要写工作区的已登记能力使用 `workspace-write`；
- 不使用 `danger-full-access` 或绕过 sandbox 的 flag；
- 读取 `thread.started.thread_id` 作为 executor_session_id；
- 映射 `turn.*`、`item.*` 和 `error` 为规范事件；
- `item.completed(agent_message)` 更新 final_message；
- `command_execution`、`file_change`、MCP 和 plan item 只保留可展示摘要与原始 payload；
- structured R1 使用 `--output-schema` 并读取 final JSON；
- 使用本机已有 CLI auth，不把 auth 文件、Token 或环境秘密写入 PG/日志。

### 9.3 OpenCode CLI

保持现有 `opencode run --format json --auto --dir ...` 解析器和 endpoint 可选能力，改为实现公共 Executor 协议。失败分类和最终文本行为保持兼容。

### 9.4 错误分类

两种执行器共用以下 failure_code：

```text
authentication_failed
model_unavailable
insufficient_balance
rate_limited
executor_error
platform_error
platform_restarted
```

`failure_reason` 永远保留执行器原始错误。不能把鉴权、余额、模型不可用或工具错误压缩成“环境问题”。

### 9.5 Codex PoC 门与实测

实现业务页面前先运行一个只读 Codex PoC，验证：

1. 本机 `codex --version` 可用；
2. `codex exec --json --sandbox read-only` 产生可逐行解析 JSONL；
3. 能取得 thread_id、最终消息、usage 和退出码；
4. 取消可以终止进程组；
5. output schema 与 final output 文件组合可用；
6. 失败时原始 stderr/JSON error 可保留。

本机当前已确认 `codex-cli 0.144.1` 暴露这些 flags；只有真实 PoC 结果才升级为 `verified`。

2026-08-30 已在实施宿主完成只读 PoC：

- 基础执行以 `exit_code=0` 完成，依次取得 `thread.started`、`turn.started`、`item.completed(agent_message)` 和带 usage 的 `turn.completed`；
- `--output-schema` 与 `-o` 同时使用成功，最终文件是符合 schema 的 JSON；
- `codex exec resume --json <thread_id>` 成功沿用同一个 thread_id；
- 本机 CLI 曾在 stderr 输出一次模型缓存格式错误，并在完成后输出文件监听取消警告，但对应执行仍有 `turn.completed` 且退出码为 0。

因此 JSONL、结构化结果、最终文件和 session resume 已是 `verified@local-poc`。Executor 必须分开捕获 stdout/stderr：stderr 诊断原样保留，但不能只因 warning/error 文本就覆盖真实终态；退出码、规范完成事件和可解析结果共同决定状态。进程组取消仍由 Adapter 集成测试验证，未验证前不得声称完成取消能力。

S0 保存原生 session 并验证可恢复，不默认跨 Run resume；一次新的协作动作仍新建平台 Run，并由 Thread 的显式上下文快照保证业务连续性。只有真实任务证明原生 resume 能增加价值且不会绕过上下文审计后，才开放为产品动作。

## 10. Prompt 与上下文边界

业务动作的 prompt 由后端构造，前端只提交补充说明。快照至少包含：

```text
subject type/id
Idea 原始内容或当前 Requirement Revision
显式选中的 Thread 人工消息
action contract
expected output
相关知识根与版本
```

- 不把完整历史 Run trace 自动塞入下一次 prompt；
- 只引用用户显式选择或当前动作必需的上游结果；
- prompt 原文仍保存到该 Run，保证可审计；
- Agent 结果是候选，不自动改写业务对象；
- 接受 Agent 候选为 Revision 时必须由 admin 显式提交。

## 11. 测试与真实验收

### 11.1 后端自动测试

- migration 幂等与旧 Run 保留；
- Idea 创建、摘要列表、详情和状态转换；
- Idea 转 Requirement 的事务与重复提交幂等；
- 直接创建 candidate Requirement；
- Revision 递增、current/accepted 指针和不可覆盖；
- accepted/rejected/deferred/merged/reopen 校验；
- S0 拒绝 `NOW`；
- Decision 与 Requirement 当前投影同事务；
- timeline 顺序、cursor 和不复制 Run payload；
- 写接口固定 admin，客户端 actor_id 被拒绝；
- Run subject/executor 过滤与摘要/详情分层；
- ExecutorRegistry 默认选择和显式覆盖；
- Codex 命令、安全 sandbox、JSONL fixture 解析和失败分类；
- OpenCode 现有 parser 回归；
- 两执行器共用单并发闸门；
- 取消和平台重启保留具体 executor 信息。

### 11.2 Vue 自动测试

- Idea Inbox 只请求摘要接口；
- 打开详情后才请求 timeline；
- Idea Capture typed submit 和错误显示；
- AgentActionPanel 默认 Codex、允许显式选择 OpenCode；
- Requirement Editor 不覆盖 props，保存创建新 Revision；
- Decision Panel 对 accepted/deferred/merged 做字段校验；
- timeline Run 卡不请求 trace，点击才路由 Run 详情；
- selected active Run 才增量刷新，终态停止；
- Codex/OpenCode 健康分别展示；
- `vue-tsc`、Vitest 和生产构建通过。

### 11.3 真实纵向验收

使用现有本地 PostgreSQL、FastAPI、Vue 和浏览器：

1. 通过页面创建“建设团队 AI 协作与交付中枢” Idea；
2. 用 Codex 执行一次查背景和一次结构化需求梳理；
3. 人修改候选后转成 candidate Requirement；
4. 保存新 Revision，并以 `NEXT` 接纳；
5. 页面展示原始 Idea、两次 Run、人的修订、Decision 和当前 accepted Revision；
6. 从能力目录以同一受控问题启动一次 OpenCode 对照 Run；正式 EvalCase 和 Judge 不属于 S0；
7. 从 PostgreSQL 与 API 回读两个执行器、session、规范事件、结果和错误；
8. Run 列表和 Requirement 列表查询不读取正文与 trace；
9. 真实浏览器验证导航、表单、时间线、错误态和响应式布局；
10. 服务重启后历史对象、Run 和 Decision 仍可读。

若 OpenCode 或 Codex 因账户、鉴权、余额或模型不可用失败，平台功能验收要求完整展示具体原因；执行器“成功完成任务”的能力验收仍保持未通过，不能用错误展示通过替代。

## 12. 发布、回滚与兼容

### 发布顺序

1. Codex 只读 PoC；
2. additive migration；
3. 双执行器 Run 后端与回归；
4. collaboration API；
5. Vue Idea/Requirement 页面；
6. 真实 S0 纵向验收；
7. 更新 `docs/handoff.md`、`component-map.md`、README 和验证报告；
8. 提交独立功能分支；Push 与 PR/MR 需再次取得人工确认。

### 回滚

- 代码回滚后旧 Agent Runtime 继续忽略新增列和新表；
- 不删除或重写历史 `t_agent_run`；
- `opencode_session_id` 在 S0 保留，避免旧代码立即失效；
- 新导航可以随代码回滚，Idea/Requirement 数据留在 PostgreSQL；
- migration 不提供自动 DROP；如必须物理删除，先导出并由人确认，不作为普通回滚动作。

## 13. 实施组件图

应用 Vue 最佳实践后的组件责任已经在第 5 节冻结：页面只组合，表单/列表/时间线拆分，props 向下、typed events 向上，API 与异步状态进入 feature composable。实现不得把四个页面和全部请求重新塞进一个巨型 `.vue` 文件。

后端继续保持 Router → Service → Repository；双执行器只通过窄 Adapter 扩展。若 Codex PoC 证明公开 CLI 契约与本规格不符，先记录具体差异并修订 Adapter，不以读取 Codex 内部数据库作为补丁。

## 14. 本地实施证据（2026-08-30）

- 实施仓：`/home/yyh/project/quality-platform-lab@feature/agent-workbench-opencode-v1`；
- PostgreSQL migration `006_create_collaboration_s0.sql` 已在现有本地库执行；
- 首条真实链路：`idea-20260830-040827-8866bc` → Codex 结构化 Run
  `run-20260830-041157-1bf223` → `req-20260830-041647-e9f632` →
  `accepted + NEXT / S1`；
- 下一阶段没有复用上述 S0 自举需求，而是通过直接创建入口形成并接纳独立的
  `req-20260830-042453-d51b4a`（“S1：由平台管理的首个标准开发闭环”，
  `accepted + NEXT / S1`），它才是 S1 R2 与首个 Work 的正式输入；
- 首次结构化 Codex Run `run-20260830-041115-de9aec` 的
  `invalid_json_schema` 被原样保存，修复严格 Schema 后重跑成功；
- OpenCode 对照 Run `run-20260830-041237-59dfb6` 暴露单行 JSON 超过默认流限制，
  原因被原样保存；Adapter 改为有界 16 MiB 流后，修复 Run
  `run-20260830-041949-740b63` 成功并回填 session、42 个规范事件和最终文本；
- Python 24 项、Vue/Vitest 34 项、`vue-tsc` 和 Vite 生产构建通过；
- Playwright Chromium 1.58.0 在 1440、1024、390、320 四档宽度完成 6 条协作路由的
  24 个路由—视口组合验收，24/24 通过；无横向溢出、未命名控件、过小可见点击目标、
  控制台/Page Error 或 4xx/5xx；
- 20/20 项真实交互通过，包括 Idea/Requirement/Run/Agent 主路径、移动导航、跳过导航、
  可见焦点、对话框入焦、Esc 关闭和焦点归还；首轮发现的问题在实施仓修复后重跑通过。

详细运行证据保存在实施仓 `docs/verification-report.md`，本机截图与机器可读审计位于其
忽略目录 `.runtime/e2e-collaboration/`。本规格因此升级为 `verified@local-s0`；验证范围是
单机 admin、本地 PostgreSQL、Codex/OpenCode CLI、API、组件测试、构建和协作页面浏览器
主路径。真实长进程取消、多用户、远程 Worker 与 S1 交付闭环仍不在这个结论内。
