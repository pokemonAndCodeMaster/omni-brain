from __future__ import annotations

import asyncio
import json
from pathlib import Path
import subprocess
from typing import Any

from src.agent_runtime.codex_executor import CodexExecutor
from src.agent_runtime.executor import ExecutorRequest, classify_failure
from src.agent_runtime.opencode_executor import OpenCodeExecutor
from src.agent_runtime.service import AgentRunService
from src.agent_runtime.worktrees import WorktreeManager


def request(*, model: str | None = "provider/model") -> ExecutorRequest:
    return ExecutorRequest(
        worktree=Path("/tmp/agent-run-1"),
        prompt="完成任务",
        run_id="run-1",
        model=model,
    )


def test_opencode_command_uses_worktree_and_optional_model() -> None:
    executor = OpenCodeExecutor(command="opencode", endpoint="http://127.0.0.1:4096")

    command = executor.command_for(request())

    assert command[:4] == ["opencode", "run", "--format", "json"]
    # Auto only resolves "ask"; explicit inline deny rules remain enforced.
    assert "--auto" in command
    assert command[command.index("--dir") + 1] == "/tmp/agent-run-1"
    assert command[command.index("--attach") + 1] == "http://127.0.0.1:4096"
    assert command[command.index("--model") + 1] == "provider/model"
    assert command[-1] == "完成任务"
    assert "codex" not in command


def test_opencode_read_only_profile_denies_edits_and_unlisted_shell_commands() -> None:
    executor = OpenCodeExecutor(command="opencode")
    environment = executor.environment_for(request())

    config = json.loads(environment["OPENCODE_CONFIG_CONTENT"])
    assert config["permission"]["edit"] == "deny"
    assert config["permission"]["external_directory"] == "deny"
    assert config["permission"]["bash"]["*"] == "deny"
    assert config["permission"]["bash"]["git diff *"] == "allow"
    assert (
        config["permission"]["bash"][
            "cd apps/quality-platform && .venv/bin/pytest *"
        ]
        == "allow"
    )
    assert config["permission"]["bash"].get("git push*", "deny") == "deny"


def test_opencode_write_profile_still_blocks_push_pr_and_merge() -> None:
    executor = OpenCodeExecutor(command="opencode")
    write_request = ExecutorRequest(
        worktree=Path("/tmp/work"),
        prompt="开发",
        run_id="run-write",
        sandbox="workspace-write",
    )
    config = json.loads(
        executor.environment_for(write_request)["OPENCODE_CONFIG_CONTENT"]
    )

    assert config["permission"]["edit"] == "allow"
    assert config["permission"]["bash"]["git push*"] == "deny"
    assert config["permission"]["bash"]["git merge*"] == "deny"
    assert config["permission"]["bash"]["gh pr create*"] == "deny"


def test_codex_command_uses_jsonl_read_only_worktree_and_optional_schema() -> None:
    executor = CodexExecutor(command="codex")
    command = executor.command_for(
        request(),
        output_file=Path("/tmp/final.json"),
        schema_file=Path("/tmp/schema.json"),
    )

    assert command[:3] == ["codex", "exec", "--json"]
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert command[command.index("-C") + 1] == "/tmp/agent-run-1"
    assert command[command.index("-m") + 1] == "provider/model"
    assert command[command.index("-o") + 1] == "/tmp/final.json"
    assert command[command.index("--output-schema") + 1] == "/tmp/schema.json"
    assert command[-1] == "完成任务"


def test_failure_classification_keeps_specific_operational_reasons() -> None:
    assert classify_failure("401 Unauthorized", 401) == "authentication_failed"
    assert classify_failure("ProviderModelNotFoundError") == "model_unavailable"
    assert classify_failure("CreditsError: insufficient balance") == "insufficient_balance"
    assert classify_failure("too many requests", 429) == "rate_limited"
    assert classify_failure("socket closed") == "executor_error"


class MemoryRunRepository:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.recorded_events: list[dict[str, Any]] = []

    def create(self, run: dict[str, Any]) -> dict[str, Any]:
        row = {**run, "status": "queued", "worktree_path": None, "branch_name": None}
        self.rows[str(row["id"])] = row
        return dict(row)

    def get(self, run_id: str) -> dict[str, Any] | None:
        row = self.rows.get(run_id)
        return dict(row) if row else None

    def update(self, run_id: str, **changes: Any) -> dict[str, Any]:
        self.rows[run_id].update(changes)
        return dict(self.rows[run_id])

    def append_event(self, **event: Any) -> dict[str, Any]:
        self.recorded_events.append(event)
        return event


class BlockingExecutor:
    name = "blocking"

    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.process: asyncio.subprocess.Process | None = None

    async def run(self, request, on_event, on_process):  # type: ignore[no-untyped-def]
        self.process = await asyncio.create_subprocess_exec(
            "bash",
            "-lc",
            "sleep 30",
            start_new_session=True,
        )
        on_process(self.process)
        self.started.set()
        await self.process.wait()
        raise AssertionError("阻塞执行器应在完成前被取消")


class DevelopmentRegistry:
    def __init__(self, repository: Path, revision: str) -> None:
        self.repository = repository
        self.revision = revision

    def get(self, agent_id: str) -> dict[str, Any]:
        return {
            "id": agent_id,
            "name": "开发 Agent",
            "default_executor": "blocking",
            "supported_executors": ["blocking"],
            "repository": str(self.repository),
            "revision": self.revision,
        }


def test_cancelling_active_run_terminates_real_process_group(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repository, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repository, check=True)
    (repository / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repository, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=repository, check=True, capture_output=True)
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    run_repository = MemoryRunRepository()
    executor = BlockingExecutor()
    service = AgentRunService(
        repository=run_repository,  # type: ignore[arg-type]
        registry=DevelopmentRegistry(repository, revision),  # type: ignore[arg-type]
        worktrees=WorktreeManager(tmp_path / "runs"),
        executors={"blocking": executor},  # type: ignore[dict-item]
        artifact_root=tmp_path / "artifacts",
    )

    async def scenario() -> None:
        run = await service.start(
            agent_id="development-agent",
            prompt="保持运行直到取消",
            title="取消测试",
            model=None,
        )
        await asyncio.wait_for(executor.started.wait(), timeout=5)
        cancelled = await service.cancel(str(run["id"]))
        assert cancelled["status"] == "cancelled"
        assert executor.process is not None
        assert executor.process.returncode is not None
        assert any(
            event["event_type"] == "run.cancelled"
            for event in run_repository.recorded_events
        )

    asyncio.run(scenario())
