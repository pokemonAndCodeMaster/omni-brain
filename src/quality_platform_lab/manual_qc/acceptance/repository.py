from __future__ import annotations

from typing import Any

from ...database import PostgresConnector
from .models import SnapshotFilter


COUNT_FIELDS = (
    "annotation_total",
    "annotation_submitted",
    "good_annotation_submitted",
    "bad_annotation_submitted",
    "total_accept_assigned",
    "total_accept_completed",
    "total_accept_passed",
    "total_accept_rejected",
    "good_accept_assigned",
    "good_accept_completed",
    "good_accept_passed",
    "good_accept_rejected",
    "bad_accept_assigned",
    "bad_accept_completed",
    "bad_accept_passed",
    "bad_accept_rejected",
)


class SnapshotRepository:
    def __init__(self, postgres: PostgresConnector) -> None:
        self._postgres = postgres
        self._table = f"{postgres.schema}.t_qc_daily_snapshot"

    @staticmethod
    def _where(filters: SnapshotFilter) -> tuple[str, dict[str, Any]]:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        for field in (
            "stat_date_start",
            "stat_date_end",
            "scene_name",
            "group_name",
            "employee_id",
        ):
            value = getattr(filters, field)
            if value in (None, ""):
                continue
            if field == "stat_date_start":
                clauses.append("stat_date >= %(stat_date_start)s")
            elif field == "stat_date_end":
                clauses.append("stat_date <= %(stat_date_end)s")
            else:
                clauses.append(f"{field} = %({field})s")
            params[field] = value
        return (" WHERE " + " AND ".join(clauses)) if clauses else "", params

    @staticmethod
    def _sum_columns() -> str:
        return ",\n".join(f"SUM({field})::integer AS {field}" for field in COUNT_FIELDS)

    def _aggregate(
        self,
        filters: SnapshotFilter,
        dimensions: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        where_sql, params = self._where(filters)
        dimension_sql = ", ".join(dimensions)
        statement = f"""
            SELECT
                {dimension_sql},
                {self._sum_columns()},
                MAX(computed_at) AS computed_at
            FROM {self._table}
            {where_sql}
            GROUP BY {dimension_sql}
            ORDER BY {dimension_sql}
        """
        return self._postgres.fetch_all(statement, params)

    def aggregate_by_scene(self, filters: SnapshotFilter) -> list[dict[str, Any]]:
        return self._aggregate(filters, ("stat_date", "scene_name"))

    def aggregate_by_group(self, filters: SnapshotFilter) -> list[dict[str, Any]]:
        return self._aggregate(filters, ("stat_date", "scene_name", "group_name"))

    def aggregate_by_employee(self, filters: SnapshotFilter) -> list[dict[str, Any]]:
        return self._aggregate(
            filters,
            ("stat_date", "scene_name", "group_name", "employee_id"),
        )

    def list_rows(
        self,
        filters: SnapshotFilter,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        where_sql, params = self._where(filters)
        params.update({"limit": limit, "offset": offset})
        statement = f"""
            SELECT *
            FROM {self._table}
            {where_sql}
            ORDER BY stat_date DESC, scene_name, group_name, employee_id
            LIMIT %(limit)s OFFSET %(offset)s
        """
        return self._postgres.fetch_all(statement, params)

    def count_rows(self, filters: SnapshotFilter) -> int:
        where_sql, params = self._where(filters)
        row = self._postgres.fetch_one(
            f"SELECT COUNT(*)::integer AS count FROM {self._table}{where_sql}",
            params,
        )
        return int(row["count"]) if row else 0
