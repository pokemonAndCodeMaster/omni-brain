# Agent 评测与知识系统参考评审

> **状态**：Research input；用于修正评测设计，不自动成为项目决定或依赖选型。  
> **调研时间**：2026-07-12。  
> **原则**：区分评测方法、数据生成、被测能力、实证模式和执行基础设施；项目宣传数字只作为待复现实验线索。

## 1. 评测方法主参考

| 来源 | 核心价值 | 当前吸收 | 不直接照搬 |
|---|---|---|---|
| [Anthropic：Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Task / Trial / Grader / Transcript / Outcome / Harness / Suite；多次试验、能力与回归、参考解、平衡任务、评分器校准、Transcript review | 作为 Omni-Brain 评测对象和生命周期的主骨架 | 不把示例 YAML 或某种 Agent 架构当成固定 Schema |
| [LangChain：How we build evals for Deep Agents](https://www.langchain.com/blog/how-we-build-evals-for-deep-agents) | 从生产行为和 dogfood 失败选题；按被测能力分组；正确性优先，再比较 ideal trajectory、步骤、工具、延迟和成本 | 行为 taxonomy、trace 驱动、正确性—效率分层和 targeted suite | 不依赖 LangSmith，不把开放任务限制成唯一理想轨迹 |

## 2. 数据生成与行为探测

| 来源 | 核心价值 | 当前吸收 | 边界 |
|---|---|---|---|
| [anthropics/evals](https://github.com/anthropics/evals) | 模型生成 persona、sycophancy、风险和偏见数据集，并结合人工数据与分析 | 后续用模型扩展候选任务、构造行为探针，再由人校准 | 这是较早的 model-written dataset，不是现代 Agent Eval Harness |

## 3. 实证与组件价值证明

| 来源 | 可借鉴实验模式 | 需要反证 |
|---|---|---|
| [gbrain](https://github.com/garrytan/gbrain) | 真实查询 capture/export/replay；检索失败族硬门禁；公开长记忆基准；跨模型检查；将 Skill 视为可评测优化对象 | 项目自身指标、Judge 和 Skill 优化是否可复现，是否存在针对性过拟合 |
| [CodeGraph](https://github.com/colbymchenry/codegraph) | with/without 组件 A/B；多个真实代码库；每组多次运行取中位数；同时报告正确性、工具调用、文件读取、时间、token、成本 | 对照是否公平、任务代表性、模型/Harness 变化、宣传结果是否能独立复现 |
| [Graphify](https://github.com/Graphify-Labs/graphify) | 相同 Harness/模型/预算比较；检索和 QA 分开；报告双 Judge 一致性 | 数据规模、Judge 校准、图构建成本和与强基线比较是否充分 |

## 4. 被测能力发现

| 来源 | 对 Omni-Brain 的能力启发 | 可转化评测族 |
|---|---|---|
| [LLM Wiki v2](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) | 置信度、替代、遗忘、分层巩固、冲突、自愈和长期维护 | 知识生命周期、冲突/过时、晋升、复用和健康 |
| [Yuxi](https://github.com/xerrors/Yuxi) | 多租户 Harness、知识库/图谱、Skills/MCP、子 Agent 与沙盒工具的一体化工作台 | 多知识源、权限、Agent 与知识服务协作、交付物 |
| [secondbrain](https://github.com/ryannli/secondbrain) | 持久认知工作区和面向知识工作者的信息流 | 捕获—加工—行动—复盘的任务连续性与人类体验 |
| [Hyper-Extract](https://github.com/yifanfeng97/hyper-extract) | 从文本抽取图、超图及时空结构 | 结构抽取完整性、关系表达能力、来源与不确定性 |
| [CodeGraph](https://github.com/colbymchenry/codegraph) | 代码符号、调用/依赖、影响范围和自动新鲜度 | 代码导航正确性、变更影响、上下文成本和新鲜度 |
| [Graphify](https://github.com/Graphify-Labs/graphify) | 代码、Schema、基础设施和多模态资料进入统一图，区分 extracted / inferred | 跨源关系、事实/推断边界、路径解释和人类可理解性 |

## 5. 执行基础设施候选

| 来源 | 适用时机 | 当前决定 |
|---|---|---|
| [Inspect AI](https://inspect.aisi.org.uk/) | 需要统一 dataset/agent/scorer、外部 CLI Agent 和多种 sandbox 后端 | 暂不安装；未来做适配 spike |
| [Harbor](https://github.com/harbor-framework/harbor) | 需要 Codex/OpenCode/Gemini 等 Agent 在容器任务中批量运行 | 暂不安装；任意 Shell、并发和容器生命周期成为瓶颈后再评估 |

## 6. 对当前设计的修正

1. 先定义有产品价值的行为和 Outcome，再设计 Harness；
2. `EvaluationCase` 拆为 Suite / Task / Trial / Grader / Transcript / Outcome；
3. 单元/集成测试与模型能力评测分开；
4. 结果正确性先于轨迹效率，安全不变量仍可作硬门禁；
5. 不以单次成功判定能力，记录多次 Trial 和 Agent Harness 身份；
6. Capability Eval 负责爬坡，稳定后才晋升 Regression Eval；
7. 每个任务需要参考解、正反例、干净环境和评分器公平性检查；
8. Runner、沙箱和第三方框架选型后置到评测对象与 Grader 稳定之后。
