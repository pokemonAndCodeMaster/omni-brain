from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from typing import Any, Awaitable, Callable

from .executor import (
    ExecutorHealth,
    ExecutorRequest,
    ExecutorResult,
    SUBPROCESS_STREAM_LIMIT,
    classify_failure,
    cleanup_process_group,
    terminate_process,
)


EventCallback = Callable[[dict[str, Any]], Awaitable[None]]


def _nested(value: Any, keys: set[str]) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and item is not None and not isinstance(item, (dict, list)):
                return str(item)
            found = _nested(item, keys)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = _nested(item, keys)
            if found:
                return found
    return None


def _text(value: Any) -> str:
    return _nested(value, {"text", "message", "content"}) or ""


def _event_summary(payload: dict[str, Any], event_type: str) -> str:
    part = payload.get("part")
    part_value = part if isinstance(part, dict) else {}
    part_type = str(part_value.get("type", ""))
    if event_type == "text" or part_type == "text":
        return str(part_value.get("text") or payload.get("text") or "text")
    if event_type == "tool_use" or part_type == "tool":
        tool = str(part_value.get("tool") or "tool")
        state = part_value.get("state")
        state_value = state if isinstance(state, dict) else {}
        title = str(state_value.get("title") or "")
        return f"{tool}: {title}" if title else tool
    if event_type == "step_finish" or part_type == "step-finish":
        reason = str(part_value.get("reason") or "finished")
        tokens = part_value.get("tokens")
        token_value = tokens if isinstance(tokens, dict) else {}
        total = token_value.get("total")
        return f"{reason} · {total} tokens" if total is not None else reason
    return _text(payload) or event_type


class OpenCodeExecutor:
    name = "opencode"

    def __init__(self, *, command: str = "opencode", endpoint: str = "") -> None:
        self.command = command
        self.endpoint = endpoint.strip()

    def health(self) -> ExecutorHealth:
        resolved = shutil.which(self.command)
        if not resolved:
            return ExecutorHealth(
                name=self.name,
                available=False,
                command=self.command,
                reason=f"找不到命令：{self.command}",
                details={"endpoint": self.endpoint or None},
            )
        try:
            result = subprocess.run(
                [resolved, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return ExecutorHealth(
                name=self.name,
                available=False,
                command=resolved,
                reason=str(exc),
                details={"endpoint": self.endpoint or None},
            )
        lines = (result.stdout or result.stderr).strip().splitlines()
        return ExecutorHealth(
            name=self.name,
            available=result.returncode == 0,
            command=resolved,
            version=lines[0] if lines else None,
            reason=None if result.returncode == 0 else "OpenCode 版本检查失败",
            details={"endpoint": self.endpoint or None},
        )

    def command_for(
        self,
        request: ExecutorRequest,
    ) -> list[str]:
        argv = [
            self.command,
            "run",
            "--format",
            "json",
            "--auto",
            "--dir",
            str(request.worktree),
            "--title",
            request.run_id,
        ]
        if self.endpoint:
            argv.extend(["--attach", self.endpoint])
        if request.model:
            argv.extend(["--model", request.model])
        argv.append(request.prompt)
        return argv

    async def run(
        self,
        request: ExecutorRequest,
        on_event: EventCallback,
        on_process: Callable[[asyncio.subprocess.Process], None],
    ) -> ExecutorResult:
        process = await asyncio.create_subprocess_exec(
            *self.command_for(request),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=SUBPROCESS_STREAM_LIMIT,
            cwd=request.worktree,
            env=os.environ.copy(),
            start_new_session=os.name == "posix",
        )
        on_process(process)
        session_id: str | None = None
        final_message = ""
        failure_reason: str | None = None
        failure_code: str | None = None
        captured: dict[str, list[str]] = {"stdout": [], "stderr": []}

        async def read(stream: asyncio.StreamReader | None, channel: str) -> None:
            nonlocal session_id, final_message, failure_reason, failure_code
            if stream is None:
                return
            while raw := await stream.readline():
                line = raw.decode("utf-8", errors="replace").rstrip("\n")
                if line and len(captured[channel]) < 200:
                    captured[channel].append(line)
                payload: dict[str, Any]
                try:
                    parsed = json.loads(line)
                    payload = parsed if isinstance(parsed, dict) else {"value": parsed}
                except json.JSONDecodeError:
                    payload = {"text": line}
                event_type = str(payload.get("type") or payload.get("event") or f"opencode.{channel}")
                found_session = _nested(
                    payload,
                    {"session_id", "sessionId", "sessionID", "thread_id", "threadId"},
                )
                if found_session:
                    session_id = found_session
                text = _event_summary(payload, event_type)
                part = payload.get("part")
                part_value = part if isinstance(part, dict) else {}
                if event_type == "text" or str(part_value.get("type", "")) == "text":
                    final_message = text
                if event_type.casefold() == "error":
                    failure_reason = _text(payload) or "OpenCode 返回错误事件"
                    raw_status = _nested(payload, {"statusCode", "status_code"})
                    try:
                        status_code = int(raw_status) if raw_status else None
                    except ValueError:
                        status_code = None
                    failure_code = classify_failure(failure_reason, status_code)
                    final_message = failure_reason
                await on_event(
                    {
                        "event_type": event_type,
                        "source": "opencode",
                        "channel": channel,
                        "summary": text,
                        "payload": payload,
                    }
                )

        readers = [
            asyncio.create_task(read(process.stdout, "stdout")),
            asyncio.create_task(read(process.stderr, "stderr")),
        ]
        try:
            exit_code = await process.wait()
            await cleanup_process_group(process)
            await asyncio.gather(*readers)
        except BaseException:
            await terminate_process(process)
            for reader in readers:
                reader.cancel()
            await asyncio.gather(*readers, return_exceptions=True)
            raise

        if exit_code != 0 and not failure_reason:
            failure_reason = "\n".join(captured["stderr"] or captured["stdout"]).strip()
            failure_reason = failure_reason or f"OpenCode 退出码 {exit_code}"
            failure_code = classify_failure(failure_reason)
            final_message = failure_reason
        return ExecutorResult(
            executor=self.name,
            exit_code=exit_code,
            session_id=session_id,
            final_message=final_message,
            failure_code=failure_code,
            failure_reason=failure_reason,
        )
