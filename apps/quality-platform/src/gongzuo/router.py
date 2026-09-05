from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import PlainTextResponse

from src.api.deps import get_actor_id

from .models import (ActivityCreate, ContextProposalCreate, ContextResolve, DiscussionCreate, EntityCreate, EntityUpdate, EvidenceCreate, EvidenceReview, ItemCreate, ItemUpdate, MeetingConfigUpdate, MeetingNoteCreate, PreferenceUpdate, RelationCreate)
from .repository import ConcurrentUpdateError
from .service import GongzuoService

router = APIRouter(prefix='/api/gongzuo/{workspace}', tags=['gongzuo'])
Actor = Annotated[str, Depends(get_actor_id)]


def service(request: Request) -> GongzuoService:
    return request.app.state.gongzuo_service


Service = Annotated[GongzuoService, Depends(service)]


def _fail(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError): return HTTPException(404, detail=f'对象不存在：{exc.args[0]}')
    if isinstance(exc, ConcurrentUpdateError): return HTTPException(409, detail=str(exc))
    return HTTPException(400, detail=str(exc))


@router.get('/state')
def get_state(workspace: str, service: Service) -> dict[str,Any]:
    try: return service.get_state(workspace)
    except ValueError as exc: raise _fail(exc) from exc


@router.get('/items')
def list_items(workspace:str,service:Service,query:str|None=None,status_filter:Annotated[str|None,Query(alias='status')]=None,item_type:Annotated[str|None,Query(alias='itemType')]=None,limit:Annotated[int,Query(ge=1,le=1000)]=100,offset:Annotated[int,Query(ge=0)]=0)->dict[str,Any]:
    try:
        items,total=service.list_items(workspace,query=query,status=status_filter,item_type=item_type,limit=limit,offset=offset)
        return {'items':items,'total':total,'limit':limit,'offset':offset}
    except ValueError as exc: raise _fail(exc) from exc


@router.post('/items',status_code=status.HTTP_201_CREATED)
def create_item(workspace:str,payload:ItemCreate,service:Service,actor_id:Actor)->dict[str,Any]:
    try: return service.create_item(workspace,actor_id=actor_id,**payload.model_dump())
    except ValueError as exc: raise _fail(exc) from exc


@router.get('/items/{item_id}')
def get_item(workspace:str,item_id:str,service:Service)->dict[str,Any]:
    try:
        item=service.get_item(workspace,item_id)
        return {**item,'relations':service.repository.list_relations(workspace,item_id),'discussions':service.repository.list_discussions(workspace,item_id=item_id),'context':service.repository.context(workspace,item_id),'contextProposals':service.repository.list_proposals(workspace,item_id),'evidence':service.repository.list_evidence(workspace,item_id),'activity':service.repository.list_activities(workspace,item_id)}
    except (KeyError,ValueError) as exc: raise _fail(exc) from exc


@router.patch('/items/{item_id}')
def update_item(workspace:str,item_id:str,payload:ItemUpdate,service:Service,actor_id:Actor)->dict[str,Any]:
    try: return service.update_item(workspace,item_id,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc: raise _fail(exc) from exc


@router.post('/items/{item_id}/accept')
def accept_item(workspace:str,item_id:str,payload:ContextResolve,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.accept_item(workspace,item_id,version=payload.version,actor_id=actor_id)
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/entities',status_code=status.HTTP_201_CREATED)
def create_entity(workspace:str,payload:EntityCreate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.create_entity(workspace,actor_id=actor_id,**payload.model_dump())
    except ValueError as exc:raise _fail(exc) from exc


@router.get('/entities')
def list_entities(workspace:str,service:Service,entity_type:Annotated[str|None,Query(alias='entityType')]=None)->list[dict[str,Any]]:
    try:return service.repository.list_entities(service._workspace(workspace),entity_type)
    except ValueError as exc:raise _fail(exc) from exc


@router.patch('/entities/{entity_id}')
def update_entity(workspace:str,entity_id:str,payload:EntityUpdate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.update_entity(workspace,entity_id,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.get('/entities/{entity_id}')
def get_entity(workspace:str,entity_id:str,service:Service)->dict[str,Any]:
    try:
        entity=service.repository.get_entity(service._workspace(workspace),entity_id)
        if entity is None: raise KeyError(entity_id)
        return {**entity,'relations':service.repository.list_relations(workspace,entity_id),'discussions':service.repository.list_discussions(workspace,entity_id=entity_id)}
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/relations',status_code=status.HTTP_201_CREATED)
def create_relation(workspace:str,payload:RelationCreate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.create_relation(workspace,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.delete('/relations/{relation_id}',status_code=status.HTTP_204_NO_CONTENT)
def delete_relation(workspace:str,relation_id:str,service:Service)->Response:
    try:
        service.delete_relation(workspace,relation_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/items/{item_id}/discussions',status_code=status.HTTP_201_CREATED)
def item_discussion(workspace:str,item_id:str,payload:DiscussionCreate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.add_discussion(workspace,item_id=item_id,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/entities/{entity_id}/discussions',status_code=status.HTTP_201_CREATED)
def entity_discussion(workspace:str,entity_id:str,payload:DiscussionCreate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.add_discussion(workspace,entity_id=entity_id,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/items/{item_id}/context',status_code=status.HTTP_201_CREATED)
def create_context(workspace:str,item_id:str,payload:dict[str,Any],service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.create_context(workspace,item_id,content=payload.get('content',{}),provenance=payload.get('provenance',[]),actor_id=actor_id)
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.get('/items/{item_id}/context/history')
def context_history(workspace:str,item_id:str,service:Service)->list[dict[str,Any]]:
    try:return service.context_history(workspace,item_id)
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/items/{item_id}/context/proposals',status_code=status.HTTP_201_CREATED)
def propose_context(workspace:str,item_id:str,payload:ContextProposalCreate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.propose_context(workspace,item_id,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/context-proposals/{proposal_id}/accept')
def accept_proposal(workspace:str,proposal_id:str,payload:ContextResolve,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.resolve_context_proposal(workspace,proposal_id,version=payload.version,accepted=True,reason=payload.reason,actor_id=actor_id)
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/context-proposals/{proposal_id}/reject')
def reject_proposal(workspace:str,proposal_id:str,payload:ContextResolve,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.resolve_context_proposal(workspace,proposal_id,version=payload.version,accepted=False,reason=payload.reason,actor_id=actor_id)
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/items/{item_id}/evidence',status_code=status.HTTP_201_CREATED)
def add_evidence(workspace:str,item_id:str,payload:EvidenceCreate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.add_evidence(workspace,item_id,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/evidence/{evidence_id}/review')
def review_evidence(workspace:str,evidence_id:str,payload:EvidenceReview,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.review_evidence(workspace,evidence_id,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/items/{item_id}/activity',status_code=status.HTTP_201_CREATED)
def add_activity(workspace:str,item_id:str,payload:ActivityCreate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.append_activity(workspace,item_id,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.put('/preferences/{key}')
def save_preference(workspace:str,key:str,payload:PreferenceUpdate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.save_preference(workspace,key,actor_id=actor_id,**payload.model_dump())
    except ValueError as exc:raise _fail(exc) from exc


@router.get('/meeting')
def get_meeting(workspace:str,service:Service)->dict[str,Any]:
    try:
        meeting=service.repository.meeting(service._workspace(workspace))
        if meeting is None: raise KeyError('meeting')
        return meeting
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.get('/meeting/preview')
def preview_meeting(workspace:str,service:Service)->dict[str,Any]:
    try:return service.meeting_projection(workspace)
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.put('/meeting')
def save_meeting(workspace:str,payload:MeetingConfigUpdate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.save_meeting(workspace,actor_id=actor_id,**payload.model_dump())
    except ValueError as exc:raise _fail(exc) from exc


@router.post('/meeting/freeze',status_code=status.HTTP_201_CREATED)
def freeze_meeting(workspace:str,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.freeze_meeting(workspace,actor_id=actor_id)
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.get('/meeting/snapshots/{snapshot_id}')
def get_meeting_snapshot(workspace:str,snapshot_id:str,service:Service)->dict[str,Any]:
    try:
        snapshot=service.repository.meeting_snapshot(service._workspace(workspace),snapshot_id)
        if snapshot is None: raise KeyError(snapshot_id)
        return snapshot
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.post('/meeting/notes',status_code=status.HTTP_201_CREATED)
def add_meeting_note(workspace:str,payload:MeetingNoteCreate,service:Service,actor_id:Actor)->dict[str,Any]:
    try:return service.add_meeting_note(workspace,actor_id=actor_id,**payload.model_dump())
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc


@router.get('/meeting/markdown',response_class=PlainTextResponse)
def export_meeting(workspace:str,service:Service,snapshot_id:Annotated[str|None,Query(alias='snapshotId')]=None)->str:
    try:return service.export_meeting_markdown(workspace,snapshot_id)
    except (KeyError,ValueError) as exc:raise _fail(exc) from exc
