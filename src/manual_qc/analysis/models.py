from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class MetricReference:
    """A catalog metric, optionally narrowed to one question option."""

    id: str
    parameters: dict[str, str] = field(default_factory=dict)

    def stable_key(self) -> tuple[str, tuple[tuple[str, str], ...]]:
        return self.id, tuple(sorted(self.parameters.items()))


@dataclass(frozen=True)
class AnalysisScope:
    date_start: date | None = None
    date_end: date | None = None
    project_names: tuple[str, ...] = ()
    task_names: tuple[str, ...] = ()
    group_names: tuple[str, ...] = ()
    employee_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisFilter:
    target: MetricReference
    operator: str
    value: Any


@dataclass(frozen=True)
class AnalysisSort:
    target: MetricReference
    direction: str


@dataclass(frozen=True)
class AnalysisPage:
    number: int = 1
    size: int = 50


@dataclass(frozen=True)
class AnalysisQuery:
    source_id: str
    scope: AnalysisScope
    group_by: tuple[str, ...]
    measures: tuple[MetricReference, ...]
    filters: tuple[AnalysisFilter, ...] = ()
    sort: tuple[AnalysisSort, ...] = ()
    page: AnalysisPage = AnalysisPage()


@dataclass(frozen=True)
class AnalysisRow:
    key: str
    dimensions: dict[str, str]
    measures: dict[str, int | float | None]
    computed_at: datetime


@dataclass(frozen=True)
class AnalysisResult:
    source_id: str
    group_by: tuple[str, ...]
    rows: list[AnalysisRow]
    total: int
    page: AnalysisPage
    computed_at: datetime | None
    warnings: tuple[str, ...] = ()
