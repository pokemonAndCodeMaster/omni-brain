from __future__ import annotations

from fastapi import Request

from src.database import DatabaseManager
from src.manual_qc.analysis import AnalysisQueryService, AnalysisRepository
from src.manual_qc.snapshot.repository import SnapshotRepository
from src.manual_qc.snapshot.snapshot_service import SnapshotQueryService
from src.portal.view_config import ViewConfigRepository, ViewConfigService


def get_database_manager(request: Request) -> DatabaseManager:
    return request.app.state.database_manager


def get_snapshot_service(request: Request) -> SnapshotQueryService:
    manager = get_database_manager(request)
    return SnapshotQueryService(SnapshotRepository(manager.postgres()))


def get_analysis_service(request: Request) -> AnalysisQueryService:
    manager = get_database_manager(request)
    return AnalysisQueryService(AnalysisRepository(manager.postgres()))


def get_view_config_service(request: Request) -> ViewConfigService:
    manager = get_database_manager(request)
    return ViewConfigService(ViewConfigRepository(manager.postgres()))
