# Agent Console v0 Codex Trial 001

## 结论

本 Trial 证明了 Agent 能力工作台的第一条真实纵向路径：从 Git/YAML 注册表选择知识问答 Agent，基于固定 Release revision 建立独立 worktree，通过后端 API 调用 Codex CLI，持续保存可见事件、session、最终回答和 workspace diff，再由一个独立 Judge 输出“任务完成 / 执行过程”双维度评价。

这只验证 `Codex + 只读知识查询 + 单 Run + Judge` 切片，不证明 OpenCode 正向执行、会话续接、真实文件修改提交或生产并发。

## 运行事实

- Release：`omni-brain-harness@7076817`
- Workbench Run：`run-20260826-153246-278e30`
- Worktree：`/home/yyh/project/.omni-brain-runs/run-20260826-153246-278e30`
- Branch：`agent-console/run-20260826-153246-278e30`
- Codex session：`01a03eb3-d8b8-7f83-8286-051752372e87`
- 状态：`completed`，退出码 `0`
- 可见事件：16
- 文件变化：无
- Judge：任务完成 `99`，执行过程 `97`，成功

## 独立检查

- Python 服务测试覆盖 worktree、事件、最终输出、双维度评分和一轮候选 revision 选择；
- React/TypeScript 生产构建通过；
- Chromium 在 1440×1000 与 390×844 下完成真实渲染，无控制台错误和横向溢出；
- 页面恢复本 Trial 的 16 条轨迹以及 99/97 评分。

## 反例与边界

OpenCode wrapper 另行真实触发了 `run-20260826-154314-aebb02` 和 `run-20260826-154553-1f0df9`：CLI、worktree、session 与 JSON 错误事件均被捕获，但当前 OpenCode 账户对默认和 `opencode-go/deepseek-v4-flash` 返回余额不足。`opencode/hy3-free` 在有界等待内无首事件，随后通过工作台 Stop API 成功终止为 `cancelled`。因此 OpenCode 目前只取得错误与停止路径证据，不得标为正向运行已验证。

线性进化已由真实 Git 仓库和假执行器服务测试覆盖基线、候选修改、提交、同题重跑和采用判断；仍需一次真实模型候选 Trial 才能升级为 `verified@slice`。
