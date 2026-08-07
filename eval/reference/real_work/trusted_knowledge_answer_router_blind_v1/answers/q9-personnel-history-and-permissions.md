# 人员历史与权限

**人员历史：** 目标模型允许同一 `employee_id` 有多行，以 `end_time` 判断当前有效记录。调组时应关闭旧有效行、插入新行并写人员操作日志，目标上在同一事务完成；旧记录保留当时组归属，用来解释历史快照，不能被后续调组覆盖。

**角色与权限：** 标注员、验收员和内部检查员至少要区分；供应商人员不能与验收责任冲突，team leader 只允许作为标注员，一个人员只能属于一个项目，未分组要显式告警。目标权限从 JWT `sub` 取得 `employee_id`，由后端按模块访问级别、角色和数据范围授权，前端只裁剪显示。

**现实边界：** `(employee_id,id)`、`personnel_id`、旧 `(employee_id,join_date)` 等标识尚未由真实 Schema/代码统一；真实 SSO、迁移、PersonnelService、事务上下文、导入一致性和前端旧字段适配都未直接核验。这些是目标边界，不是生产实现事实。

依据：[人员、筛选员与权限边界](../../../../../../omni-brain-harness-quality-check-v1/knowledge/domains/quality/manual/personnel-and-permissions.md)。
