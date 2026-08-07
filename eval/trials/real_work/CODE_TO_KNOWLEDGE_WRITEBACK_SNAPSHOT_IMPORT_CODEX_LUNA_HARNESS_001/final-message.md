已完成一次真实“代码变化 → 既有正式知识候选更新”，当前停在待人工审查，未发布。

候选工作区：

- [review.md](/home/yyh/project/omni-brain-snapshot-import-writeback-luna-v1/workspaces/knowledge-ingestion/qpl-snapshot-csv-writeback-20260807/review.md)
- [候选知识目录](/home/yyh/project/omni-brain-snapshot-import-writeback-luna-v1/workspaces/knowledge-ingestion/qpl-snapshot-csv-writeback-20260807/draft/knowledge)

已纳入：

- CSV → 领域对象 → 当前行 → 差异计划 → 确认令牌 → PostgreSQL 事务 UPSERT 的完整链路；
- 来源字段、人工确认/执行状态保护及问题选项缺失边界；
- CLI、Service、Repository、数据库公共能力、快照表和修改入口；
- 首写、重复导入、脏批、过期确认、状态保护等固定报告结果；
- 领域入口、学习旅程、来源/系统导航和未知问题。

审查状态：`publish_ready`，4 个读者问题与结构检查均通过。固定报告正文标注的实现 commit 与冻结 commit 不一致，已明确保留为待人工复核，不作无条件事实。

正式 `knowledge/`、`config/` 和原始代码均保持不变。