---
type: Concept
title: 验收数据粒度与快照口径
description: 说明 scene_name、clip/task、日期和组/人员维度在验收管理、采样和统计中的边界，并记录快照设计与当前 vertical slice 的差异。
tags: [manual-quality, acceptance, scene-name, snapshot]
---

# 验收数据粒度与快照口径

## 目的与边界

- **解决的问题**：避免把管理批次、实际操作任务和日统计行混为一层，导致抽样、查询或批量执行范围错误。
- **包含**：scene_name、clip/task、date、group/employee 以及快照字段分组的候选口径。
- **不包含**：没有真实 Delta 样例时对所有项目命名规则的最终确认。

## 三层粒度

- **结论**：候选模型把 `scene_name` 视为质检流程的最小管理/聚合单元；一个 scene 包含多个 clip/task；clip/task 是标注或验收的最小操作单元；date 是统计与预览下钻单元。group/employee 用于责任和聚合。
- **现实形态**：人工决定/目标设计；source-b 明确了这一层级关系。
- **依据**：[quality_check 设计来源](../../../sources/omni-brain-m1-quality-check.md#粒度与快照)；[ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md#当前实现)
- **适用范围**：验收列表、日期展开、按 scene 采样、快照联合键和执行前 task 解析。
- **冲突/未知**：source-b 同时记录 `scene_name` 从 Delta `task_name` 提取的 e2e/vpd 差异及历史 project 推断缺陷；必须用当前真实字段确认。

## 快照与统计

- **结论**：目标快照设计按日、scene、组、人员保留标注进度、验收分配/提交、Good/Bad 结果和执行结论；统计刷新应与执行状态分离，避免刷新覆盖执行或人工结论。source-a 的已实现 vertical slice 则以 `t_qc_daily_snapshot` 提供查询输入，并用 `t_qc_delivery_task`/`t_qc_operation_preview` 支撑首个验收纵切。
- **现实形态**：目标设计 + 当前 vertical slice 实现；不是同一 schema 的等同声明。
- **依据**：[quality_check 设计来源](../../../sources/omni-brain-m1-quality-check.md#粒度与快照)；[ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md#当前实现)
- **适用范围**：按任务查询、按日下钻、采样可用量和结果展示。
- **冲突/未知**：source-b 目标表字段/迁移版本与 source-a vertical slice migration 不一致；Q3 未决。

## 关联与边界

选择和配额建立在这些粒度之上，见[验收抽样与分配预览](sampling-and-preview.md)；实际查询、日期下钻和响应字段见[验收前后端实现边界](implementation-boundaries.md)。

# Citations

1. [quality_check 设计来源](../../../sources/omni-brain-m1-quality-check.md)
2. [ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md)
