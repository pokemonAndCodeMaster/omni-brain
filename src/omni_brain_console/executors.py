from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from .utils import first_text, nested_value, utc_now


EventCallback = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass
class ExecutionResult:
    exit_code: int
    session_id: str | None
    last_message: str
    error_message: str | None = None


class CliExecutor:
    def command(
        self,
        *,
        executor: str,
        worktree: Path,
        prompt: str,
        final_path: Path,
        model: str | None,
        session_id: str | None,
        run_id: str,
    ) -> tuple[list[str], bytes | None]:
        if executor == "codex":
            if session_id:
                argv = [
                    "codex",
                    "exec",
                    "resume",
                    "--json",
                    "-c",
                    'approval_policy="never"',
                    "-o",
                    str(final_path),
                ]
                if model:
                    argv.extend(["-m", model])
                argv.extend([session_id, "-"])
            else:
                argv = [
                    "codex",
                    "exec",
                    "--json",
                    "--color",
                    "never",
                    "-c",
                    'approval_policy="never"',
                    "-s",
                    "workspace-write",
                    "-C",
                    str(worktree),
                    "-o",
                    str(final_path),
                ]
                if model:
                    argv.extend(["-m", model])
                argv.append("-")
            return argv, prompt.encode("utf-8")
        if executor == "opencode":
            argv = [
                "opencode",
                "run",
                "--format",
                "json",
                "--auto",
                "--dir",
                str(worktree),
                "--title",
                run_id,
            ]
            if model:
                argv.extend(["--model", model])
            if session_id:
                argv.extend(["--session", session_id])
            argv.append(prompt)
            return argv, None
        raise ValueError(f"不支持的执行器：{executor}")

    async def run(
        self,
        *,
        executor: str,
        worktree: Path,
        prompt: str,
        final_path: Path,
        model: str | None,
        session_id: str | None,
        run_id: str,
        on_event: EventCallback,
        on_process: Callable[[asyncio.subprocess.Process], None],
    ) -> ExecutionResult:
        argv, stdin_data = self.command(
            executor=executor,
            worktree=worktree,
            prompt=prompt,
            final_path=final_path,
            model=model,
            session_id=session_id,
            run_id=run_id,
        )
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE if stdin_data is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=worktree,
        )
        on_process(process)
        if stdin_data is not None and process.stdin is not None:
            process.stdin.write(stdin_data)
            await process.stdin.drain()
            process.stdin.close()

        detected_session = session_id
        last_message = ""
        error_message: str | None = None

        async def read_stream(stream: asyncio.StreamReader | None, channel: str) -> None:
            nonlocal detected_session, error_message, last_message
            if stream is None:
                return
            while True:
                raw = await stream.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").rstrip("\n")
                payload: Any = line
                event_type = f"{executor}.{channel}"
                try:
                    payload = json.loads(line)
                    if isinstance(payload, dict):
                        event_type = str(
                            payload.get("type")
                            or payload.get("event")
                            or payload.get("method")
                            or event_type
                        )
                        found_session = nested_value(
                            payload,
                            {"thread_id", "threadId", "session_id", "sessionId", "sessionID"},
                        )
                        if found_session:
                            detected_session = found_session
                        text = first_text(payload)
                        if text:
                            last_message = text
                        if str(payload.get("type", "")).lower() == "error":
                            error_message = nested_value(payload, {"message"}) or text or "执行器错误"
                except json.JSONDecodeError:
                    if line.strip():
                        last_message = line.strip()
                await on_event(
                    {
                        "timestamp": utc_now(),
                        "source": executor,
                        "channel": channel,
                        "type": event_type,
                        "summary": (first_text(payload) if isinstance(payload, (dict, list)) else line) or event_type,
                        "payload": payload,
                    }
                )

        await asyncio.gather(
            read_stream(process.stdout, "stdout"),
            read_stream(process.stderr, "stderr"),
        )
        exit_code = await process.wait()
        if final_path.is_file():
            final_text = final_path.read_text(encoding="utf-8", errors="replace").strip()
            if final_text:
                last_message = final_text
        elif last_message:
            final_path.write_text(last_message + "\n", encoding="utf-8")
        return ExecutionResult(exit_code, detected_session, last_message, error_message)
