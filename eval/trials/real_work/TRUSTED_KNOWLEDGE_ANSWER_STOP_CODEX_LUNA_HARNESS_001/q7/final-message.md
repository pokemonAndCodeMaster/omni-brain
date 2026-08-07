结论：

- 最终目标：20
- Good 计划：15
- Bad 计划：5
- `shortage`：0
- Warning：`Bad 可用量不足，已由 Good 补足`

计算：理论目标为 Good 10、Bad 10；Bad 只有 5，因此先分配 Bad 5，再由 Good 补足剩余 5，最终达到总量 20。

这份预览只完成“各范围抽多少”中的 Ratio 数量规划；完整分配仍未决定：

1. 具体抽哪些 `task`
2. 哪些任务最终固定进样本
3. 由哪些验收员接收

若 Good+Bad 总容量只有 12：

- 最终目标必须显示为 12
- 总量 `shortage` 必须显示为 8
- 必须显示“总可用量不足，无法满足请求的 20”
- Good/Bad 计划还需按实际两类容量计算；仅知道总容量 12，不能精确推出两类计划，不能静默只显示总量 12。

依据：[Ratio 数量算法与示例](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/sampling-and-assignment.md>)。