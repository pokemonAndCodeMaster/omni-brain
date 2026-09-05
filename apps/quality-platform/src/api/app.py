from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.agent_runtime import (
    AgentRegistry,
    AgentRunRepository,
    AgentRunService,
    CodexExecutor,
    OpenCodeExecutor,
    WorktreeManager,
)
from src.api.routers.agent_runtime import router as agent_runtime_router
from src.api.routers.analysis import router as analysis_router
from src.api.routers.collaboration import router as collaboration_router
from src.api.routers.snapshot import router as snapshot_router
from src.api.routers.view_config import router as view_config_router
from src.api.routers.work import router as work_router
from src.api.schemas import HealthResponse
from src.config import ConfigManager
from src.collaboration import CollaborationRepository, CollaborationService
from src.database import DatabaseManager
from src.work import WorkRepository, WorkService
from src.gongzuo import GongzuoRepository, GongzuoService
from src.gongzuo.router import router as gongzuo_router
from src.gongzuo_knowledge import GongzuoKnowledgeRepository, GongzuoKnowledgeService
from src.gongzuo_knowledge.router import router as gongzuo_knowledge_router
from src.gongzuo_runtime.repository import GongzuoRuntimeRepository
from src.gongzuo_runtime.service import GongzuoRuntimeService
from src.gongzuo_runtime.models import RunOut
from src.gongzuo_runtime.router import router as gongzuo_runtime_router


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
    codex_config = config.get_nested("agent_runtime.codex", {})
    agent_run_service = AgentRunService(
        repository=AgentRunRepository(database_manager.postgres()),
        registry=AgentRegistry(configured_path("agent_runtime.registry_path")),
        worktrees=WorktreeManager(configured_path("agent_runtime.worktree_root")),
        executors={
            "codex": CodexExecutor(
                command=str(codex_config.get("command", "codex")),
            ),
            "opencode": OpenCodeExecutor(
                command=str(opencode_config.get("command", "opencode")),
                endpoint=str(opencode_config.get("endpoint", "")),
            ),
        },
        artifact_root=configured_path("agent_runtime.artifact_root"),
    )
    collaboration_service = CollaborationService(
        repository=CollaborationRepository(database_manager.postgres()),
        run_service=agent_run_service,
        run_repository=agent_run_service.repository,
    )
    work_service = WorkService(
        repository=WorkRepository(database_manager.postgres()),
        run_service=agent_run_service,
        worktrees=agent_run_service.worktrees,
    )
    gongzuo_service = GongzuoService(GongzuoRepository(database_manager.postgres()))
    personal_knowledge_root = configured_path('gongzuo.knowledge_roots.personal')
    personal_knowledge_root.mkdir(parents=True, exist_ok=True)
    team_knowledge_root = configured_path('gongzuo.knowledge_roots.team')
    enabled_workspaces = [key.strip() for key in str(config.get_nested('gongzuo.workspaces','personal,team')).split(',') if key.strip()]
    if not enabled_workspaces or set(enabled_workspaces) - {'personal','team'}:
        raise ValueError('GONGZUO_WORKSPACES 只支持 personal、team 或 personal,team')
    gongzuo_knowledge_service = GongzuoKnowledgeService(
        GongzuoKnowledgeRepository(database_manager.postgres()),
        roots={'personal':personal_knowledge_root, 'team':team_knowledge_root},
        gongzuo_service=gongzuo_service,
    )
    gongzuo_runtime_service = GongzuoRuntimeService(
        repository=GongzuoRuntimeRepository(database_manager.postgres()),
        gongzuo_service=gongzuo_service,
        executors=agent_run_service.executors,
        runtime_root=root / '.runtime/gongzuo',
        repository_root=root.parents[1],
        registration_tokens=config.get_nested('gongzuo.registration_tokens',{}),
        capability_provider=gongzuo_knowledge_service.published_context,
    )
    gongzuo_knowledge_service.run_reader = lambda workspace, run_id: RunOut.model_validate(
        gongzuo_runtime_service.get_run(workspace,run_id)
    ).model_dump(by_alias=True,mode='json')

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.config = config
        app.state.database_manager = database_manager
        app.state.agent_run_service = agent_run_service
        app.state.collaboration_service = collaboration_service
        app.state.work_service = work_service
        app.state.gongzuo_service = gongzuo_service
        app.state.gongzuo_knowledge_service = gongzuo_knowledge_service
        app.state.gongzuo_runtime_service = gongzuo_runtime_service
        database_manager.postgres().open()
        agent_run_service.recover()
        gongzuo_runtime_service.recover_expired_leases()
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
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    app.include_router(analysis_router)
    app.include_router(agent_runtime_router)
    app.include_router(collaboration_router)
    app.include_router(snapshot_router)
    app.include_router(view_config_router)
    app.include_router(work_router)
    app.include_router(gongzuo_router)
    app.include_router(gongzuo_knowledge_router)
    app.include_router(gongzuo_runtime_router)

    @app.middleware('http')
    async def workspace_boundary(request: Request, call_next):
        parts=request.url.path.split('/')
        if len(parts)>3 and parts[1:3]==['api','gongzuo'] and parts[3] in {'personal','team'} and parts[3] not in enabled_workspaces:
            return JSONResponse(status_code=404,content={'detail':'此部署不提供该工作区'})
        return await call_next(request)

    @app.get('/api/gongzuo/config')
    def gongzuo_config():
        return {'workspaces':enabled_workspaces,'defaultWorkspace':enabled_workspaces[0],'identityMode':'local-admin'}

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
