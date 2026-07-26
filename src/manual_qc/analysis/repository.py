from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from src.database import PGConnector

from .catalog import get_dimension
from .models import (
    AnalysisFilter,
    AnalysisQuery,
    AnalysisRow,
    AnalysisScope,
    MetricReference,
)


_DIMENSION_COLUMNS = {
    "date": "stat_date",
    "project": "project_name",
    "task": "scene_name",
    "group": "group_name",
    "employee": "employee_id",
}


class AnalysisRepository:
    """Compile catalog-only manual-QC analysis requests into parameterized SQL."""

    def __init__(self, postgres: PGConnector) -> None:
        self._postgres = postgres
        self._table = f"{postgres.schema}.t_qc_daily_snapshot"

    def query(self, query: AnalysisQuery) -> tuple[list[AnalysisRow], int]:
        all_metrics = self._required_metrics(query)
        metric_aliases = {
            reference.stable_key(): f"metric_{index}"
            for index, reference in enumerate(all_metrics)
        }
        params: dict[str, Any] = {}
        where_parts = self._scope_where(query.scope, params)
        where_parts.extend(self._dimension_filters(query.filters, params))
        dimension_selects = []
        dimension_groups = []
        dimension_aliases: list[tuple[str, str]] = []
        for index, identifier in enumerate(query.group_by):
            column = _DIMENSION_COLUMNS[identifier]
            alias = f"dimension_{index}"
            dimension_selects.append(f"s.{column} AS {alias}")
            dimension_groups.append(f"s.{column}")
            dimension_aliases.append((identifier, alias))

        metric_selects = [
            f"{self._metric_expression(reference, alias, params)} AS {alias}"
            for reference, alias in (
                (reference, metric_aliases[reference.stable_key()])
                for reference in all_metrics
            )
        ]
        select_parts = [*dimension_selects, *metric_selects, "MAX(s.computed_at) AS computed_at"]
        filter_parts = self._aggregate_filters(query.filters, metric_aliases, params)
        order_sql = self._order_sql(query, metric_aliases, dimension_aliases)
        select_sql = ",\n                    ".join(select_parts)
        source_where_sql = "WHERE " + " AND ".join(where_parts) if where_parts else ""
        aggregate_where_sql = (
            "WHERE " + " AND ".join(filter_parts) if filter_parts else ""
        )
        params["limit"] = query.page.size
        params["offset"] = (query.page.number - 1) * query.page.size

        statement = f"""
            WITH aggregated AS (
                SELECT
                    {select_sql}
                FROM {self._table} AS s
                {source_where_sql}
                GROUP BY {", ".join(dimension_groups)}
            ), filtered AS (
                SELECT *, COUNT(*) OVER() AS full_count
                FROM aggregated
                {aggregate_where_sql}
            )
            SELECT *
            FROM filtered
            {order_sql}
            LIMIT %(limit)s OFFSET %(offset)s
        """
        records = self._postgres.fetch_all(statement, params)
        total = int(records[0]["full_count"]) if records else 0
        rows = [
            self._to_row(record, query, metric_aliases, dimension_aliases)
            for record in records
        ]
        return rows, total

    @staticmethod
    def _required_metrics(query: AnalysisQuery) -> tuple[MetricReference, ...]:
        references: list[MetricReference] = list(query.measures)
        references.extend(
            item.target
            for item in query.filters
            if get_dimension(item.target.id) is None
        )
        references.extend(
            item.target
            for item in query.sort
            if get_dimension(item.target.id) is None
        )
        unique: dict[tuple[str, tuple[tuple[str, str], ...]], MetricReference] = {}
        for reference in references:
            unique.setdefault(reference.stable_key(), reference)
        return tuple(unique.values())

    @staticmethod
    def _scope_where(scope: AnalysisScope, params: dict[str, Any]) -> list[str]:
        clauses: list[str] = []
        if scope.date_start:
            clauses.append("s.stat_date >= %(scope_date_start)s")
            params["scope_date_start"] = scope.date_start
        if scope.date_end:
            clauses.append("s.stat_date <= %(scope_date_end)s")
            params["scope_date_end"] = scope.date_end
        for field, values in (
            ("project_name", scope.project_names),
            ("scene_name", scope.task_names),
            ("group_name", scope.group_names),
            ("employee_id", scope.employee_ids),
        ):
            if values:
                parameter = f"scope_{field}"
                clauses.append(f"s.{field} = ANY(%({parameter})s::text[])")
                params[parameter] = list(values)
        return clauses

    def facets(
        self,
        *,
        scope: AnalysisScope,
        dimension_id: str,
        question_label: str | None,
    ) -> list[str]:
        params: dict[str, Any] = {"limit": 200}
        where_parts = self._scope_where(scope, params)
        if dimension_id in _DIMENSION_COLUMNS:
            column = _DIMENSION_COLUMNS[dimension_id]
            statement = f"""
                SELECT DISTINCT s.{column} AS value
                FROM {self._table} AS s
                {"WHERE " + " AND ".join(where_parts) if where_parts else ""}
                ORDER BY value
                LIMIT %(limit)s
            """
        elif dimension_id == "question_label":
            statement = f"""
                SELECT DISTINCT label.value AS value
                FROM {self._table} AS s
                CROSS JOIN LATERAL jsonb_object_keys(s.option_metrics)
                    AS label(value)
                {"WHERE " + " AND ".join(where_parts) if where_parts else ""}
                ORDER BY value
                LIMIT %(limit)s
            """
        else:
            assert dimension_id == "question_option"
            params["facet_question_label"] = question_label
            label_clause = "question.label = %(facet_question_label)s"
            clauses = [*where_parts, label_clause]
            statement = f"""
                SELECT DISTINCT option_value.value AS value
                FROM {self._table} AS s
                CROSS JOIN LATERAL jsonb_each(s.option_metrics)
                    AS question(label, options)
                CROSS JOIN LATERAL jsonb_object_keys(question.options)
                    AS option_value(value)
                WHERE {" AND ".join(clauses)}
                ORDER BY value
                LIMIT %(limit)s
            """
        rows = self._postgres.fetch_all(statement, params)
        return [str(row["value"]) for row in rows]

    @staticmethod
    def _dimension_filters(
        filters: Iterable[AnalysisFilter],
        params: dict[str, Any],
    ) -> list[str]:
        clauses: list[str] = []
        for index, item in enumerate(filters):
            if get_dimension(item.target.id) is None:
                continue
            column = _DIMENSION_COLUMNS[item.target.id]
            parameter = f"dimension_filter_{index}"
            if item.operator == "equals":
                clauses.append(f"s.{column} = %({parameter})s")
                params[parameter] = item.value
            elif item.operator == "in":
                clauses.append(f"s.{column} = ANY(%({parameter})s::text[])")
                params[parameter] = list(item.value)
            elif item.operator == "contains":
                clauses.append(f"s.{column} ILIKE %({parameter})s")
                params[parameter] = f"%{item.value}%"
            elif item.operator == "between":
                minimum, maximum = item.value
                clauses.append(
                    f"s.{column} >= %({parameter}_minimum)s "
                    f"AND s.{column} <= %({parameter}_maximum)s"
                )
                params[f"{parameter}_minimum"] = minimum
                params[f"{parameter}_maximum"] = maximum
        return clauses

    @staticmethod
    def _metric_json_value(metric_column: str, key: str) -> str:
        return (
            "SUM(COALESCE(NULLIF("
            f"s.{metric_column}->>'{key}', '')::bigint, 0))"
        )

    @staticmethod
    def _rate(numerator: str, denominator: str) -> str:
        return f"(100.0 * ({numerator}) / NULLIF(({denominator}), 0))"

    def _metric_expression(
        self,
        reference: MetricReference,
        alias: str,
        params: dict[str, Any],
    ) -> str:
        good_submitted = self._metric_json_value("good_metrics", "annotation_submitted")
        bad_submitted = self._metric_json_value("bad_metrics", "annotation_submitted")
        allocated = (
            f"({self._metric_json_value('good_metrics', 'actual_alloc')} + "
            f"{self._metric_json_value('bad_metrics', 'actual_alloc')})"
        )
        expected_allocated = (
            f"({self._metric_json_value('good_metrics', 'expect_alloc')} + "
            f"{self._metric_json_value('bad_metrics', 'expect_alloc')})"
        )
        completed = (
            f"({self._metric_json_value('good_metrics', 'actual_complete')} + "
            f"{self._metric_json_value('bad_metrics', 'actual_complete')})"
        )
        passed = (
            f"({self._metric_json_value('good_metrics', 'actual_pass')} + "
            f"{self._metric_json_value('bad_metrics', 'actual_pass')})"
        )
        rejected = (
            f"({self._metric_json_value('good_metrics', 'actual_reject')} + "
            f"{self._metric_json_value('bad_metrics', 'actual_reject')})"
        )
        submitted = "SUM(s.annotation_submitted)"
        expressions = {
            "annotation.total": "SUM(s.annotation_total)",
            "annotation.submitted": submitted,
            "annotation.good_submitted": good_submitted,
            "annotation.bad_submitted": bad_submitted,
            "annotation.good_rate": self._rate(good_submitted, submitted),
            "annotation.bad_rate": self._rate(bad_submitted, submitted),
            "acceptance.expected_allocated": expected_allocated,
            "acceptance.allocated": allocated,
            "acceptance.allocation_coverage_rate": self._rate(allocated, submitted),
            "acceptance.allocation_fulfillment_rate": self._rate(
                allocated,
                expected_allocated,
            ),
            "acceptance.completed": completed,
            "acceptance.pending": f"GREATEST(({allocated}) - ({completed}), 0)",
            "acceptance.completion_rate": self._rate(completed, allocated),
            "acceptance.passed": passed,
            "acceptance.rejected": rejected,
            "acceptance.pass_rate": self._rate(passed, completed),
            "acceptance.reject_rate": self._rate(rejected, completed),
        }
        if reference.id in expressions:
            return expressions[reference.id]
        if reference.id.startswith("option."):
            label_parameter = f"{alias}_question_label"
            option_parameter = f"{alias}_question_option"
            params[label_parameter] = reference.parameters["question_label"]
            params[option_parameter] = reference.parameters["question_option"]
            option_submitted = (
                "SUM(COALESCE(NULLIF(s.option_metrics #>> ARRAY["
                f"%({label_parameter})s, %({option_parameter})s, "
                "'annotation_submitted'], '')::bigint, 0))"
            )
            if reference.id == "option.annotation_submitted":
                return option_submitted
            if reference.id == "option.annotation_rate_of_bad":
                return self._rate(option_submitted, bad_submitted)
        raise ValueError(f"不支持的分析指标：{reference.id}")

    def _aggregate_filters(
        self,
        filters: Iterable[AnalysisFilter],
        metric_aliases: dict[tuple[str, tuple[tuple[str, str], ...]], str],
        params: dict[str, Any],
    ) -> list[str]:
        clauses: list[str] = []
        for index, item in enumerate(filters):
            if get_dimension(item.target.id) is not None:
                continue
            expression = metric_aliases[item.target.stable_key()]
            parameter = f"filter_{index}"
            if item.operator == "greater_than":
                clauses.append(f"{expression} > %({parameter})s")
                params[parameter] = item.value
            elif item.operator == "less_than":
                clauses.append(f"{expression} < %({parameter})s")
                params[parameter] = item.value
            elif item.operator == "between":
                minimum, maximum = item.value
                clauses.append(
                    f"{expression} >= %({parameter}_minimum)s "
                    f"AND {expression} <= %({parameter}_maximum)s"
                )
                params[f"{parameter}_minimum"] = minimum
                params[f"{parameter}_maximum"] = maximum
        return clauses

    def _order_sql(
        self,
        query: AnalysisQuery,
        metric_aliases: dict[tuple[str, tuple[tuple[str, str], ...]], str],
        dimension_aliases: list[tuple[str, str]],
    ) -> str:
        parts: list[str] = []
        dimension_alias_map = dict(dimension_aliases)
        for item in query.sort:
            direction = "ASC" if item.direction == "ascending" else "DESC"
            if item.target.id in dimension_alias_map:
                parts.append(f"{dimension_alias_map[item.target.id]} {direction}")
            else:
                alias = metric_aliases[item.target.stable_key()]
                parts.append(f"{alias} {direction} NULLS LAST")
        if not parts:
            parts = [f"{alias} ASC" for _, alias in dimension_aliases]
        return "ORDER BY " + ", ".join(parts)

    @staticmethod
    def _to_number(value: Any) -> int | float | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        numeric = float(value)
        return round(numeric, 4) if not numeric.is_integer() else int(numeric)

    def _to_row(
        self,
        record: dict[str, Any],
        query: AnalysisQuery,
        metric_aliases: dict[tuple[str, tuple[tuple[str, str], ...]], str],
        dimension_aliases: list[tuple[str, str]],
    ) -> AnalysisRow:
        dimensions = {
            identifier: str(record[alias])
            for identifier, alias in dimension_aliases
        }
        measures = {
            reference.id
            if not reference.parameters
            else f"{reference.id}:{reference.parameters['question_label']}/{reference.parameters['question_option']}": self._to_number(
                record[metric_aliases[reference.stable_key()]]
            )
            for reference in query.measures
        }
        computed_at = record["computed_at"]
        if not isinstance(computed_at, datetime):
            raise RuntimeError("分析查询缺少 computed_at")
        return AnalysisRow(
            key="::".join(dimensions[identifier] for identifier in query.group_by),
            dimensions=dimensions,
            measures=measures,
            computed_at=computed_at,
        )
