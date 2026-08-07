已完成一次真实代码变化回写，候选状态为 `publish_ready`，未发布正式知识。

产物：

- [候选知识目录](</home/yyh/project/omni-brain-knowledge-writeback-luna-v4/workspaces/knowledge-ingestion/qpl-allocation-writeback-20260807/draft/knowledge/index.md>)
- [QPL 系统页](</home/yyh/project/omni-brain-knowledge-writeback-luna-v4/workspaces/knowledge-ingestion/qpl-allocation-writeback-20260807/draft/knowledge/systems/qpl-gap-ref.md>)
- [QPL 软件结构](</home/yyh/project/omni-brain-knowledge-writeback-luna-v4/workspaces/knowledge-ingestion/qpl-allocation-writeback-20260807/draft/knowledge/domains/quality/manual/acceptance/qpl-software-architecture.md>)
- [采样与分配口径](</home/yyh/project/omni-brain-knowledge-writeback-luna-v4/workspaces/knowledge-ingestion/qpl-allocation-writeback-20260807/draft/knowledge/domains/quality/manual/acceptance/sampling-and-assignment.md>)
- [数据流与 JSONB 快照](</home/yyh/project/omni-brain-knowledge-writeback-luna-v4/workspaces/knowledge-ingestion/qpl-allocation-writeback-20260807/draft/knowledge/domains/quality/manual/acceptance/data-flow-and-state.md>)
- [审查说明 review.md](</home/yyh/project/omni-brain-knowledge-writeback-luna-v4/workspaces/knowledge-ingestion/qpl-allocation-writeback-20260807/review.md>)

已确认并写入候选：

- 18 字段快照、Good/Bad 13 字段指标对象及 JSONB 层级；
- `expect_alloc`、`actual_alloc`、达成率、覆盖率和分配缺口；
- 缺口按 Good/Bad、当前聚合粒度分别计算，超额不能跨类别或位置抵消；
- 任务→日期→组→标注员四级任务表；
- 当前源码为 10 个基础指标 + 最多 5 个问题选项；
- Router、Schema、Service、Catalog、Repository、Vue feature、shared workbench 的责任链和修改入口；
- QPL 与早期 Ratio 原型为不同系统。

已保留的未知/冲突：

- 验证报告中的“9+5”与当前源码“10+5”不一致；
- 不证明生产部署、生产 Schema、SSO、外部执行、人工确认、部分失败或状态回查；
- 未新增现场运行，使用固定 commit 自带的真实 PostgreSQL/API/Vue/Edge 验证记录。

结构检查已通过；正式 `knowledge/`、配置、原始代码均未修改。接下来需要人工审查，批准后再决定是否发布。