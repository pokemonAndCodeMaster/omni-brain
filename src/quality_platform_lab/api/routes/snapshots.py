from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ...manual_qc.acceptance.models import SnapshotFilter
from ...manual_qc.acceptance.service import SnapshotQueryService
from ..deps import get_snapshot_service
from ..schemas import (
    DataResponse,
    EmployeeAggregateOut,
    GroupAggregateOut,
    SceneAggregateOut,
    SnapshotRowOut,
)


router = APIRouter(prefix="/api/snapshots", tags=["acceptance-snapshots"])
SnapshotService = Annotated[SnapshotQueryService, Depends(get_snapshot_service)]


def _filters(
    stat_date_start: date | None,
    stat_date_end: date | None,
    scene_name: str | None,
    group_name: str | None,
    employee_id: str | None = None,
) -> SnapshotFilter:
    if stat_date_start and stat_date_end and stat_date_start > stat_date_end:
        raise HTTPException(status_code=422, detail="stat_date_start 不能晚于 stat_date_end")
    return SnapshotFilter(
        stat_date_start=stat_date_start,
        stat_date_end=stat_date_end,
        scene_name=scene_name or None,
        group_name=group_name or None,
        employee_id=employee_id or None,
    )


def _computed_at(items: list[dict[str, Any]]) -> Any:
    values = [item.get("computed_at") for item in items if item.get("computed_at")]
    return max(values) if values else None


@router.get("/aggregate/scene", response_model=DataResponse[SceneAggregateOut])
def aggregate_by_scene(
    service: SnapshotService,
    stat_date_start: date | None = Query(None),
    stat_date_end: date | None = Query(None),
    scene_name: str | None = Query(None),
    group_name: str | None = Query(None),
) -> DataResponse[SceneAggregateOut]:
    items = service.aggregate(
        "scene",
        _filters(stat_date_start, stat_date_end, scene_name, group_name),
    )
    return DataResponse(
        items=[SceneAggregateOut.model_validate(item) for item in items],
        total=len(items),
        computed_at=_computed_at(items),
    )


@router.get("/aggregate/group", response_model=DataResponse[GroupAggregateOut])
def aggregate_by_group(
    service: SnapshotService,
    scene_name: str = Query(min_length=1),
    stat_date_start: date | None = Query(None),
    stat_date_end: date | None = Query(None),
    group_name: str | None = Query(None),
) -> DataResponse[GroupAggregateOut]:
    try:
        items = service.aggregate(
            "group",
            _filters(stat_date_start, stat_date_end, scene_name, group_name),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DataResponse(
        items=[GroupAggregateOut.model_validate(item) for item in items],
        total=len(items),
        computed_at=_computed_at(items),
    )


@router.get("/aggregate/employee", response_model=DataResponse[EmployeeAggregateOut])
def aggregate_by_employee(
    service: SnapshotService,
    scene_name: str = Query(min_length=1),
    group_name: str = Query(min_length=1),
    stat_date_start: date | None = Query(None),
    stat_date_end: date | None = Query(None),
) -> DataResponse[EmployeeAggregateOut]:
    try:
        items = service.aggregate(
            "employee",
            _filters(stat_date_start, stat_date_end, scene_name, group_name),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DataResponse(
        items=[EmployeeAggregateOut.model_validate(item) for item in items],
        total=len(items),
        computed_at=_computed_at(items),
    )


@router.get("/rows", response_model=DataResponse[SnapshotRowOut])
def list_rows(
    service: SnapshotService,
    stat_date_start: date | None = Query(None),
    stat_date_end: date | None = Query(None),
    scene_name: str | None = Query(None),
    group_name: str | None = Query(None),
    employee_id: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> DataResponse[SnapshotRowOut]:
    filters = _filters(
        stat_date_start,
        stat_date_end,
        scene_name,
        group_name,
        employee_id,
    )
    items, total = service.list_rows(filters, limit=limit, offset=offset)
    return DataResponse(
        items=[SnapshotRowOut.model_validate(item) for item in items],
        total=total,
        computed_at=_computed_at(items),
    )
