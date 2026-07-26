from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class DashboardLayout(CamelModel):
    x: int = Field(ge=0, le=11)
    y: int = Field(ge=0)
    w: int = Field(ge=2, le=12)
    h: int = Field(ge=3, le=20)
    min_w: int = Field(default=3, ge=1, le=12)
    min_h: int = Field(default=4, ge=1, le=20)


class DashboardChartStyle(CamelModel):
    chart_type: Literal["bar", "line", "pie"] = "bar"
    stacked: bool = False
    show_legend: bool = True
    show_labels: bool = False
    smooth: bool = True
    palette: Literal["business", "quality", "contrast"] = "business"
    orientation: Literal["vertical", "horizontal"] = "vertical"


class DashboardQuery(CamelModel):
    source_id: str = Field(min_length=1, max_length=128)
    dimension_id: str = Field(min_length=1, max_length=128)
    measure_ids: list[str] = Field(min_length=1, max_length=12)
    filters: dict[str, str] = Field(default_factory=dict)
    filter_summary: str = Field(default="", max_length=1000)


class DashboardCard(CamelModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    kind: Literal["chart"] = "chart"
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=500)
    query: DashboardQuery
    style: DashboardChartStyle
    layout: DashboardLayout


class DashboardConfig(CamelModel):
    schema_version: Literal["dashboard-v1"] = "dashboard-v1"
    cards: list[DashboardCard] = Field(default_factory=list, max_length=80)


class DashboardConfigResponse(CamelModel):
    owner_id: str
    page_key: str
    view_name: str
    view_type: Literal["dashboard"]
    config: DashboardConfig
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime
