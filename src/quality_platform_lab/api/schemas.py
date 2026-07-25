from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    schema_version: str
    database_alias: str
    database: str
    postgres_version: str


class SnapshotCounts(BaseModel):
    annotation_total: int
    annotation_submitted: int
    good_annotation_submitted: int
    bad_annotation_submitted: int
    total_accept_assigned: int
    total_accept_completed: int
    total_accept_passed: int
    total_accept_rejected: int
    good_accept_assigned: int
    good_accept_completed: int
    good_accept_passed: int
    good_accept_rejected: int
    bad_accept_assigned: int
    bad_accept_completed: int
    bad_accept_passed: int
    bad_accept_rejected: int


class SceneAggregateOut(SnapshotCounts):
    stat_date: date
    scene_name: str
    computed_at: datetime


class GroupAggregateOut(SceneAggregateOut):
    group_name: str


class EmployeeAggregateOut(GroupAggregateOut):
    employee_id: str


class SnapshotRowOut(EmployeeAggregateOut):
    model_config = ConfigDict(extra="forbid")

    project_name: str
    option_metrics: dict[str, Any]
    overall_conclusion: str | None = None
    conclusion_reason: str | None = None
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    execution: dict[str, Any]
    executed_by: str | None = None
    executed_at: datetime | None = None
    source_version: str
    created_at: datetime
    updated_at: datetime


T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    schema_version: str = "lab-v1"
    items: list[T]
    total: int = Field(ge=0)
    computed_at: datetime | None = None
