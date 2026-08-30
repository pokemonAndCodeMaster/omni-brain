from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .agent_runtime import AgentRunOut, AgentRunSummaryOut, ExecutorName


WorkStatus = Literal[
    "planned",
    "in_progress",
    "in_review",
    "revision_requested",
    "accepted",
    "cancelled",
]
StepStatus = Literal[
    "blocked",
    "ready",
    "running",
    "awaiting_gate",
    "failed",
    "completed",
]


class WorkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=256)
    owner_id: str = Field(default="admin", min_length=1, max_length=128)
    reviewer_id: str = Field(default="admin", min_length=1, max_length=128)
    timebox_start: datetime | None = None
    timebox_end: datetime | None = None
    repository_path: str | None = Field(default=None, max_length=4096)
    base_revision: str | None = Field(default=None, max_length=256)

    @model_validator(mode="after")
    def validate_timebox(self) -> WorkCreate:
        if self.timebox_start and self.timebox_end and self.timebox_end <= self.timebox_start:
            raise ValueError("时间盒结束时间必须晚于开始时间")
        return self


class WorkUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_id: str | None = Field(default=None, min_length=1, max_length=128)
    reviewer_id: str | None = Field(default=None, min_length=1, max_length=128)
    timebox_start: datetime | None = None
    timebox_end: datetime | None = None

    @model_validator(mode="after")
    def require_change(self) -> WorkUpdate:
        if not self.model_fields_set:
            raise ValueError("至少提交一项 Work 元数据")
        return self


class WorkStepRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executor: ExecutorName | None = None
    model: str | None = Field(default=None, max_length=256)
    instruction: str = Field(default="", max_length=20_000)


class WorkStepComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str = Field(min_length=1, max_length=10_000)


class WorkEvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verification_summary: str | None = Field(default=None, max_length=30_000)
    review_summary: str | None = Field(default=None, max_length=30_000)
    pull_request_url: str | None = Field(default=None, max_length=2048)
    knowledge_proposal: str | None = Field(default=None, max_length=30_000)
    candidate_eval_case: str | None = Field(default=None, max_length=30_000)

    @model_validator(mode="after")
    def require_useful_evidence(self) -> WorkEvidenceCreate:
        values = (
            self.verification_summary,
            self.review_summary,
            self.pull_request_url,
            self.knowledge_proposal,
            self.candidate_eval_case,
        )
        if not any(value and value.strip() for value in values):
            raise ValueError("至少补充一项验证、审查或交付候选信息")
        return self


class WorkDecisionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_type: Literal["accept", "request_changes"]
    reason: str = Field(min_length=1, max_length=10_000)


class WorkEvidenceOut(BaseModel):
    id: str
    work_id: str
    payload: dict[str, Any]
    created_by: str
    created_at: datetime


class WorkDecisionOut(BaseModel):
    id: str
    work_id: str
    decision_type: Literal["accept", "request_changes"]
    reason: str
    evidence_id: str | None = None
    commit_sha: str | None = None
    actor_id: str
    created_at: datetime


class PlanStepOut(BaseModel):
    id: str
    work_plan_id: str
    position: int
    step_key: str
    title: str
    description: str
    actor_kind: Literal["agent", "human"]
    agent_id: str | None = None
    default_executor: ExecutorName | None = None
    status: Literal["pending", "ready", "completed"]
    display_status: StepStatus
    completion_note: str | None = None
    completed_by: str | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    runs: list[AgentRunSummaryOut] = Field(default_factory=list)


class WorkPlanOut(BaseModel):
    id: str
    work_id: str
    recipe_key: Literal["standard_development_v1"]
    revision_no: int
    status: Literal["active", "completed"]
    created_by: str
    created_at: datetime
    completed_at: datetime | None = None
    steps: list[PlanStepOut]


class WorkSummaryOut(BaseModel):
    id: str
    requirement_id: str
    requirement_revision_id: str
    requirement_title: str
    title: str
    status: WorkStatus
    owner_id: str
    reviewer_id: str
    repository_path: str
    base_commit: str
    branch_name: str
    run_count: int
    completed_step_count: int
    step_count: int
    created_at: datetime
    updated_at: datetime


class WorkOut(WorkSummaryOut):
    model_config = ConfigDict(from_attributes=True)

    requirement_status: str
    timebox_start: datetime | None = None
    timebox_end: datetime | None = None
    worktree_path: str
    created_by: str
    accepted_at: datetime | None = None
    plan: WorkPlanOut
    latest_evidence: WorkEvidenceOut | None = None
    decisions: list[WorkDecisionOut] = Field(default_factory=list)


class WorkListOut(BaseModel):
    items: list[WorkSummaryOut]
    total: int
    limit: int
    offset: int


class WorkRunOut(AgentRunOut):
    pass
