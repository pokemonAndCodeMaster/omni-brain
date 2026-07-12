# Omni-Brain 当前工作台

> **用途**：从上次讨论快速续接当前工作；只保存短摘要和权威链接，不复制完整知识或会话。  
> **状态**：Provisional view；维护规则见 [`specs/conversation-knowledge-lifecycle.md`](specs/conversation-knowledge-lifecycle.md)。  
> **最近整理**：2026-07-12。

## 当前目标

处于 R0→R1 过渡：以人工质检验收作为真实测试夹具，先验证“任务框架与问题缺口 → 存量盘点与补知 → 规范知识编织 → 决策准备度 → 任务投影/长期知识分流”，再逐步推进方案、产物、验证与回写。完整质检平台能力建设闭环仍作长期牵引，领域工具不是当前首要结果。详见 [Blueprint](blueprint.md) 与 [产品讨论稿](product-direction-discussion.md)。

## 活跃线程

1. **持续问题处理与对话回收**｜Provisional｜让日常困扰和讨论结论成为可追溯的验证输入，而不是聊天记录堆积。→ [问题处理协议](specs/continuous-problem-loop.md)｜[对话回收协议](specs/conversation-knowledge-lifecycle.md)
2. **日志规范案例**｜Triaged｜验证 AI 在写代码时能否带入带范围的工程规范，并识别历史冲突写法；不是日志整改任务。→ [案例](problems/2026-07-11-logging-standard-not-applied.md)
3. **任务知识准备能力**｜Implemented@mechanical-ledger｜一次基础模型重放准确恢复了语义结果，但依靠 Skill 猜测、目录搜索、全量阅读和环境变更补偿；已加入“显式 ID 直读 `case.yaml`、按需下钻、不为恢复加载工作流 Skill”的快速通道，待同类模型复测。→ [任务案](../workspaces/task-cases/acceptance-knowledge-prep/overview.md)｜[质检场景](scenarios/quality-domain-knowledge-workbench.md)
4. **人工质检具体能力产物**｜后置候选｜在知识准备与后续建设组件得到切片证据后再选择；验收任务分配闭环目前只是领域假设。→ [问题案例](problems/2026-07-11-manual-quality-capability-construction-gap.md)｜[实验协议](specs/capability-slice-experiment.md)
5. **讨论行动交接**｜Experimenting｜试行“本轮决定 + 现在怎么继续”，降低开放式总结造成的阅读与行动负担。→ [问题案例](problems/2026-07-11-discussion-action-handoff-unclear.md)｜[对话协议](specs/conversation-knowledge-lifecycle.md)

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

## 下一步候选

- 用同类基础模型复测显式任务案恢复快速通道，目标为结果字段完整、零搜索、零无关读取和零环境变更；
- 快速通道稳定后，优先验证原子 question-answer/resolve 回写；若仍不稳定再设计单一 resume 输出；
- 设计任务投影与长期知识变更候选的分流门禁，并用人类浏览视图检查知识是否碎片化；
- 将日志案例改写为可运行的用户旅程与验收表；
- 用两条旅程手工组装第一版任务上下文包，并记录从方案到产物验证的失败类型；
- 达到触发条件时评审当前工作台的容量、字段和续接效果。
- 用后续五轮非简单讨论验证行动交接是否降低阅读负担，之后更新问题结果。

## 最近变化

1. 建立持续问题处理协议与首个日志案例。
2. 建立对话结论回收与续接协议。
3. 启用本工作台作为项目续接入口。
4. 完成本轮沉淀：明确以高标准纵向切片验证上下文、检索与协作架构。
5. 沉淀人工质检全流程痛点与目标，并确立“长期完整闭环牵引、短期真实能力产物验证”的双层目标。
6. 建立能力切片四级证据协议，并记录验收能力可能从不同知识和需求清晰度起步。
7. 更新对话规则：重要讨论必须形成可执行行动交接，并建立互动术语与结果说明。
8. 校正首个切片主线：验收任务先作为测试夹具，建设任务知识准备能力；同时约束短期任务价值、长期知识复利、人类浏览和基础模型可重放。
9. 实现最小 `task_case.py` 账本工具与验收探索恢复夹具；当前只形成机械实现证据，真实会话重放仍待进行。
10. 首次 Gemini 重放结果准确但引导路径失败；登记执行轨迹，并将任务案恢复与 C 类工作流执行拆开，等待第二次重放验证。
