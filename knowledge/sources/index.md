# 来源记录

来源记录保存“这批材料是什么、版本在哪里、能证明什么和不能证明什么”，用于追溯与复核；它不是规范知识正文。业务定义、算法步骤、状态边界和软件结构必须在对应知识页中被充分解释，不能压成一两句后把理解责任推给下面的链接。

- [人工语义决定](human-decisions.md)：三阶段边界和执行全集；两份文件完全重复，缺原始对话。
- [历史验收运行快照](historical-pipeline.md)：旧分配、阈值、通过打回、状态刷新和中间表链路。
- [目标验收平台设计](target-design.md)：平台、人工质检、快照、采样、规则、外部系统和 Repository 的目标方案。
- [当前验收原型](current-prototype.md)：固定提交中的 Python、SQL、前端和直接依赖。

以上来源全部属于 Batch 1。Batch 2 尚未登记到 K0。

## 来源怎样进入规范知识

| 来源 | 已内化的主要知识 | 仍保留在来源记录中的内容 |
|---|---|---|
| 人工语义决定 | [生命周期与阶段边界](../domains/quality/manual/acceptance/lifecycle.md)、[结论与执行对象](../domains/quality/manual/acceptance/conclusion-and-execution.md) | 原始决定缺失、重复文件和可证明边界 |
| 历史运行快照 | [采样算法与历史策略](../domains/quality/manual/acceptance/sampling-and-assignment.md)、[历史结论规则](../domains/quality/manual/acceptance/conclusion-and-execution.md) | 历史材料身份及为何不能外推当前 |
| 目标设计 | [数据流与状态](../domains/quality/manual/acceptance/data-flow-and-state.md)、[系统架构](../domains/quality/manual/acceptance/system-architecture.md) | 目标方案的来源范围和未实现边界 |
| 当前原型 | [Python 软件结构](../domains/quality/manual/acceptance/python-architecture-and-implementation.md)、[当前仓库原型](../systems/manual-qc-acceptance-prototype.md) | 固定提交、实际读取文件和测试证据边界 |

如果规范知识页只剩摘要而必须打开原始来源才能知道机制、算法、约束或例外，应判定为摄入不完整；来源链接只能用于核验和继续下钻，不能用于补偿正文缺失。
