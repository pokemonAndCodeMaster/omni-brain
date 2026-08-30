from __future__ import annotations

import asyncio
import os
import signal
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Protocol


EventCallback = Callable[[dict[str, Any]], Awaitable[None]]
ProcessCallback = Callable[[asyncio.subprocess.Process], None]
SUBPROCESS_STREAM_LIMIT = 16 * 1024 * 1024


@dataclass(frozen=True)
class ExecutorRequest:
    worktree: Path
    prompt: str
    run_id: str
    model: str | None = None
    sandbox: str = "read-only"
    output_schema: dict[str, Any] | None = None
    artifact_path: Path | None = None


@dataclass(frozen=True)
class ExecutorResult:
    executor: str
    exit_code: int
    session_id: str | None
    final_message: str
    final_payload: dict[str, Any] | None = None
    failure_code: str | None = None
    failure_reason: str | None = None


@dataclass(frozen=True)
class ExecutorHealth:
    name: str
    available: bool
    command: str
    version: str | None = None
    reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class AgentExecutor(Protocol):
    name: str

    def health(self) -> ExecutorHealth: ...

    async def run(
        self,
        request: ExecutorRequest,
        on_event: EventCallback,
        on_process: ProcessCallback,
    ) -> ExecutorResult: ...


def classify_failure(message: str, status_code: int | None = None) -> str:
    folded = message.casefold()
    if "insufficient balance" in folded or "creditserror" in folded:
        return "insufficient_balance"
    if status_code in {401, 403} or any(
        marker in folded
        for marker in (
            "unauthorized",
            "forbidden",
            "invalid api key",
            "authentication",
            "not logged in",
        )
    ):
        return "authentication_failed"
    if any(
        marker in folded
        for marker in (
            "model not found",
            "providermodelnotfounderror",
            "model is not available",
            "unsupported model",
        )
    ):
        return "model_unavailable"
    if status_code == 429 or "rate limit" in folded or "too many requests" in folded:
        return "rate_limited"
    return "executor_error"


async def terminate_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    else:
        process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except asyncio.TimeoutError:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        await process.wait()


async def cleanup_process_group(process: asyncio.subprocess.Process) -> None:
    """Stop a detached executor child that outlives its CLI parent."""

    if os.name != "posix":
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    await asyncio.sleep(0.05)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
