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
        service = SnapshotQueryService(SnapshotRepository(manager.postgres()))
        analysis_service = AnalysisQueryService(AnalysisRepository(manager.postgres()))
        filters = SnapshotFilter()
        rows, total = service.list_rows(filters, limit=1000, offset=0)
        projects = service.aggregate("project", filters)
        scene = service.aggregate("scene", filters)
        groups = service.aggregate(
            "group",
            SnapshotFilter(
                project_name="城区/高速",
                scene_name="城区交互任务-A",
            ),
        )
        employees = service.aggregate(
            "employee",
            SnapshotFilter(
                project_name="城区/高速",
                scene_name="城区交互任务-A",
                group_name="一组",
            ),
        )
        assert total == 16, f"expected 16 rows, got {total}"
        assert len(rows) == 16
        assert {row["project_name"] for row in projects} == {"园区", "城区/高速"}
        assert len(projects) == 4, (
            f"expected 4 date-project rows, got {len(projects)}"
        )
        assert len(scene) == 8, f"expected 8 date-task rows, got {len(scene)}"
        assert len(groups) == 4, f"expected 4 date-group rows, got {len(groups)}"
        assert len(employees) == 2, (
            f"expected 2 date-employee rows, got {len(employees)}"
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
        assert task_result.total == 4, (
            f"expected 4 period-task rows, got {task_result.total}"
        )
        task_totals = {row.key: row.measures for row in task_result.rows}
        assert task_totals["城区/高速::城区交互任务-A"]["annotation.submitted"] == 447
        assert task_totals["城区/高速::城区交互任务-A"]["annotation.good_rate"] == 75.3915

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
        assert [row.key for row in low_pass_result.rows] == [
            "园区::园区泊车任务-D",
            "城区/高速::高速变道任务-B",
        ]

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
                filters=(AnalysisFilter(cut_in_rate, "greater_than", 20),),
                sort=(AnalysisSort(cut_in_rate, "descending"),),
                page=AnalysisPage(),
            )
        )
        assert [row.key for row in option_result.rows] == ["城区/高速::城区交互任务-A"]
        assert analysis_service.facets(
            scope=AnalysisScope(),
            dimension_id="question_option",
            question_label="驾驶行为分类",
        ) == ["CUT_IN", "MERGE", "YIELD"]
        print(
            json.dumps(
                {
                    "status": "verified",
                    "snapshot_rows": total,
                    "date_project_rows": len(projects),
                    "date_task_rows": len(scene),
                    "task_date_group_rows": len(groups),
                    "task_group_date_employee_rows": len(employees),
                    "period_task_rows": task_result.total,
                    "low_pass_tasks": len(low_pass_result.rows),
                    "cut_in_high_rate_tasks": len(option_result.rows),
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
