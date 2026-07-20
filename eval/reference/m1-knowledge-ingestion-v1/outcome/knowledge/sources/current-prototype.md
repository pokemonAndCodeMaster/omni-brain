---
type: Source Record
title: 人工质检验收当前原型来源
description: 固定代码版本中的 Python、接口数据结构、数据库迁移脚本和测试，是当前仓库实现的直接来源。
tags: [source, code, prototype]
---

# 人工质检验收当前原型来源

## 身份与基线

- **仓库**：`/home/yyh/project/ai-knowledge-base`
- **commit**：`3cf393479d59dae57280df3c80a1ff213a936909`
- **信息性质**：当前仓库原型，不等于生产部署。

## 实际读取范围

- `src/manual_qc/acceptance/router.py`
- `src/manual_qc/acceptance/sampler.py`
- `src/manual_qc/acceptance/services/assignment_preview_service.py`
- `src/manual_qc/acceptance/services/query_service.py`
- `src/manual_qc/repository.py` 中 `AcceptanceRepository`
- `src/api/schemas/acceptance.py`
- `src/api/deps.py`
- `src/database/postgresql.py`
- `src/database/manager.py`
- `migrations/20260705_acceptance_vertical_slice.sql`
- `tests/test_acceptance_vertical_slice.py`

## 能证明

- 当前原型声明和实现的接口、数据结构、按比例分配算法、数据库查询、预览保存方式、数据库连接组织和局部测试覆盖；
- 代码中不存在的正式执行、验收规则和外部任务状态系统能力不能被视为已实现。

## 不能证明

- 真实数据库兼容性、生产数据口径、外部接口、部署状态和端到端运行；
- 模拟 PostgreSQL 的测试不能证明真实 PostgreSQL 或外部任务状态系统行为。
