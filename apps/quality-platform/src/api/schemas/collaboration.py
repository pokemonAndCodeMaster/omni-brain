from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .agent_runtime import ExecutorName


IdeaStatus = Literal["captured", "discussing", "converted", "archived"]
RequirementStatus = Literal[
    "candidate",
    "accepted",
    "rejected",
    "deferred",
    "merged",
    "superseded",
    "closed",
]
Commitment = Literal["NOW", "NEXT", "LATER"]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RequirementContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    background: str = ""
    target_users: list[str] = Field(default_factory=list)
    current_problem: str = ""
    value: str = ""
    expected_outcome: str = ""
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    key_actions: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class RequirementDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    content: RequirementContent


class IdeaCreate(StrictInput):
    title: str = Field(min_length=1, max_length=256)
    raw_content: str = Field(min_length=1, max_length=100_000)
    domain_key: str | None = Field(default=None, max_length=128)


class IdeaSummaryOut(BaseModel):
    id: str
    title: str
    domain_key: str | None
    status: IdeaStatus
    owner_id: str
    requirement_id: str | None = None
    run_count: int = 0
    created_at: datetime
    updated_at: datetime


class IdeaOut(IdeaSummaryOut):
    raw_content: str
    created_by: str
    thread_id: str


class IdeaListOut(BaseModel):
    items: list[IdeaSummaryOut]
    total: int
    limit: int
    offset: int


class MessageCreate(StrictInput):
    body: str = Field(min_length=1, max_length=100_000)


class ThreadEntryOut(BaseModel):
    id: int
    thread_id: str
    entry_type: Literal["human_message", "system"]
    actor_type: Literal["admin", "system"]
    actor_id: str
    body: str
    payload: dict[str, Any]
    created_at: datetime


class AgentActionCreate(StrictInput):
    action: Literal["knowledge_context", "shape_requirement"]
    executor: ExecutorName | None = None
    model: str | None = Field(default=None, max_length=256)
    instruction: str = Field(default="", max_length=20_000)


class IdeaConvertToRequirement(StrictInput):
    title: str = Field(min_length=1, max_length=256)
    content: RequirementContent = Field(default_factory=RequirementContent)
    source_run_id: str | None = Field(default=None, max_length=64)


class RequirementCreate(StrictInput):
    title: str = Field(min_length=1, max_length=256)
    content: RequirementContent = Field(default_factory=RequirementContent)
    source_run_id: str | None = Field(default=None, max_length=64)


class RequirementRevisionCreate(StrictInput):
    content: RequirementContent
    source_run_id: str | None = Field(default=None, max_length=64)


class RequirementRevisionOut(BaseModel):
    id: str
    requirement_id: str
    revision_no: int
    content: dict[str, Any] | None = None
    source_run_id: str | None = None
    created_by: str
    created_at: datetime


class RequirementSummaryOut(BaseModel):
    id: str
    title: str
    source_type: Literal["direct", "idea"]
    source_idea_id: str | None = None
    status: RequirementStatus
    commitment: Commitment | None = None
    owner_id: str
    current_revision_no: int
    run_count: int = 0
    work_id: str | None = None
    created_at: datetime
    updated_at: datetime


class RequirementOut(RequirementSummaryOut):
    current_revision_id: str
    accepted_revision_id: str | None = None
    target_window: str | None = None
    entry_condition: str | None = None
    review_at: datetime | None = None
    merged_into_id: str | None = None
    created_by: str
    thread_id: str
    current_revision: RequirementRevisionOut


class RequirementListOut(BaseModel):
    items: list[RequirementSummaryOut]
    total: int
    limit: int
    offset: int


class RequirementDecisionCreate(StrictInput):
    decision_type: Literal["accept", "reject", "defer", "merge", "reopen"]
    revision_id: str | None = Field(default=None, max_length=64)
    reason: str | None = Field(default=None, max_length=20_000)
    commitment: Commitment | None = None
    target_window: str | None = Field(default=None, max_length=256)
    entry_condition: str | None = Field(default=None, max_length=20_000)
    review_at: datetime | None = None
    merged_into_id: str | None = Field(default=None, max_length=64)
    revision_content: RequirementContent | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> "RequirementDecisionCreate":
        if self.decision_type == "accept":
            if self.commitment not in {"NEXT", "LATER"}:
                raise ValueError("接纳需求必须选择 NEXT 或 LATER")
            if self.commitment == "NEXT" and not (
                self.target_window or self.entry_condition
            ):
                raise ValueError("NEXT 必须填写预计窗口或进入条件")
            if self.commitment == "LATER" and not (
                self.review_at or self.entry_condition
            ):
                raise ValueError("LATER 必须填写复审时间或触发条件")
        if self.decision_type in {"reject", "defer", "merge"} and not self.reason:
            raise ValueError("驳回、延期或合并必须填写原因")
        if self.decision_type == "defer" and not (
            self.review_at or self.entry_condition
        ):
            raise ValueError("延期必须填写复审时间或触发条件")
        if self.decision_type == "merge" and not self.merged_into_id:
            raise ValueError("合并必须指定承接 Requirement")
        if self.decision_type == "reopen" and self.revision_content is None:
            raise ValueError("重新打开必须提交新的 Revision 内容")
        return self


class RequirementDecisionOut(BaseModel):
    id: str
    requirement_id: str
    revision_id: str | None = None
    decision_type: str
    reason: str | None = None
    commitment: Commitment | None = None
    target_window: str | None = None
    entry_condition: str | None = None
    review_at: datetime | None = None
    merged_into_id: str | None = None
    actor_id: str
    created_at: datetime


class TimelineItemOut(BaseModel):
    item_type: Literal["entry", "run", "revision", "decision"]
    item_id: str
    occurred_at: datetime
    payload: dict[str, Any]


class TimelinePageOut(BaseModel):
    items: list[TimelineItemOut]
    next_cursor: int | None = None
