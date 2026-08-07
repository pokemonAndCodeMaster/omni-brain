结论：不能确认。现有正式知识反而明确表明，固定 migration 后的空 PostgreSQL 不能被证明跑通任务查询和 Ratio 预览；最直接的已知缺口是查询依赖的快照表没有被迁移创建。

具体缺口：

- 迁移 `20260705_acceptance_vertical_slice.sql` 只创建了：
  - `t_qc_delivery_task`
  - `t_qc_operation_preview`
  - `t_portal_view_config`
- `AcceptanceRepository` 的任务查询、按日展开和 Ratio 预览容量查询同时依赖 `t_qc_daily_snapshot`，但该表未创建。
- 快照相关字段还存在版本差异，例如代码使用的 `acceptance_submitted/completed` 与目标材料中的字段口径不完全一致，无法确认 SQL 投影和行映射兼容。
- Ratio 算法本身是纯 Python 内存计算；但预览流程需要先从快照表读取统计单元，并把结果写入 `t_qc_operation_preview`，因此不能绕过数据库缺口。
- 现有 7 项测试使用 `FakePostgres` 或内存 Repository，没有真实 PostgreSQL、真实 migration、真实 SQL 的执行证据。

现有证据最多能证明：

- 固定提交 `3cf393479d59dae57280df3c80a1ff213a936909` 中存在任务查询、日期展开、Ratio 数量计算、预览保存/读取的代码链路。
- 参数化筛选、分页排序、Ratio 配额计算、预览权限等局部 Python 行为在替身环境下通过测试。
- 不能证明空库初始化成功、真实 SQL 可执行、字段与 Schema 兼容、服务可启动，或前端到真实数据库的端到端路径可用。

真正确认前的最小直接证据是：

1. 在该精确 commit 的干净 clone 上，对全新的 PostgreSQL 执行仓库内全部 migration，并确认成功。
2. 用实际应用配置启动服务，确认真实数据库健康检查和应用启动成功。
3. 对空库调用任务查询，确认返回预期的空分页结果，而不是缺表/缺列错误。
4. 写入一组最小有效的任务与快照 fixture，真实调用日期展开和 `POST /assignment/preview`，确认能从快照读取、计算 Ratio、写入并读取 `t_qc_operation_preview`。
5. 记录真实 HTTP 响应、SQL 错误日志和数据库表/字段结果。

依据：[当前验收原型]( /home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/systems/manual-qc-acceptance-prototype.md)、[数据库访问公共能力]( /home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/capabilities/database-access.md)、[业务到代码地图]( /home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/implementation-map.md)。