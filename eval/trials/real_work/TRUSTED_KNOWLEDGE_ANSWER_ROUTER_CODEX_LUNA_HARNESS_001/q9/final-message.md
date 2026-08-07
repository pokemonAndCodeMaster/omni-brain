结论：现有知识建议采用“人员主表 SCD Type 2 + 历史操作日志 + 快照保留当时归属”的模型，但这仍是目标设计，不能直接视为生产实现。

- 当前有效记录：`t_data_check_screeners` 中同一 `employee_id` 可有多行；复合主键为 `(employee_id, id)`，以 `end_time IS NULL` 表示当前有效记录。
- 调组：在同一事务内关闭旧有效记录、插入新组归属记录，并写入 `t_personnel_op_log`。不要更新旧记录的组字段，否则历史快照无法解释。
- 历史统计：快照最小维度包含 `(stat_date, scene_name, group_name, employee_id)`；其中 `group_name` 表示统计时的历史归属，员工之后调组不能回写旧快照。
- 审计：日志至少应记录人员变更及操作上下文；关闭旧记录、插入新记录、写操作日志应原子完成，避免人员状态与审计记录不一致。

角色/权限边界：

- 至少区分标注员、验收员、内部检查员；供应商人员不得承担冲突的验收责任。
- `team_leader` 只能作为标注员。
- 一个人只能属于一个项目；未分组人员必须显式告警。
- 权限由后端依据 JWT `sub` 得到的 `employee_id`，结合模块访问级别、角色和数据范围判断；前端只能做显示裁剪，不能承担真实授权。

仍不能当作生产事实：

- `t_personnel` 到 `t_data_check_screeners` 是否已部署；
- 实际 Schema、唯一当前记录约束、事务实现和 `t_personnel_op_log` 是否存在并生效；
- `personnel_id`、`employee_id`、旧 `(employee_id, join_date)` 三种标识的最终统一口径；
- 真实 SSO、PersonnelService、导入一致性算法和前端旧字段适配；
- 文档或测试中的“已落地”描述、QA 数字，以及存在冲突的快照字段版本，均不能替代源码、Schema 或运行证据。

具体依据：

- [人工质检验收数据对象、数据流与状态](/home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/data-flow-and-state.md)
- [人员、筛选员与权限边界](/home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/personnel-and-permissions.md)

因此，当前可确认的是“推荐的数据与权限边界”；生产是否实现，仍需直接核验迁移、Schema、代码和运行结果。