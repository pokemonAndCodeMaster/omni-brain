# 验收未完成量增量知识回写用例

## 用户结果

一项真实跨层开发已经完成：人工质检任务分析表能够直接查看“验收未完成量”。本用例检验 Harness 能否把这项变化**有机更新进既有候选知识**，使业务读者理解指标，开发者能定位实现与修改入口，同时保留父知识、生产未知和证据边界。

这不是从零整理 Quality Platform Lab，也不是为本次提交写一篇开发周报。

## 固定输入

| 输入 | 固定身份 |
|---|---|
| 父知识候选 | `omni-brain-knowledge-writeback-ref@28b0951be7c49f00439365113d3d0b1c90dbdf44` |
| 当前 Harness | `omni-brain-harness@4edf0a20fded0a2ccc1a070213b69f7cda610dcd` |
| 代码来源 | `/home/yyh/project/qpl-pending-ref@26db0e1c98657cd120430cec0b92964c888cacd5` |
| 实现父版本 | `35948aebf41b8772b77df18bd68ce9ff2d295344` |
| 固定验证报告 | 代码来源中的 `docs/acceptance-pending-visibility-verification.md` |

候选不能读取本用例的 `eval/reference/`、历史 Trial 或专家参考工作树。正式发布知识仓 `/home/yyh/project/omni-brain-harness-quality-check-v1` 保持只读。

## 变化的关键性质

- 这是**同一系统的新版本**，不是新系统；
- `acceptance.pending` 的后端目录和 Repository 公式在父版本已经存在；
- 本次开发主要贯通前端请求、类型、映射和任务表消费，同时将最大指标组合从 15 调整为 16；
- 指标用于定位“已分但未完成”的工作，不应擅自定义成风险或异常阈值；
- 父知识中的分配缺口、早期 Ratio 原型、目标设计和生产未知继续成立。

## 用户最终应看到

- 位于隔离摄入案中的候选规范知识和产品视图；
- 原位更新的系统、来源、业务/数据、软件实现、公共能力和导航；
- 一份可审查的 `review.md`，明确修改、保持、证据和待确认内容；
- 未经人工批准，不修改正式知识或来源代码。

## 验证方式

1. 从候选根入口找到当前实验系统与验收未完成量；
2. 从业务含义下钻到公式、聚合顺序、后端既有能力和前端消费链；
3. 追溯固定 commit、验证范围、四级真实值和不能外推的边界；
4. 对照 [`content-questions.yaml`](content-questions.yaml) 评估 24 项内容与融合问题；
5. 检查父知识差异、链接、索引、日志和候选隔离状态。
