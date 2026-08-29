from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .opencode_executor import OpenCodeExecutor, terminate_process
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
        executor: OpenCodeExecutor,
        artifact_root: Path,
    ) -> None:
        self.repository = repository
        self.registry = registry
        self.worktrees = worktrees
        self.executor = executor
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

    def opencode_health(self) -> dict[str, Any]:
        resolved = shutil.which(self.executor.command)
        if not resolved:
            return {
                "available": False,
                "command": self.executor.command,
                "reason": f"找不到命令：{self.executor.command}",
            }
        result = subprocess.run(
            [resolved, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        version = (result.stdout or result.stderr).strip().splitlines()
        return {
            "available": result.returncode == 0,
            "command": resolved,
            "version": version[0] if version else None,
            "endpoint": self.executor.endpoint or None,
            "reason": None if result.returncode == 0 else "OpenCode 版本检查失败",
        }

    async def start(
        self,
        *,
        agent_id: str,
        prompt: str,
        title: str | None,
        model: str | None,
        actor_id: str,
    ) -> dict[str, Any]:
        agent = self.registry.get(agent_id)
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
                "repository_path": agent["repository"],
                "base_revision": agent["revision"],
                "artifact_path": str(artifact_path),
            }
        )
        task = asyncio.create_task(self._execute(run_id), name=f"agent-run:{run_id}")
        self._tasks[run_id] = task
        task.add_done_callback(lambda _task: self._tasks.pop(run_id, None))
        return run

    async def _execute(self, run_id: str) -> None:
        async with self._semaphore:
            run = self.repository.get(run_id)
            if run is None or run["status"] != "queued":
                return
            artifact_path = Path(str(run["artifact_path"]))
            try:
                self.repository.update(
                    run_id,
                    status="running",
                    started_at=datetime.now(timezone.utc),
                )
                self.repository.append_event(
                    run_id=run_id,
                    event_type="run.started",
                    summary="开始建立隔离 worktree",
                    payload={"executor": "opencode"},
                )
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
                    await asyncio.to_thread(
                        self.repository.append_event,
                        run_id=run_id,
                        event_type=str(event["event_type"]),
                        summary=str(event["summary"]),
                        payload=dict(event["payload"]),
                        source=str(event["source"]),
                        channel=event.get("channel"),
                    )

                result = await self.executor.run(
                    worktree=Path(workspace["path"]),
                    prompt=str(run["prompt"]),
                    run_id=run_id,
                    model=run.get("model"),
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
                    opencode_session_id=result.session_id,
                    exit_code=result.exit_code,
                    result_summary=result.final_message,
                    failure_code=result.failure_code,
                    failure_reason=result.failure_reason,
                    finished_at=datetime.now(timezone.utc),
                )
                self.repository.append_event(
                    run_id=run_id,
                    event_type=f"run.{final_status}",
                    summary=(
                        "OpenCode 任务执行完成"
                        if succeeded
                        else result.failure_reason or "OpenCode 任务执行失败"
                    ),
                    payload={
                        "exit_code": result.exit_code,
                        "session_id": result.session_id,
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
