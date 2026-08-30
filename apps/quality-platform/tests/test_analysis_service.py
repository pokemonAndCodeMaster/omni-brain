from __future__ import annotations

from datetime import date

import pytest

from src.manual_qc.analysis.analysis_service import (
    AnalysisQueryService,
    AnalysisValidationError,
)
from src.manual_qc.analysis.catalog import SOURCE_ID, catalog_payload
from src.manual_qc.analysis.models import (
    AnalysisFilter,
    AnalysisPage,
    AnalysisQuery,
    AnalysisScope,
    MetricReference,
)
from src.api.routers.analysis import _metric_reference
from src.api.schemas.analysis import AnalysisMetricReferenceIn


class UnusedRepository:
    def query(self, query: AnalysisQuery):  # pragma: no cover - invalid before query
        raise AssertionError(f"repository should not receive {query}")


def query_with(**changes: object) -> AnalysisQuery:
    base = {
        "source_id": SOURCE_ID,
        "scope": AnalysisScope(),
        "group_by": ("project", "task"),
        "measures": (MetricReference("annotation.submitted"),),
        "filters": (),
        "sort": (),
        "page": AnalysisPage(),
    }
    base.update(changes)
    return AnalysisQuery(**base)


def test_catalog_exposes_human_labels_and_question_option_requirement() -> None:
    catalog = catalog_payload()
    metrics = {item["id"]: item for item in catalog["metrics"]}

    assert catalog["source_id"] == SOURCE_ID
    assert metrics["annotation.good_rate"]["label"] == "Good 占比"
    assert metrics["option.annotation_rate_of_bad"]["requires_question_option"]
    assert metrics["good.acceptance.completion_rate"]["label"] == "Good 验收完成率"
    assert metrics["option.acceptance.pass_rate"]["requires_question_option"]


def test_rejects_unknown_metric_before_repository_access() -> None:
    service = AnalysisQueryService(UnusedRepository())  # type: ignore[arg-type]

    with pytest.raises(AnalysisValidationError, match="未知统计指标"):
        service.query(query_with(measures=(MetricReference("not.a.metric"),)))


def test_rejects_question_option_metric_without_both_parameters() -> None:
    service = AnalysisQueryService(UnusedRepository())  # type: ignore[arg-type]
    option_metric = MetricReference(
        "option.annotation_rate_of_bad",
        {"question_label": "驾驶行为分类"},
    )

    with pytest.raises(AnalysisValidationError, match="必须指定问题标签和问题选项"):
        service.query(query_with(measures=(option_metric,)))


def test_rejects_reverse_date_range_and_invalid_dimension_filter() -> None:
    service = AnalysisQueryService(UnusedRepository())  # type: ignore[arg-type]

    with pytest.raises(AnalysisValidationError, match="开始日期不能晚于结束日期"):
        service.query(
            query_with(
                scope=AnalysisScope(
                    date_start=date(2026, 7, 26),
                    date_end=date(2026, 7, 25),
                )
            )
        )

    with pytest.raises(AnalysisValidationError, match="不支持 greater_than 筛选"):
        service.query(
            query_with(
                filters=(
                    AnalysisFilter(
                        target=MetricReference("project"),
                        operator="greater_than",
                        value=1,
                    ),
                ),
            )
        )


def test_http_question_option_parameters_are_normalized_at_api_boundary() -> None:
    reference = _metric_reference(
        AnalysisMetricReferenceIn(
            id="option.annotation_rate_of_bad",
            parameters={
                "questionLabel": "驾驶行为分类",
                "questionOption": "CUT_IN",
            },
        )
    )

    assert reference.parameters == {
        "question_label": "驾驶行为分类",
        "question_option": "CUT_IN",
    }


def test_facets_reject_unknown_source_before_repository_access() -> None:
    service = AnalysisQueryService(UnusedRepository())  # type: ignore[arg-type]

    with pytest.raises(AnalysisValidationError, match="未知分析数据源"):
        service.facets(
            source_id="unknown.source",
            scope=AnalysisScope(),
            dimension_id="task",
            question_label=None,
        )
