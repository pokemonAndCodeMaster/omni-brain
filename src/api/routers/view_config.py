from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from src.api.deps import get_view_config_service
from src.api.schemas.view_config import (
    DashboardConfig,
    DashboardConfigResponse,
    DataWorkbenchConfig,
    DataWorkbenchConfigResponse,
)
from src.portal.view_config import ViewConfigService


router = APIRouter(prefix="/api/view-configs", tags=["portal-view-configs"])
ViewConfig = Annotated[ViewConfigService, Depends(get_view_config_service)]
PageKey = Annotated[str, Path(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")]


@router.get(
    "/dashboard/{page_key}",
    response_model=DashboardConfigResponse,
    responses={204: {"description": "尚未保存个人看板"}},
)
def get_dashboard(
    page_key: PageKey,
    service: ViewConfig,
) -> DashboardConfigResponse | Response:
    row = service.get_dashboard(page_key)
    if row is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return DashboardConfigResponse.model_validate(row)


@router.put(
    "/dashboard/{page_key}",
    response_model=DashboardConfigResponse,
)
def save_dashboard(
    page_key: PageKey,
    payload: DashboardConfig,
    service: ViewConfig,
) -> DashboardConfigResponse:
    try:
        row = service.save_dashboard(
            page_key,
            payload.model_dump(mode="json", by_alias=True),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return DashboardConfigResponse.model_validate(row)


@router.get(
    "/data-workbench/{page_key}",
    response_model=DataWorkbenchConfigResponse,
    responses={204: {"description": "尚未保存数据工作台配置"}},
)
def get_data_workbench(
    page_key: PageKey,
    service: ViewConfig,
) -> DataWorkbenchConfigResponse | Response:
    row = service.get_data_workbench(page_key)
    if row is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return DataWorkbenchConfigResponse.model_validate(row)


@router.put(
    "/data-workbench/{page_key}",
    response_model=DataWorkbenchConfigResponse,
)
def save_data_workbench(
    page_key: PageKey,
    payload: DataWorkbenchConfig,
    service: ViewConfig,
) -> DataWorkbenchConfigResponse:
    try:
        row = service.save_data_workbench(
            page_key,
            payload.model_dump(mode="json", by_alias=True),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return DataWorkbenchConfigResponse.model_validate(row)
