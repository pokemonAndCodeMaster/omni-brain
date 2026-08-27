# Agent 能力工作台 v0

> 状态：verified@codex-readonly-run-eval-and-one-linear-evolution-slice；OpenCode 正向执行仍为 implemented
> 范围：本地、单用户、同一时间一个受管任务

## 用户结果

Agent 能力的建设者和运营者可以从一个本地网页入口：

1. 按业务领域查看已经注册的 Agent 能力、当前版本和验证状态；
2. 输入任务并启动 Codex 或 OpenCode，在独立 Git worktree 中执行；
3. 实时查看可见消息、工具事件、进程状态、最终输出和代码差异；
4. 查看本工作台的新运行和设计仓已经封存的历史 Trial；
5. 用一个 Judge 对“任务完成”和“执行过程”两个维度形成结构化评价；
6. 从一个 Seed 开始，查看线性进化中每个候选的问题、修改、结果和取舍。
7. 在 Run 结束且 worktree 干净后显式释放现场，同时保留运行记录、分支和 commit。

领域页面以后可以直接调用同一套 Run API。领域页面负责在具体业务上下文中使用能力；本工作台负责跨领域的能力发现、任务历史、评测、进化和版本治理。

## 已确认取舍

- 用户一级对象统一叫“Agent 能力”；Harness、Skill 和执行器只在高级详情中出现。
- Codex 和 OpenCode 是内部执行器，不建立 HostProfile 产品对象。
- v0 不使用 Docker。每个 Run 从 Agent 仓库的固定 revision 创建一个 Git worktree，只承诺代码和文件隔离。
- v0 假定同一时间只有一个受管 Run，不建设并发调度。
- Agent 与评测定义继续由 Git/YAML 管理；运行状态和事件写入可删除的 `.derived/agent-console/`。
- 评测默认使用一个 Judge，顶层只有任务完成与执行过程两个维度。
- 进化采用线性 `执行 -> 评测 -> 改进 -> 选择`，每个候选保留可审计快照；不做种群搜索和自动合入。

## 运行边界

Worktree 不隔离进程、网络、系统服务和凭证。v0 只用于受信任仓库与受信任 Agent。只有真实任务证明文件隔离不足时，才引入 Docker。

## 最薄验收

- 能从浏览器看到当前 Release 中至少四项可使用的 Agent 能力和现有评测用例；
- 能选择一个 Agent，创建 worktree 并启动一次真实 Codex/OpenCode 任务；
- 页面刷新后仍能恢复任务、事件、最终输出、分支和差异；
- 能停止运行、在已有 session 上续接，并对已完成 Run 发起双维度评测；
- 能看到历史封存 Trial；
- 能创建一次进化记录，并按候选时间线查看评价、修改和相对效果；
- 后端、前端构建和关键 API 测试通过。

## 2026-08-26 验证结果

- `knowledge-assistant + Codex` 从 `release/harness@7076817` 建立独立 worktree，保存 16 个事件、session、最终回答与零文件差异；刷新后可以恢复；
- 单一 Judge 对同一 Run 给出任务完成 `99`、执行过程 `97`，证据封存在 [`AGENT_CONSOLE_V0_CODEX_001`](../../eval/trials/agent_console/AGENT_CONSOLE_V0_CODEX_001/README.md)；
- OpenCode CLI 的 worktree、session、结构化错误与 Stop 路径已真实触发；当前账户余额不足，免费模型在有界时间无首事件，因此正向执行仍未验证；
- 线性进化完成一次真实模型 Trial：Seed `98.0`，候选 `73d23ab` 经 91 项 Release 测试与同题重跑后为 `98.5`，实验内选择但未自动合入；证据与过拟合风险见 [`AGENT_CONSOLE_V0_EVOLUTION_001`](../../eval/trials/agent_console/AGENT_CONSOLE_V0_EVOLUTION_001/README.md)；
- Chromium 在 1440×1000 和 390×844 下无控制台错误或横向溢出，TypeScript 与生产构建通过。
