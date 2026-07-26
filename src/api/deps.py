from __future__ import annotations

from fastapi import Request

from src.database import DatabaseManager
from src.manual_qc.snapshot.repository import SnapshotRepository
from src.manual_qc.snapshot.snapshot_service import SnapshotQueryService


def get_database_manager(request: Request) -> DatabaseManager:
    return request.app.state.database_manager


def get_snapshot_service(request: Request) -> SnapshotQueryService:
    manager = get_database_manager(request)
    return SnapshotQueryService(SnapshotRepository(manager.postgres()))
