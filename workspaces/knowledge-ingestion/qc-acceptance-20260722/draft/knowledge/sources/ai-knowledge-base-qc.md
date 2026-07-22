---
type: Source Record
title: ai-knowledge-base：人工质检验收实现与知识材料
description: 带 Git 版本的代码、SQL、测试和人工质检 wiki 混合来源；本轮用于区分当前 vertical slice、旧版流程和综合设计。
tags: [source, manual-quality, acceptance]
---

# ai-knowledge-base：人工质检验收实现与知识材料

## 身份与基线

- **位置**：用户指定的 `ai-knowledge-base` 项目。
- **类型**：代码、SQL、测试、文档、历史/生成综合混合。
- **版本或快照**：Git commit `3cf393479d59dae57280df3c80a1ff213a936909`。
- **所有者**：未在本轮材料中确认。
- **本轮实际读取范围**：根 `index.md`、`implementation_plan.md`、`task.md`、`log.md`；人工质检验收 wiki 与 code 卡；`src/manual_qc/acceptance/`、相关 API schema/router/repository；验收 migration、fixture、单元测试和验证脚本。未读取无关 raw 学习材料。Git 工作区已有 `.gitignore` 修改和未跟踪 `.chunks/code_skeleton.md`、`.claude/`，均未纳入结论。

## 能证明

### 当前实现

- `QuerySpec` 查询、按日期 breakdown、metadata 和 assignment preview 路由在代码中存在。
- `plan_ratio_sampling()` 的容量补足、比例分配、稳定取整和 warning 行为有测试覆盖。
- preview 保存选择、请求、结果摘要、source_version、创建人和 expires_at；回读按 owner/status/过期时间过滤。
- migration、fixture、测试和 shell 验证脚本形成一个首个验收 vertical slice 的可回查链。
- 旧版 wiki 描述了人工验收分配、批量通过/打回、状态刷新/GT 回写等历史流程，但正文自带“上游快照/路径不自动等同当前仓库”的警告。

## 不能证明

- 不能证明生产 Delta/DMP 已成功执行、当前外部 API 契约或实际部署状态。
- 不能证明旧版阈值、状态码和路径仍是正式规则。
- 不能证明未提交工作区材料已通过测试或属于当前版本。

## 权威与时效

- **现实形态**：代码/SQL/测试优先视为当前实现；旧 wiki 视为历史快照或生成综合；实现计划视为目标/计划。
- **时间边界**：commit 基线及文件内 2026-06 至 2026-07 记录；没有本轮之后的运行快照。
- **与其他来源的冲突**：与 `quality_check` 的目标快照、Repository、execute 状态机和旧版阈值存在差异；冲突保留在候选页和开放问题中。

### 旧版人工质检流程

旧版 wiki 描述的验收分配、批量通过/打回和状态刷新只作为历史快照引用，不代表当前代码实现。

## 定位

- 当前查询/preview：`src/manual_qc/acceptance/`、`src/api/schemas/acceptance.py`、`src/manual_qc/repository.py`。
- 当前迁移：`migrations/20260705_acceptance_vertical_slice.sql`。
- 当前验证：`tests/test_acceptance_vertical_slice.py`、`scripts/verify_acceptance_vertical_slice.sh`。
- 旧版人工质检：`wiki/quality_portal/人工质检-⑧验收分配.md`、`人工质检-⑨批量通过打回.md`、`人工质检-⑩状态刷新与GT回写.md`、`人工质检-交付任务与行动项机制.md`。
