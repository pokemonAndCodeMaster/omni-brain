from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_analysis_service
from src.api.schemas.analysis import (
    AnalysisCatalogOut,
    AnalysisFacetIn,
    AnalysisFacetOut,
    AnalysisFilterIn,
    AnalysisMetricReferenceIn,
    AnalysisQueryIn,
    AnalysisQueryOut,
    AnalysisRowOut,
    AnalysisSortIn,
)
from src.manual_qc.analysis.analysis_service import (
    AnalysisQueryService,
    AnalysisValidationError,
)
from src.manual_qc.analysis.models import (
    AnalysisFilter,
    AnalysisPage,
    AnalysisQuery,
    AnalysisScope,
    AnalysisSort,
    MetricReference,
)


router = APIRouter(prefix="/api/manual-qc/analysis", tags=["manual-qc-analysis"])
AnalysisService = Annotated[AnalysisQueryService, Depends(get_analysis_service)]

# HTTP 使用 camelCase，与其余 API 字段一致；领域层使用 Python 的 snake_case。
# `parameters` 是自由键字典，Pydantic 的 alias generator 不会自动递归转换它，
# 所以必须在这个唯一的边界显式归一化，不能让 Repository 或前端各自猜测。
_PARAMETER_KEY_ALIASES = {
    "questionLabel": "question_label",
    "questionOption": "question_option",
}


def _metric_reference(value: AnalysisMetricReferenceIn) -> MetricReference:
    return MetricReference(
        id=value.id,
        parameters={
            _PARAMETER_KEY_ALIASES.get(key, key): parameter_value
            for key, parameter_value in value.parameters.items()
        },
    )


def _scope(value: AnalysisQueryIn | AnalysisFacetIn) -> AnalysisScope:
    scope = value.scope
    return AnalysisScope(
        date_start=scope.date_start,
        date_end=scope.date_end,
        project_names=tuple(scope.project_names),
        task_names=tuple(scope.task_names),
        group_names=tuple(scope.group_names),
        employee_ids=tuple(scope.employee_ids),
    )


def _filter(value: AnalysisFilterIn) -> AnalysisFilter:
    return AnalysisFilter(
        target=_metric_reference(value.target),
        operator=value.operator,
        value=value.value,
    )


def _sort(value: AnalysisSortIn) -> AnalysisSort:
    return AnalysisSort(
        target=_metric_reference(value.target),
        direction=value.direction,
    )


@router.get("/catalog", response_model=AnalysisCatalogOut)
def catalog(service: AnalysisService) -> AnalysisCatalogOut:
    return AnalysisCatalogOut.model_validate(service.catalog())


@router.post("/query", response_model=AnalysisQueryOut)
def query(
    payload: AnalysisQueryIn,
    service: AnalysisService,
) -> AnalysisQueryOut:
    domain_query = AnalysisQuery(
        source_id=payload.source_id,
        scope=_scope(payload),
        group_by=tuple(payload.group_by),
        measures=tuple(_metric_reference(item) for item in payload.measures),
        filters=tuple(_filter(item) for item in payload.filters),
        sort=tuple(_sort(item) for item in payload.sort),
        page=AnalysisPage(number=payload.page.number, size=payload.page.size),
    )
    try:
        result = service.query(domain_query)
    except AnalysisValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AnalysisQueryOut(
        source_id=result.source_id,
        group_by=list(result.group_by),
        rows=[
            AnalysisRowOut(
                key=row.key,
                dimensions=row.dimensions,
                measures=row.measures,
                computed_at=row.computed_at,
            )
            for row in result.rows
        ],
        total=result.total,
        page=payload.page,
        computed_at=result.computed_at,
        warnings=list(result.warnings),
    )


@router.post("/facets", response_model=AnalysisFacetOut)
def facets(
    payload: AnalysisFacetIn,
    service: AnalysisService,
) -> AnalysisFacetOut:
    try:
        values = service.facets(
            source_id=payload.source_id,
            scope=_scope(payload),
            dimension_id=payload.dimension_id,
            question_label=payload.question_label,
        )
    except AnalysisValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AnalysisFacetOut(dimension_id=payload.dimension_id, values=values)
