---
type: Domain Overview
title: 人工质检
description: 管理从需求登记、标注、验收、返修到交付完成的人工质检业务语义。
tags: [domain, manual-quality]
---

# 人工质检

## 边界

- **包含**：交付任务、规范与适配就绪、标注与验收阶段、质量结论、返修、行动项和最终交付确认。
- **排除**：上游数据生产算法、通用学习资料、未由本轮来源证明的生产部署事实。

## 领域位置

- **上级**：根领域
- **子域**：[人工质检验收](acceptance/overview.md)

## 关键旅程

- [理解人工质检验收闭环](../../views/by-journey/acceptance-understanding.md)：从交付轨道进入验收分配、实际验收、结论、返修和交付核对。

## 核心知识

- [人工质检验收](acceptance/overview.md)：说明验收在业务闭环中的位置和完成定义。

## 跨领域入口

人工质检验收依赖上游标注提交和规则/适配版本，但本轮只摄入验收边界；[验收数据粒度与快照口径](acceptance/data-granularity-and-snapshot.md)说明统计输入如何进入验收视图。

## 当前未知

- 交付完成的留存率、正式责任人和权限矩阵未冻结。
- source-b 的“已完成”标记尚未逐项关联到可验证 commit 或运行记录。
