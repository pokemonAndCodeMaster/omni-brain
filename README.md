# Omni-Brain

> 面向工作、开发和业务协作的知识与决策系统——把分散在文档、代码、数据、流程和人员经验中的信息，转化为人能理解、AI 能可靠调用、长期可维护的知识体系。

## 项目目标

当用户需要理解、设计或建设一项业务/软件能力时，Omni-Brain 能够：

1. 从可能不完整的目标出发，盘点已有知识，识别并补足关键缺口
2. 在目标澄清与知识编织的迭代中，形成**可核验、可下钻且不过载的任务上下文**
3. 辅助形成方案和真实能力产物，以运行或任务证据验证结果
4. 将稳定知识安全地纳入规范底座和可浏览视图，避免重复准备，也不让知识库碎片化

## 当前阶段

项目处于**产品基调与信息架构发现阶段**，正在通过质检业务（人工质检 → 自动化质检 → 大模型质检）的真实场景验证架构假设。

**已有成果：**

- 产品方向收束与 Blueprint
- 质检领域四块业务差异、流程和平台化边界的初步调研
- Markdown/YAML 知识目录、taxonomy 和手工摄入流程
- Agent Skill 体系（知识摄入、查询、健康检查、任务知识准备等）
- 最小任务案框架和评测夹具

**尚未实现：**

- 产品网站、视图引擎和任务上下文引擎
- 确定性检索（当前脚本均为 stub）
- 代码/Schema 索引和数据血缘
- 完整治理与 change set 执行器

详见 [Blueprint](docs/blueprint.md) 中的组件成熟度表。

## 顶层架构

```
产品体验（浏览/学习 · 精确问答 · 任务上下文 · 方案设计 · 实现影响 · 治理）
         │
    上下文与决策层（意图识别 · 检索与有界扩图 · 上下文组装 · 影响分析）
         │
    知识层（规范知识底座 · 领域模式包 · 来源与状态 · 公共能力与使用契约）
    ├── 派生结构（全文索引 · 关系图 · 代码符号图 · Schema 清单 · 血缘 · 新鲜度）
         │
    事实源（原始资料 · 代码 · API/Schema · 数据库/数据资产 · 运行系统 · 人工确认）

    治理与评测控制面横切所有层
```

## 目录结构

```
omni-brain/
├── docs/                    # 项目文档
│   ├── blueprint.md         #   目标、架构、组件成熟度、路线（总入口）
│   ├── product-direction-discussion.md  #   产品方向推理与争议
│   ├── design-discussion.md #   早期调研与组件议题
│   ├── now.md               #   当前工作台与续接视图
│   ├── scenarios/           #   真实领域验证场景
│   ├── specs/               #   组件实施契约
│   └── problems/            #   持续问题记录
├── knowledge/               # 规范知识库
│   ├── index.md             #   全局索引
│   ├── taxonomy.yaml        #   分类法定义
│   ├── log.md               #   操作时间线
│   ├── raw/                 #   不可变原始资料（禁止修改）
│   ├── synthesis/           #   合成知识卡
│   ├── concepts/            #   概念卡
│   ├── entities/            #   实体卡
│   ├── experiences/         #   经历与经验卡
│   ├── norms/               #   操作规范卡
│   ├── pitfalls/            #   避坑指南卡
│   └── ...                  #   其他知识类型目录
├── .agents/                 # AI Agent 配置
│   └── skills/              #   可复用 Agent 技能（12 项）
├── scripts/                 # 确定性工具（当前多为 stub）
├── eval/                    # 评测系统与固定数据集
├── workspaces/              # 任务工作区（不提交具体任务内容）
│   └── task-cases/          #   任务案执行状态
├── src/                     # 产品实现（待开发）
├── tests/                   # 测试
├── config/                  # 配置
├── AGENTS.md                # AI Agent 操作契约
├── pyproject.toml           # Python 项目配置
└── environment.yml          # Conda 环境定义
```

## 快速开始

```bash
# 创建 Conda 环境
conda env create -f environment.yml
conda activate omni-brain
```

当前核心脚本（`scripts/compile_index.py`、`search_engine.py`、`ingest_pipeline.py`、`health_checker.py`）均为占位实现，可执行以确认状态，但尚不具备真实检索、索引或摄入能力。知识操作目前主要通过 Agent Skill 以人机协作方式完成。

## Agent 能力工作台 v0

本地工作台把 Agent 能力发现、任务运行、历史轨迹、评测和线性进化放在一个入口。用户只需要选择“知识问答 Agent”“方案形成 Agent”等业务能力；Harness、Skill、执行器和 revision 只在高级详情出现。领域页面以后仍可调用同一 Run API，汇总工作台负责跨领域的历史、评测、进化和版本治理。

```bash
python -m pip install -e .
cd apps/agent-console
npm install
npm run build
cd ../..
python scripts/agent_console.py
```

浏览器打开 `http://127.0.0.1:8787`。v0 同时只允许一个受管任务，运行现场位于 `/home/yyh/project/.omni-brain-runs/<run-id>/`；它只提供 Git 文件隔离，不隔离进程、网络或凭证。具体边界和验证证据见 [Agent 能力工作台 v0](docs/specs/agent-workbench-v0.md)。

## 路线图

| 阶段 | 目标 | 状态 |
|---|---|---|
| R0 | 收束目标与架构：维护 Blueprint，明确组件边界和验证方式 | 进行中 |
| R1 | 质检最小能力建设切片：手工建立规范对象、三种视图和上下文包，验证理解—设计—建设—验证—回写闭环 | 下一步 |
| R2 | 确定性编译与检索 MVP：FTS、Schema 校验、有界关系扩展 | 待启动 |
| R3 | 产品视图与方案工作区 MVP：领域/流程/查询视图、view registry | 待启动 |
| R4 | 治理、Brownfield 与跨领域扩展 | 待启动 |

## 关键文档

- **[Blueprint](docs/blueprint.md)**：当前目标、架构、组件成熟度和路线的总入口
- **[产品方向讨论](docs/product-direction-discussion.md)**：产品判断的推理过程、争议和备选方案
- **[设计讨论](docs/design-discussion.md)**：早期调研、组件议题和历史上下文
- **[AGENTS.md](AGENTS.md)**：AI Agent 在本项目中的操作契约

## 许可证

待定。
