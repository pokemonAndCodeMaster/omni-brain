# Omni-Brain 评测驱动建设策略

> **状态**：Provisional；当前先证明任务案恢复评测本身公平、可重复，再实现自动 Runner。  
> **目的**：用真实行为和结果定义组件边界，让评测在设计前提供方向、在实现后提供回归证据。  
> **关联**：[能力切片协议](capability-slice-experiment.md)｜[参考评审](../research/agent-evaluation-reference-review.md)｜[首个恢复任务](../../eval/datasets/task_case/acceptance_exploration.yaml)

## 1. 核心判断

评测不是对现有功能做事后打分，也不是先搭建一个能批量运行模型的 Harness。起点是：从真实工作和失败中选出值得塑造的行为，定义可核验 Outcome，再决定需要怎样的环境、Transcript 和 Grader。

当前采用 Anthropic 的 Agent Eval 对象与生命周期作为主骨架，结合 LangChain 的 targeted behavior、trace 驱动和正确性—效率分层；知识系统项目用于发现被测能力和可复现实验模式。Inspect AI、Harbor 仅是后续执行基础设施候选。

## 2. 评测领域模型

```text
EvaluationSuite
└─ Task
   ├─ instruction + clean environment
   ├─ capability / behavior / scope
   ├─ reference solution + acceptable strategies
   ├─ Graders[]
   └─ Trials[]
      ├─ model + agent harness + eval harness identity
      ├─ Transcript
      └─ Outcome
```

| 对象 | 责任 |
|---|---|
| Suite | 围绕一个能力或行为族组织任务、覆盖和成熟度 |
| Task | 一次明确、可解、可公平判定的输入和成功标准 |
| Trial | 某模型与 Agent Harness 对一个 Task 的一次随机尝试 |
| Grader | 对 Outcome、Transcript 或知识状态的一项断言/评分 |
| Transcript | 工具、消息、中间结果和状态变化的完整运行记录 |
| Outcome | Trial 结束时环境和产物的真实状态，不等同于模型自述 |
| Eval Harness | 准备环境、运行 Trial、收集轨迹、评分和聚合 |
| Agent Harness | 把模型变成可行动 Agent 的工具、循环、上下文和权限系统 |

同一模型换 Codex、OpenCode 或 Antigravity 后不是同一个被测系统；报告必须同时标识模型和 Agent Harness。

## 3. 验证层级

| 层级 | 回答的问题 | 落点 |
|---|---|---|
| 单元/集成测试 | 确定性代码和状态契约是否正确 | `tests/` |
| 契约检查 | 文件、Schema、链接和操作规则是否一致 | `scripts/check_*.py` + `tests/` |
| Agent Capability Eval | 当前系统能否完成尚不稳定的目标行为 | `eval/datasets`、`fixtures`、`reports` |
| Agent Regression Eval | 已经可靠的行为是否因变更退化 | 固定 Suite + baseline + CI/定期运行 |
| 能力切片验证 | 真实业务结果与 Omni-Brain 组件是否形成可信闭环 | task case + `eval/reports` |

任何模型都能通过的 SDK/脚本确定性行为不进入模型能力分数；单元测试通过也不能证明 Agent 会正确调用组件。

## 4. Omni-Brain 能力 Taxonomy

初版按“测什么”而非来源分组：

| 能力族 | 代表行为 |
|---|---|
| routing | A/B/C 分流、Skill 选择、何时不启动重流程 |
| task_continuity | 冷启动恢复、压缩后续接、状态与下一动作 |
| retrieval | 精确查找、跨文件/跨源、多跳、召回与上下文预算 |
| grounding | 来源质量、Claim 可追溯、事实/推断/目标区分 |
| task_framing | 模糊需求澄清、关键问题、范围和知识缺口 |
| knowledge_lifecycle | 摄入、冲突、新鲜度、替代、晋升、复用和遗忘 |
| decision_readiness | 知识是否足以支持行动、风险接受和失败处理 |
| knowledge_handoff | 任务投影与长期知识分流、归属、关系和视图影响 |
| human_experience | 浏览、学习、解释、争议处理和行动交接 |
| code_context | 符号/依赖/影响、新鲜度和最小源码下钻 |
| system_evolution | AGENTS/Skill/Schema 变化、回归、回滚和自我优化 |

Taxonomy 只用于组织覆盖和中层观察，不是最终产品本体。只有跨任务反复出现后才稳定命名和层级。

## 5. Task 设计门禁

每个 Task 在进入 Suite 前必须满足：

1. 来自真实用户旅程、dogfood、失败或明确产品要求；
2. 两位有背景的人原则上能独立得出相近通过/失败判断；
3. 指令公开 Grader 会检查的必要约束，不用隐藏假设坑 Agent；
4. 有已知可行的参考解，能够通过全部必需 Grader；
5. 同时考虑行为应触发和不应触发的平衡任务；
6. 环境从干净状态开始，Trial 之间不共享会影响结果的文件、缓存或历史；
7. 记录非目标和允许的替代策略，避免把一种实现写成唯一答案。

0% 通过率首先触发 Task/Grader 审计，而不是直接归因于 Agent 无能力。

## 6. Grader 设计

### 评分对象

| Grader | 典型问题 | 优先方式 |
|---|---|---|
| outcome | 最终任务或环境状态是否正确 | 确定性状态/测试 |
| knowledge_state | 来源、冲突、状态、归属和关系是否正确 | Schema + 确定性检查 + 专家 |
| safety_invariant | 是否越权、破坏或污染环境 | 确定性审计，必需项可硬失败 |
| transcript_behavior | 是否使用正确能力、出现明显补偿或遗漏 | 规则 + 模型/人工 rubric |
| quality | 解释、方案、交接是否满足任务标准 | 分维度模型评分 + 人工校准 |
| efficiency | 步骤、工具、token、延迟和人工介入 | 轨迹统计，正确后比较 |

尽可能使用代码 Grader；开放质量使用模型 Grader 时，要提供 `Unknown` 选项并与人工样本校准。一个 Judge 不同时承担所有主观维度。

### Outcome 优先，轨迹有界

不要求固定工具调用顺序。只有事实源、安全边界、授权和知识状态等产品不变量可以成为路径硬门禁。对合理策略差异使用软指标或 rubric；简单任务可以维护 ideal trajectory，开放任务用当前最佳可接受轨迹作为可更新参考。

部分完成应获得分项结果，不能用一个总分掩盖失败发生在检索、编织、决策还是交接。

## 7. Trial、随机性与报告

单次成功只是一条 Trial 证据。初期至少保留每次 Trial，而非只保留聚合分数；条件允许时对关键 Task 重复运行，报告：

- pass@1：首次尝试成功概率；
- pass@k：多次尝试至少一次成功，适合允许探索的任务；
- pass^k：多次尝试全部成功，适合任务恢复、治理和用户期望稳定的能力；
- 分项 Grader、错误类型、成本和 Harness 身份。

小样本阶段不伪装统计显著性，先用 Transcript review 验证题目、Grader 和失败分类是否公平。

## 8. Suite 生命周期

1. 从人工测试、用户反馈和真实 Transcript 捕获候选 Task；
2. 明确目标行为、参考解、正反例和 Grader；
3. 先跑当前实现形成 baseline，并人工审查 Transcript；
4. 实现最小能力，比较 Outcome、失败类型和效率；
5. 新失败进入 Task 或现有 Task 的边界，不自动新增全局规则；
6. Capability Eval 达到稳定高通过率后，挑选代表任务晋升 Regression Eval；
7. 监控饱和、失效来源、题目歧义和 Judge 漂移；
8. Domain/产品人员负责成功标准和任务，评测维护者负责 Harness、Schema 和 Grader 质量。

更多 Task 不等于更好。每个 Task 应说明它塑造的行为、生产价值和与其他任务的非重复性。

## 9. 环境隔离

环境稳定性是可信 Trial 的前提，但当前不先建设重型沙箱。按最低充分等级演进：

| 等级 | 场景 | 机制 |
|---|---|---|
| E0 | 只读恢复/查询 | 冻结 fixture + 只读权限 |
| E1 | 受控文件写入 | 临时目录或 Git worktree + diff/回滚 |
| E2 | 有限 Shell | Agent 原生 sandbox/严格权限 |
| E3 | 装依赖、并发、任意命令 | 容器 + 网络/挂载限制 |
| E4 | 不可信代码/安全评测 | microVM 或远程强隔离 |

Git 只能隔离工作树和回滚文件，不隔离进程、网络、HOME、凭据和依赖。是否升级由 Task 风险与环境噪声决定，不由框架功能清单决定。

## 10. 首个 Suite：task_continuity

当前 `TC_ACCEPTANCE_EXPLORATION_001` 是 Capability Eval 的首个 Task：新会话从权威任务案恢复状态。两次 Gemini 运行是两条人工记录 Trial，不足以估计稳定性。

迁移要求：

- 冻结 Task 输入与环境；
- 补齐明确 prompt、模型与 Agent Harness 身份；
- 建立参考 Outcome，而非唯一工具顺序；
- 将状态准确性、安全不变量、轨迹行为和效率拆成 Grader；
- 增加无 ID、ID 不存在、只查看、继续推进等平衡任务；
- 多次运行并人工审查 Transcript 后，才决定是否晋升 Regression Eval。

## 11. 实施门禁

在以下内容完成前，不实现通用 `eval/runner.py`：

1. 当前 Task 能以新领域模型完整表达；
2. 有冻结 fixture 和可通过的参考解；
3. 至少一轮人工 Grader 校准能解释两次既有 Trial；
4. 明确 Runner 首版必须自动化的重复工作，而不是预建并发、沙箱和多提供商平台。

Runner 首版只在对象稳定后承担加载、确定性评分和报告；Inspect AI/Harbor 等适配在 Agent 调用、容器生命周期、轨迹标准化或并发成为真实瓶颈时做 spike。

## 12. 当前边界

仓库已经具备首个冻结 fixture、参考响应、正反任务和人工 Grader 校准，但仍无可运行 Runner、模型 Judge 校准、完整 Transcript/Agent Harness 身份和足量重复 Trial；`eval-runner` Skill 仍引用不存在的 `eval/runner.py`。因此当前只能声称“首个 Task 的评测定义具备实现 Runner 的前置条件”，不能声称已形成自动评测平台或稳定回归能力。
