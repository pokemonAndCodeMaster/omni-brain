from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


SOURCE_ID = "manual_qc.snapshot.v20260709"


@dataclass(frozen=True)
class DimensionDefinition:
    id: str
    label: str
    value_type: Literal["date", "text"]
    filter_operators: tuple[str, ...]
    groupable: bool = True
    sortable: bool = True


@dataclass(frozen=True)
class MetricDefinition:
    id: str
    label: str
    unit: Literal["count", "percent"]
    description: str
    filter_operators: tuple[str, ...]
    sortable: bool = True
    requires_question_option: bool = False


DIMENSIONS: tuple[DimensionDefinition, ...] = (
    DimensionDefinition("date", "日期", "date", ("equals", "between")),
    DimensionDefinition("project", "项目", "text", ("equals", "in", "contains")),
    DimensionDefinition("task", "标注任务", "text", ("equals", "in", "contains")),
    DimensionDefinition("group", "组", "text", ("equals", "in", "contains")),
    DimensionDefinition("employee", "标注员", "text", ("equals", "in", "contains")),
)


METRICS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        "annotation.total",
        "标注总量",
        "count",
        "选定范围内 annotation_total 的合计。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "annotation.submitted",
        "标注提交量",
        "count",
        "选定范围内 annotation_submitted 的合计。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "annotation.good_submitted",
        "Good 提交量",
        "count",
        "Good 指标对象中 annotation_submitted 的合计。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "annotation.bad_submitted",
        "Bad 提交量",
        "count",
        "Bad 指标对象中 annotation_submitted 的合计。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "annotation.good_rate",
        "Good 占比",
        "percent",
        "Good 提交量 ÷ 标注提交量；分母为零时为空。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "annotation.bad_rate",
        "Bad 占比",
        "percent",
        "Bad 提交量 ÷ 标注提交量；分母为零时为空。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.expected_allocated",
        "预期验收分配量",
        "count",
        "Good 和 Bad 指标对象 expect_alloc 的合计。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.allocated",
        "实际验收分配量",
        "count",
        "Good 和 Bad 指标对象 actual_alloc 的合计。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.allocation_coverage_rate",
        "分配覆盖率",
        "percent",
        "实际验收分配量 ÷ 标注提交量；不强制截断到 100%。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.allocation_fulfillment_rate",
        "分配达成率",
        "percent",
        "实际验收分配量 ÷ 预期验收分配量；分母为零时为空。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.completed",
        "验收完成量",
        "count",
        "Good 和 Bad 指标对象 actual_complete 的合计。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.pending",
        "验收未完成量",
        "count",
        "实际验收分配量减验收完成量，不小于零。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.completion_rate",
        "验收完成率",
        "percent",
        "验收完成量 ÷ 实际验收分配量；分母为零时为空。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.passed",
        "验收通过量",
        "count",
        "Good 和 Bad 指标对象 actual_pass 的合计。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.rejected",
        "验收打回量",
        "count",
        "Good 和 Bad 指标对象 actual_reject 的合计。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.pass_rate",
        "验收通过率",
        "percent",
        "验收通过量 ÷ 验收完成量；分母为零时为空。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "acceptance.reject_rate",
        "验收打回率",
        "percent",
        "验收打回量 ÷ 验收完成量；分母为零时为空。",
        ("greater_than", "less_than", "between"),
    ),
    MetricDefinition(
        "option.annotation_submitted",
        "问题选项标注量",
        "count",
        "指定问题标签和问题选项的 annotation_submitted 合计。",
        ("greater_than", "less_than", "between"),
        requires_question_option=True,
    ),
    MetricDefinition(
        "option.annotation_rate_of_bad",
        "问题选项占 Bad 比例",
        "percent",
        "指定问题选项标注量 ÷ Bad 提交量；多选选项之和可能超过 100%。",
        ("greater_than", "less_than", "between"),
        requires_question_option=True,
    ),
)


_DIMENSIONS_BY_ID = {item.id: item for item in DIMENSIONS}
_METRICS_BY_ID = {item.id: item for item in METRICS}


def get_dimension(identifier: str) -> DimensionDefinition | None:
    return _DIMENSIONS_BY_ID.get(identifier)


def get_metric(identifier: str) -> MetricDefinition | None:
    return _METRICS_BY_ID.get(identifier)


def catalog_payload() -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "dimensions": [asdict(item) for item in DIMENSIONS],
        "metrics": [asdict(item) for item in METRICS],
    }
