# Omni-Brain

> 一套面向工作、开发和业务协作的可移植 Agent Harness：把分散在文档、代码、数据、流程和人员经验中的信息，转化为人能理解、AI 能可靠调用、长期可维护的知识与工作能力。

## 项目目标

当用户需要理解、设计或建设一项业务或软件能力时，Omni-Brain 希望能够：

1. 从真实目标出发，取得**最低充分**的业务、系统、代码和运行知识；
2. 区分当前事实、历史做法、目标设计、冲突、推断和未知；
3. 按任务难度完成方案、实现或业务动作，并用真实环境验证；
4. 把稳定的新知识、规则、经验和验证方法安全回收到长期资产；
5. 换会话、模型或 Codex/OpenCode 宿主后，仍能依靠项目内 Harness 工作。

完整质检平台是长期验证场景，不是当前交付物。Omni-Brain 当前要建设的是支持知识、流程、软件和后续 Agent 能力持续形成与演进的基座。

## 一条复利闭环

```text
真实目标
→ 判断任务强度
→ 取得最低充分知识
→ 形成并执行方案
→ 产生代码、知识、SQL、配置或其他真实产物
→ 在真实环境验证
→ 提出可复用知识、规则、Skill、验证方法和评测候选
→ 审查与晋升
→ 后续任务复用
→ 聚合失败并改进 Harness
```

知识管理、日常开发、运行验证、Skills、评测和系统优化是这条闭环中的不同责任，不是六套需要并行开工的平台。

## 三种规划对象

| 规划对象 | 回答什么 | 在项目中的位置 |
|---|---|---|
| **长期责任地图** | 完整系统不能漏掉哪些责任 | Blueprint 的 C1—C10；不是组件施工顺序 |
| **当前最薄底座** | 当前纵向切片用什么真正运行 | 宿主会话、`AGENTS.md`、少量 Skills、确定性工具、文件工作区、Markdown/Git 和真实评测 |
| **用户能力路线** | 每一阶段用户新增什么可用能力 | M1—M5；后一阶段必须实际消费前一阶段产物 |

项目不再使用旧的 `R0—R4` 路线，也不新增另一套 `R0—R6` 编号。架构负责不漏责任，能力阶段负责交付价值，真实失败负责批准复杂度。

## 当前阶段

M1“知识整理与摄入”已经完成首个质检增量文档切片：候选内容经用户批准进入正式知识，干净会话能够直接消费，Luna 与 Terra 在同一用例上均达到内容线，86 项回归通过。

当前推进**开发优先的 M2+M3 组合切片**。目标是让真实开发先产生可用结果，同时从正式知识和当前事实源取得最低充分上下文，完成项目实际验证并提出知识变化候选。首个用例“验收配额可见性”已经形成隔离参考并完成 Luna 基线 Trial；候选功能可用且反向修正了参考遗漏，下一步按真实差距补最薄开发 Harness 后重放。

当前是否已经完成审计、正在修哪一层以及下一次 Trial 用什么固定输入，统一以[实验与评测总账](eval/STATUS.md)为准。根 README 只保留稳定路线，避免随着每次实验反复改写。

## 当前工程形态

```text
用户真实需求
  ↓
Codex / OpenCode 原生会话
  ↓
AGENTS.md：稳定路由与安全边界
  ↓
Skills：专项语义工作流
  ↓
确定性工具与文件工作区：状态、选源、隔离运行、校验、Diff
  ↓
Markdown / OKF + Git：规范知识、产品视图、审查与回滚
  ↓
真实任务、认证参考和跨模型 Trial：证明是否有效
```

当前不自研模型运行时，不以图数据库或向量数据库作为知识真相源，也不建设大规模多 Agent 或微服务。Agent 控制面复用现有质检平台的 Vue3、FastAPI 和 PostgreSQL，只封装 OpenCode CLI、Git worktree 与运行证据，不接管模型运行时；Docker、资源级调度和远程执行仍等待真实瓶颈再评估。

## Agent 能力工作台 v0.1

工作台宿主位于 `/home/yyh/project/quality-platform-lab`，直接扩展现有 Vue3 一站式平台，不再维护本仓的 React 页面。当前最薄纵切提供 Agent 能力目录、OpenCode 启动、Run 历史、session、结果和按需增量 trace；评测与进化仍是后续纵切。

```bash
cd /home/yyh/project/quality-platform-lab
scripts/postgres.sh init
.venv/bin/python -m src.cli migrate
.venv/bin/uvicorn src.api.app:create_app --factory --port 8000

cd src/frontend
npm install
npm run dev
```

浏览器打开 `http://127.0.0.1:5173/ai/agents` 或 `/ai/runs`。Agent 定义仍由本仓 `config/agent-registry.yaml` 与发布 Harness 管理；Run 元数据和规范事件写入质检平台现有 PostgreSQL，完整产物留在 `.runtime/agent-runs/`。运行现场位于 `/home/yyh/project/.omni-brain-runs/<run-id>/`。Git worktree 只隔离代码和文件，当前仍不隔离 CPU、内存、网络或凭证，也没有内建用户鉴权。具体边界和验证证据见 [`Agent 能力工作台 v0.1`](docs/specs/agent-workbench-v0.md)。

## 两个仓库角色

| 仓库 | 角色 |
|---|---|
| `omni-brain` | 设计与实践仓：Blueprint、讨论、研究、认证参考、私有 Eval 和 Trial 证据 |
| `omni-brain-harness` | 精简发布与实验仓：独立 Harness Release、领域知识集成分支、根规则、Skills、工具和公开能力状态 |

设计仓中的强模型参考答案和私有评分不能进入候选 Harness。候选模型必须只依靠待发布能力和用户授权的真实材料完成任务。

当前 `/home/yyh/project/omni-brain-harness` 是空知识的可移植 M1 Harness Release；质检知识集成版单独检出到 `/home/yyh/project/omni-brain-harness-quality-check-v1`。两者共享 Git 历史，但发布身份和用途不同。

## 目录导航

```text
docs/blueprint.md        长期目标、C1—C10 责任地图与成熟度
docs/harness-roadmap.md  完整 Master Roadmap：时间线、组件、用例、产物、验证与进度
docs/now.md              当前工作台与下一动作
docs/briefings/          面向外部讨论的项目说明包
docs/specs/              已批准或待验证的具体切片方案
docs/research/           开源项目和技术选项的一手研究
knowledge/raw/           不可变原始材料
knowledge/               当前设计仓的知识资产
eval/STATUS.md           用例、参考成果、Trial 与动态状态总账
.agents/skills/          设计仓当前保留的实验性工作协议
scripts/                 确定性工具；多项历史脚本仍是占位实现
workspaces/              可恢复任务和研究工作区
AGENTS.md                本项目 Agent 操作契约
```

## 用户能力路线

| 阶段 | 用户新增能力 | 当前状态 |
|---|---|---|
| M1 | 把混乱材料整理并正式摄入为可浏览、可查询、可追溯的知识 | 首个质检增量切片已发布并完成跨模型重放 |
| M2 | 立即知道已有、缺失、冲突、可信范围和补知责任 | 与 M3 交错推进；从真实开发切片提取首批上下文 |
| M3 | 用合适粒度知识完成真实任务和运行验证 | 首个局部开发参考与 Luna 基线 Trial 已完成；进入 Harness 修订与重放 |
| M4 | 代码、规则和流程变化后安全更新知识与可复用资产 | 未开始 |
| M5 | 已跑通能力换模型、换领域和扩大规模后仍可用 | 未开始 |

阶段、组件、用例、时间线与当前实现的完整映射见[Master Roadmap](docs/harness-roadmap.md)。

## 关键入口

- [项目 Blueprint](docs/blueprint.md)：目标、责任地图、成熟度与边界；
- [Agent Harness 讨论包](docs/briefings/agent-harness/README.md)：用于与他人快速讨论愿景、工程方案、现状和待决策点；
- [Master Roadmap](docs/harness-roadmap.md)：完整时间线、组件计划、用例、产物、验证、进度和下一动作；
- [当前工作台](docs/now.md)：现在做到哪里、下一步做什么；
- [实验与评测总账](eval/STATUS.md)：真实用例、参考成果、Trial 和结果；
- [项目操作契约](AGENTS.md)：Agent 在本仓库中的工作方式。

## 许可证

待定。
