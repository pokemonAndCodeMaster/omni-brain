from __future__ import annotations

from typing import Any

from .catalog import SOURCE_ID, catalog_payload, get_dimension, get_metric
from .models import (
    AnalysisFilter,
    AnalysisQuery,
    AnalysisResult,
    AnalysisScope,
    MetricReference,
)
from .repository import AnalysisRepository


class AnalysisValidationError(ValueError):
    """A user-correctable controlled-analysis request error."""


class AnalysisQueryService:
    """Validate business identifiers before the repository builds SQL."""

    def __init__(self, repository: AnalysisRepository) -> None:
        self._repository = repository

    @staticmethod
    def catalog() -> dict[str, object]:
        return catalog_payload()

    def query(self, query: AnalysisQuery) -> AnalysisResult:
        self._validate(query)
        rows, total = self._repository.query(query)
        latest = max((row.computed_at for row in rows), default=None)
        return AnalysisResult(
            source_id=query.source_id,
            group_by=query.group_by,
            rows=rows,
            total=total,
            page=query.page,
            computed_at=latest,
        )

    def facets(
        self,
        *,
        source_id: str,
        scope: AnalysisScope,
        dimension_id: str,
        question_label: str | None,
    ) -> list[str]:
        if source_id != SOURCE_ID:
            raise AnalysisValidationError(f"未知分析数据源：{source_id}")
        allowed = {
            "project",
            "task",
            "group",
            "employee",
            "question_label",
            "question_option",
        }
        if dimension_id not in allowed:
            raise AnalysisValidationError(f"不支持的候选值维度：{dimension_id}")
        if dimension_id == "question_option" and not question_label:
            raise AnalysisValidationError("读取问题选项前必须指定问题标签")
        if scope.date_start and scope.date_end and scope.date_start > scope.date_end:
            raise AnalysisValidationError("开始日期不能晚于结束日期")
        return self._repository.facets(
            scope=scope,
            dimension_id=dimension_id,
            question_label=question_label,
        )

    def _validate(self, query: AnalysisQuery) -> None:
        if query.source_id != SOURCE_ID:
            raise AnalysisValidationError(f"未知分析数据源：{query.source_id}")
        if query.scope.date_start and query.scope.date_end:
            if query.scope.date_start > query.scope.date_end:
                raise AnalysisValidationError("开始日期不能晚于结束日期")
        if not 1 <= len(query.group_by) <= 3:
            raise AnalysisValidationError("一次查询必须按 1 到 3 个维度分组")
        if len(set(query.group_by)) != len(query.group_by):
            raise AnalysisValidationError("分组维度不能重复")
        for identifier in query.group_by:
            if get_dimension(identifier) is None:
                raise AnalysisValidationError(f"不支持的分组维度：{identifier}")
        if not 1 <= len(query.measures) <= 12:
            raise AnalysisValidationError("一次查询必须选择 1 到 12 个指标")
        if len({item.stable_key() for item in query.measures}) != len(query.measures):
            raise AnalysisValidationError("同一指标不能重复选择")
        if len(query.filters) > 12:
            raise AnalysisValidationError("一次查询最多使用 12 个筛选条件")
        if len(query.sort) > 3:
            raise AnalysisValidationError("一次查询最多使用 3 个排序条件")
        if not 1 <= query.page.number <= 10_000:
            raise AnalysisValidationError("页码超出允许范围")
        if not 1 <= query.page.size <= 200:
            raise AnalysisValidationError("每页最多返回 200 行")

        for reference in query.measures:
            self._validate_reference(reference)
        for item in query.filters:
            self._validate_filter(item)
        for item in query.sort:
            self._validate_reference(item.target, allow_dimension=True)
            if item.direction not in {"ascending", "descending"}:
                raise AnalysisValidationError("排序方向只能是 ascending 或 descending")
            if get_dimension(item.target.id) is not None and item.target.id not in query.group_by:
                raise AnalysisValidationError("只能按当前分组结果中的维度排序")

    def _validate_reference(
        self,
        reference: MetricReference,
        *,
        allow_dimension: bool = False,
    ) -> None:
        dimension = get_dimension(reference.id)
        if dimension is not None:
            if allow_dimension:
                return
            raise AnalysisValidationError(f"{dimension.label} 是维度，不能作为统计指标")
        metric = get_metric(reference.id)
        if metric is None:
            raise AnalysisValidationError(f"未知统计指标：{reference.id}")
        if metric.requires_question_option:
            required = {"question_label", "question_option"}
            actual = set(reference.parameters)
            if actual != required or not all(reference.parameters.values()):
                raise AnalysisValidationError(
                    f"指标“{metric.label}”必须指定问题标签和问题选项"
                )
        elif reference.parameters:
            raise AnalysisValidationError(f"指标“{metric.label}”不接受附加参数")

    def _validate_filter(self, item: AnalysisFilter) -> None:
        dimension = get_dimension(item.target.id)
        if dimension is not None:
            if item.operator not in dimension.filter_operators:
                raise AnalysisValidationError(
                    f"维度“{dimension.label}”不支持 {item.operator} 筛选"
                )
            self._validate_filter_value(item.operator, item.value)
            return
        self._validate_reference(item.target)
        metric = get_metric(item.target.id)
        assert metric is not None
        if item.operator not in metric.filter_operators:
            raise AnalysisValidationError(
                f"指标“{metric.label}”不支持 {item.operator} 筛选"
            )
        self._validate_filter_value(item.operator, item.value)

    @staticmethod
    def _validate_filter_value(operator: str, value: Any) -> None:
        if operator == "in":
            if not isinstance(value, (list, tuple)) or not value:
                raise AnalysisValidationError("in 筛选需要至少一个值")
            return
        if operator == "between":
            if (
                not isinstance(value, (list, tuple))
                or len(value) != 2
                or value[0] is None
                or value[1] is None
            ):
                raise AnalysisValidationError("between 筛选需要两个边界值")
            return
        if value is None or value == "":
            raise AnalysisValidationError("筛选条件不能为空")
