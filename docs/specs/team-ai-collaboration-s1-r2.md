# 团队 AI 协作与交付中枢 S1 可施工规格

> 状态：approved → implementation in progress
> 依据：`docs/team-ai-collaboration-delivery-hub-product-design.md` 与已接纳 Requirement
> `req-20260830-042453-d51b4a` / Revision `rev-20260830-042453-c19d81`。

## 1. 本轮用户结果

管理员从一条已接纳 Requirement 创建 Work 后，在一个页面完成以下闭环：

1. 看见固定目标仓、base commit、worktree、分支、Owner、Reviewer 和时间盒；
2. 按 `standard_development_v1` 逐步启动知识上下文、方案、开发、验证和审查 Run；
3. 每次重试都新增不可覆盖 Run，并可进入既有 Run 详情查看输出、具体失败和 trace；
4. 从真实 worktree 刷新 Commit、工作区状态和 Diff 摘要，补充验证、审查证据；
5. 证据满足门禁后由人接受交付，或记录要求修订的决定。

创建 Work 与固定计划必须在一个 PostgreSQL 事务中完成，且只在创建成功后把 Requirement
承诺从 `NEXT` 改为 `NOW`。Git worktree 创建失败时不得产生 Work 或 NOW 假状态。

## 2. 固定计划

S1 不实现工作流 DSL，只提供以下六个有序节点：

| 顺序 | step_key | 执行主体 | 默认执行器 | 完成门禁 |
|---:|---|---|---|---|
| 1 | `knowledge_context` | `knowledge-assistant` | Codex | 成功 Run + 人工确认 |
| 2 | `solution` | `solution-agent` | Codex | 成功 Run + 人工确认 |
| 3 | `development` | `development-agent` | Codex | 成功 Run + 人工确认 |
| 4 | `verification` | `review-agent` | OpenCode | 成功 Run + 人工确认 |
| 5 | `review` | `review-agent` | OpenCode | 成功 Run + 人工确认 |
| 6 | `acceptance` | `admin` | 无 | 交付证据完整 + 人工决定 |

只有前序步骤完成后下一步才可启动。失败、取消或待确认的步骤可以重跑；旧 Run 不更新、不覆盖。
方案步骤的人工完成动作就是 S1 的方案 Gate。

## 3. 状态与事实责任

- PostgreSQL：Work、WorkPlan、PlanStep、步骤完成记录、Run 关联、证据快照和人工决定；
- Git：base commit、分支、最终 Commit、工作区状态和 Diff；
- `.runtime/agent-runs/`：完整 CLI 原始产物；
- `t_agent_run`：原子 Run 与规范事件，增加显式 `work_id`、`plan_step_id` 关联；
- CLI session：执行器定位信息，不作为 Work 或计划的业务事实源。

Work 列表只查询摘要和 Run 数量；进入详情后才读取计划、步骤和 Run 摘要。完整 Run prompt、输出与
事件继续由 Run 详情按需获取。

## 4. 工作区与 Git 边界

一个 Work 只建立一个共享 worktree，所有步骤在同一 worktree 中读取或修改。单仓同时只允许一个
未结束的写入型 Work。知识、方案、验证和审查步骤只读，开发步骤使用 workspace-write。

Agent 可以修改、验证和 Commit。平台不会自动 Push、创建 PR/MR 或 Merge；PR/MR 仅保存人工操作后
回填的引用。接受交付至少要求：

- 前五个步骤均已人工确认完成；
- `HEAD` 与固定 base commit 不同；
- worktree 无未提交变更；
- 验证摘要和审查摘要非空；
- 接受决定明确引用最新证据快照和 Commit。

## 5. API 纵切

- `POST /api/requirements/{id}/work`：创建 Work、共享 worktree 和固定计划；
- `GET /api/works`：Work 摘要列表；
- `GET /api/works/{id}`：Work、计划、步骤、Run 摘要、最新证据和决定；
- `POST /api/works/{id}/steps/{step_id}/runs`：启动一次新 Run；
- `POST /api/works/{id}/steps/{step_id}/complete`：人工确认成功 Run；
- `POST /api/works/{id}/evidence`：从 Git 读取事实并保存验证/审查补充；
- `POST /api/works/{id}/decisions`：接受交付或要求修订。

## 6. 不在 S1 内

身份认证、多人权限、Docker、远程 Worker、Lease、RunAttempt、通用模板编辑、自动 Push/PR/Merge、
正式 EvalCase/Judge、自进化 Loop 与远端 ArtifactStore 均不进入本次实现。

Knowledge Proposal 与 Candidate EvalCase 在 S1 先作为交付审查包中的显式候选输出，不建设新的正式
治理对象；其晋升模型留到对应 Requirement 和 S4。

## 7. 验收与回滚

验收必须覆盖：空列表、从 accepted Requirement 创建 Work、重复创建、单仓并发冲突、六步上限、
前序 Gate、失败重跑保留历史、Git 证据、接受门禁、服务重启后回读，以及桌面/平板/手机真实 Chromium。

迁移前先通过 `pg_dump` 保存本地运行库。代码回滚不删除历史表；需要恢复实验运行库时，从迁移前备份
重建本地 PostgreSQL。worktree 只在创建事务失败时自动清理，已创建 Work 的回收属于后续显式操作。
