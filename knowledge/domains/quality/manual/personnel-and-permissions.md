---
type: Domain Boundary
title: 人员、筛选员与权限边界
description: 人员 SCD2、角色规则和权限目标；未核验实现保持为候选。
tags: [quality, manual-qc, personnel, permissions]
---

# 人员、筛选员与权限边界

## 人员历史模型

目标设计把旧 `t_personnel` 迁向 `t_data_check_screeners`：业务主键候选为 `(employee_id, id)`，当前记录以 `end_time` 判断，旧记录关闭、新记录插入和操作日志应在同一事务中完成。这样可以按当前人员查询，也能按某日的历史组归属解释旧快照。字段映射和实际迁移是否部署，尚无直接代码/数据库证据。

## 业务约束

- 角色至少区分标注员、验收员和内部检查员；供应商人员不能与验收责任冲突。
- team_leader 只允许作为标注员；一个人员只能属于一个项目；未分组人员必须显式告警。
- 人员标识在材料中出现 `personnel_id`、`employee_id` 和旧 `(employee_id, join_date)` 三种形态。当前不能静默选一个；接口、操作日志和快照必须由真实 Schema/代码统一。

## 权限目标与现实边界

目标是从 JWT `sub` 取得 `employee_id`，由后端按模块访问级别、角色和数据范围授权，前端只做显示裁剪。真实 SSO、PersonnelService、事务上下文、导入一致性算法和前端旧字段适配均未被直接核验；“测试通过”类数字也不能替代这些证据。

# Citations

- [来源记录](../../../sources/index.md)

## 来源

直接材料：`batch-2:quality_check/人工质检-人力管理体系设计.txt`、`batch-2:quality_check/质检平台-API契约与前端交互设计.txt`、`batch-2:quality_check/质检平台-人工质检前端页面与状态设计.txt`。
