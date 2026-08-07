# 快照结构冲突的决策结论

**当前不能判断生产快照是哪一种，也不能据此直接修改生产数据库。** “26 个扁平字段”和“18 个字段加 `good_metrics` / `bad_metrics` / `option_metrics` JSONB”是两套尚未裁决的目标结构版本，不是可以自动合并的同义描述。

冲突不止字段数量：当前 Repository 期待 `acceptance_submitted`、`good_passed`、`bad_passed`，较新目标材料使用 `acceptance_completed`、`good_completed`、`bad_completed`；执行状态也出现 `conclusion/is_executed` 与 `exec_status` 两套表示。固定迁移没有创建 `t_qc_daily_snapshot`，所以当前代码只能证明“查询期望什么”，不能证明真实表结构或空库可运行。

**修改前的最小直接证据：**

1. 数据负责人提供当前生产 DDL/迁移、字段字典、血缘与脱敏样例，并以只读查询确认实际列和 JSONB 形状；
2. 原型或系统维护者提供对应的当前源码提交、部署版本和查询链，核对哪套字段正在被消费；
3. 业务负责人只需裁决会影响业务口径的部分，例如 completed/submitted、通过率分母和执行状态语义。

取得这些证据后再形成可回滚迁移、兼容读取和数据验证方案；现在若直接选一套改生产库，既可能破坏现有读取，也无法证明业务口径正确。

依据：[数据对象、数据流与状态](../../../../../../omni-brain-harness-quality-check-v1/knowledge/domains/quality/manual/acceptance/data-flow-and-state.md)、[当前仓库原型](../../../../../../omni-brain-harness-quality-check-v1/knowledge/systems/manual-qc-acceptance-prototype.md)、[当前未知与冲突](../../../../../../omni-brain-harness-quality-check-v1/knowledge/domains/quality/manual/acceptance/open-questions.md)。
