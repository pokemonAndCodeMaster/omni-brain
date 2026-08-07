# 本地快照 CSV 导入知识回写参考

## 参考身份

- 候选仓库：`/home/yyh/project/omni-brain-snapshot-import-writeback-ref`；
- 分支：`reference/m4-snapshot-import-writeback-v1`；
- 父知识：`c625f40`；
- 参考提交：`b798af8`；
- 固定代码来源：`/home/yyh/project/qpl-evolution-import-v1@ea10860103a9d282dd05da3639f50f00cf45b882`；
- 固定问题：[`content-questions.yaml`](../../../fixtures/real_work/code_to_knowledge_writeback_snapshot_import_v1/content-questions.yaml)。

该参考是在问题清单冻结后，根据固定父知识、源码和来源内真实验证形成的专家候选。它用于比较 Harness Trial，不自动成为用户正式知识。

## 结果结构

参考没有为同一系统新建第二个来源或系统身份。它原位更新现有 QPL 来源、系统、数据、系统架构、实现地图、数据库公共能力、根入口和两种产品视图，并新增一篇长期归属明确的软件结构页：

- `knowledge/domains/quality/manual/acceptance/snapshot-import-architecture-and-implementation.md`。

新页从用户动作出发，完整说明 CSV 11 列、四字段自然键、七个来源字段、指标校验、字符串行到写入参数的转换、人工状态合并、确认令牌、事务锁、参数化 UPSERT、幂等、真实 PostgreSQL 结果和设计失效条件。既有分析纵切、分配缺口、Ratio 原型、历史和生产未知继续可达。

## 内容自审

| 题组 | 结果 | 主要落点 |
|---|---:|---|
| C01—C16 代码与运行内容 | 16/16 | 新软件结构页、QPL 来源页、系统页 |
| I01—I04 增量融合 | 4/4 | 原位修改 17 页、新增 1 页；根入口、领域视图、学习旅程同步 |
| S01—S04 安全与结构 | 4/4 | 独立 worktree；来源与正式知识未改；生产边界保留；知识检查通过 |
| **合计** | **24/24** | 所有关键题可由规范知识本身回答 |

结构验证：

- `python scripts/knowledge_check.py`：通过，37 个 Markdown、28 个概念，链接、frontmatter 和产品视图可达；
- `git diff --check`：通过；
- 参考仓库的通用 Harness 单测有 91/95 通过；4 项失败是集成版已经包含领域知识且 manifest 为 M4，而这些测试专门断言空 M1 发布包。空 RC1 `a5104ec` 的 95 项回归已经独立通过，因此不通过修改测试来掩盖角色差异。

## 参考边界

- 固定日期锚定只是让动态种子可重放，不是产品能力；
- 当前入口只适合本地低频小批量，不是生产 ETL、上传页面或批次平台；
- CSV 是完整来源结构，不承诺保留文件中缺失的问题选项；
- 固定 PostgreSQL 结果不外推生产权限、负载、并发或部署；
- 参考答案也允许被后续 Trial、运行证据和用户审查纠正。
