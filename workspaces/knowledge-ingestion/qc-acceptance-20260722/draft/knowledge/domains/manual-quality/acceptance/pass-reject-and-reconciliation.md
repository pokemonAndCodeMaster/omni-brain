---
type: Concept
title: 通过打回与状态回查
description: 对照旧版人工质检规则、M1 目标执行状态机和当前已证实实现范围，说明 PASS/REJECT 的安全边界。
tags: [manual-quality, acceptance, pass-reject, reconciliation]
---

# 通过打回与状态回查

## 目的与边界

- **解决的问题**：把质量结论、外部状态变化、执行进度和返修循环分开，避免一次点击被误认为最终完成。
- **包含**：PENDING/PASS/REJECT 语义、旧版通过率规则、目标 exec_status、两次打回回查、执行前后再聚合。
- **不包含**：未经确认的正式阈值、当前生产 Delta API 成功率和幂等保证。

## 历史旧版行为

- **结论**：source-a 旧版卡记录过人工触发的 Good/Bad 通过率判定、通过链路和打回链路；source-b 设计材料进一步记录了“先退待验收，再等待外部状态，再退待审核/审核中”的两次调用及 60 秒等待。这些是历史/设计证据，不应直接当作当前规则。
- **现实形态**：历史快照 + 目标设计。
- **依据**：[ai-knowledge-base 来源](../../../sources/ai-knowledge-base-qc.md#旧版人工质检流程)；[quality_check 来源](../../../sources/omni-brain-m1-quality-check.md#通过打回与状态回查)
- **适用范围**：回查旧系统行为、识别迁移风险。
- **冲突/未知**：旧版文档中的阈值、状态码、路径与 M1 vertical slice 不一致；Q1、Q2、Q4 必须先解决。

## 目标执行状态机

- **结论**：source-b 目标设计把 `conclusion`（决策）与 `exec_status`（执行进度）分离；维度可独立执行，终态不可逆，执行失败保持 EXECUTING 由重试/人工介入处理；PENDING 不可执行，execute 前后应重新聚合并验证数据版本。
- **现实形态**：目标设计/人工决定，未由 source-a 当前代码证明。
- **依据**：[quality_check 来源](../../../sources/omni-brain-m1-quality-check.md#通过打回与状态回查)
- **适用范围**：未来 execute 服务、执行审计和快照刷新边界。
- **冲突/未知**：当前代码没有 execute route 或状态机实现的直接证据；不能发布为当前能力。

## 执行门禁

- **结论**：候选安全顺序是：校验权限 → 拒绝 PENDING → 确认用户提交结论与新聚合一致 → 按范围重新查询 task_ids/状态 → 调用外部平台 → 返回即时成功/跳过/失败 → 依靠后续回查确认最终状态并刷新统计。REJECT 的范围和是否全量回退仍需业务确认。
- **现实形态**：目标设计。
- **依据**：[quality_check 来源](../../../sources/omni-brain-m1-quality-check.md#通过打回与状态回查)
- **适用范围**：所有会改变外部任务状态的验收执行。
- **冲突/未知**：没有当前运行证据证明重试、幂等、部分失败和外部延迟已处理。

## 关联与边界

分配预览提供执行前的可审查结果，见[验收抽样与分配预览](sampling-and-preview.md)；粒度决定执行范围，见[验收数据粒度与快照口径](data-granularity-and-snapshot.md)；当前仅实现的 API 见[验收前后端实现边界](implementation-boundaries.md)。

# Citations

1. [quality_check 来源](../../../sources/omni-brain-m1-quality-check.md)
2. [ai-knowledge-base 来源](../../../sources/ai-knowledge-base-qc.md)
