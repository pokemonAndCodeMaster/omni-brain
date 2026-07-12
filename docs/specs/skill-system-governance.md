# Skill 体系治理协议

> **状态**：Implemented@contract / Provisional；首轮历史 Skill 已治理，仍需独立模型路由和端到端知识变更 Trial。  
> **目的**：让 Skill 只表达已经具备或明确降级的可重复行为，避免初始化设想、stub 和偶然做法成为默认能力。  
> **证据入口**：[Skill 审计](../research/skill-system-audit-2026-07-12.md)｜[Blueprint](../blueprint.md)｜[评测策略](evaluation-strategy.md)

## 1. Skill 的定位

Skill 是 Agent Harness 的行为契约：它把一段需要重复、可观察、可评测的过程或共享参考带入会话。它不是产品路线图、组件愿望清单、知识库目录或不存在工具的接口说明。

一个候选过程只有同时满足以下条件，才值得成为模型可发现 Skill：

1. 有独立且可描述的触发分支；
2. 默认模型行为不足以稳定完成，需要契约降低方差；
3. 步骤或参考在多个任务中具有复用价值；
4. 所依赖的工具真实存在，或写明可验证的人工降级；
5. 状态变更、授权边界、失败方式和完成标准清楚；
6. 至少有一个正例和一个不应触发的反例；
7. 与 AGENTS、其他 Skill 和代码保持单一事实源。

“出现两次”只能产生候选，不能自动证明以上条件。

## 2. 三类职责

- **操作型 Skill**：调用真实工具或执行稳定步骤；必须验证依赖、失败降级和结果状态。
- **编排型 Skill**：跨多个能力维护任务进度；必须有权威账本、阶段门禁和可恢复交接。
- **参考型 Skill**：提供 Agent 需要共享的判断尺度；不应伪装成 Omni-Brain 已实现组件。

同一 Skill 同时承担捕获、知识晋升、任务关闭和创建新 Skill 时，应先拆责任，而不是继续追加步骤。

## 3. 采用强度

Skill 的产品成熟度沿用 Blueprint，但运行采用强度单独记录：

```text
quarantined → explicit-experiment → recommended@verified-slice → default@verified-scope
```

- `quarantined`：保留迁移证据，不允许按旧描述自动执行；
- `explicit-experiment`：只由用户或上层已验证编排显式触发，并报告人工补偿；
- `recommended@verified-slice`：只在已通过 Eval 的任务切片推荐；
- `default@verified-scope`：多个代表场景稳定后，才可成为适用任务默认方式。

活动 Skill 目录中的文件必须服从采用强度，不能把尚不可用的能力草图放在目录中等待运行时自行判断。

## 4. 准入与变更门禁

新建或重写 Skill 先形成 change set：

- 解决的真实失败与来源 Transcript；
- 触发与反触发边界；
- 与 Blueprint 组件和其他契约的职责关系；
- 工具依赖及当前实现证据；
- 持久化、授权和回滚边界；
- 正例、反例、失败例和参考结果；
- description/context load 与用户 cognitive load 取舍；
- 旧 Skill 的迁移、替代或退役方式。

先校准 Eval，再提升采用强度。仅修改措辞但没有行为证据，状态仍是 implemented，而不是 verified。

## 5. 内容边界

SKILL.md 内只保留每次调用都需要的步骤、完成标准和护栏。条件分支的详细 rubric、Schema 或示例通过明确的 context pointer 下沉；动态成熟度、当前 gap、产品路线和评测结果分别留在 Blueprint、spec、派生视图和 `eval/`。

每次审查执行四项清理：

1. 删除不存在接口和过时实现；
2. 删除与 AGENTS/代码重复的含义，改为指向权威源；
3. 收窄宽泛 description，补反触发边界；
4. 删除不改变模型行为的 no-op 和历史 sediment。

## 6. 首轮验证

以 `knowledge-ingest` 为第一个治理切片：

- 正例：用户明确要求把已完成的 Eval 研究形成长期可复用知识；
- 反例：用户只要求总结一次回答、查看状态或整理临时任务材料；
- Outcome：研究输入、provisional 设计、规范知识候选和实施用例被正确分流；未经授权不保存完整原料、不批量建卡；
- 失败门禁：不得调用 stub 冒充检索/编译成功，不得把外部观点或讨论假设写成已批准规范。

首轮只治理有真实问题证据的 Skill，不设计额外的 Skill 清单或状态系统。

## 7. 首轮实现状态

- `knowledge-ingest` 已重写为长期知识变更 Skill，仍保持模型可发现，但 description 只覆盖明确长期知识授权或已批准候选；
- `eval-runner`、项目 `skill-creator`、`task-reflector`、`knowledge-health`、`code-ingest` 已从活动 Skill 目录删除，待对应实现和用例成熟后重新创建或恢复；
- 未创建 `skill-change-proposal`，长期公共能力变更先按 C 类任务形成 change set，再显式使用系统级 Skill 创建能力；
- 无仓库消费者的 `.agents/skills.json` 已删除；当前不建设另一套 registry，Skill 文件本身就是活动集合；
- 13 个路由 fixture 与静态契约测试已经建立，但尚未形成 Agent Harness Trial，不能升级为 `recommended@verified-slice`。
