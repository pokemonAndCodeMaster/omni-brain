from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import ConfigManager
from src.database import DatabaseManager
from src.manual_qc.analysis import AnalysisQueryService, AnalysisRepository
from src.manual_qc.analysis.catalog import SOURCE_ID
from src.manual_qc.analysis.models import (
    AnalysisFilter,
    AnalysisPage,
    AnalysisQuery,
    AnalysisScope,
    AnalysisSort,
    MetricReference,
)
from src.manual_qc.snapshot.models import SnapshotFilter
from src.manual_qc.snapshot.repository import SnapshotRepository
from src.manual_qc.snapshot.snapshot_service import SnapshotQueryService


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _runtime() -> tuple[ConfigManager, DatabaseManager]:
    config = ConfigManager(project_root=project_root())
    config.setup_logging()
    return config, DatabaseManager(config)


def _execute_sql_directory(directory: Path) -> None:
    _, manager = _runtime()
    connector = manager.postgres()
    try:
        for file_path in sorted(directory.glob("*.sql")):
            connector.execute_script(file_path.read_text(encoding="utf-8"))
            print(f"applied {file_path.relative_to(project_root())}")
    finally:
        manager.close()


def command_migrate() -> None:
    _execute_sql_directory(project_root() / "migrations")


def command_seed() -> None:
    _execute_sql_directory(project_root() / "seeds")


def command_health() -> None:
    config, manager = _runtime()
    try:
        result = manager.postgres().health_check()
        print(
            json.dumps(
                {
                    "status": "ok",
                    "schema_version": config.get_nested("app.schema_version"),
                    "database_alias": result.alias,
                    "database": result.database,
                    "postgres_version": result.server_version,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        manager.close()


def command_verify() -> None:
    _, manager = _runtime()
    try:
        postgres = manager.postgres()
        service = SnapshotQueryService(SnapshotRepository(postgres))
        analysis_service = AnalysisQueryService(AnalysisRepository(postgres))
        filters = SnapshotFilter()
        rows, total = service.list_rows(filters, limit=100, offset=0)
        projects = service.aggregate("project", filters)
        scene = service.aggregate("scene", filters)
        groups = service.aggregate(
            "group",
            SnapshotFilter(
                project_name="城区/高速",
                scene_name="城区交互任务-01",
            ),
        )
        employees = service.aggregate(
            "employee",
            SnapshotFilter(
                project_name="城区/高速",
                scene_name="城区交互任务-01",
                group_name="质检组-01",
            ),
        )
        dimensions = postgres.fetch_one(
            """
            SELECT
                COUNT(DISTINCT stat_date)::integer AS dates,
                COUNT(DISTINCT scene_name)::integer AS tasks,
                COUNT(DISTINCT group_name)::integer AS groups,
                COUNT(DISTINCT employee_id)::integer AS employees
            FROM manual_qc_lab.t_qc_daily_snapshot
            """
        )
        assert dimensions is not None
        assert total == 3024, f"expected 3024 rows, got {total}"
        assert len(rows) == 100
        assert dimensions == {
            "dates": 14,
            "tasks": 24,
            "groups": 12,
            "employees": 120,
        }
        assert {row["project_name"] for row in projects} == {"园区", "城区/高速"}
        assert len(projects) == 28, (
            f"expected 28 date-project rows, got {len(projects)}"
        )
        assert len(scene) == 336, f"expected 336 date-task rows, got {len(scene)}"
        assert len(groups) == 42, f"expected 42 date-group rows, got {len(groups)}"
        assert len(employees) == 42, (
            f"expected 42 date-employee rows, got {len(employees)}"
        )
        task_result = analysis_service.query(
            AnalysisQuery(
                source_id=SOURCE_ID,
                scope=AnalysisScope(),
                group_by=("project", "task"),
                measures=(
                    MetricReference("annotation.submitted"),
                    MetricReference("annotation.good_rate"),
                    MetricReference("acceptance.pass_rate"),
                ),
                sort=(
                    AnalysisSort(
                        MetricReference("annotation.submitted"),
                        "descending",
                    ),
                ),
                page=AnalysisPage(),
            )
        )
        assert task_result.total == 24, (
            f"expected 24 period-task rows, got {task_result.total}"
        )
        task_totals = {row.key: row.measures for row in task_result.rows}
        raw_task = postgres.fetch_one(
            """
            SELECT
                SUM(annotation_submitted)::integer AS submitted,
                100.0 * SUM(
                    COALESCE((good_metrics->>'annotation_submitted')::integer, 0)
                ) / NULLIF(SUM(annotation_submitted), 0) AS good_rate
            FROM manual_qc_lab.t_qc_daily_snapshot
            WHERE scene_name = '城区交互任务-01'
            """
        )
        assert raw_task is not None
        task_one = task_totals["城区/高速::城区交互任务-01"]
        assert task_one["annotation.submitted"] == raw_task["submitted"]
        assert task_one["annotation.good_rate"] == round(
            float(raw_task["good_rate"]),
            4,
        )

        low_pass_result = analysis_service.query(
            AnalysisQuery(
                source_id=SOURCE_ID,
                scope=AnalysisScope(),
                group_by=("project", "task"),
                measures=(
                    MetricReference("annotation.submitted"),
                    MetricReference("acceptance.pass_rate"),
                ),
                filters=(
                    AnalysisFilter(
                        MetricReference("acceptance.pass_rate"),
                        "less_than",
                        80,
                    ),
                ),
                sort=(
                    AnalysisSort(
                        MetricReference("acceptance.pass_rate"),
                        "ascending",
                    ),
                ),
                page=AnalysisPage(),
            )
        )
        assert low_pass_result.rows
        assert all(
            row.measures["acceptance.pass_rate"] is not None
            and row.measures["acceptance.pass_rate"] < 80
            for row in low_pass_result.rows
        )
        assert any(
            row.key == "城区/高速::复杂掉头任务-12"
            for row in low_pass_result.rows
        )

        boundary_result = analysis_service.query(
            AnalysisQuery(
                source_id=SOURCE_ID,
                scope=AnalysisScope(
                    task_names=(
                        "拥堵跟车任务-08",
                        "复杂掉头任务-12",
                        "零提交边界任务-23",
                        "重复验收边界任务-24",
                    )
                ),
                group_by=("project", "task"),
                measures=(
                    MetricReference("annotation.good_rate"),
                    MetricReference("acceptance.allocation_coverage_rate"),
                    MetricReference("acceptance.completion_rate"),
                    MetricReference("acceptance.pass_rate"),
                ),
                page=AnalysisPage(),
            )
        )
        boundaries = {row.dimensions["task"]: row.measures for row in boundary_result.rows}
        assert boundaries["拥堵跟车任务-08"]["acceptance.completion_rate"] < 50
        assert boundaries["复杂掉头任务-12"]["acceptance.pass_rate"] < 60
        assert boundaries["零提交边界任务-23"]["annotation.good_rate"] is None
        assert (
            boundaries["零提交边界任务-23"][
                "acceptance.allocation_coverage_rate"
            ]
            is None
        )
        assert (
            boundaries["重复验收边界任务-24"][
                "acceptance.allocation_coverage_rate"
            ]
            > 100
        )

        cut_in_rate = MetricReference(
            "option.annotation_rate_of_bad",
            {
                "question_label": "驾驶行为分类",
                "question_option": "CUT_IN",
            },
        )
        option_result = analysis_service.query(
            AnalysisQuery(
                source_id=SOURCE_ID,
                scope=AnalysisScope(),
                group_by=("project", "task"),
                measures=(cut_in_rate,),
                filters=(AnalysisFilter(cut_in_rate, "greater_than", 0),),
                sort=(AnalysisSort(cut_in_rate, "descending"),),
                page=AnalysisPage(),
            )
        )
        assert option_result.total > 0
        assert analysis_service.facets(
            source_id=SOURCE_ID,
            scope=AnalysisScope(),
            dimension_id="question_option",
            question_label="驾驶行为分类",
        ) == ["CUT_IN", "FOLLOW_TOO_CLOSE", "MERGE", "YIELD"]
        option_boundaries = postgres.fetch_all(
            """
            SELECT
                option.value AS question_option,
                SUM((option.metrics->>'actual_alloc')::integer)::integer
                    AS allocated,
                SUM((option.metrics->>'actual_complete')::integer)::integer
                    AS completed,
                SUM((option.metrics->>'actual_pass')::integer)::integer
                    AS passed
            FROM manual_qc_lab.t_qc_daily_snapshot AS snapshot
            CROSS JOIN LATERAL jsonb_each(snapshot.option_metrics)
                AS question(label, options)
            CROSS JOIN LATERAL jsonb_each(question.options)
                AS option(value, metrics)
            WHERE option.value IN ('YIELD', 'STATIC')
            GROUP BY option.value
            """
        )
        option_metrics = {row["question_option"]: row for row in option_boundaries}
        assert (
            option_metrics["YIELD"]["completed"]
            / option_metrics["YIELD"]["allocated"]
            < 0.2
        )
        assert (
            option_metrics["STATIC"]["passed"]
            / option_metrics["STATIC"]["completed"]
            < 0.3
        )
        unallocated = postgres.fetch_one(
            """
            SELECT COUNT(*)::integer AS count
            FROM manual_qc_lab.t_qc_daily_snapshot
            WHERE annotation_submitted > 0
              AND COALESCE((good_metrics->>'actual_alloc')::integer, 0)
                  + COALESCE((bad_metrics->>'actual_alloc')::integer, 0) = 0
            """
        )
        assert unallocated == {"count": 1}
        print(
            json.dumps(
                {
                    "status": "verified",
                    "snapshot_rows": total,
                    "dates": dimensions["dates"],
                    "tasks": dimensions["tasks"],
                    "groups": dimensions["groups"],
                    "employees": dimensions["employees"],
                    "date_project_rows": len(projects),
                    "date_task_rows": len(scene),
                    "task_date_group_rows": len(groups),
                    "task_group_date_employee_rows": len(employees),
                    "period_task_rows": task_result.total,
                    "low_pass_tasks": len(low_pass_result.rows),
                    "cut_in_tasks": option_result.total,
                    "unallocated_rows": unallocated["count"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        manager.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Quality Platform Lab commands")
    parser.add_argument("command", choices=("migrate", "seed", "health", "verify"))
    args = parser.parse_args()
    {
        "migrate": command_migrate,
        "seed": command_seed,
        "health": command_health,
        "verify": command_verify,
    }[args.command]()


if __name__ == "__main__":
    main()
