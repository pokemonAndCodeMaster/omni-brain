from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .executor import AgentExecutor, ExecutorRequest, terminate_process
from .registry import AgentRegistry
from .repository import AgentRunRepository
from .worktrees import WorktreeManager


ACTIVE_STATUSES = {"queued", "running"}


class AgentRunService:
    def __init__(
        self,
        *,
        repository: AgentRunRepository,
        registry: AgentRegistry,
        worktrees: WorktreeManager,
        executors: dict[str, AgentExecutor],
        artifact_root: Path,
    ) -> None:
        self.repository = repository
        self.registry = registry
        self.worktrees = worktrees
        self.executors = executors
        if not self.executors:
            raise ValueError("至少需要登记一个 Agent Executor")
        self.artifact_root = artifact_root.resolve()
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self._semaphore = asyncio.Semaphore(1)
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    def recover(self) -> int:
        return self.repository.fail_interrupted()

    def agents(self, *, refresh: bool = False) -> list[dict[str, Any]]:
        agents = self.registry.refresh() if refresh else self.registry.list()
        counts = self.repository.counts_by_agent()
        for agent in agents:
            agent["run_counts"] = counts.get(
                str(agent["id"]),
                {"total": 0, "active": 0, "succeeded": 0, "failed": 0},
            )
        return agents

    def agent(self, agent_id: str) -> dict[str, Any]:
        agent = self.registry.get(agent_id)
        counts = self.repository.counts_by_agent()
        agent["run_counts"] = counts.get(
            agent_id,
            {"total": 0, "active": 0, "succeeded": 0, "failed": 0},
        )
        return agent

    def executor_health(self) -> dict[str, Any]:
        values = []
        for name in ("codex", "opencode"):
            executor = self.executors.get(name)
            if executor is None:
                values.append(
                    {
                        "name": name,
                        "available": False,
                        "command": name,
                        "version": None,
                        "reason": "执行器未登记",
                        "details": {},
                    }
                )
                continue
            health = executor.health()
            values.append(
                {
                    "name": health.name,
                    "available": health.available,
                    "command": health.command,
                    "version": health.version,
                    "reason": health.reason,
                    "details": health.details,
                }
            )
        return {"executors": values}

    async def start(
        self,
        *,
        agent_id: str,
        prompt: str,
        title: str | None,
        model: str | None,
        actor_id: str = "admin",
        executor: str | None = None,
        subject_type: str | None = None,
        subject_id: str | None = None,
        thread_id: str | None = None,
        trigger_action: str | None = None,
        output_schema: dict[str, Any] | None = None,
        work_id: str | None = None,
        plan_step_id: str | None = None,
        repository_path: str | None = None,
        base_revision: str | None = None,
        workspace_path: str | None = None,
        branch_name: str | None = None,
    ) -> dict[str, Any]:
        agent = self.registry.get(agent_id)
        selected_executor = executor or str(agent["default_executor"])
        if selected_executor not in agent["supported_executors"]:
            raise ValueError(
                f"Agent {agent_id} 不支持执行器：{selected_executor}"
            )
        if selected_executor not in self.executors:
            raise ValueError(f"执行器未登记：{selected_executor}")
        if (subject_type is None) != (subject_id is None):
            raise ValueError("subject_type 与 subject_id 必须同时提供")
        if (work_id is None) != (plan_step_id is None):
            raise ValueError("work_id 与 plan_step_id 必须同时提供")
        if workspace_path and not branch_name:
            raise ValueError("复用 worktree 时必须提供 branch_name")
        run_id = f"run-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"
        artifact_path = self.artifact_root / run_id
        artifact_path.mkdir(parents=True)
        (artifact_path / "prompt.md").write_text(prompt + "\n", encoding="utf-8")
        run = self.repository.create(
            {
                "id": run_id,
                "agent_id": agent_id,
                "agent_name": agent["name"],
                "title": title.strip() if title and title.strip() else prompt.strip()[:80],
                "prompt": prompt,
                "actor_id": actor_id,
                "model": model.strip() if model and model.strip() else None,
                "repository_path": repository_path or agent["repository"],
                "base_revision": base_revision or agent["revision"],
                "worktree_path": workspace_path,
                "branch_name": branch_name,
                "artifact_path": str(artifact_path),
                "executor": selected_executor,
                "subject_type": subject_type,
                "subject_id": subject_id,
                "thread_id": thread_id,
                "trigger_action": trigger_action,
                "work_id": work_id,
                "plan_step_id": plan_step_id,
            }
        )
        task = asyncio.create_task(
            self._execute(run_id, output_schema=output_schema),
            name=f"agent-run:{run_id}",
        )
        self._tasks[run_id] = task
        task.add_done_callback(lambda _task: self._tasks.pop(run_id, None))
        return run

    async def _execute(
        self,
        run_id: str,
        *,
        output_schema: dict[str, Any] | None = None,
    ) -> None:
        async with self._semaphore:
            run = self.repository.get(run_id)
            if run is None or run["status"] != "queued":
                return
            artifact_path = Path(str(run["artifact_path"]))
            executor_name = str(run["executor"])
            executor = self.executors[executor_name]
            try:
                self.repository.update(
                    run_id,
                    status="running",
                    started_at=datetime.now(timezone.utc),
                )
                self.repository.append_event(
                    run_id=run_id,
                    event_type="run.started",
                    summary=(
                        "开始使用 Work 共享 worktree"
                        if run.get("worktree_path")
                        else "开始建立隔离 worktree"
                    ),
                    payload={"executor": executor_name},
                )
                if run.get("worktree_path"):
                    workspace = {
                        "path": str(run["worktree_path"]),
                        "branch": str(run["branch_name"]),
                        "base_revision": str(run["base_revision"]),
                    }
                    if not Path(workspace["path"]).is_dir():
                        raise FileNotFoundError(
                            f"Work worktree 不存在：{workspace['path']}"
                        )
                    self.repository.append_event(
                        run_id=run_id,
                        event_type="workspace.reused",
                        summary=f"复用 Work 分支 {workspace['branch']}",
                        payload=workspace,
                    )
                else:
                    workspace = await asyncio.to_thread(
                        self.worktrees.create,
                        run_id,
                        Path(str(run["repository_path"])),
                        str(run["base_revision"]),
                    )
                    self.repository.update(
                        run_id,
                        worktree_path=workspace["path"],
                        branch_name=workspace["branch"],
                    )
                    self.repository.append_event(
                        run_id=run_id,
                        event_type="workspace.created",
                        summary=f"已建立 {workspace['branch']}",
                        payload=workspace,
                    )

                async def on_event(event: dict[str, Any]) -> None:
                    payload = dict(event["payload"])
                    if (
                        event["event_type"] == "thread.started"
                        and payload.get("thread_id")
                    ):
                        await asyncio.to_thread(
                            self.repository.update,
                            run_id,
                            executor_session_id=str(payload["thread_id"]),
                        )
                    await asyncio.to_thread(
                        self.repository.append_event,
                        run_id=run_id,
                        event_type=str(event["event_type"]),
                        summary=str(event["summary"]),
                        payload=payload,
                        source=str(event["source"]),
                        channel=event.get("channel"),
                    )

                sandbox = (
                    "workspace-write"
                    if str(run["agent_id"]) == "development-agent"
                    else "read-only"
                )
                result = await executor.run(
                    ExecutorRequest(
                        worktree=Path(workspace["path"]),
                        prompt=str(run["prompt"]),
                        run_id=run_id,
                        model=run.get("model"),
                        sandbox=sandbox,
                        output_schema=output_schema,
                        artifact_path=artifact_path,
                    ),
                    on_event=on_event,
                    on_process=lambda process: self._processes.__setitem__(run_id, process),
                )
                self._processes.pop(run_id, None)
                snapshot = await asyncio.to_thread(
                    self.worktrees.snapshot,
                    Path(workspace["path"]),
                )
                (artifact_path / "workspace.json").write_text(
                    json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                if result.final_message:
                    (artifact_path / "final.md").write_text(
                        result.final_message + "\n",
                        encoding="utf-8",
                    )
                succeeded = result.exit_code == 0 and result.failure_reason is None
                final_status = "succeeded" if succeeded else "failed"
                self.repository.update(
                    run_id,
                    status=final_status,
                    executor_session_id=result.session_id,
                    opencode_session_id=(
                        result.session_id if executor_name == "opencode" else None
                    ),
                    exit_code=result.exit_code,
                    result_summary=result.final_message,
                    result_payload=result.final_payload,
                    failure_code=result.failure_code,
                    failure_reason=result.failure_reason,
                    finished_at=datetime.now(timezone.utc),
                )
                self.repository.append_event(
                    run_id=run_id,
                    event_type=f"run.{final_status}",
                    summary=(
                        f"{executor_name} 任务执行完成"
                        if succeeded
                        else result.failure_reason or "OpenCode 任务执行失败"
                    ),
                    payload={
                        "exit_code": result.exit_code,
                        "session_id": result.session_id,
                        "executor": executor_name,
                        "failure_code": result.failure_code,
                    },
                )
            except asyncio.CancelledError:
                process = self._processes.pop(run_id, None)
                if process is not None:
                    await terminate_process(process)
                current = self.repository.get(run_id)
                if current and current["status"] in ACTIVE_STATUSES:
                    self.repository.update(
                        run_id,
                        status="cancelled",
                        finished_at=datetime.now(timezone.utc),
                    )
                    self.repository.append_event(
                        run_id=run_id,
                        event_type="run.cancelled",
                        summary="任务已取消",
                        payload={},
                    )
                raise
            except Exception as exc:
                self._processes.pop(run_id, None)
                reason = str(exc) or exc.__class__.__name__
                self.repository.update(
                    run_id,
                    status="failed",
                    failure_code="platform_error",
                    failure_reason=reason,
                    finished_at=datetime.now(timezone.utc),
                )
                self.repository.append_event(
                    run_id=run_id,
                    event_type="run.failed",
                    summary=reason,
                    payload={"exception_type": exc.__class__.__name__},
                )

    async def cancel(self, run_id: str) -> dict[str, Any]:
        run = self.repository.get(run_id)
        if run is None:
            raise KeyError(run_id)
        if run["status"] not in ACTIVE_STATUSES:
            raise ValueError(f"Run 当前状态不可取消：{run['status']}")
        task = self._tasks.get(run_id)
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        else:
            self.repository.update(
                run_id,
                status="cancelled",
                finished_at=datetime.now(timezone.utc),
            )
            self.repository.append_event(
                run_id=run_id,
                event_type="run.cancelled",
                summary="排队任务已取消",
                payload={},
            )
        result = self.repository.get(run_id)
        if result is None:
            raise KeyError(run_id)
        return result

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
