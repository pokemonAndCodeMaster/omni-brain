from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import ConfigManager
from src.database import DatabaseManager
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
        print(
            json.dumps(
                {
                    "status": "verified",
                    "snapshot_rows": total,
                    "date_project_rows": len(projects),
                    "date_task_rows": len(scene),
                    "task_date_group_rows": len(groups),
                    "task_group_date_employee_rows": len(employees),
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
