from __future__ import annotations

from typing import Any, Literal

from .models import SnapshotFilter
from .repository import SnapshotRepository


AggregateLevel = Literal["scene", "group", "employee"]


class SnapshotQueryService:
    def __init__(self, repository: SnapshotRepository) -> None:
        self._repository = repository

    def aggregate(
        self,
        level: AggregateLevel,
        filters: SnapshotFilter,
    ) -> list[dict[str, Any]]:
        if level == "scene":
            return self._repository.aggregate_by_scene(filters)
        if level == "group":
            if not filters.scene_name:
                raise ValueError("按组聚合必须提供 scene_name")
            return self._repository.aggregate_by_group(filters)
        if level == "employee":
            if not filters.scene_name or not filters.group_name:
                raise ValueError("按员工聚合必须提供 scene_name 和 group_name")
            return self._repository.aggregate_by_employee(filters)
        raise ValueError(f"未知聚合级别：{level}")

    def list_rows(
        self,
        filters: SnapshotFilter,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        return (
            self._repository.list_rows(filters, limit=limit, offset=offset),
            self._repository.count_rows(filters),
        )
