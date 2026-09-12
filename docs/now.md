# 当前工作台

> 更新时间：2026-09-13
> 本页只回答：**现在到哪里、产物在哪里、下一步做什么**。完整用例与 Trial 看
> [Eval 总账](../eval/STATUS.md)，长期架构看 [Blueprint](blueprint.md)。

## 个人工作台当前入口

[打开 Linear 工作台](https://linear.app/yyhpokemonmaster/document/abed03cc1da2)，可以记想法、选事情、进入完整文档目录和已有知识能力。
本地全文阅读页位于 `.derived/personal-workbench/index.html`，生成与使用见 [说明](linear-workbench/README.md)。
本机全局 Codex 入口已完成另一项目新会话的无编号读取与普通问答反例验证；非交互写回测试受工具审批策略阻止，YYH-11 继续跟踪。
上下文材料与来源变化检查、文档发布和完整目录已验证。具体结果与适用范围见
[本轮交付说明](../workspaces/reviews/personal-workbench-operating/review.md)。

## 共作 v03 当前交付

用户已批准根目录《共作-协作工作台-交互原型-v03.html》和《共作-产品定义与Linear拆解-v03.md》作为本轮设计与开发输入。
当前主线新增共作工作台，可在本地记录想法、组织工作、保存目标和资料、委托 AI、查看结果和准备会议。
这条产品工作已经取代下文历史 S1 的固定六步流程作为新的工作入口；原 `/ai` 与 `/manual-qc` 仍可访问。

使用与启动：[apps/quality-platform/docs/gongzuo.md](../apps/quality-platform/docs/gongzuo.md)。
方案、实现、真实运行证据与尚未验证的边界统一见
[共作 v03 交付说明](../workspaces/reviews/team-workbench-product-definition/review.md)。
本地实现合入不代表公司部署或正式知识包发布；知识变化目前保留为待审候选。
2026-09-06 发现的子事项委托传错目标问题已在 YYH-15 修复：浏览器真实请求提交子事项，服务输入保留子目标和父背景，旧运行不漂移。验证使用隔离数据，未重新证明用户数据库和外部 AI 执行。
CodeHub 自动同步、公司登录、
团队工作站和容器运行，以及复杂真实需求的设计与验收效果仍未证明，不能统称整项需求已完成。

下面保留 2026-08-30 的历史阶段记录，便于定位已有能力，不作为新一轮实施待办。

## 当前判断

Omni-Brain 已收口为一个产品主线。团队 AI 协作与交付平台、Harness、规范知识、Agent/Skill、
评测资产与产品设计统一进入本仓；历史独立仓和实验分支只作为迁移来源或短期隔离现场，不再作为
新的正式开发入口。

这解决的是产品和资产长期分叉问题，但不等于所有历史实验代码已经无条件合并。每项实验仍需先
回到 Idea/Requirement，经过验证后分别晋升实现、知识和评测证据；失败实验只保留最小审计。

## 已进入主线的可用产物

| 位置 | 当前作用 | 状态 |
|---|---|---|
| `apps/quality-platform/` | Vue3 + FastAPI + PostgreSQL 的协作与 Agent 控制面 | S0 `verified`；S1 Work 纵切 `implemented / awaiting human acceptance` |
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

S1 已建立可运行候选：accepted Requirement 可原子创建一个共享 worktree 的 Work 和固定六步
`standard_development_v1`；Run 显式关联 Work/PlanStep，失败或重试不覆盖历史；Work 页面按需读取
计划与 Run 摘要，并管理 Git/验证证据和人工交付决定。首个真实对象是
`work-20260830-060651-5cb1fa`。真实 Codex 开发、OpenCode 验证/审查、45 项后端、38 项前端、
类型/构建和三档 Chromium 已跑通；当前只等待用户审查并作出接受或要求修订决定，不能称为已接受。施工边界见
[`team-ai-collaboration-s1-r2.md`](specs/team-ai-collaboration-s1-r2.md)。

## 仍需保留但不再并行发展的资产

- Spider 分支已经有真实实现与验证证据，后续应先登记为主线 Requirement，再审查哪些代码、知识和
  EvalCase 可以晋升；当前不能因“曾经成功”整分支无条件并入。
- 人工质检多维结果分析、知识问答、方案形成与开发 Trial 已进入 `eval/` 总账；可复用质检知识已先
  进入 `knowledge/published/quality-check/`。
- `/home/yyh/project/quality-platform-lab`、`/home/yyh/project/omni-brain-harness` 和
  `/home/yyh/project/omni-brain-harness-quality-check-v1` 只保留迁移复核价值；新工作从本仓主线开始。

## 当前下一动作

1. 用户审查首个 S1 Work 的最终 Commit、验证与审查证据，并选择接受交付或要求修订；
2. 建立历史实验资产晋升清单，逐项登记为 Requirement/EvalCase，而不是继续维护平行产品仓；
3. 以主线正式知识运行首个知识问答/开发任务，验证平台 Run 确实消费 `knowledge/published/`；
4. 为知识浏览、查询和受审更新形成下一条 Requirement，让知识不只在文件中可调用，也能在平台中治理。

用户当前无需为目录或分支继续拍板；主线复验通过后，下一处需要用户确认的是 S1 的真实交付页面与
“什么证据允许 Work 完成”的交互，而不是底层仓库拓扑。
