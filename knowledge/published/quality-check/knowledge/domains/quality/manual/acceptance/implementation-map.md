---
type: Traceability Map
title: 人工质检验收业务到组件、代码与证据地图
description: 将验收业务步骤映射到产品动作、目标组件、固定代码、数据对象和证据状态。
tags: [manual-qc, acceptance, traceability, implementation]
---

# 人工质检验收业务到组件、代码与证据地图

## 本页导航

- [实现地图概览](#实现地图概览)
- [全链路追溯表](#全链路追溯表)
- [当前代码入口](#当前代码入口)
- [数据表与代码的不一致](#数据表与代码的不一致)
- [下钻路径](#下钻路径)

## 实现地图概览

**当前实现范围：** 当前代码只贯通任务查询、按天展开和 Ratio 数量预览。后续的具体样本选择、正式分配、结论、通过/打回和状态回查都只有历史做法或目标设计，不能因为出现了组件名称就视为已经实现。

**相关知识边界：** 交付任务与行动项、人员权限和统一数据工作台已有业务及目标设计知识；这些内容不等于验收页面、API、SSO、Schema 或端到端生产实现已经存在。

**本页用途：** 下面的追溯表把每个业务步骤与用户结果、目标责任、当前代码、数据对象和证据状态放在同一行核对。它用于快速定位实现和证据，不替代生命周期、算法或软件设计正文。

## 全链路追溯表

**追溯方法：** 只有“当前代码与接口”能够定位且“证据判断”支持当前状态时，才能把能力称为原型实现。

| 业务步骤 | 用户可见结果 | 目标软件责任 | 固定代码与接口 | 数据对象 | 证据判断 |
|---|---|---|---|---|---|
| 查看待验收任务 | 任务队列、筛选、分页和汇总 | Router → QueryService → Repository | `POST /tasks/query`；`router.py`、`query_service.py`、`repository.py` | `t_qc_delivery_task` + 快照聚合 | 当前代码已实现；真实数据库未验证 |
| 按日期下钻 | 每天标注和验收计数 | QueryService → Repository | `GET /tasks/{id}/breakdown?dimension=date` | `t_qc_daily_snapshot` | 当前代码已实现日期；其他维度未实现 |
| 选择采样范围 | 任务/日期或筛选全选 | Selection Schema + PreviewService | `SelectionSpec`、`_resolve_selection` | task_ids/date_keys/filter_snapshot | 当前代码已实现 task/date 解析 |
| 计算 Ratio 配额 | 总目标、Good/Bad、每桶数量、缺口 | 纯采样算法 | `SamplingBucket`、`SamplingPlan`、`plan_ratio_sampling` | 内存 dataclass | 当前代码和测试可证明 |
| 保存并读取预览 | preview_id、结果、有效期和创建人边界 | PreviewService → Repository | `POST /assignment/preview`、`GET /assignment/previews/{id}` | `t_qc_operation_preview` | 当前代码已实现；只冻结数量与统计单元 |
| 选择具体样本 | 可执行 task_ids | 目标 Repository/AssignmentService | 无 | 外部 task/clip | 未实现；具体排序未知 |
| 正式分配验收 | 成功/跳过/失败/待回查 | 目标 AssignmentService + DeltaClient | 无 execute API 或 client | 外部任务状态、实际 allocated | 未实现 |
| 形成结论 | PASS/REJECT/PENDING 与依据 | 目标 PassRule + ExecutionService | 无 `pass_rules.py` | 当前指标、规则、范围 | 历史规则与目标设计；当前未实现 |
| 通过或打回 | 对范围内标注全集执行 | 目标 ExecutionService + DeltaClient | 无 | task_ids、即时结果 | 历史脚本存在；当前未实现 |
| 状态回查 | 实际成功量和最终状态 | 目标客户端/调度/统计刷新 | 无 | 外部状态、快照新鲜度 | 历史与目标；当前未实现 |

目标组件名称、历史脚本或前端标签均不能单独证明能力存在。

## 当前代码入口

**入口范围：** 下列路径只覆盖查询、按日展开和 Ratio 数量预览这条纵向链路。

```text
src/manual_qc/acceptance/router.py
  HTTP 路由、错误映射、请求头操作者

src/api/schemas/acceptance.py
  查询、选择、Ratio 参数、预览和任务行 Pydantic 结构

src/manual_qc/acceptance/services/query_service.py
  队列与按天展开的应用编排

src/manual_qc/acceptance/services/assignment_preview_service.py
  选择解析、配额调用、响应组装和预览保存

src/manual_qc/acceptance/sampler.py
  Ratio 纯算法

src/manual_qc/repository.py
  交付任务、快照统计单元和预览 SQL

src/database/manager.py + postgresql.py
  数据库公共能力
```

## 数据表与代码的不一致

**核心冲突：** Repository 依赖的快照表没有出现在同一迁移中，目标材料还存在多套字段版本，因此代码存在不等于数据库可以直接运行。

- 当前迁移 `20260705_acceptance_vertical_slice.sql` 创建 `t_qc_delivery_task`、`t_qc_operation_preview` 和 `t_portal_view_config`；
- Repository 同时查询 `t_qc_daily_snapshot`，但该迁移没有创建此表；
- 目标材料还提供了多个快照 Schema 版本，字段命名与固定代码不完全一致。

因此，现有代码可以证明结构和局部行为，不能证明系统可以从空库运行，也不能证明生产字段已经冻结。

## 下钻路径

- 想理解业务，先读[生命周期](lifecycle.md)；现有知识已覆盖交付任务、行动项、人员权限和统一数据工作台的业务与目标设计边界，但仍不足以证明完整产品工作台已经实现。
- 想理解代码，读[Python 软件结构与实现](python-architecture-and-implementation.md)并沿上面实际路径下钻。
- 想确认某个能力是否存在，先看“固定代码与接口”和“证据判断”，不要从目标组件名称推断。
- 需要真实生产行为时，进入[当前未知与冲突](open-questions.md)查看补知责任。

# Citations

1. [当前验收原型](../../../../sources/current-prototype.md)
2. [目标验收平台设计](../../../../sources/target-design.md)
3. [历史验收运行快照](../../../../sources/historical-pipeline.md)
