---
type: Navigation View
title: 人工质检验收领域位置
description: 从人工质检领域进入验收闭环的规范知识、实现事实和待确认边界。
tags: [view, manual-quality, acceptance]
---

# 人工质检验收领域位置

## 你现在在哪里

你位于[人工质检](../../domains/manual-quality/overview.md)下的[人工质检验收](../../domains/manual-quality/acceptance/overview.md)子域。

## 这条路线解决什么问题

它把交付任务、scene/task/date 粒度、快照统计、抽样预览和通过打回放在同一个业务边界里，同时区分当前代码和设计目标。

## 从头理解

1. [人工质检领域总览](../../domains/manual-quality/overview.md) — 先理解验收在交付闭环中的位置。
2. [人工质检验收子域总览](../../domains/manual-quality/acceptance/overview.md) — 建立对象粒度、阶段和核心入口。
3. [验收数据粒度与快照口径](../../domains/manual-quality/acceptance/data-granularity-and-snapshot.md) — 理解 scene、task、date 与统计边界。
4. [验收抽样与分配预览](../../domains/manual-quality/acceptance/sampling-and-preview.md) — 理解可执行前的配额计算和冻结结果。
5. [通过打回与状态回查](../../domains/manual-quality/acceptance/pass-reject-and-reconciliation.md) — 区分历史规则、目标状态机和当前已证实范围。
6. [验收前后端实现边界](../../domains/manual-quality/acceptance/implementation-boundaries.md) — 回到 API、Repository、Vue 与测试入口。

## 按问题查找

- **验收什么时候算交付完成？** → [人工质检验收子域总览](../../domains/manual-quality/acceptance/overview.md)
- **一个 scene、task、日期分别代表什么？** → [验收数据粒度与快照口径](../../domains/manual-quality/acceptance/data-granularity-and-snapshot.md)
- **如何计算抽样配额并避免前端自算？** → [验收抽样与分配预览](../../domains/manual-quality/acceptance/sampling-and-preview.md)
- **PASS/REJECT 如何执行？** → [通过打回与状态回查](../../domains/manual-quality/acceptance/pass-reject-and-reconciliation.md)
- **当前代码实际有哪些接口？** → [验收前后端实现边界](../../domains/manual-quality/acceptance/implementation-boundaries.md)

## 按现实形态查看

- 当前实现：[验收 vertical slice 当前实现](../../systems/acceptance-vertical-slice.md)
- 历史快照：来源记录中的旧版人工质检卡与 `quality_check` 旧版行为摘录。
- 目标设计：[通过打回与状态回查](../../domains/manual-quality/acceptance/pass-reject-and-reconciliation.md)、[验收抽样与分配预览](../../domains/manual-quality/acceptance/sampling-and-preview.md)
- 开放问题：见工作台根目录的 `review.md` 与 `assets/questions.md`。

## 系统与实现入口

- [当前实现边界](../../domains/manual-quality/acceptance/implementation-boundaries.md)列出代码、SQL、测试和验证脚本位置；它们是来源定位，不是本仓库内的代码副本。

## 仍需谁补什么

- 业务负责人确认阈值、正式 schema、scene_name 规则和完成口径。
- 工程负责人提供 execute/回查的当前运行证据。
