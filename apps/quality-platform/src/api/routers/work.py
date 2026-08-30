from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import get_actor_id, get_work_service
from src.api.schemas.work import (
    WorkCreate,
    WorkDecisionCreate,
    WorkDecisionOut,
    WorkEvidenceCreate,
    WorkEvidenceOut,
    WorkListOut,
    WorkOut,
    WorkRunOut,
    WorkStepComplete,
    WorkStepRunCreate,
    WorkUpdate,
)
from src.work import WorkService


router = APIRouter(tags=["work"])
Service = Annotated[WorkService, Depends(get_work_service)]
Actor = Annotated[str, Depends(get_actor_id)]
StatusFilter = Literal[
    "planned",
    "in_progress",
    "in_review",
    "revision_requested",
    "accepted",
    "cancelled",
]


def _raise_http(exc: Exception) -> None:
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail=f"业务对象不存在：{exc.args[0]}") from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/api/requirements/{requirement_id}/work",
    response_model=WorkOut,
    status_code=status.HTTP_201_CREATED,
)
def create_work(
    requirement_id: str,
    payload: WorkCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return service.create_for_requirement(
            requirement_id=requirement_id,
            payload=payload,
            actor_id=actor_id,
        )
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        _raise_http(exc)


@router.get("/api/works", response_model=WorkListOut)
def list_works(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
    work_status: Annotated[list[StatusFilter] | None, Query(alias="status")] = None,
) -> WorkListOut:
    rows, total = service.repository.list(
        limit=limit,
        offset=offset,
        statuses=work_status or (),
    )
    return WorkListOut(items=rows, total=total, limit=limit, offset=offset)


@router.get("/api/works/{work_id}", response_model=WorkOut)
def get_work(work_id: str, service: Service) -> dict:
    try:
        return service.detail(work_id)
    except KeyError as exc:
        _raise_http(exc)


@router.patch("/api/works/{work_id}", response_model=WorkOut)
def update_work(
    work_id: str,
    payload: WorkUpdate,
    service: Service,
) -> dict:
    try:
        return service.repository.update_metadata(
            work_id=work_id,
            changes=payload.model_dump(exclude_unset=True),
        )
    except (KeyError, ValueError) as exc:
        _raise_http(exc)


@router.post(
    "/api/works/{work_id}/steps/{step_id}/runs",
    response_model=WorkRunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_work_step(
    work_id: str,
    step_id: str,
    payload: WorkStepRunCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return await service.start_step(
            work_id=work_id,
            step_id=step_id,
            executor=payload.executor,
            model=payload.model,
            instruction=payload.instruction,
            actor_id=actor_id,
        )
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        _raise_http(exc)


@router.post(
    "/api/works/{work_id}/steps/{step_id}/complete",
    response_model=WorkOut,
)
def complete_work_step(
    work_id: str,
    step_id: str,
    payload: WorkStepComplete,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return service.repository.complete_step(
            work_id=work_id,
            step_id=step_id,
            note=payload.note,
            actor_id=actor_id,
        )
    except (KeyError, ValueError) as exc:
        _raise_http(exc)


@router.post("/api/works/{work_id}/evidence", response_model=WorkEvidenceOut)
def record_work_evidence(
    work_id: str,
    payload: WorkEvidenceCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return service.record_evidence(
            work_id=work_id,
            payload=payload,
            actor_id=actor_id,
        )
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        _raise_http(exc)


@router.post("/api/works/{work_id}/decisions", response_model=WorkDecisionOut)
def decide_work(
    work_id: str,
    payload: WorkDecisionCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return service.decide(
            work_id=work_id,
            decision_type=payload.decision_type,
            reason=payload.reason,
            actor_id=actor_id,
        )
    except (KeyError, ValueError) as exc:
        _raise_http(exc)
