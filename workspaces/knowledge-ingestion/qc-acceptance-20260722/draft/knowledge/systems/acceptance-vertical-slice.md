---
type: System
title: 验收 vertical slice 当前实现
description: 记录 source-a Git 基线中已存在的人工质检验收首个纵切及其验证边界。
tags: [system, manual-quality, acceptance]
---

# 验收 vertical slice 当前实现

## 目的与边界

- **解决的问题**：为后续模型提供一个可回查的当前代码事实入口。
- **包含**：查询、日期下钻、Ratio preview、相关表和测试。
- **不包含**：外部 Delta execute、生产运行状态和正式业务规则裁决。

## 已证实组件

- **结论**：代码存在验收查询 Router/Service/Repository、日期 breakdown、metadata、Ratio sampler、AssignmentPreviewService 和 preview 持久化 migration；测试覆盖这些组件的局部契约。
- **现实形态**：当前实现。
- **依据**：[ai-knowledge-base 当前代码来源](../sources/ai-knowledge-base-qc.md#当前实现)
- **适用范围**：Git `3cf3934` 指向的来源文件。
- **冲突/未知**：来源仓库 dirty；未提交文件不作为本页事实。

## 关联与边界

详细业务解释见[验收前后端实现边界](../domains/manual-quality/acceptance/implementation-boundaries.md)，完整业务路线见[人工质检验收子域总览](../domains/manual-quality/acceptance/overview.md)。

# Citations

1. [ai-knowledge-base 当前代码来源](../sources/ai-knowledge-base-qc.md)
