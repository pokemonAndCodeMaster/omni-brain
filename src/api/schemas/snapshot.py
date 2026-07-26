from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    schema_version: str
    database_alias: str
    database: str
    postgres_version: str


class MetricTotals(BaseModel):
    annotation_total: int = Field(ge=0)
    annotation_submitted: int = Field(ge=0)
    expect_alloc: int = Field(ge=0)
    actual_alloc: int = Field(ge=0)
    actual_complete: int = Field(ge=0)
    correct: int = Field(ge=0)
    incorrect: int = Field(ge=0)
    expect_pass: int = Field(ge=0)
    expect_reject: int = Field(ge=0)
    actual_pass: int = Field(ge=0)
    actual_reject: int = Field(ge=0)


class MetricState(MetricTotals):
    conclusion: Literal["pass", "reject", "pending"] | None = None
    exec_status: Literal[
        "PENDING",
        "PASS_EXECUTING",
        "PASS_DONE",
        "REJECT_EXECUTING",
        "REJECT_DONE",
    ] | None = None


class SceneAggregateOut(BaseModel):
    stat_date: date
    scene_name: str
    annotation_total: int = Field(ge=0)
    annotation_submitted: int = Field(ge=0)
    good_metrics: MetricTotals
    bad_metrics: MetricTotals
    computed_at: datetime


class GroupAggregateOut(SceneAggregateOut):
    group_name: str


class EmployeeAggregateOut(GroupAggregateOut):
    employee_id: str


class SnapshotRowOut(BaseModel):
    """The current 18-column snapshot contract."""

    model_config = ConfigDict(extra="forbid")

    id: int
    stat_date: date
    scene_name: str
    group_name: str
    employee_id: str
    project_name: str
    annotation_total: int = Field(ge=0)
    annotation_submitted: int = Field(ge=0)
    good_metrics: MetricState
    bad_metrics: MetricState
    option_metrics: dict[str, dict[str, MetricState]]
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    executed_by: str | None = None
    executed_at: datetime | None = None
    execution_note: str | None = None
    computed_at: datetime
    updated_at: datetime


T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    schema_version: str = "snapshot-jsonb-v20260709"
    items: list[T]
    total: int = Field(ge=0)
    computed_at: datetime | None = None
