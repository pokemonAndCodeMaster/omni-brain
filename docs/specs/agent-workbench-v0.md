# Agent 能力工作台 v0.1

> 状态：implemented-and-verified-at-one-opencode-control-slice
> 日期：2026-08-29
> 宿主：`/home/yyh/project/quality-platform-lab`
> 范围：现有 Vue3 质检平台、PostgreSQL、OpenCode-only、单服务单并发、Git worktree 文件隔离

## 用户结果

团队成员可以在现有质检一站式平台中：

1. 按知识管理、软件开发、质量治理等类别查看已发布 Agent 能力和轻量 Run 计数；
2. 选择一个 Agent，填写任务、可选标题和 OpenCode 模型并启动；
3. 在 Run 列表查看状态、操作者、模型和时间，不为列表加载完整 prompt、结果或 trace；
4. 选择具体 Run 后查看任务、worktree、分支、OpenCode session、原始失败原因、最终输出和增量事件；
5. 保留 worktree 与本地产物，供后续人工检查、提交和 MR 流程使用。

入口：

- `/ai/agents`：能力目录和启动；
- `/ai/runs`：Run 摘要、详情和 trace。

## 已批准取舍

- 前端不再维护 React 控制台；直接复用质检平台的 Vue3 `AppShell`、Vue Router、设计 token、HTTP 层和测试体系。
- Run 元数据和规范事件不再以 SQLite 为事实源；复用平台 `DatabaseManager → PGConnector → PostgreSQL` 公共链路。
- 第一版只实现 OpenCode，不提供 Codex 适配、执行器选择或多模型置信度路由。
- Agent 定义继续来自本仓 `config/agent-registry.yaml` 和发布 Harness；进程启动时读取并缓存，显式刷新才重新扫描。
- worktree 只负责代码和文件隔离。第一版不使用 Docker，也不声称隔离进程、端口、CPU、内存、网络、依赖或凭据。
- 默认直接运行本机 `opencode run`，由 OpenCode 选择随机端口；已有单个 OpenCode server 时可配置 `OPENCODE_ENDPOINT`。
- 当前服务以单进程、单 OpenCode 并发为运行假设。多 worker、远程工作站、租户权限和资源调度必须由后续真实团队工况单独设计与验证。

## 数据与读取边界

PostgreSQL 表：

- `manual_qc_lab.t_agent_run`：Run 身份、Agent、操作者、状态、模型、repository/revision、worktree/branch、session、结果、具体失败、产物路径和时间；
- `manual_qc_lab.t_agent_run_event`：每个 Run 内单调递增的规范事件，保存事件摘要和原始 JSONB payload。

读取固定分层：

```text
GET /api/agents
  → Agent 摘要与聚合 Run 计数
GET /api/agents/{id}
  → 单 Agent 能力、示例和发布身份

GET /api/agent-runs
  → Run 摘要分页
GET /api/agent-runs/{id}
  → 单 Run 完整详情
GET /api/agent-runs/{id}/events?after_sequence=N
  → 只取新增事件
```

Agent 目录无后台轮询。Run 列表只在进入页面或用户刷新时读取；只有已选择且仍活跃的 Run 每 8 秒续拉详情和新增事件，进入终态后停止。

## 失败信息

平台在保留 OpenCode 原始事件和具体 `failure_reason` 的同时附加可查询 `failure_code`：

- `authentication_failed`；
- `model_unavailable`；
- `insufficient_balance`；
- `rate_limited`；
- `opencode_error`；
- `platform_error` / `platform_restarted`。

不能把余额、鉴权、模型不可用等原因统一简化为“环境问题”。

## 历史迁移

`quality-platform-lab/scripts/import_opencode_runs.py` 可一次性读取旧
`.derived/agent-console/agent-console.sqlite3`，只迁移 `executor=opencode` 的 Run 与事件；
按 Run ID 幂等跳过，不导入 Codex。旧 SQLite 文件在人工确认迁移结果前保留为只读核对源，
不再承担在线读取。

## 验证证据

- Python 18 项测试通过；
- Vue/Vitest 32 项测试、`vue-tsc` 和生产构建通过；
- `run-20260829-154603-c81456`：真实 OpenCode、独立 worktree、session、10 个规范事件、零文件变化；
- `run-20260829-154845-cd07a9`：最终文本解析回归成功，结果为 `OpenCode trace parser verified.`；
- 4 条旧 OpenCode 历史迁入 PostgreSQL，余额不足的原始原因与 HTTP/APIError 信息保留；
- 真实实现与更完整验证记录位于 `quality-platform-lab/docs/verification-report.md`。

## 尚未实现

- 多用户鉴权、权限与审计身份可信注入；
- 多工作站注册、心跳、任务领取和 OBS 回传；
- Docker 或其他进程/依赖/网络隔离；
- 多 OpenCode server 调度、多 worker 一致性和跨进程并发租约；
- 评测用例启动、Judge、评测报告和进化 loop；
- commit、push、MR 创建与合入门禁自动化。

这些边界是后续纵切候选，不能因为表、字段或旧实现曾存在就声称已经支持。
