---
type: Navigation View
title: 理解人工质检验收闭环
description: 面向人和后续模型的零背景阅读路线，沿业务问题逐步回到当前实现与来源。
tags: [view, journey, acceptance]
---

# 理解人工质检验收闭环

## 你现在在哪里

从[人工质检验收领域位置](../by-domain/acceptance-map.md)进入，目标是理解一条交付任务如何从标注完成走到验收、结论、返修或交付。

## 这条路线解决什么问题

先建立业务语义，再读取代码事实，最后把历史规则和设计目标放回审查清单，避免模型只看到某一份杂乱材料就下结论。

## 从头理解

1. [人工质检领域总览](../../domains/manual-quality/overview.md) — 明确验收不是孤立页面，而是交付轨道的一段。
2. [人工质检验收子域总览](../../domains/manual-quality/acceptance/overview.md) — 识别阶段、结论和完成定义。
3. [验收数据粒度与快照口径](../../domains/manual-quality/acceptance/data-granularity-and-snapshot.md) — 识别管理单元与可操作单元。
4. [验收抽样与分配预览](../../domains/manual-quality/acceptance/sampling-and-preview.md) — 理解从选择到可审查配额的过程。
5. [验收前后端实现边界](../../domains/manual-quality/acceptance/implementation-boundaries.md) — 用代码、schema、测试验证当前能力。
6. [通过打回与状态回查](../../domains/manual-quality/acceptance/pass-reject-and-reconciliation.md) — 识别仍需人工决策的执行闭环。

## 按问题查找

- **为什么 REJECT 不是流程终点？** → [人工质检验收子域总览](../../domains/manual-quality/acceptance/overview.md)
- **为什么需要 source_version 和过期 preview？** → [验收抽样与分配预览](../../domains/manual-quality/acceptance/sampling-and-preview.md)
- **为什么不能把 PENDING 当成可执行？** → [通过打回与状态回查](../../domains/manual-quality/acceptance/pass-reject-and-reconciliation.md)
- **哪些接口有测试证据？** → [验收前后端实现边界](../../domains/manual-quality/acceptance/implementation-boundaries.md)

## 按现实形态查看

- 当前实现：[验收 vertical slice 当前实现](../../systems/acceptance-vertical-slice.md)
- 历史快照：来源记录 [ai-knowledge-base](../../sources/ai-knowledge-base-qc.md) 中的旧版人工质检卡。
- 目标设计：来源记录 [quality_check 设计材料](../../sources/omni-brain-m1-quality-check.md)及各候选页的“目标设计”段落。
- 开放问题：见工作台根目录的 `assets/questions.md`。

## 系统与实现入口

阅读到实现时，按候选页中的相对来源链接回查文件、符号、测试方法和 SQL；不要把来源路径当作本知识库内的可执行代码。

## 仍需谁补什么

人工批准候选规则后，后续模型才能把选定版本当作正式规范；在此之前应保留“候选/未决”措辞。
