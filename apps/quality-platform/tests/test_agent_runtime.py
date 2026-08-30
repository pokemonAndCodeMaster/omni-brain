from __future__ import annotations

from pathlib import Path

from src.agent_runtime.codex_executor import CodexExecutor
from src.agent_runtime.executor import ExecutorRequest, classify_failure
from src.agent_runtime.opencode_executor import OpenCodeExecutor


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
    assert command[command.index("--dir") + 1] == "/tmp/agent-run-1"
    assert command[command.index("--attach") + 1] == "http://127.0.0.1:4096"
    assert command[command.index("--model") + 1] == "provider/model"
    assert command[-1] == "完成任务"
    assert "codex" not in command


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
