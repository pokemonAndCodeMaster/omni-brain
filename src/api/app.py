from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.agent_runtime import (
    AgentRegistry,
    AgentRunRepository,
    AgentRunService,
    OpenCodeExecutor,
    WorktreeManager,
)
from src.api.routers.agent_runtime import router as agent_runtime_router
from src.api.routers.analysis import router as analysis_router
from src.api.routers.snapshot import router as snapshot_router
from src.api.routers.view_config import router as view_config_router
from src.api.schemas import HealthResponse
from src.config import ConfigManager
from src.database import DatabaseManager


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def create_app() -> FastAPI:
    root = project_root()
    config = ConfigManager(project_root=root)
    config.setup_logging()
    database_manager = DatabaseManager(config)

    def configured_path(key: str) -> Path:
        value = Path(str(config.get_nested(key, required=True)))
        return value.resolve() if value.is_absolute() else (root / value).resolve()

    opencode_config = config.get_nested("agent_runtime.opencode", {})
    agent_run_service = AgentRunService(
        repository=AgentRunRepository(database_manager.postgres()),
        registry=AgentRegistry(configured_path("agent_runtime.registry_path")),
        worktrees=WorktreeManager(configured_path("agent_runtime.worktree_root")),
        executor=OpenCodeExecutor(
            command=str(opencode_config.get("command", "opencode")),
            endpoint=str(opencode_config.get("endpoint", "")),
        ),
        artifact_root=configured_path("agent_runtime.artifact_root"),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.config = config
        app.state.database_manager = database_manager
        app.state.agent_run_service = agent_run_service
        database_manager.postgres().open()
        agent_run_service.recover()
        yield
        await agent_run_service.shutdown()
        database_manager.close()

    app = FastAPI(
        title=str(config.get_nested("app.name", "Quality Platform Lab")),
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["*"],
    )
    app.include_router(analysis_router)
    app.include_router(agent_runtime_router)
    app.include_router(snapshot_router)
    app.include_router(view_config_router)

    @app.get("/api/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        manager: DatabaseManager = request.app.state.database_manager
        result = manager.postgres().health_check()
        return HealthResponse(
            status="ok",
            app=str(config.get_nested("app.name", "Quality Platform Lab")),
            schema_version=str(
                config.get_nested(
                    "app.schema_version",
                    "snapshot-jsonb-v20260709",
                )
            ),
            database_alias=result.alias,
            database=result.database,
            postgres_version=result.server_version,
        )

    return app
