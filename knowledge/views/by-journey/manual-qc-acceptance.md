---
type: Navigation View
title: 人工质检验收学习与任务旅程
description: 按先业务、再数据与规则、最后软件和代码的顺序学习当前候选知识。
tags: [view, journey, learning, manual-qc, acceptance]
---

# 人工质检验收学习与任务旅程

## 业务全貌与继续工作的入口

[质检领域](../../domains/quality/overview.md) → [人工质检总览](../../domains/quality/manual/overview.md) → [交付与行动项](../../domains/quality/manual/delivery-management.md) → [人员与权限](../../domains/quality/manual/personnel-and-permissions.md) → [统一数据工作台](../../capabilities/quality-data-workbench.md)

[平台与模块地图](../../domains/quality/manual/platform-and-module-map.md) · [业务到组件、代码与证据地图](../../domains/quality/manual/acceptance/implementation-map.md) · [前端状态与验收工作台](../../domains/quality/manual/acceptance/python-architecture-and-implementation.md)

## 学完这条路线应当获得什么

这条路线把同一套知识组织成完整学习、业务动作追踪和问题直达三种用法。完成学习后，读者应能说明验收是什么、历史流程怎样运行、目标平台怎样分层、当前代码走到了哪里，以及哪些生产问题仍不能可靠回答。

当前候选不能充当当前生产操作手册或完整交付管理手册；它已提供交付、人员权限和共享工作台的目标边界，但真实操作和开发任务仍需进入相应规范页与直接事实源核验。

## 学习层次

```mermaid
flowchart LR
    P[1 领域位置] --> B[2 阶段与业务链]
    B --> R[3 采样、规则与执行]
    R --> D[4 数据与状态]
    D --> S[5 系统与代码]
    S --> U[6 未知与核验]
```

| 层次 | 需要形成的认识 | 避免的误区 |
|---|---|---|
| 领域位置 | 验收属于人工质检，并处于标注与执行之间 | 从局部代码反推完整业务 |
| 阶段与业务链 | 标注、验收、结论、执行和返工的边界 | 把验收样本当执行全集 |
| 采样、规则与执行 | 数量、样本、结论和状态变化的机制 | 把算法结果当执行结果 |
| 数据与状态 | task、scene、快照、预览和新鲜度 | 把派生统计当原始事实 |
| 系统与代码 | 组件职责、调用顺序和实现限制 | 从目标类名推断已经实现 |
| 未知与核验 | 现实形态、冲突和补知责任 | 把历史或目标写成当前生产 |

## 完整学习路线

1. [领域位置](../by-domain/quality.md)
2. [验收总览](../../domains/quality/manual/acceptance/overview.md)
3. [验收生命周期](../../domains/quality/manual/acceptance/lifecycle.md)
4. [采样与分配](../../domains/quality/manual/acceptance/sampling-and-assignment.md)
5. [结论与执行](../../domains/quality/manual/acceptance/conclusion-and-execution.md)
6. [数据流与状态](../../domains/quality/manual/acceptance/data-flow-and-state.md)
7. [系统架构](../../domains/quality/manual/acceptance/system-architecture.md)
8. [Python 软件结构](../../domains/quality/manual/acceptance/python-architecture-and-implementation.md)
9. [当前原型](../../systems/manual-qc-acceptance-prototype.md)
10. [未知与冲突](../../domains/quality/manual/acceptance/open-questions.md)

## 业务动作路径

```text
已有标注结果
→ 选择验收范围
→ 计算抽样或分配配额
→ 分配验收并完成人工作业（历史与目标）
→ 汇总质量依据
→ 确认通过/打回结论
→ 对决定覆盖的标注全集执行
→ 回查最终状态
```

固定提交当前仍只覆盖这条链中的“查询范围 → Ratio 数量预览 → 保存/读取预览”；候选新增的交付、人员权限和工作台内容是业务/目标设计知识，不改变这一固定代码事实，其他验收步骤要么只有历史记录，要么只有目标方案。

## 问题捷径

| 问题 | 先读 |
|---|---|
| 为什么验收不是通过/打回按钮 | [生命周期](../../domains/quality/manual/acceptance/lifecycle.md) |
| 历史抽样和当前 Ratio 算法有什么区别 | [采样与分配](../../domains/quality/manual/acceptance/sampling-and-assignment.md) |
| 为什么接口成功后还要回查 | [结论与执行](../../domains/quality/manual/acceptance/conclusion-and-execution.md) |
| 快照、任务和预览怎样连接 | [数据流与状态](../../domains/quality/manual/acceptance/data-flow-and-state.md) |
| 代码怎样完成一次分配预览 | [Python 软件结构](../../domains/quality/manual/acceptance/python-architecture-and-implementation.md) |
| 哪些内容仍不可信 | [未知与冲突](../../domains/quality/manual/acceptance/open-questions.md) |

## 旅程边界与继续核验

交付任务、行动项、人员权限和统一数据工作台已作为长期主题接入这条路线；它们描述业务边界与目标设计，不证明对应页面、API、SSO 或端到端执行已经部署。需要继续工作时，应从交付任务、人员模型、数据契约和直接源码/Schema 证据分别核验，不能把产品视图或材料中的完成声明当作实现事实。
