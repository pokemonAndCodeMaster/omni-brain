---
type: System Implementation
title: 人工质检验收当前仓库原型
description: 记录固定提交中实际存在的 API、Python 结构、数据库访问、Ratio 预览、迁移和测试边界。
tags: [manual-qc, acceptance, prototype, code]
---

# 人工质检验收当前仓库原型

## 先看结论

固定提交 `3cf393479d59dae57280df3c80a1ff213a936909` 实现了一条局部纵向链路：查询验收任务、按日期展开、计算 Ratio 分配数量并保存/读取预览。它没有真正分配 task、形成结论、通过/打回、调用外部任务系统或跟踪返工，也没有证据表明已部署。

## 当前能力边界

```mermaid
flowchart LR
    Q[任务查询\n已实现] --> B[按日期展开\n已实现]
    B --> P[Ratio 数量预览\n已实现]
    P -.未实现.-> I[固定具体 task_ids]
    I -.未实现.-> A[正式分配]
    A -.未实现.-> C[验收结论]
    C -.未实现.-> E[通过/打回]
    E -.未实现.-> V[状态回查与返工]
```

## API 入口

| 方法与路径 | 当前行为 |
|---|---|
| `POST /api/v1/manual-qc/acceptance/tasks/query` | 按 name、topic、priority、status 过滤，分页和排序 |
| `GET /tasks/{task_id}/breakdown?dimension=date` | 按天聚合；其他维度返回未实现 |
| `GET /metadata` | 声明 date 已实现，group/annotator/scene 未实现，采样只有 ratio |
| `POST /assignment/preview` | 解析选择、查询统计单元、计算数量并保存预览 |
| `GET /assignment/previews/{preview_id}` | 仅创建人可读取 READY 且未过期的预览 |

## Python 代码结构

| 文件 | 当前实际职责 |
|---|---|
| `src/manual_qc/acceptance/router.py` | FastAPI 路由、操作者请求头和错误映射 |
| `src/api/schemas/acceptance.py` | 查询、选择、Ratio 规则、任务行和预览 Pydantic 结构 |
| `src/manual_qc/acceptance/services/query_service.py` | 查询与按天展开编排 |
| `src/manual_qc/acceptance/services/assignment_preview_service.py` | 选择解析、算法调用、预览组装和保存 |
| `src/manual_qc/acceptance/sampler.py` | `SamplingBucket`、`SamplingPlan` 与 Ratio 纯算法 |
| `src/manual_qc/repository.py` | 队列、日期、统计单元和预览 SQL |
| `src/api/deps.py` | 从公共数据库能力组装 Repository 和 Service |
| `src/database/*.py` | 命名连接、懒加载池、事务和查询封装 |

完整业务到代码走读见[Python 软件结构与实现](../domains/quality/manual/acceptance/python-architecture-and-implementation.md)。

## 当前预览保存什么

`t_qc_operation_preview` 保存：

- `preview_id`、操作类型、创建人、状态和有效期；
- 选择描述与原始请求 JSON；
- 预览响应 JSON；
- 基于统计单元 ID、available 和 computed_at 生成的 `source_version`；
- executed_at 预留字段。

默认有效期为 30 分钟。当前结果包含每个日期桶的可用量和 Good/Bad 计划，但没有具体 task_ids。因此“预览已保存”不能解释为“执行集合已冻结”。

## 数据库迁移与查询缺口

迁移 `20260705_acceptance_vertical_slice.sql` 创建：

- `t_qc_delivery_task`；
- `t_qc_operation_preview`；
- `t_portal_view_config`。

Repository 查询依赖 `t_qc_daily_snapshot`，该迁移没有创建此表。代码和目标材料对 `acceptance_submitted/completed` 等字段也存在版本差异。因此当前提交不能证明空库初始化后端到端查询可运行。

## 测试能证明什么

7 项聚焦测试覆盖：

- 参数化筛选、分页和排序参数；
- Service 返回带时区计算时间的类型化页面；
- 五个路由已注册；
- Router 的统一响应；
- Ratio 类别不足补足和总量守恒；
- 预览保存创建人和结果；
- 非法选择 ID 被拒绝。

这些测试使用 `FakePostgres` 或小型内存 Repository。它们可以证明局部 Python 行为，不证明真实 PostgreSQL SQL、生产字段、外部任务状态或完整用户路径。

## 设计观察

当前代码用薄 Router、用例 Service、纯算法和 Repository 建立了清楚的短链路，适合当前原型规模。真正的限制是能力尚浅，而不是缺少更多设计模式：新增策略仍需修改 Schema、Service、metadata 和查询；Service 直接依赖 API Schema；Repository 继续扩张后才可能需要按职责拆分。具体判断见[Python 软件结构与实现](../domains/quality/manual/acceptance/python-architecture-and-implementation.md)。

# Citations

1. [当前验收原型来源](../sources/current-prototype.md)
