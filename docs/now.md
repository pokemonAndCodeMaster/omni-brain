# Omni-Brain 当前工作台

> **用途**：从上次讨论快速续接当前工作；只保存短摘要和权威链接，不复制完整知识或会话。  
> **状态**：Provisional view；维护规则见 [`specs/conversation-knowledge-lifecycle.md`](specs/conversation-knowledge-lifecycle.md)。  
> **最近整理**：2026-07-12。

## 当前目标

处于 R0→R1 过渡：以人工质检验收作为真实测试夹具，先验证“任务框架与问题缺口 → 存量盘点与补知 → 规范知识编织 → 决策准备度 → 任务投影/长期知识分流”，再逐步推进方案、产物、验证与回写。完整质检平台能力建设闭环仍作长期牵引，领域工具不是当前首要结果。详见 [Blueprint](blueprint.md) 与 [产品讨论稿](product-direction-discussion.md)。

## 活跃线程

1. **持续问题处理与对话回收**｜Provisional｜让日常困扰和讨论结论成为可追溯的验证输入，而不是聊天记录堆积。→ [问题处理协议](specs/continuous-problem-loop.md)｜[对话回收协议](specs/conversation-knowledge-lifecycle.md)
2. **日志规范案例**｜Triaged｜验证 AI 在写代码时能否带入带范围的工程规范，并识别历史冲突写法；不是日志整改任务。→ [案例](problems/2026-07-11-logging-standard-not-applied.md)
3. **任务知识准备能力**｜L1@recovery-core｜冷启动恢复 Outcome 已跑通；Task v2 已有冻结 fixture、参考响应、两次 Trial 人工校准和不存在 ID 的反向任务。下一步可测试先行实现只评分既有 Trial、不调用模型的最小 Runner。→ [任务案](../workspaces/task-cases/acceptance-knowledge-prep/overview.md)｜[评测策略](specs/evaluation-strategy.md)｜[校准报告](../eval/reports/task_case/2026-07-12-task-v2-grader-calibration.md)
4. **人工质检具体能力产物**｜后置候选｜在知识准备与后续建设组件得到切片证据后再选择；验收任务分配闭环目前只是领域假设。→ [问题案例](problems/2026-07-11-manual-quality-capability-construction-gap.md)｜[实验协议](specs/capability-slice-experiment.md)
5. **讨论行动交接**｜Experimenting｜试行“本轮决定 + 现在怎么继续”，降低开放式总结造成的阅读与行动负担。→ [问题案例](problems/2026-07-11-discussion-action-handoff-unclear.md)｜[对话协议](specs/conversation-knowledge-lifecycle.md)
6. **Skill 体系治理**｜Implemented@contract / Provisional｜活动 Skill 已由九个收敛为四个；不合理 Skill 和无消费者清单直接删除，`knowledge-ingest` 完成窄触发重写，已有 13 个路由 fixture 和静态契约测试。下一步做独立基础模型 Trial。→ [任务案](../workspaces/task-cases/skill-system-audit/overview.md)｜[审计](research/skill-system-audit-2026-07-12.md)｜[治理协议](specs/skill-system-governance.md)

## 近期关键结论

1. 先做范围受控、但满足真实质量约束的纵向切片；不预建全覆盖平台。→ [讨论稿](product-direction-discussion.md)
2. 高召回、上下文预算、延迟/成本和多 Agent 知识共享应从首轮作为验收约束；复杂技术仅在指标证明必要时引入。→ [日志案例](problems/2026-07-11-logging-standard-not-applied.md)
3. 讨论内容按原料、讨论判断、Blueprint、问题案例、评测和规范知识分流；Blueprint 是当前方向入口，不是全部历史。→ [对话回收协议](specs/conversation-knowledge-lifecycle.md)
4. 应同时用“工程规范进入代码任务”和“人工质检验收变更”两类旅程反证可复用底座与领域差异。→ [日志案例](problems/2026-07-11-logging-standard-not-applied.md)｜[质检场景](scenarios/quality-domain-knowledge-workbench.md)
5. `docs/now.md` 是有容量上限的续接视图，不是历史归档；达到触发条件后人工整理其字段和线程。→ [对话回收协议](specs/conversation-knowledge-lifecycle.md)
6. Omni-Brain 当前定位为知识、流程、方案、软件/工具产物和后续 Agent 能力的建设与演进基座，不预设直接承载质检运行态。→ [讨论稿](product-direction-discussion.md)
7. 完整质检平台能力建设闭环负责长期牵引；验收任务先用于逼出和验证 Omni-Brain 组件，领域工具不是当前首要结果。→ [讨论稿](product-direction-discussion.md)
8. 检索只是任务知识准备的一项活动；目标澄清、存量健康、补知、编织、验证和准备度判断需要迭代完成。→ [质检场景](scenarios/quality-domain-knowledge-workbench.md)
9. 任务知识准备同时产出短期任务投影和长期知识变更候选；稳定知识必须可归属、可浏览、可复用，不能形成一次性碎片。→ [讨论稿](product-direction-discussion.md)
10. 强模型临场完成的步骤只算人工基线；Omni-Brain 能力需要组件契约、门禁和基础模型/其他执行者的重放证据。→ [实验协议](specs/capability-slice-experiment.md)

## 开放问题

1. 最小任务案契约和机械门禁已实现；语义准备度、跨组件状态变化和框架版本失效规则怎样通过真实任务收敛？
2. 日志案例的目标代码库中，什么是可确认的权威规范、适用范围和历史反例？
3. 两个首批旅程的上下文预算、证据覆盖、准确/召回和成本阈值怎样定义？
4. 问题案例、评测旅程和规范知识之间需要哪些最小字段与稳定链接？
5. 任务投影中的新知识怎样按稳定性、粒度、复用和浏览价值分流到规范底座与产品视图？
6. 零背景学习、模糊痛点和明确重构三种入口怎样汇合，任务框架、问题缺口和知识切片如何迭代推进？
7. 哪些知识准备步骤必须先工具化，才能让基础模型可靠调用而不是依靠强模型补偿？
8. 知识准备切片验证后，第一项人工质检领域产物是否仍选择验收任务分配闭环？
9. Skill 的采用强度怎样通过真实 Trial 表达在 Blueprint 与 Eval 中，而不再预设一套 registry？

## 下一步候选

- 测试先行实现只负责 Schema/fixture 校验、既有 Trial 确定性评分和报告的最小 Runner；
- 用独立基础模型运行 Skill 治理路由 fixture，优先验证 `knowledge-ingest` 的正触发、反触发和 stub 降级；
- 设计任务投影与长期知识变更候选的分流门禁，并用人类浏览视图检查知识是否碎片化；
- 将日志案例改写为可运行的用户旅程与验收表；
- 用两条旅程手工组装第一版任务上下文包，并记录从方案到产物验证的失败类型；
- 达到触发条件时评审当前工作台的容量、字段和续接效果。
- 用后续五轮非简单讨论验证行动交接是否降低阅读负担，之后更新问题结果。

## 最近变化

1. 明确以高标准纵向切片验证上下文、检索与协作架构。
2. 沉淀人工质检全流程痛点与双层目标：长期完整闭环牵引、短期真实能力验证。
3. 建立能力切片四级证据协议，并记录验收能力的不同发现入口。
4. 更新对话行动交接规则，降低开放式总结带来的阅读与行动负担。
5. 校正首个切片主线：验收任务作为夹具，优先建设可复用、可重放的任务知识准备能力。
6. 实现最小 `task_case.py` 账本工具、机械双门禁和恢复夹具。
7. 两次 Gemini 重放形成“首次路径失败、第二次核心通过”的 L1 证据；建立 AGENTS 自治理与最小评测策略。
8. 吸收 Anthropic、LangChain 与知识系统项目实践，按方法论优先重构评测领域模型。
9. 冻结恢复 fixture，建立参考响应、人工 Grader 校准和不存在 ID 的反向任务；满足最小 Runner 的设计前置条件。
10. 完成九个项目 Skill 的来源审计和首轮治理：活动面收敛为四个，重写 `knowledge-ingest`，退役五个超前或冲突 Skill，并建立 13 个路由 fixture 与契约测试。
