# 验收未完成量复合开发认证参考

## 参考状态

- 状态：`certified_review_reference`；
- 产品基线：`35948aebf41b8772b77df18bd68ce9ff2d295344`；
- 参考分支：`reference/manual-qc-pending-visibility-v1`；
- 参考提交：`26db0e1c98657cd120430cec0b92964c888cacd5`；
- 参考工作树：`/home/yyh/project/qpl-pending-ref`；
- 正式知识输入：`omni-brain-harness-quality-check-v1@900cf85`；
- 固定工况：[用例说明](../../../fixtures/real_work/manual_qc_pending_visibility_composite_v1/README.md)。

参考成果由代码、真实 PostgreSQL、HTTP、Edge 用户交互和全量回归共同支持，并已吸收用户对审查顺序、需求表达、方案图示、实现说明和反馈方式的多轮意见。它作为本用例的认证真值比较 Harness 结果；后续弱模型候选由 Agent 对照真值独立评分，不再要求用户逐轮复审候选。

## 用户结果

任务分析表现在直接显示“验收未完成量”。验收负责人可以先按该列降序找到未完成最多的任务，也可设置数字区间，再沿任务 → 日期 → 组 → 标注员定位具体工作量；不再需要逐行用实际分配量减完成量。

本切片不判断未完成量是否构成风险，也不生成阈值、责任人、催办或告警。

## 软件方案

当前 Repository 和指标目录已经公开 `acceptance.pending`，因此本次没有增加或复制业务计算。最小责任链是：

```text
既有 acceptance.pending
    ↓ 加入任务表默认请求
AnalysisRow → TaskAnalysisRow 统一转换
    ↓
任务表数量列
    ├─ 既有排序
    ├─ 既有数字区间筛选
    ├─ 旧列配置兼容
    └─ 既有四级下钻
```

前端新增 `acceptancePending` 类型字段并在统一转换边界读取接口值；表格只负责展示和交互，没有在组件内计算差值。任务表默认指标由 10 个变为 11 个，叠加 5 个固定问题选项后，共享上限从 15 最小调整到 16。Pydantic Schema 和 Service 继续共用 `MAX_ANALYSIS_MEASURES`。

## 固定运行证据

本地 PostgreSQL 16 使用既有 3024 条员工日快照，覆盖 2026-07-13 至 2026-07-26；本轮没有执行 migration、seed、reset 或数据写入。

| 路径 | 对象 | 未完成量 |
|---|---|---:|
| 任务 | 拥堵跟车任务-08 | 1737 |
| 日期 | 2026-07-16 | 144 |
| 组 | 质检组-12 | 51 |
| 员工 | E120 | 20 |

11 个默认指标加 5 个固定问题选项返回 HTTP 200 和 24 个任务；第 17 项返回 HTTP 422。Windows Edge 151 实际证明新列和值可见、首次点击按未完成量降序、范围筛选缩为 1/24 个任务，四级下钻依次得到 1737、144、51、20，控制台无错误。

全量结果为 Python 18 项、Vue 30 项、`vue-tsc` 和生产构建通过；构建保留已有大 chunk 警告。详细证据固定在参考提交的 [`docs/acceptance-pending-visibility-verification.md`](/home/yyh/project/qpl-pending-ref/docs/acceptance-pending-visibility-verification.md)。

## Harness 评测意义

本题刻意选择“服务端能力已存在、消费链缺失”的工况。优秀 Harness 应帮助模型先发现 owner，再只连接必要消费者；如果模型直接在 Vue 中相减、重造接口或宽泛摄入知识，即使页面出现正确数字，也说明组合能力没有通过。

知识路由是否真正被调用、读取范围是否最低充分、当前源码是否裁决精确行为，与最终功能同等重要。模型还必须留下可进入下一阶段知识回写的稳定交接，而不是只说“文档可能需要更新”。

## 知识变化候选

见 [knowledge-change-candidate.md](knowledge-change-candidate.md)。正式知识没有在参考开发阶段被修改。
