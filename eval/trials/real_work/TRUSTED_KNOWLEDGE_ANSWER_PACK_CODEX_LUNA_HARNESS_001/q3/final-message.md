结论：现在不能据此修改生产数据库。当前知识不能确认生产快照属于“26 个扁平字段”还是“18 个字段 + 三个 JSONB”，甚至不能确认 `t_qc_daily_snapshot` 已在生产部署。

冲突具体是：

- 一套材料描述约 26 个扁平字段；
- 另一套目标材料描述约 18 个字段，并将 `good_metrics`、`bad_metrics`、`option_metrics` 放入 JSONB；
- 同时还有字段命名冲突，例如 `acceptance_submitted` 与 `acceptance_completed`、`good_passed` 与 `good_completed`，以及 `conclusion/is_executed` 与 `exec_status`；
- 固定迁移只创建交付任务、预览和视图配置，没有创建快照表；Repository 却会查询 `t_qc_daily_snapshot`。

因此现有知识只能确认：

- 快照是供页面、采样和规则使用的派生读模型，不是可直接替代原始 task 状态的事实源；
- 当前原型代码期望某些扁平字段；
- 目标设计存在另一种 JSONB 结构；
- 两者属于未裁决的版本冲突；
- 当前生产 Schema、部署版本、刷新任务和真实数据均未被直接验证。

不能确认：

- 生产表实际采用哪套字段；
- 两套结构是否分别对应不同环境、迁移版本或历史/目标方案；
- JSONB 内部键名、类型、非空约束和兼容规则；
- 当前部署代码是否与生产表结构匹配。

在决定修改前，最少需要取得以下直接证据：

1. 数据负责人提供生产库只读 DDL 或 `information_schema` 结果，包括表、列、类型、约束和当前 Schema/迁移版本。
2. 原型维护者提供生产实际部署的代码提交/镜像版本，并确认 Repository 查询与该 Schema 的对应关系。
3. 数据负责人提供快照刷新任务的来源、SQL/代码、最近刷新时间和一条脱敏样例记录，确认 JSONB 键与扁平字段的真实语义。
4. 验收业务负责人确认字段映射和业务口径，尤其是 `submitted`/`completed`、Good/Bad 指标及执行状态字段。
5. DBA 或发布负责人完成只读兼容检查、备份/回滚方案和变更审批。

责任边界是：数据负责人确认“生产实际结构和刷新血缘”；原型维护者确认“部署代码契约”；验收业务负责人裁决“字段业务含义”；DBA/发布负责人负责“是否执行及如何安全变更”。

依据：[数据对象与数据流](../knowledge/domains/quality/manual/acceptance/data-flow-and-state.md)、[当前未知与冲突](../knowledge/domains/quality/manual/acceptance/open-questions.md)、[业务到代码地图](../knowledge/domains/quality/manual/acceptance/implementation-map.md)。