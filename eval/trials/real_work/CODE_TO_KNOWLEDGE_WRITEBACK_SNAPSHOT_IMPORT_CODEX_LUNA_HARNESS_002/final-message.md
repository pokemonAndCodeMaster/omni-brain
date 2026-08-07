已完成一次真实“代码变化 → 既有正式知识候选更新”，并停在待人工审查状态。

候选工作区：

- [review.md](/home/yyh/project/omni-brain-snapshot-import-writeback-luna-v2/workspaces/knowledge-ingestion/qpl-snapshot-csv-writeback-20260807/review.md)
- [候选知识目录](/home/yyh/project/omni-brain-snapshot-import-writeback-luna-v2/workspaces/knowledge-ingestion/qpl-snapshot-csv-writeback-20260807/draft/knowledge/)
- [候选状态](/home/yyh/project/omni-brain-snapshot-import-writeback-luna-v2/workspaces/knowledge-ingestion/qpl-snapshot-csv-writeback-20260807/.state/case.json)

结果：

- 固定 commit `ea108601...` 已确认是 `Quality Platform Lab` 同系统顺序演进，不属于 Ratio 原型。
- 已回写 CSV 契约、领域对象、差异计划、确认令牌、状态保护、锁、事务、UPSERT、幂等和 CLI 到 PostgreSQL 的完整调用链。
- 已内化固定 PostgreSQL 证据：首写、重复导入、脏批、过期令牌、人工状态保护及 26/30 项回归结果。
- 已同步领域入口、验收学习旅程、来源记录、系统页、未知页和变更日志。
- 已通过 4 个知识单元检查和全局 review，状态为 `publish_ready`。
- 原始代码、正式 `knowledge/` 和正式配置均未修改；当前仅新增隔离候选工作区。

仍明确保留为未知：生产数据库/上传、跨会话审批、批次审计、生产并发、对象存储、外部任务执行，以及问题选项缺失时的业务承诺。

请审查候选和 `review.md`；批准后再执行发布。