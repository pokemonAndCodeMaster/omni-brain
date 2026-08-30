from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.agent_runtime import AgentRunService
from src.api.deps import get_actor_id, get_agent_run_service
from src.api.schemas.agent_runtime import (
    AgentOut,
    AgentSummaryOut,
    AgentRunCreate,
    AgentRunEventListOut,
    AgentRunListOut,
    AgentRunOut,
    AgentRuntimeHealthOut,
)


router = APIRouter(tags=["agent-runtime"])
Service = Annotated[AgentRunService, Depends(get_agent_run_service)]
Actor = Annotated[str, Depends(get_actor_id)]
StatusFilter = Literal["queued", "running", "succeeded", "failed", "cancelled"]


@router.get("/api/agents", response_model=list[AgentSummaryOut])
def list_agents(service: Service) -> list[dict]:
    return service.agents()


@router.post("/api/agents/refresh", response_model=list[AgentSummaryOut])
def refresh_agents(service: Service) -> list[dict]:
    return service.agents(refresh=True)


@router.get("/api/agents/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str, service: Service) -> dict:
    try:
        return service.agent(agent_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"未登记 Agent：{agent_id}") from exc


@router.get("/api/agent-runtime/health", response_model=AgentRuntimeHealthOut)
def agent_runtime_health(service: Service) -> dict:
    return service.executor_health()


@router.get("/api/agent-runs", response_model=AgentRunListOut)
def list_agent_runs(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
    agent_id: str | None = None,
    executor: Literal["codex", "opencode"] | None = None,
    subject_type: Literal["idea", "requirement", "work"] | None = None,
    subject_id: str | None = None,
    run_status: Annotated[list[StatusFilter] | None, Query(alias="status")] = None,
) -> AgentRunListOut:
    rows, total = service.repository.list(
        limit=limit,
        offset=offset,
        agent_id=agent_id,
        executor=executor,
        subject_type=subject_type,
        subject_id=subject_id,
        statuses=run_status or (),
    )
    return AgentRunListOut(items=rows, total=total, limit=limit, offset=offset)


@router.post(
    "/api/agent-runs",
    response_model=AgentRunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_agent_run(
    payload: AgentRunCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return await service.start(**payload.model_dump(), actor_id=actor_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"未登记 Agent：{payload.agent_id}") from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/agent-runs/{run_id}", response_model=AgentRunOut)
def get_agent_run(run_id: str, service: Service) -> dict:
    row = service.repository.get(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run 不存在：{run_id}")
    return row


@router.get(
    "/api/agent-runs/{run_id}/events",
    response_model=AgentRunEventListOut,
)
def list_agent_run_events(
    run_id: str,
    service: Service,
    after_sequence: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> AgentRunEventListOut:
    if service.repository.get(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Run 不存在：{run_id}")
    rows = service.repository.events(
        run_id,
        after_sequence=after_sequence,
        limit=limit,
    )
    next_sequence = int(rows[-1]["sequence"]) if rows else after_sequence
    return AgentRunEventListOut(items=rows, next_sequence=next_sequence)


@router.post("/api/agent-runs/{run_id}/cancel", response_model=AgentRunOut)
async def cancel_agent_run(run_id: str, service: Service) -> dict:
    try:
        return await service.cancel(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Run 不存在：{run_id}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
