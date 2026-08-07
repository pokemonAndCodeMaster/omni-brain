已完成隔离回写候选，Harness 全局审查通过（`publish_ready`）。

候选覆盖：

- 验收未完成量与分配缺口的业务区别；
- 后端指标 → API → Vue 任务表消费链与修改入口；
- 11 个基础指标、16 项查询上限及旧列配置兼容；
- 固定验证结果与不可外推的生产边界；
- 根入口和验收学习路线导航。

审查文件：[review.md](/home/yyh/project/omni-brain-pending-writeback-luna-v5/workspaces/knowledge-ingestion/qc-acceptance-pending-writeback-26db0e1/review.md)

候选目录：[draft/knowledge](/home/yyh/project/omni-brain-pending-writeback-luna-v5/workspaces/knowledge-ingestion/qc-acceptance-pending-writeback-26db0e1/draft/knowledge)

正式 `knowledge/`、`config/` 未修改，也未读取 `eval/reference/` 或历史 Trial。请审查后决定批准发布或退回。