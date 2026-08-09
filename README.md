# Omni-Brain Harness — M1 知识 Release

这是从 `omni-brain` 设计仓库提取出的可移植实验 Harness。它直接使用 OpenCode 原生支持的根 `AGENTS.md` 和 `.agents/skills/`，不需要额外适配器或模型运行时。

当前包含：

- 可恢复任务案与本地 Git 来源范围能力；
- 已用真实材料验证基础整理、聚焦代码、跨模型增量融合和整库阅读整改的 M1 知识摄入能力；
- 已发布的人工质检与验收知识、显式领域地图和两种产品视图；
- 只读知识校验器。

当前正式知识来自用户授权材料和人工发布决定；其中的目标设计、历史做法、冲突和未知已与当前实现事实分开，不能据此推断生产系统已经部署。
M1 已完成首个切片，当前开始 M2 查询与任务上下文设计。

## 安装与自检

```bash
cd /home/yyh/project/omni-brain-harness
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python scripts/knowledge_check.py
```

## 开始一次知识摄入

在项目根运行：

```bash
opencode
```

然后像真实工作一样只说需求，例如：

```text
请把 <材料路径> 中与 <主题> 有关的杂乱材料整理并摄入这个项目的知识库，让我和后续模型可以浏览、理解、追溯和继续使用。
```

模型应从项目规则自动触发 `ingest-knowledge`，先在工作台形成候选并把 `review.md` 交给你；你批准前不会修改正式知识。

如果任务是整体优化已有知识库的阅读体验，仍只需提出自然语言目标。Harness 会复制正式知识到隔离候选，按读者问题每次交给模型一至三页，直到交付完整候选。

## 项目边界

- 本项目：OpenCode、其他模型和跨会话使用载体；
- 外部材料：只有用户在当前任务中明确指定后才进入读取范围，并始终保持只读。

能力状态和限制以 [harness.yaml](harness.yaml) 为准；阶段路线见 [docs/roadmap.md](docs/roadmap.md)。
