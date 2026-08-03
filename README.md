# Omni-Brain Harness — M1 知识摄入能力发布版

这是从 `omni-brain` 设计仓库提取出的可移植 Harness Release。它直接使用 OpenCode 和 Codex 可发现的根 `AGENTS.md`、`.agents/skills/` 与确定性工具，不需要额外 Agent 运行时。

当前包含：

- 可恢复任务案与本地 Git 来源范围能力；
- 已用真实材料验证基础整理、聚焦代码和跨模型增量融合切片的 M1 知识摄入能力；
- 空的 OKF 兼容知识 Bundle、显式领域地图和产品视图入口；
- 只读知识校验器。

## 发布对象

本 Release 发布的是 **Harness 能力本体**：规则、Skills、工具、模板、状态工作区和测试。它不包含任何正式领域知识；正式知识必须由用户通过真实材料摄入产生，或从单独的领域知识包装载。

质检知识集成版保留在 `release/m1-quality-knowledge-v1`，用于展示真实产物并作为后续查询实验输入，不代表通用 Harness 的默认内容。模型 Trial、评分和参考答案只保存在设计仓库，不进入本 Release。

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

## 项目边界

- 本项目：OpenCode、其他模型和跨会话使用载体；
- 外部材料：只有用户在当前任务中明确指定后才进入读取范围，并始终保持只读。

能力状态和限制以 [harness.yaml](harness.yaml) 为准；阶段路线见 [docs/roadmap.md](docs/roadmap.md)。
