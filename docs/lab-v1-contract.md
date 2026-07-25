# `lab-v1` 快照契约

## 粒度

一行表示：

```text
stat_date × scene_name × group_name × employee_id
```

场景和组聚合由查询生成，不向同表写入 NULL 维度汇总行。

## 计数不变量

- 所有计数非负；
- `annotation_submitted <= annotation_total`；
- Good/Bad 标注提交之和不超过总提交；
- 验收完成不超过分配；
- 验收通过与打回分别不超过完成；
- Good/Bad 各级计数不超过相应总计数。

## API

| 路径 | 返回粒度 |
|---|---|
| `GET /api/snapshots/rows` | 最小快照行 |
| `GET /api/snapshots/aggregate/scene` | 日期 × 场景 |
| `GET /api/snapshots/aggregate/group` | 日期 × 场景 × 组 |
| `GET /api/snapshots/aggregate/employee` | 日期 × 场景 × 组 × 员工 |

所有响应包含 `schema_version: "lab-v1"`、`items`、`total` 和最新 `computed_at`。

## 更新边界

快照重算可以更新统计计数、`option_metrics`、`source_version` 和 `computed_at`；不得覆盖人工结论、确认人、执行记录和执行时间。
