---
type: Source Record
title: 人工质检验收当前原型来源
description: 固定代码版本中的 Python、接口数据结构、数据库迁移脚本和测试，是当前仓库实现的直接来源。
tags: [source, code, prototype]
---

# 人工质检验收当前原型来源

## 来源记录的责任与范围

这是代码来源的追溯页，不是当前原型知识正文。它按**固定版本 → 实际读取范围 → 能证明/不能证明 → 已内化去向**组织，用来检查知识结论有没有超出代码证据。

## 身份与基线

- **仓库**：`/home/yyh/project/ai-knowledge-base`
- **commit**：`3cf393479d59dae57280df3c80a1ff213a936909`
- **K0 输入位置**：`/home/yyh/project/omni-brain-m1-brownfield-input-v1/batch-1/`
- **信息性质**：当前仓库原型，不等于生产部署。

## 实际读取范围

- `src/manual_qc/acceptance/router.py`
- `src/manual_qc/acceptance/sampler.py`
- `src/manual_qc/acceptance/services/assignment_preview_service.py`
- `src/manual_qc/acceptance/services/query_service.py`
- `src/manual_qc/repository.py` 中 `AcceptanceRepository`
- `src/api/schemas/acceptance.py`
- `src/api/deps.py`
- `src/api/app.py`、`src/api/schemas/common.py`
- `src/config/` 与 `config/application.yaml`
- `src/database/postgresql.py`
- `src/database/manager.py`
- `src/frontend/src/features/manual-qc/acceptance/`
- `src/frontend/src/shared/api/`、`data-workbench/` 与 `dashboard/`
- `migrations/20260705_acceptance_vertical_slice.sql`
- `tests/test_acceptance_vertical_slice.py`

## 能证明

- 当前原型声明和实现的接口、数据结构、按比例分配算法、数据库查询、预览保存方式、数据库连接组织、前端任务队列/按日展开/预览交互和局部测试覆盖；
- 代码中不存在的正式执行、验收规则和外部任务状态系统能力不能被视为已实现。

## 不能证明

- 真实数据库兼容性、生产数据口径、外部接口、部署状态和端到端运行；前端源码存在也不证明构建产物已部署；
- 模拟 PostgreSQL 的测试不能证明真实 PostgreSQL 或外部任务状态系统行为。

## 规范知识去向

- [当前仓库原型](../systems/manual-qc-acceptance-prototype.md)：API、前端、Python、持久化和测试边界；
- [Python 软件结构](../domains/quality/manual/acceptance/python-architecture-and-implementation.md)：业务场景、对象协作、代码层级、运行过程和设计评价；
- [采样与分配](../domains/quality/manual/acceptance/sampling-and-assignment.md)：Ratio 算法、选择范围、预览和正式分配缺口；
- [数据库访问公共能力](../capabilities/database-access.md)：连接、事务、依赖组装和领域使用契约。
