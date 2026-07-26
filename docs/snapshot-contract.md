# 验收快照契约

## 版本依据

本地表对齐原始资料《质检平台-综合快照表设计》中 **V20260709_01 JSONB 重构更新**。该更新明确声明旧 26/28 字段说明已经过时，当前为 18 个顶层字段。

## 粒度

一行表示：

```text
stat_date × scene_name × group_name × employee_id
```

场景和组聚合由查询生成，不向同表写入 NULL 维度汇总行。

唯一键为：

```text
(stat_date, scene_name, group_name, employee_id)
```

## 顶层字段

| # | 字段 | 类型 | 用途 |
|---:|---|---|---|
| 1 | `id` | bigint | 本地实验表自增主键 |
| 2 | `stat_date` | date | 统计日期 |
| 3 | `scene_name` | varchar(256) | 场景/任务组 |
| 4 | `group_name` | varchar(128) | 当日组别快照 |
| 5 | `employee_id` | varchar(64) | 标注员工号 |
| 6 | `project_name` | varchar(64) | 项目名 |
| 7 | `annotation_total` | integer | 标注总量 |
| 8 | `annotation_submitted` | integer | 已提交标注量 |
| 9 | `good_metrics` | jsonb | Good 维度的标注、验收、结论与执行状态 |
| 10 | `bad_metrics` | jsonb | Bad 维度的标注、验收、结论与执行状态 |
| 11 | `option_metrics` | jsonb | 问题标签 → 选项 → 同构指标对象 |
| 12 | `confirmed_by` | varchar(64) | 确认人 |
| 13 | `confirmed_at` | timestamptz | 确认时间 |
| 14 | `executed_by` | varchar(64) | 执行人 |
| 15 | `executed_at` | timestamptz | 执行时间 |
| 16 | `execution_note` | text | 执行备注 |
| 17 | `computed_at` | timestamptz | 指标计算时间 |
| 18 | `updated_at` | timestamptz | 行更新时间 |

`option_metrics` 必须保留实际业务中的问题标签层级：

```json
{
  "驾驶行为分类": {
    "CUT_IN": {
      "annotation_total": 12,
      "annotation_submitted": 12
    }
  }
}
```

`good_metrics`、`bad_metrics` 以及
`option_metrics.<question_label>.<option_name>` 的叶子节点使用同一结构：

```json
{
  "annotation_total": 0,
  "annotation_submitted": 0,
  "expect_alloc": 0,
  "actual_alloc": 0,
  "actual_complete": 0,
  "correct": 0,
  "incorrect": 0,
  "conclusion": null,
  "expect_pass": 0,
  "expect_reject": 0,
  "actual_pass": 0,
  "actual_reject": 0,
  "exec_status": null
}
```

原始资料把这一组描述为“12 计数键 + exec_status”，但其显式字段清单实际包含 **11 个数值键、`conclusion` 和 `exec_status`**；本地 Pydantic 与 TypeScript 契约按显式字段清单实现。

关于 `option_metrics` 的两份来源存在一层与两层结构冲突；2026-07-26 经业务方
明确确认，实际业务必须保留“问题标签”层，故当前契约采用两层 key。旧数据迁移
无法判断标签时统一进入 `待确认问题标签`，避免由代码虚构业务含义。
数据库约束会拒绝把指标对象直接放在 `option_metrics.<option_name>` 的旧式平层写法。

## 计数不变量

- 所有计数非负；
- `annotation_submitted <= annotation_total`；
- Good/Bad/选项内部计数非负；
- `actual_complete <= actual_alloc`；
- `correct + incorrect <= actual_complete`；
- 实际通过、打回量不得超过相应可执行范围。

## API

| 路径 | 返回粒度 |
|---|---|
| `GET /api/snapshots/rows` | 最小快照行 |
| `GET /api/snapshots/aggregate/scene` | 日期 × 场景 |
| `GET /api/snapshots/aggregate/group` | 日期 × 场景 × 组 |
| `GET /api/snapshots/aggregate/employee` | 日期 × 场景 × 组 × 员工 |

所有响应包含 `schema_version: "snapshot-jsonb-v20260709"`、`items`、`total` 和最新 `computed_at`。

## 更新边界

快照重算可以更新统计计数、`option_metrics` 和 `computed_at`；不得覆盖 `exec_status`、人工结论、确认人、执行记录和执行时间。
