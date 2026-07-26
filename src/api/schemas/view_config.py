from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
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
    chart_type: Literal["bar", "line", "pie", "combo"] = "bar"
    stacked: bool = False
    show_legend: bool = True
    show_labels: bool = False
    smooth: bool = True
    palette: Literal["business", "quality", "contrast"] = "business"
    orientation: Literal["vertical", "horizontal"] = "vertical"
    legend_position: Literal["top", "bottom"] = "top"
    font_scale: Literal["small", "medium", "large"] = "medium"
    show_area: bool = False
    sort_direction: Literal["natural", "value-desc"] = "natural"
    max_categories: int = Field(default=20, ge=0, le=100)


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


class LegacyDashboardMetricStyle(CamelModel):
    accent_color: str = Field(default="#2458d3", pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str = Field(
        default="#ffffff",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    text_color: str = Field(default="#17212b", pattern=r"^#[0-9A-Fa-f]{6}$")
    title_size: int = Field(default=14, ge=11, le=28)
    value_size: int = Field(default=34, ge=22, le=64)
    density: Literal["compact", "comfortable"] = "comfortable"
    show_project_breakdown: bool = True


class DashboardMetricStyle(CamelModel):
    accent_color: str = Field(default="#2458d3", pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str = Field(
        default="#ffffff",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    text_color: str = Field(default="#17212b", pattern=r"^#[0-9A-Fa-f]{6}$")
    title_size: int = Field(default=14, ge=11, le=28)
    density: Literal["compact", "comfortable"] = "comfortable"


class DashboardMetricOrigin(CamelModel):
    type: Literal["system-preset", "user"]
    preset_id: str | None = Field(default=None, max_length=128)
    preset_version: int | None = Field(default=None, ge=1)


class DashboardMetricReference(CamelModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    parameters: dict[str, str] = Field(default_factory=dict, max_length=8)


class DashboardMetricValueStyle(CamelModel):
    value_size: int = Field(default=34, ge=18, le=64)
    value_color: str = Field(default="#16233a", pattern=r"^#[0-9A-Fa-f]{6}$")
    label_size: int = Field(default=11, ge=9, le=20)
    label_color: str = Field(default="#667085", pattern=r"^#[0-9A-Fa-f]{6}$")


class DashboardMetricValueBlock(CamelModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    kind: Literal["metric-value"] = "metric-value"
    metric: DashboardMetricReference
    label: str = Field(min_length=1, max_length=80)
    emphasis: Literal["primary", "supporting"] = "supporting"
    width: Literal["full", "half", "third"] = "half"
    style: DashboardMetricValueStyle


class DashboardMetricTextStyle(CamelModel):
    font_size: int = Field(default=11, ge=9, le=24)
    color: str = Field(default="#667085", pattern=r"^#[0-9A-Fa-f]{6}$")


class DashboardMetricTextBlock(CamelModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    kind: Literal["text"] = "text"
    content: str = Field(default="", max_length=500)
    width: Literal["full", "half", "third"] = "full"
    style: DashboardMetricTextStyle


class DashboardMetricBreakdownBlock(CamelModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    kind: Literal["breakdown"] = "breakdown"
    dimension: Literal["project", "task", "group"]
    metrics: list[DashboardMetricReference] = Field(min_length=1, max_length=8)
    limit: int = Field(default=8, ge=1, le=30)
    width: Literal["full", "half", "third"] = "full"


DashboardMetricBlock = Annotated[
    DashboardMetricValueBlock
    | DashboardMetricTextBlock
    | DashboardMetricBreakdownBlock,
    Field(discriminator="kind"),
]


class DashboardMetricQuery(CamelModel):
    scope_mode: Literal["inherit-page"] = "inherit-page"
    filters: list[dict[str, str | int | float | bool]] = Field(
        default_factory=list,
        max_length=12,
    )


class DashboardMetricAction(CamelModel):
    type: Literal["jump"] = "jump"
    target_card_id: Literal[
        "annotation-quality",
        "bad-options",
        "acceptance-progress",
        "acceptance-result",
        "snapshot-detail",
    ]


class DashboardMetricCard(CamelModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")
    kind: Literal["metric"] = "metric"
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=500)
    metric_id: Literal[
        "annotation_quality",
        "acceptance_allocation",
        "acceptance_completion",
        "acceptance_result",
    ] | None = None
    jump_target: Literal[
        "annotation-quality",
        "bad-options",
        "acceptance-progress",
        "acceptance-result",
        "snapshot-detail",
    ] | None = None
    origin: DashboardMetricOrigin | None = None
    query: DashboardMetricQuery | None = None
    blocks: list[DashboardMetricBlock] | None = Field(default=None, max_length=20)
    action: DashboardMetricAction | None = None
    style: DashboardMetricStyle | LegacyDashboardMetricStyle
    layout: DashboardLayout

    @model_validator(mode="after")
    def validate_metric_version(self) -> "DashboardMetricCard":
        legacy = self.metric_id is not None and self.jump_target is not None
        current = (
            self.origin is not None
            and self.query is not None
            and self.blocks is not None
        )
        if legacy == current:
            raise ValueError("总览卡片必须且只能使用 V1 或 V2 一种结构")
        if current:
            primary_count = sum(
                isinstance(block, DashboardMetricValueBlock)
                and block.emphasis == "primary"
                for block in self.blocks or []
            )
            if primary_count > 1:
                raise ValueError("总览卡片最多只能有一个主指标")
        return self


DashboardCardUnion = Annotated[
    DashboardCard | DashboardMetricCard,
    Field(discriminator="kind"),
]


class DashboardConfig(CamelModel):
    schema_version: Literal["dashboard-v1", "dashboard-v2"] = "dashboard-v1"
    cards: list[DashboardCardUnion] = Field(default_factory=list, max_length=80)


class DashboardConfigResponse(CamelModel):
    owner_id: str
    page_key: str
    view_name: str
    view_type: Literal["dashboard"]
    config: DashboardConfig
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime


class DataWorkbenchMetricReference(CamelModel):
    id: str = Field(
        pattern=r"^[A-Za-z0-9_.:-]{1,128}$",
    )
    parameters: dict[str, str] = Field(default_factory=dict, max_length=8)


class DataWorkbenchColumnState(CamelModel):
    visibility: dict[str, bool] = Field(default_factory=dict, max_length=80)
    order: list[str] = Field(default_factory=list, max_length=80)
    sizing: dict[str, int] = Field(default_factory=dict, max_length=80)


class DataWorkbenchConfig(CamelModel):
    schema_version: Literal["manual-qc-task-table-v1"] = (
        "manual-qc-task-table-v1"
    )
    pinned_metrics: list[DataWorkbenchMetricReference] = Field(
        default_factory=list,
        max_length=5,
    )
    columns: DataWorkbenchColumnState = Field(
        default_factory=DataWorkbenchColumnState,
    )


class DataWorkbenchConfigResponse(CamelModel):
    owner_id: str
    page_key: str
    view_name: str
    view_type: Literal["data_workbench"]
    config: DataWorkbenchConfig
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime
