from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


RunStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
ExecutorName = Literal["codex", "opencode"]


class AgentCapabilityOut(BaseModel):
    id: str
    adoption: str
    adoption_label: str
    entrypoints: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)


class AgentRunCountsOut(BaseModel):
    total: int = 0
    active: int = 0
    succeeded: int = 0
    failed: int = 0


class AgentSummaryOut(BaseModel):
    id: str
    name: str
    category: str
    description: str
    state: str
    default_executor: ExecutorName
    supported_executors: list[ExecutorName]
    revision_short: str
    run_counts: AgentRunCountsOut


class AgentOut(AgentSummaryOut):
    examples: list[str]
    capabilities: list[AgentCapabilityOut]
    repository: str
    revision: str
    release_channel: str | None = None
    release_date: str | None = None


class ExecutorHealthOut(BaseModel):
    name: ExecutorName
    available: bool
    command: str
    version: str | None = None
    reason: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AgentRuntimeHealthOut(BaseModel):
    executors: list[ExecutorHealthOut]


class AgentRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1, max_length=100_000)
    title: str | None = Field(default=None, max_length=256)
    model: str | None = Field(default=None, max_length=256)
    executor: ExecutorName | None = None
    subject_type: Literal["idea", "requirement", "work"] | None = None
    subject_id: str | None = Field(default=None, max_length=64)
    thread_id: str | None = Field(default=None, max_length=64)
    trigger_action: str | None = Field(default=None, max_length=64)


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    agent_name: str
    title: str
    prompt: str
    actor_id: str
    status: RunStatus
    model: str | None = None
    repository_path: str
    base_revision: str
    worktree_path: str | None = None
    branch_name: str | None = None
    executor: ExecutorName
    executor_session_id: str | None = None
    opencode_session_id: str | None = None
    subject_type: Literal["idea", "requirement", "work"] | None = None
    subject_id: str | None = None
    thread_id: str | None = None
    trigger_action: str | None = None
    work_id: str | None = None
    plan_step_id: str | None = None
    exit_code: int | None = None
    result_summary: str | None = None
    result_payload: dict[str, Any] | None = None
    failure_code: str | None = None
    failure_reason: str | None = None
    artifact_path: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime


class AgentRunSummaryOut(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    title: str
    actor_id: str
    status: RunStatus
    model: str | None = None
    branch_name: str | None = None
    executor: ExecutorName
    executor_session_id: str | None = None
    subject_type: Literal["idea", "requirement", "work"] | None = None
    subject_id: str | None = None
    thread_id: str | None = None
    trigger_action: str | None = None
    work_id: str | None = None
    plan_step_id: str | None = None
    exit_code: int | None = None
    failure_code: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime


class AgentRunListOut(BaseModel):
    items: list[AgentRunSummaryOut]
    total: int
    limit: int
    offset: int


class AgentRunEventOut(BaseModel):
    id: int
    run_id: str
    sequence: int
    occurred_at: datetime
    event_type: str
    source: str
    channel: str | None = None
    summary: str
    payload: dict[str, Any]


class AgentRunEventListOut(BaseModel):
    items: list[AgentRunEventOut]
    next_sequence: int
