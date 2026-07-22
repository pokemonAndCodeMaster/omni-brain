---
type: Concept
title: 验收抽样与分配预览
description: 说明验收选择如何解析为统计单元、如何按 Good/Bad 比例计算配额，以及为什么要冻结可审查的 preview。
tags: [manual-quality, acceptance, sampling, preview]
---

# 验收抽样与分配预览

## 目的与边界

- **解决的问题**：在外部执行前，把选择、可用量、Good/Bad 配额、缺口和数据版本变成可审查结果，避免前端重复计算或直接对变化中的数据执行。
- **包含**：Ratio 采样、容量不足补足、稳定取整、显式/筛选全选、排除项、preview TTL/owner/source_version。
- **不包含**：source-b 提到的旧版组内/个人/供应商轮询是否仍是正式策略，以及真实 Delta 执行。

## 当前可证明的 Ratio 计划

- **结论**：当前 source-a 的 `plan_ratio_sampling()` 汇总 Good/Bad 可用量，先按 `good_ratio` 计算目标，再在一侧不足时由另一侧补足；每个桶按容量比例分配，取整后按小数余数和稳定 `id` 顺序补余数，并返回 shortage/warnings。
- **现实形态**：当前实现。
- **依据**：[ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md#当前实现)
- **适用范围**：`strategy=ratio` 的验收分配预览；不是所有历史采样策略的统一结论。
- **冲突/未知**：source-b 还描述 GroupSampler、PersonalSampler 和旧版 Good/Bad 常量；正式策略需要 Q1/Q6 决定。

## Preview 闭环

- **结论**：`SelectionSpec` 支持 explicit/filtered 两种选择；日期 ID 形如 `<task_id>-date-<YYYY-MM-DD>`，可携带排除项。服务解析选择并查询可用单元，创建带 `preview_id`、30 分钟默认过期时间、`source_version`、结果摘要的 READY 预览；回读必须按创建人且未过期。当前路由只提供 POST 创建和 GET 回读，没有 execute 路由。
- **现实形态**：当前实现。
- **依据**：[ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md#当前实现)
- **适用范围**：当前 vertical slice 的前端/后端预览链。
- **冲突/未知**：是否需要按业务版本、权限和外部平台状态再次失效，材料未提供已运行证据。

## 关联与边界

预览的输入粒度来自[验收数据粒度与快照口径](data-granularity-and-snapshot.md)，预览结果最终属于[通过打回与状态回查](pass-reject-and-reconciliation.md)的执行前门禁；当前接口和测试入口见[验收前后端实现边界](implementation-boundaries.md)。

# Citations

1. [ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md)
2. [quality_check 设计来源](../../../sources/omni-brain-m1-quality-check.md)
