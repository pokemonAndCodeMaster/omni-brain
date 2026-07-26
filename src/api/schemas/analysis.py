from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AnalysisCamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class AnalysisMetricReferenceIn(AnalysisCamelModel):
    id: str = Field(min_length=1, max_length=128)
    parameters: dict[str, str] = Field(default_factory=dict, max_length=4)


class AnalysisScopeIn(AnalysisCamelModel):
    date_start: date | None = None
    date_end: date | None = None
    project_names: list[str] = Field(default_factory=list, max_length=50)
    task_names: list[str] = Field(default_factory=list, max_length=200)
    group_names: list[str] = Field(default_factory=list, max_length=200)
    employee_ids: list[str] = Field(default_factory=list, max_length=500)


class AnalysisFilterIn(AnalysisCamelModel):
    target: AnalysisMetricReferenceIn
    operator: Literal[
        "equals",
        "in",
        "contains",
        "greater_than",
        "less_than",
        "between",
    ]
    value: Any


class AnalysisSortIn(AnalysisCamelModel):
    target: AnalysisMetricReferenceIn
    direction: Literal["ascending", "descending"]


class AnalysisPageIn(AnalysisCamelModel):
    number: int = Field(default=1, ge=1, le=10_000)
    size: int = Field(default=50, ge=1, le=200)


class AnalysisQueryIn(AnalysisCamelModel):
    source_id: str = Field(min_length=1, max_length=128)
    scope: AnalysisScopeIn = Field(default_factory=AnalysisScopeIn)
    group_by: list[str] = Field(min_length=1, max_length=3)
    measures: list[AnalysisMetricReferenceIn] = Field(min_length=1, max_length=12)
    filters: list[AnalysisFilterIn] = Field(default_factory=list, max_length=12)
    sort: list[AnalysisSortIn] = Field(default_factory=list, max_length=3)
    page: AnalysisPageIn = Field(default_factory=AnalysisPageIn)


class AnalysisDimensionOut(AnalysisCamelModel):
    id: str
    label: str
    value_type: Literal["date", "text"]
    filter_operators: list[str]
    groupable: bool
    sortable: bool


class AnalysisMetricOut(AnalysisCamelModel):
    id: str
    label: str
    unit: Literal["count", "percent"]
    description: str
    filter_operators: list[str]
    sortable: bool
    requires_question_option: bool


class AnalysisCatalogOut(AnalysisCamelModel):
    source_id: str
    dimensions: list[AnalysisDimensionOut]
    metrics: list[AnalysisMetricOut]


class AnalysisRowOut(AnalysisCamelModel):
    key: str
    dimensions: dict[str, str]
    measures: dict[str, int | float | None]
    computed_at: datetime


class AnalysisQueryOut(AnalysisCamelModel):
    source_id: str
    group_by: list[str]
    rows: list[AnalysisRowOut]
    total: int = Field(ge=0)
    page: AnalysisPageIn
    computed_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)


class AnalysisFacetIn(AnalysisCamelModel):
    source_id: str = Field(min_length=1, max_length=128)
    scope: AnalysisScopeIn = Field(default_factory=AnalysisScopeIn)
    dimension_id: Literal[
        "project",
        "task",
        "group",
        "employee",
        "question_label",
        "question_option",
    ]
    question_label: str | None = Field(default=None, max_length=256)


class AnalysisFacetOut(AnalysisCamelModel):
    dimension_id: str
    values: list[str]
