已完成真实代码变化 → 既有正式知识候选回写，当前停在 `publish_ready` 待人工审查，未修改正式 `knowledge/`、原始代码或配置。

候选产物：

- [review.md](/home/yyh/project/omni-brain-snapshot-import-writeback-luna-v3/workspaces/knowledge-ingestion/snapshot-import-writeback-luna-v3/review.md)
- 候选知识目录：`workspaces/knowledge-ingestion/snapshot-import-writeback-luna-v3/draft/knowledge/`

本次已确认并融入：

- 同一 `Quality Platform Lab` 从 `35948ae` 演进至 `ea108601...`；
- CSV → 领域对象 → 差异计划 → PostgreSQL 的完整转换与字段所有权；
- 文件 SHA-256、确认令牌、锁、事务、UPSERT、幂等和状态保护；
- CLI、Service、Repository、PGConnector、快照表修改入口；
- 固定 PostgreSQL 首写、重复、脏批、过期确认、状态保护及全量回归结果；
- 既有分析、分配缺口、Ratio 原型和生产未知均保留。

审查通过后，下一步才可批准发布；当前候选可拒绝或回滚。