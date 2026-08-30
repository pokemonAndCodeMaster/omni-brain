from __future__ import annotations

from typing import Any, Literal

from .models import METRIC_NUMBER_KEYS, SnapshotFilter
from .repository import SnapshotRepository


AggregateLevel = Literal["project", "scene", "group", "employee"]


class SnapshotQueryService:
    def __init__(self, repository: SnapshotRepository) -> None:
        self._repository = repository

    def aggregate(
        self,
        level: AggregateLevel,
        filters: SnapshotFilter,
    ) -> list[dict[str, Any]]:
        if level == "project":
            rows = self._repository.aggregate_by_project(filters)
            return [self._shape_aggregate(row) for row in rows]
        if level == "scene":
            rows = self._repository.aggregate_by_scene(filters)
            return [self._shape_aggregate(row) for row in rows]
        if level == "group":
            if not filters.scene_name:
                raise ValueError("按组聚合必须提供 scene_name")
            rows = self._repository.aggregate_by_group(filters)
            return [self._shape_aggregate(row) for row in rows]
        if level == "employee":
            if not filters.scene_name or not filters.group_name:
                raise ValueError("按员工聚合必须提供 scene_name 和 group_name")
            rows = self._repository.aggregate_by_employee(filters)
            return [self._shape_aggregate(row) for row in rows]
        raise ValueError(f"未知聚合级别：{level}")

    def list_rows(
        self,
        filters: SnapshotFilter,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        return (
            self._repository.list_minimum_rows(filters, limit=limit, offset=offset),
            self._repository.count_rows(filters),
        )

    @staticmethod
    def _shape_aggregate(row: dict[str, Any]) -> dict[str, Any]:
        shaped = dict(row)
        for dimension in ("good", "bad"):
            shaped[f"{dimension}_metrics"] = {
                key: shaped.pop(f"{dimension}_{key}")
                for key in METRIC_NUMBER_KEYS
            }
        return shaped
