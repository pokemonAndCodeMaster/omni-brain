from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.config = config
        app.state.database_manager = database_manager
        database_manager.postgres().open()
        yield
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
        allow_methods=["GET", "PUT"],
        allow_headers=["*"],
    )
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
