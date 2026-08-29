from __future__ import annotations

import asyncio
import json
import os
import signal
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable


EventCallback = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass(frozen=True)
class OpenCodeResult:
    exit_code: int
    session_id: str | None
    final_message: str
    failure_code: str | None = None
    failure_reason: str | None = None


def classify_failure(message: str, status_code: int | None = None) -> str:
    folded = message.casefold()
    if "insufficient balance" in folded or "creditserror" in folded:
        return "insufficient_balance"
    if status_code in {401, 403} or any(
        marker in folded
        for marker in ("unauthorized", "forbidden", "invalid api key", "authentication")
    ):
        return "authentication_failed"
    if any(
        marker in folded
        for marker in ("model not found", "providermodelnotfounderror", "model is not available")
    ):
        return "model_unavailable"
    if status_code == 429 or "rate limit" in folded or "too many requests" in folded:
        return "rate_limited"
    return "opencode_error"


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
    """Stop a local OpenCode server child that outlives the CLI process."""

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


class OpenCodeExecutor:
    def __init__(self, *, command: str = "opencode", endpoint: str = "") -> None:
        self.command = command
        self.endpoint = endpoint.strip()

    def command_for(
        self,
        *,
        worktree: Path,
        prompt: str,
        run_id: str,
        model: str | None,
    ) -> list[str]:
        argv = [
            self.command,
            "run",
            "--format",
            "json",
            "--auto",
            "--dir",
            str(worktree),
            "--title",
            run_id,
        ]
        if self.endpoint:
            argv.extend(["--attach", self.endpoint])
        if model:
            argv.extend(["--model", model])
        argv.append(prompt)
        return argv

    async def run(
        self,
        *,
        worktree: Path,
        prompt: str,
        run_id: str,
        model: str | None,
        on_event: EventCallback,
        on_process: Callable[[asyncio.subprocess.Process], None],
    ) -> OpenCodeResult:
        process = await asyncio.create_subprocess_exec(
            *self.command_for(
                worktree=worktree,
                prompt=prompt,
                run_id=run_id,
                model=model,
            ),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=worktree,
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
        return OpenCodeResult(
            exit_code=exit_code,
            session_id=session_id,
            final_message=final_message,
            failure_code=failure_code,
            failure_reason=failure_reason,
        )
