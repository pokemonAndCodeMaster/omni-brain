from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


Workspace = Literal["personal", "team"]
Engine = Literal["codex", "opencode"]
RuntimeKind = Literal["native", "docker"]
RunState = Literal[
    "queued",
    "claimed",
    "running",
    "pause_requested",
    "paused",
    "cancelling",
    "cancelled",
    "succeeded",
    "failed",
    "unavailable",
]


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class RunCreate(CamelModel):
    item_id: str = Field(min_length=1, max_length=64)
    instruction: str = Field(min_length=1, max_length=100_000)
    engine: Engine
    runtime: RuntimeKind = "native"
    image: str | None = Field(default=None, max_length=512)
    directory: str | None = Field(default=None, max_length=4096)
    branch: str | None = Field(default=None, max_length=256)
    model: str | None = Field(default=None, max_length=256)
    machine_id: str | None = Field(default=None, max_length=64)
    permission: Literal["read-only", "workspace-write"] = "read-only"
    capability_candidate_id: str | None = Field(default=None, max_length=64)


class RetryRun(CamelModel):
    sync_context: bool = False
    instruction: str | None = Field(default=None, min_length=1, max_length=100_000)
    machine_id: str | None = Field(default=None, max_length=64)


class RunOut(CamelModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    id: str
    workspace: Workspace
    item_id: str
    attempt: int
    retry_of: str | None = None
    state: RunState
    instruction: str
    engine: Engine
    runtime: RuntimeKind
    machine: str | None = None
    requested_machine_id: str | None = None
    session: str | None = None
    rev: int
    context_version_id: str
    capability_candidate_id: str | None = None
    capabilities: list[dict[str, Any]] = Field(default_factory=list)
    image: str | None = None
    directory: str
    repository_path: str | None = None
    repository_revision: str | None = None
    branch: str | None = None
    model: str | None = None
    sandbox: str
    exit_code: int | None = None
    error: str | None = None
    failure_code: str | None = None
    result: str | None = None
    result_payload: dict[str, Any] | None = None
    artifact_candidates: list[dict[str, Any]] = Field(default_factory=list)
    evidence_candidates: list[dict[str, Any]] = Field(default_factory=list)
    environment_snapshot: dict[str, Any] = Field(default_factory=dict)
    stale_context: bool = False
    current_rev: int | None = None
    business_accepted: bool = False
    created_at: datetime
    claimed_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime


class RunListOut(CamelModel):
    items: list[RunOut]
    total: int
    limit: int
    offset: int


class RunEventOut(CamelModel):
    id: int
    run_id: str
    sequence: int
    occurred_at: datetime
    event_type: str
    source: str
    channel: str | None = None
    summary: str
    payload: dict[str, Any]


class RunEventListOut(CamelModel):
    items: list[RunEventOut]
    next_sequence: int


class MachineRegister(CamelModel):
    name: str = Field(min_length=1, max_length=160)
    capacity: int = Field(ge=1, le=32)
    engines: list[Engine] = Field(min_length=1, max_length=2)
    runtimes: list[RuntimeKind] = Field(min_length=1, max_length=2)
    images: list[str] = Field(default_factory=list, max_length=64)
    labels: dict[str, str] = Field(default_factory=dict)


class MachineRegistered(CamelModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    id: str
    workspace: Workspace
    name: str
    status: str
    capacity: int
    current_run_id: str | None = None
    active_runs: int = 0
    last_seen_at: datetime
    capabilities: dict[str, Any]
    worker_token: str


class MachineOut(CamelModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    id: str
    workspace: Workspace
    name: str
    status: str
    capacity: int
    current_run_id: str | None = None
    active_runs: int = 0
    last_seen_at: datetime
    capabilities: dict[str, Any]


class MachineAction(CamelModel):
    action: Literal["enable", "pause", "drain"]


class WorkerClaim(CamelModel):
    lease_seconds: int = Field(default=30, ge=10, le=300)


class WorkerHeartbeatLease(CamelModel):
    run_id: str
    lease_id: str


class WorkerHeartbeat(CamelModel):
    leases: list[WorkerHeartbeatLease] = Field(default_factory=list, max_length=32)
    lease_seconds: int = Field(default=30, ge=10, le=300)


class WorkerEvent(CamelModel):
    lease_id: str
    event_type: str = Field(min_length=1, max_length=128)
    source: str = Field(default="worker", min_length=1, max_length=64)
    channel: str | None = Field(default=None, max_length=32)
    summary: str = Field(default="", max_length=20_000)
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkerReport(CamelModel):
    lease_id: str
    outcome: Literal["running", "succeeded", "failed", "unavailable", "cancelled", "paused"]
    session_id: str | None = Field(default=None, max_length=256)
    exit_code: int | None = None
    result: str | None = Field(default=None, max_length=1_000_000)
    result_payload: dict[str, Any] | None = None
    artifacts: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    evidence: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    environment: dict[str, Any] = Field(default_factory=dict)
    failure_code: str | None = Field(default=None, max_length=64)
    error: str | None = Field(default=None, max_length=100_000)
