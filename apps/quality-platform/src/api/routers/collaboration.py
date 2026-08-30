from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from src.api.deps import get_actor_id, get_collaboration_service
from src.api.schemas.agent_runtime import AgentRunOut
from src.api.schemas.collaboration import (
    AgentActionCreate,
    Commitment,
    IdeaConvertToRequirement,
    IdeaCreate,
    IdeaListOut,
    IdeaOut,
    IdeaStatus,
    MessageCreate,
    RequirementCreate,
    RequirementDecisionCreate,
    RequirementDecisionOut,
    RequirementListOut,
    RequirementOut,
    RequirementRevisionCreate,
    RequirementRevisionOut,
    RequirementStatus,
    ThreadEntryOut,
    TimelinePageOut,
)
from src.collaboration import CollaborationService


router = APIRouter(tags=["collaboration"])
Service = Annotated[CollaborationService, Depends(get_collaboration_service)]
Actor = Annotated[str, Depends(get_actor_id)]


def _not_found(kind: str, object_id: str, exc: KeyError) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{kind} 不存在：{object_id}")


@router.get("/api/ideas", response_model=IdeaListOut)
def list_ideas(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
    idea_status: Annotated[list[IdeaStatus] | None, Query(alias="status")] = None,
) -> IdeaListOut:
    rows, total = service.repository.list_ideas(
        limit=limit,
        offset=offset,
        statuses=idea_status or (),
    )
    return IdeaListOut(items=rows, total=total, limit=limit, offset=offset)


@router.post(
    "/api/ideas",
    response_model=IdeaOut,
    status_code=status.HTTP_201_CREATED,
)
def create_idea(payload: IdeaCreate, service: Service, actor_id: Actor) -> dict:
    return service.create_idea(**payload.model_dump(), actor_id=actor_id)


@router.get("/api/ideas/{idea_id}", response_model=IdeaOut)
def get_idea(idea_id: str, service: Service) -> dict:
    try:
        return service.idea(idea_id)
    except KeyError as exc:
        raise _not_found("Idea", idea_id, exc) from exc


@router.post("/api/ideas/{idea_id}/messages", response_model=ThreadEntryOut)
def add_idea_message(
    idea_id: str,
    payload: MessageCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return service.repository.add_message(
            subject_type="idea",
            subject_id=idea_id,
            body=payload.body,
            actor_id=actor_id,
        )
    except KeyError as exc:
        raise _not_found("Idea", idea_id, exc) from exc


@router.get("/api/ideas/{idea_id}/timeline", response_model=TimelinePageOut)
def idea_timeline(
    idea_id: str,
    service: Service,
    cursor: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> TimelinePageOut:
    try:
        rows, next_cursor = service.repository.timeline(
            subject_type="idea",
            subject_id=idea_id,
            cursor=cursor,
            limit=limit,
        )
    except KeyError as exc:
        raise _not_found("Idea", idea_id, exc) from exc
    return TimelinePageOut(items=rows, next_cursor=next_cursor)


@router.post(
    "/api/ideas/{idea_id}/agent-actions",
    response_model=AgentRunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_idea_action(
    idea_id: str,
    payload: AgentActionCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return await service.start_action(
            subject_type="idea",
            subject_id=idea_id,
            actor_id=actor_id,
            **payload.model_dump(),
        )
    except KeyError as exc:
        raise _not_found("Idea", idea_id, exc) from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/api/ideas/{idea_id}/convert-to-requirement",
    response_model=RequirementOut,
)
def convert_idea(
    idea_id: str,
    payload: IdeaConvertToRequirement,
    response: Response,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        result, created = service.create_requirement(
            **payload.model_dump(),
            actor_id=actor_id,
            source_idea_id=idea_id,
        )
    except KeyError as exc:
        raise _not_found("Idea", idea_id, exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return result


@router.post("/api/ideas/{idea_id}/archive", response_model=IdeaOut)
def archive_idea(idea_id: str, service: Service) -> dict:
    try:
        return service.archive_idea(idea_id)
    except KeyError as exc:
        raise _not_found("Idea", idea_id, exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/api/requirements", response_model=RequirementListOut)
def list_requirements(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
    requirement_status: Annotated[
        list[RequirementStatus] | None,
        Query(alias="status"),
    ] = None,
    commitment: Annotated[list[Commitment] | None, Query()] = None,
    query: Annotated[str | None, Query(max_length=256)] = None,
) -> RequirementListOut:
    rows, total = service.repository.list_requirements(
        limit=limit,
        offset=offset,
        statuses=requirement_status or (),
        commitments=commitment or (),
        query=query,
    )
    return RequirementListOut(items=rows, total=total, limit=limit, offset=offset)


@router.post(
    "/api/requirements",
    response_model=RequirementOut,
    status_code=status.HTTP_201_CREATED,
)
def create_requirement(
    payload: RequirementCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        result, _ = service.create_requirement(
            **payload.model_dump(),
            actor_id=actor_id,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/requirements/{requirement_id}", response_model=RequirementOut)
def get_requirement(requirement_id: str, service: Service) -> dict:
    try:
        return service.requirement(requirement_id)
    except KeyError as exc:
        raise _not_found("Requirement", requirement_id, exc) from exc


@router.get(
    "/api/requirements/{requirement_id}/revisions",
    response_model=list[RequirementRevisionOut],
)
def list_requirement_revisions(
    requirement_id: str,
    service: Service,
    include_content: bool = False,
) -> list[dict]:
    try:
        return service.repository.list_revisions(
            requirement_id,
            include_content=include_content,
        )
    except KeyError as exc:
        raise _not_found("Requirement", requirement_id, exc) from exc


@router.post(
    "/api/requirements/{requirement_id}/revisions",
    response_model=RequirementRevisionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_requirement_revision(
    requirement_id: str,
    payload: RequirementRevisionCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return service.add_revision(
            requirement_id=requirement_id,
            actor_id=actor_id,
            **payload.model_dump(),
        )
    except KeyError as exc:
        raise _not_found("Requirement", requirement_id, exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/api/requirements/{requirement_id}/messages",
    response_model=ThreadEntryOut,
)
def add_requirement_message(
    requirement_id: str,
    payload: MessageCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return service.repository.add_message(
            subject_type="requirement",
            subject_id=requirement_id,
            body=payload.body,
            actor_id=actor_id,
        )
    except KeyError as exc:
        raise _not_found("Requirement", requirement_id, exc) from exc


@router.get(
    "/api/requirements/{requirement_id}/timeline",
    response_model=TimelinePageOut,
)
def requirement_timeline(
    requirement_id: str,
    service: Service,
    cursor: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> TimelinePageOut:
    try:
        rows, next_cursor = service.repository.timeline(
            subject_type="requirement",
            subject_id=requirement_id,
            cursor=cursor,
            limit=limit,
        )
    except KeyError as exc:
        raise _not_found("Requirement", requirement_id, exc) from exc
    return TimelinePageOut(items=rows, next_cursor=next_cursor)


@router.post(
    "/api/requirements/{requirement_id}/agent-actions",
    response_model=AgentRunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_requirement_action(
    requirement_id: str,
    payload: AgentActionCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        return await service.start_action(
            subject_type="requirement",
            subject_id=requirement_id,
            actor_id=actor_id,
            **payload.model_dump(),
        )
    except KeyError as exc:
        raise _not_found("Requirement", requirement_id, exc) from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/api/requirements/{requirement_id}/decisions",
    response_model=RequirementDecisionOut,
    status_code=status.HTTP_201_CREATED,
)
def decide_requirement(
    requirement_id: str,
    payload: RequirementDecisionCreate,
    service: Service,
    actor_id: Actor,
) -> dict:
    try:
        decision, _ = service.decide(
            requirement_id=requirement_id,
            actor_id=actor_id,
            **payload.model_dump(),
        )
        return decision
    except KeyError as exc:
        raise _not_found("Requirement", requirement_id, exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
