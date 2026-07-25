from __future__ import annotations

from fastapi import Request

from ..database import DatabaseManager
from ..manual_qc.acceptance.repository import SnapshotRepository
from ..manual_qc.acceptance.service import SnapshotQueryService


def get_database_manager(request: Request) -> DatabaseManager:
    return request.app.state.database_manager


def get_snapshot_service(request: Request) -> SnapshotQueryService:
    manager = get_database_manager(request)
    return SnapshotQueryService(SnapshotRepository(manager.postgres()))
