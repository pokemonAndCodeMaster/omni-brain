---
type: Concept
title: 验收前后端实现边界
description: 将人工质检验收的当前代码入口、HTTP 契约、数据访问、前端消费和测试证据集中到一页，并明确没有实现的部分。
tags: [manual-quality, acceptance, implementation, api]
---

# 验收前后端实现边界

## 目的与边界

- **解决的问题**：让后续模型能从业务页回到当前代码，而不把设计文档的计划目录误当成仓库现状。
- **包含**：QuerySpec 查询、日期下钻、metadata、AssignmentPreviewService、Ratio sampler、Repository、migration、测试和验证脚本。
- **不包含**：真实 execute、DeltaClient、完整权限系统、生产部署和 source-b 目标四级快照契约。

## 当前 vertical slice

- **结论**：source-a 代码证明了 FastAPI 路由 `POST /api/v1/manual-qc/acceptance/tasks/query`、`GET /tasks/{task_id}/breakdown?dimension=date`、`GET /metadata`、`POST /assignment/preview` 和 `GET /assignment/previews/{preview_id}`；metadata 仅把 date 标为 implemented，其余 group/annotator/scene 展开为未实现。`AssignmentPreviewService` 调用 Repository 查询选择单元并持久化结果，查询 Service 负责分页/计算时间。
- **现实形态**：当前实现。
- **依据**：[ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md#当前实现)
- **适用范围**：当前仓库 commit 的首个验收纵切。
- **冲突/未知**：不能由这些路由推断外部验收执行已存在；source-b 的目录和类名有部分只是计划目标。

## 可回查实现入口

- **结论**：核心实现入口是 `src/api/schemas/acceptance.py`、`src/manual_qc/acceptance/router.py`、`src/manual_qc/acceptance/services/query_service.py`、`src/manual_qc/acceptance/services/assignment_preview_service.py`、`src/manual_qc/acceptance/sampler.py` 和 `src/manual_qc/repository.py`；纵切 migration 为 `20260705_acceptance_vertical_slice.sql`，测试为 `tests/test_acceptance_vertical_slice.py`，端到端验证为 `scripts/verify_acceptance_vertical_slice.sh`。
- **现实形态**：当前实现/代码索引。
- **依据**：[ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md#当前实现)
- **适用范围**：代码阅读、回归验证和后续实现接续。
- **冲突/未知**：来源仓库工作区存在未提交改动；本轮只按 commit 基线和指定文件读取，没有把未跟踪材料纳入结论。

## 结构测试的边界

- **结论**：source-a 测试能证明路由注册、参数化查询形态、类型化响应、Ratio 补足、preview 保存/回读和非法选择失败；验证脚本还能证明一个 PostgreSQL vertical slice 的固定 fixture 断言。它不能证明生产数据正确、外部平台成功或业务阈值正确。
- **现实形态**：当前测试证据。
- **依据**：[ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md#当前实现)
- **适用范围**：评估当前实现证据强度。
- **冲突/未知**：没有本轮执行外部来源仓库测试；来源只读，且没有用户授权修改/运行其外部环境。

## 关联与边界

业务语义从[人工质检验收子域总览](overview.md)开始，数据口径见[data-granularity-and-snapshot](data-granularity-and-snapshot.md)，配额见[sampling-and-preview](sampling-and-preview.md)。

# Citations

1. [ai-knowledge-base 当前代码来源](../../../sources/ai-knowledge-base-qc.md)
