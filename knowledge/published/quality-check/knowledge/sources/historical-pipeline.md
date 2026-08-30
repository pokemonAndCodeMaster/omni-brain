---
type: Source Record
title: 人工质检验收历史运行快照来源
description: 记录旧脚本式分配、通过打回、状态刷新和中间表链路，仅作为历史事实。
tags: [source, historical]
---

# 人工质检验收历史运行快照来源

## 来源记录的责任与范围

这是历史材料的追溯页，不是现行操作说明。它按**来源身份 → 历史材料能证明什么 → 为什么不能外推当前 → 已读取范围 → 已内化去向**组织，防止具体阈值和脚本行为在失去时间语境后被继续沿用。

## 身份与基线

- **位置**：`raw/notebooklm_exports/fc03a900-e886-44a5-85b0-73983c0efa41/20_*`、`30_*`—`33_*`
- **版本**：来源仓 commit `3cf393479d59dae57280df3c80a1ff213a936909`
- **类型**：NotebookLM 原始下载中的旧代码/流程概念快照。

## 能证明

- 当时材料记录的验收分配、Good/Bad 抽样、通过打回、状态刷新和中间表处理方式；
- 旧材料记录的阈值、状态值、接口动作、调度周期和表名。

## 不能证明

- 当前生产仍使用同一脚本、阈值、接口、状态值、表或调度周期；
- 文档中的链接和 related_code 在当前来源仓仍可执行。

## 实际读取范围

- 20：验收与通过打回总览；
- 30：验收分配、抽样和输出；
- 31：批量通过打回规则与动作；
- 32：状态刷新与 GT 回写；
- 33：中间表更新和历史状态映射。

## 规范知识去向

- [验收生命周期](../domains/quality/manual/acceptance/lifecycle.md)：历史步骤在完整业务闭环中的位置；
- [采样与分配](../domains/quality/manual/acceptance/sampling-and-assignment.md)：Group、Personal 历史策略和 Ratio 对照；
- [结论与执行](../domains/quality/manual/acceptance/conclusion-and-execution.md)：完成度、阈值、严格比较和历史打回链；
- [当前未知与冲突](../domains/quality/manual/acceptance/open-questions.md)：哪些历史规则仍需当前业务证据。
