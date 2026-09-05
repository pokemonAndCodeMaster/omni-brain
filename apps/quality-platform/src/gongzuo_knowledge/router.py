from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from src.gongzuo.models import WorkspaceKey

router=APIRouter(prefix='/api/gongzuo/{workspace}',tags=['gongzuo-knowledge'])


class CandidateCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title: str=Field(min_length=1,max_length=256)
    target: Literal['knowledge','skill','agent','harness']='knowledge'
    content: str=Field(min_length=1,max_length=200000)
    desiredBehavior: str=Field(min_length=1,max_length=10000)
    validationPlan: str=Field(min_length=1,max_length=20000)
    sourcePath: str | None=None
    baseVersion: str | None=None
    sourceItemId: str | None=None
    sourceEntityId: str | None=None


class VerificationCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    runId: str
    evidenceId: str
    result: Literal['accepted','rejected']
    assessment: str=Field(min_length=1,max_length=20000)


class PublicationCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    version: str=Field(min_length=1)


def call(request: Request, name: str, *args):
    try:
        return getattr(request.app.state.gongzuo_knowledge_service,name)(*args)
    except KeyError as exc:
        raise HTTPException(404,'找不到此工作区中的材料或候选') from exc
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


@router.get('/knowledge')
def catalog(request: Request, workspace: WorkspaceKey, q: str=Query('',max_length=200)):
    return call(request,'catalog',workspace,q)


@router.get('/knowledge/document')
def document(request: Request, workspace: WorkspaceKey, path: str=Query(min_length=1,max_length=2000)):
    return call(request,'document',workspace,path)


@router.get('/capabilities')
def candidates(request: Request, workspace: WorkspaceKey):
    service=request.app.state.gongzuo_knowledge_service
    return {'items':service.repository.list(workspace)}


@router.get('/capabilities/{candidate_id}')
def candidate(request: Request, workspace: WorkspaceKey, candidate_id: str):
    try: return request.app.state.gongzuo_knowledge_service.repository.get(workspace,candidate_id)
    except KeyError as exc: raise HTTPException(404,'候选不存在') from exc


@router.post('/knowledge/proposals',status_code=201)
@router.post('/capabilities',status_code=201)
def create(request: Request, workspace: WorkspaceKey, body: CandidateCreate):
    return call(request,'create',workspace,body.model_dump(),'admin')


@router.post('/capabilities/{candidate_id}/verify')
def verify(request: Request, workspace: WorkspaceKey, candidate_id: str, body: VerificationCreate):
    return call(request,'verify',workspace,candidate_id,body.model_dump(),'admin')


@router.post('/capabilities/{candidate_id}/publish')
def publish(request: Request, workspace: WorkspaceKey, candidate_id: str, body: PublicationCreate):
    return call(request,'publish',workspace,candidate_id,body.version,'admin')
