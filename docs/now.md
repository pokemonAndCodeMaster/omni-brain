# 当前工作台

> 更新时间：2026-08-30
> 本页只回答：**现在到哪里、产物在哪里、下一步做什么**。完整用例与 Trial 看
> [Eval 总账](../eval/STATUS.md)，长期架构看 [Blueprint](blueprint.md)。

## 当前判断

Omni-Brain 已收口为一个产品主线。团队 AI 协作与交付平台、Harness、规范知识、Agent/Skill、
评测资产与产品设计统一进入本仓；历史独立仓和实验分支只作为迁移来源或短期隔离现场，不再作为
新的正式开发入口。

这解决的是产品和资产长期分叉问题，但不等于所有历史实验代码已经无条件合并。每项实验仍需先
回到 Idea/Requirement，经过验证后分别晋升实现、知识和评测证据；失败实验只保留最小审计。

## 已进入主线的可用产物

| 位置 | 当前作用 | 状态 |
|---|---|---|
| `apps/quality-platform/` | Vue3 + FastAPI + PostgreSQL 的协作与 Agent 控制面 | `verified@mainline-s0` |
| `harness.yaml`、`.agents/skills/` | 主线 Agent 能力与运行规则 | 已接入 |
| `packages/harness/` | `release/harness@7076817` 的可追溯发布快照 | 已导入，主线 90 项回归通过 |
| `knowledge/published/quality-check/` | 首批认证质检知识 | 已导入，33 文件/24 概念校验与主线查询通过 |
| `knowledge/raw/quality_check/` | 认证知识可回溯的不可变来源 | 已登记 |
| `config/agent-registry.yaml` | 平台从主线注册 Agent 的入口 | 已改为当前仓 `HEAD` |

S0 当前提供 Idea、candidate/accepted Requirement、不可覆盖 Revision、人机时间线、Agent 能力目录、
Codex/OpenCode 启动、Run 历史、session、结果和按需增量 trace。列表只取摘要；仅在进入 Agent 或
Run 详情后读取 prompt、结果和 trace，活跃 Run 才增量刷新。Run 元数据与规范事件进入 PostgreSQL，
完整运行产物进入应用 `.runtime/agent-runs/`，worktree 只隔离代码和文件。

当前仍不使用 Docker，也没有内建身份认证、远程工作站调度、正式评测执行或进化 Loop。S0 设计
边界见 [`team-ai-collaboration-s0-r2.md`](specs/team-ai-collaboration-s0-r2.md)。

## 仍需保留但不再并行发展的资产

- Spider 分支已经有真实实现与验证证据，后续应先登记为主线 Requirement，再审查哪些代码、知识和
  EvalCase 可以晋升；当前不能因“曾经成功”整分支无条件并入。
- 人工质检多维结果分析、知识问答、方案形成与开发 Trial 已进入 `eval/` 总账；可复用质检知识已先
  进入 `knowledge/published/quality-check/`。
- `/home/yyh/project/quality-platform-lab`、`/home/yyh/project/omni-brain-harness` 和
  `/home/yyh/project/omni-brain-harness-quality-check-v1` 只保留迁移复核价值；新工作从本仓主线开始。

## 当前下一动作

1. 开始 S1 Work 纵切：Requirement 生成 Work、关联 Agent Run、Git 分支/提交/MR 和验证证据；
2. 建立历史实验资产晋升清单，逐项登记为 Requirement/EvalCase，而不是继续维护平行产品仓；
3. 以主线正式知识运行首个知识问答/开发任务，验证平台 Run 确实消费 `knowledge/published/`；
4. 为知识浏览、查询和受审更新形成下一条 Requirement，让知识不只在文件中可调用，也能在平台中治理。

用户当前无需为目录或分支继续拍板；主线复验通过后，下一处需要用户确认的是 S1 的真实交付页面与
“什么证据允许 Work 完成”的交互，而不是底层仓库拓扑。
