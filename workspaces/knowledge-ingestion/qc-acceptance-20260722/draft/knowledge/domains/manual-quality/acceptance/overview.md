---
type: Concept
title: 人工质检验收子域总览
description: 定义验收阶段的业务对象、流程位置、结论语义和交付完成边界；不把设计目标自动视为当前实现。
tags: [manual-quality, acceptance, workflow]
---

# 人工质检验收子域总览

## 目的与边界

- **解决的问题**：让人和模型知道验收处理什么、按什么粒度组织、何时进入结论、打回后如何继续，以及哪些事实尚未落地。
- **包含**：交付任务上下文、验收分配与执行、PASS/REJECT/PENDING 结论、返修循环、可交付 Good 数量和归档条件。
- **不包含**：标注任务生产的完整实现、Delta/DMP 的当前生产契约和未经确认的业务阈值。

## 业务闭环

- **结论**：候选业务轨道是“需求对齐 → 数据/规则/适配就绪 → 任务生产 → 标注 → 验收分配 → 实际验收 → 通过/打回与状态回查 → 可交付 Good 数量确认 → 交付完成”。REJECT 会回到返修标注，再进入验收，不是流程终点。
- **现实形态**：目标设计与人工决定；source-a 的旧版 wiki 还记录了历史手动分配/通过打回流程。
- **依据**：[quality_check 设计来源](../../../sources/omni-brain-m1-quality-check.md#业务闭环与交付完成)；[ai-knowledge-base 来源](../../../sources/ai-knowledge-base-qc.md#旧版人工质检流程)
- **适用范围**：以“一个数据集/批次”为交付管理上下文，以验收任务和统计单元执行操作。
- **冲突/未知**：当前实现只证明查询和 preview；真实 execute 与状态回查未被 source-a 代码/测试证明。

## 状态不要混成一个字段

- **结论**：交付阶段、健康状态、行动项状态和验收结论是四类不同语义；前端需要同时表达任务走到哪里、是否有风险、下一动作和质量判定。
- **现实形态**：目标设计。
- **依据**：[quality_check 设计来源](../../../sources/omni-brain-m1-quality-check.md#业务闭环与交付完成)
- **适用范围**：交付中心和验收中心的列表、详情、时间线和下一动作。
- **冲突/未知**：当前 vertical slice schema 的 `status` 是单个任务字段，不能证明已经实现四维状态模型。

## 交付完成的候选定义

- **结论**：至少要确认通过/打回执行及回查完成、验收通过中的 Good 能形成最终交付量、与期望数量对照、质检规范和适配版本等关键记录归档；“验收页面没有待处理项”本身不足以证明交付完成。
- **现实形态**：目标设计；留存率正式口径明确待人类补充。
- **依据**：[quality_check 设计来源](../../../sources/omni-brain-m1-quality-check.md#业务闭环与交付完成)
- **适用范围**：交付盖章和退出活跃队列前的业务门禁。
- **冲突/未知**：预计验收时长、最终 Good 口径、留存率、责任人和权限尚未冻结。

## 关联与边界

验收的数量与层级口径见[验收数据粒度与快照口径](data-granularity-and-snapshot.md)，可执行前的选择和配额见[验收抽样与分配预览](sampling-and-preview.md)，结论执行的历史与目标边界见[通过打回与状态回查](pass-reject-and-reconciliation.md)，当前代码证据集中在[验收前后端实现边界](implementation-boundaries.md)。

## Citations

1. [quality_check 设计来源](../../../sources/omni-brain-m1-quality-check.md)
2. [ai-knowledge-base 来源](../../../sources/ai-knowledge-base-qc.md)
