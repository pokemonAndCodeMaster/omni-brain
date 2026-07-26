from __future__ import annotations

from typing import Any

from src.database import PGConnector
from .models import SnapshotFilter


METRIC_NUMBER_KEYS = (
    "annotation_total",
    "annotation_submitted",
    "expect_alloc",
    "actual_alloc",
    "actual_complete",
    "correct",
    "incorrect",
    "expect_pass",
    "expect_reject",
    "actual_pass",
    "actual_reject",
)


class SnapshotRepository:
    def __init__(self, postgres: PGConnector) -> None:
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
            "project_name",
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
        columns = [
            "SUM(annotation_total)::integer AS annotation_total",
            "SUM(annotation_submitted)::integer AS annotation_submitted",
        ]
        for metric_column in ("good_metrics", "bad_metrics"):
            prefix = metric_column.removesuffix("_metrics")
            columns.extend(
                "SUM(COALESCE(NULLIF("
                f"{metric_column}->>'{key}', '')::integer, 0))::integer "
                f"AS {prefix}_{key}"
                for key in METRIC_NUMBER_KEYS
            )
        return ",\n".join(columns)

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

    def list_minimum_rows(
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

    # Kept as an explicit alias for existing callers while the source-aligned
    # name becomes the public contract.
    list_rows = list_minimum_rows

    def count_rows(self, filters: SnapshotFilter) -> int:
        where_sql, params = self._where(filters)
        row = self._postgres.fetch_one(
            f"SELECT COUNT(*)::integer AS count FROM {self._table}{where_sql}",
            params,
        )
        return int(row["count"]) if row else 0
