from __future__ import annotations

from pathlib import Path

from src.agent_runtime.opencode_executor import OpenCodeExecutor, classify_failure


def test_opencode_command_uses_worktree_and_optional_model() -> None:
    executor = OpenCodeExecutor(command="opencode", endpoint="http://127.0.0.1:4096")

    command = executor.command_for(
        worktree=Path("/tmp/agent-run-1"),
        prompt="完成任务",
        run_id="run-1",
        model="provider/model",
    )

    assert command[:4] == ["opencode", "run", "--format", "json"]
    assert command[command.index("--dir") + 1] == "/tmp/agent-run-1"
    assert command[command.index("--attach") + 1] == "http://127.0.0.1:4096"
    assert command[command.index("--model") + 1] == "provider/model"
    assert command[-1] == "完成任务"
    assert "codex" not in command


def test_failure_classification_keeps_specific_operational_reasons() -> None:
    assert classify_failure("401 Unauthorized", 401) == "authentication_failed"
    assert classify_failure("ProviderModelNotFoundError") == "model_unavailable"
    assert classify_failure("CreditsError: insufficient balance") == "insufficient_balance"
    assert classify_failure("too many requests", 429) == "rate_limited"
    assert classify_failure("socket closed") == "opencode_error"
