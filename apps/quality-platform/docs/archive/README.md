# 历史设计归档

本目录保存已经实施完毕、被后续实现替代，或仅用于解释历史取舍的设计与计划。
它们仍然是有价值的决策证据，但不再是当前执行入口。

| 文档 | 归档原因 | 当前替代入口 |
|---|---|---|
| [`manual-qc-analysis-workbench-v2-design.md`](manual-qc-analysis-workbench-v2-design.md) | V2 五个实施切片已经完成 | [`../handoff.md`](../handoff.md)、[`../component-map.md`](../component-map.md) |
| [`snapshot-page-plan.md`](snapshot-page-plan.md) | 页面规划已经落成当前工作台 | [`../handoff.md`](../handoff.md)、[`../verification-report.md`](../verification-report.md) |

使用规则：

- 需要理解“为什么这样设计”时阅读归档；
- 判断当前代码行为时以源码、当前契约和新鲜运行结果为准；
- 不从归档文档中的“下一步”“建议新增”直接开始开发；
- 若重新采用历史方案，先对照当前实现和真实业务工况重新确认。
