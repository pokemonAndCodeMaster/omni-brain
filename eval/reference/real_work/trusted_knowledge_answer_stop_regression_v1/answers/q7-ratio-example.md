# Ratio 算例

**结果：** 请求目标 20 没有超过总容量 45，所以最终目标是 **20**、总量 `shortage = 0`。50% 原本要求 Good 10 / Bad 10；Bad 只有 5，剩余 5 由 Good 补足，因此计划是 **Good 15 / Bad 5**。用户必须看到“Bad 可用量不足，已由 Good 补足”的 warning。

这仍只是数量规划，没有决定**具体抽哪些 task、分给哪些验收员、是否已经调用外部系统正式分配**。

如果 Good+Bad 总容量只有 12，最终目标必须降为 **12**，并明确显示总量 `shortage = 8`；不能只悄悄返回一个更小数字。

依据：[人工质检验收采样、选择与分配](../../../../../../omni-brain-harness-quality-check-v1/knowledge/domains/quality/manual/acceptance/sampling-and-assignment.md)。
