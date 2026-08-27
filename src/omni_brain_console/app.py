from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .executors import CliExecutor
from .judge import JudgeService
from .registry import AgentRegistry
from .service import TERMINAL_STATES, WorkbenchService
from .settings import FRONTEND_DIST, PROJECT_ROOT, REGISTRY_PATH, RUN_SITES_ROOT, STATE_ROOT
from .storage import RunStore
from .worktrees import WorktreeManager


class StartRunRequest(BaseModel):
    agent_id: str
    prompt: str = ""
    executor: str | None = None
    model: str | None = None
    eval_case_id: str | None = None


class ResumeRunRequest(BaseModel):
    prompt: str = Field(min_length=1)


class EvaluateRunRequest(BaseModel):
    model: str | None = None


class CommitRunRequest(BaseModel):
    message: str = Field(min_length=1, max_length=160)


class StartEvolutionRequest(BaseModel):
    agent_id: str
    prompt: str = ""
    eval_case_id: str | None = None
    executor: str | None = None
    model: str | None = None
    judge_model: str | None = None
    max_iterations: int = Field(default=1, ge=1, le=3)


def create_service(
    *,
    project_root: Path = PROJECT_ROOT,
    registry_path: Path = REGISTRY_PATH,
    state_root: Path = STATE_ROOT,
    run_sites_root: Path = RUN_SITES_ROOT,
    executor: CliExecutor | None = None,
    judge: JudgeService | None = None,
) -> WorkbenchService:
    store = RunStore(state_root)
    return WorkbenchService(
        registry=AgentRegistry(project_root, registry_path),
        store=store,
        worktrees=WorktreeManager(run_sites_root),
        executor=executor,
        judge=judge,
    )


def create_app(service: WorkbenchService | None = None, frontend_dist: Path = FRONTEND_DIST) -> FastAPI:
    app = FastAPI(title="Omni-Brain Agent Workbench", version="0.1.0")
    workbench = service or create_service()
    app.state.workbench = workbench

    def translate_error(exc: Exception) -> HTTPException:
        if isinstance(exc, KeyError):
            return HTTPException(status_code=404, detail=f"未找到：{exc.args[0]}")
        if isinstance(exc, (ValueError, RuntimeError, FileExistsError)):
            return HTTPException(status_code=409, detail=str(exc))
        return HTTPException(status_code=500, detail=str(exc))

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "mode": "local-single-run", "isolation": "git-worktree"}

    @app.get("/api/agents")
    async def agents() -> list[dict[str, Any]]:
        try:
            return workbench.agents()
        except Exception as exc:
            raise translate_error(exc) from exc

    @app.get("/api/eval-cases")
    async def eval_cases() -> list[dict[str, Any]]:
        return workbench.registry.list_eval_cases()

    @app.get("/api/trials")
    async def archived_trials() -> list[dict[str, Any]]:
        return workbench.registry.list_archived_trials()

    @app.get("/api/runs")
    async def runs() -> list[dict[str, Any]]:
        return workbench.store.list_runs()

    @app.post("/api/runs", status_code=202)
    async def start_run(request: StartRunRequest) -> dict[str, Any]:
        try:
            return await workbench.start_run(**request.model_dump())
        except Exception as exc:
            raise translate_error(exc) from exc

    @app.get("/api/runs/{run_id}")
    async def run_detail(run_id: str) -> dict[str, Any]:
        try:
            return workbench.run_detail(run_id)
        except Exception as exc:
            raise translate_error(exc) from exc

    @app.get("/api/runs/{run_id}/events")
    async def run_events(run_id: str, after: int = Query(0, ge=0)) -> list[dict[str, Any]]:
        if not workbench.store.get_run(run_id):
            raise HTTPException(status_code=404, detail="Run 不存在")
        return workbench.store.events(run_id, after)

    @app.get("/api/runs/{run_id}/events/stream")
    async def run_event_stream(run_id: str, after: int = Query(0, ge=0)) -> StreamingResponse:
        if not workbench.store.get_run(run_id):
            raise HTTPException(status_code=404, detail="Run 不存在")

        async def stream() -> AsyncIterator[str]:
            cursor = after
            idle = 0
            while True:
                events = workbench.store.events(run_id, cursor)
                for event in events:
                    cursor = max(cursor, int(event.get("seq", cursor)))
                    yield f"event: trace\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                run = workbench.store.get_run(run_id) or {}
                if run.get("status") in TERMINAL_STATES and not events:
                    idle += 1
                    if idle >= 2:
                        yield f"event: done\ndata: {json.dumps(run, ensure_ascii=False)}\n\n"
                        return
                else:
                    idle = 0
                yield ": keepalive\n\n"
                await asyncio.sleep(1)

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.post("/api/runs/{run_id}/stop")
    async def stop_run(run_id: str) -> dict[str, Any]:
        try:
            return await workbench.stop_run(run_id)
        except Exception as exc:
            raise translate_error(exc) from exc

    @app.post("/api/runs/{run_id}/resume", status_code=202)
    async def resume_run(run_id: str, request: ResumeRunRequest) -> dict[str, Any]:
        try:
            return await workbench.resume_run(run_id, request.prompt)
        except Exception as exc:
            raise translate_error(exc) from exc

    @app.post("/api/runs/{run_id}/evaluate", status_code=202)
    async def evaluate_run(run_id: str, request: EvaluateRunRequest) -> dict[str, Any]:
        try:
            return await workbench.evaluate_run(run_id, request.model)
        except Exception as exc:
            raise translate_error(exc) from exc

    @app.post("/api/runs/{run_id}/commit")
    async def commit_run(run_id: str, request: CommitRunRequest) -> dict[str, Any]:
        try:
            return await workbench.commit_run(run_id, request.message)
        except Exception as exc:
            raise translate_error(exc) from exc

    @app.post("/api/runs/{run_id}/release-worktree")
    async def release_worktree(run_id: str) -> dict[str, Any]:
        try:
            return await workbench.release_worktree(run_id)
        except Exception as exc:
            raise translate_error(exc) from exc

    @app.get("/api/evolutions")
    async def evolutions() -> list[dict[str, Any]]:
        return workbench.store.list_evolutions()

    @app.get("/api/evolutions/{evolution_id}")
    async def evolution_detail(evolution_id: str) -> dict[str, Any]:
        record = workbench.store.get_evolution(evolution_id)
        if not record:
            raise HTTPException(status_code=404, detail="进化记录不存在")
        return record

    @app.post("/api/evolutions", status_code=202)
    async def start_evolution(request: StartEvolutionRequest) -> dict[str, Any]:
        try:
            return await workbench.start_evolution(**request.model_dump())
        except Exception as exc:
            raise translate_error(exc) from exc

    if frontend_dist.is_dir():
        assets = frontend_dist / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{full_path:path}")
        async def frontend(full_path: str) -> FileResponse:
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API 不存在")
            candidate = frontend_dist / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(frontend_dist / "index.html")

    return app


app = create_app()
