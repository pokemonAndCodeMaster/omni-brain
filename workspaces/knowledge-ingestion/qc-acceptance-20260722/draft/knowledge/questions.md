---
type: Navigation View
title: 人工质检验收候选开放问题
description: 候选知识发布前必须保留的冲突、未知和证据缺口。
tags: [view, questions, acceptance]
---

# 人工质检验收候选开放问题

## 仍未证实

- **Q1 规则版本**：旧版 Good/Bad 阈值与 M1 目标状态机不能自动合并。
- **Q2 粒度口径**：`scene_name` 的正式提取和 project 推断仍需当前字段/代码确认。
- **Q3 数据库版本**：`t_qc_delivery_task`、`t_qc_operation_preview` 与目标 `t_qc_daily_snapshot` 的正式关系未知。
- **Q4 执行闭环**：当前 source-a 只证明 preview；没有 execute、Delta 回查、幂等和重试的当前实现证据。
- **Q5 交付完成**：留存率、Good 交付量、责任人与权限矩阵未冻结。
- **Q6 设计完成标记**：source-b 的完成情况没有逐项绑定 commit、测试报告或人工决定。

## 处理规则

这些问题不会用常识补齐。进入正式发布前，用户需要逐项批准、拒绝、保留或指定补证来源；本页只提供导航，不替代摄入案根入口的完整登记。

# Citations

1. [ai-knowledge-base 来源](sources/ai-knowledge-base-qc.md)
2. [quality_check 来源](sources/omni-brain-m1-quality-check.md)
