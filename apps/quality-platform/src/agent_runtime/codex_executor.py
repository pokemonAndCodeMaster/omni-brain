from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .executor import (
    EventCallback,
    ExecutorHealth,
    ExecutorRequest,
    ExecutorResult,
    ProcessCallback,
    SUBPROCESS_STREAM_LIMIT,
    classify_failure,
    cleanup_process_group,
    terminate_process,
)


def _codex_summary(payload: dict[str, Any], event_type: str) -> str:
    item = payload.get("item")
    item_value = item if isinstance(item, dict) else {}
    item_type = str(item_value.get("type") or "")
    if item_type == "agent_message":
        return str(item_value.get("text") or "Agent 已返回消息")
    if item_type == "command_execution":
        command = item_value.get("command")
        status = item_value.get("status")
        return f"{command or 'command'} · {status or 'updated'}"
    if item_type == "file_change":
        return str(item_value.get("path") or item_value.get("summary") or "文件发生变化")
    if item_type:
        return str(item_value.get("text") or item_value.get("summary") or item_type)
    if event_type == "turn.completed":
        usage = payload.get("usage")
        return f"执行完成 · usage={json.dumps(usage, ensure_ascii=False)}"
    if event_type == "error":
        return str(payload.get("message") or payload.get("error") or "Codex 返回错误")
    return event_type


class CodexExecutor:
    name = "codex"

    def __init__(self, *, command: str = "codex") -> None:
        self.command = command

    def health(self) -> ExecutorHealth:
        resolved = shutil.which(self.command)
        if not resolved:
            return ExecutorHealth(
                name=self.name,
                available=False,
                command=self.command,
                reason=f"找不到命令：{self.command}",
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
            )
        lines = (result.stdout or result.stderr).strip().splitlines()
        return ExecutorHealth(
            name=self.name,
            available=result.returncode == 0,
            command=resolved,
            version=lines[0] if lines else None,
            reason=None if result.returncode == 0 else "Codex 版本检查失败",
        )

    def command_for(
        self,
        request: ExecutorRequest,
        *,
        output_file: Path | None = None,
        schema_file: Path | None = None,
    ) -> list[str]:
        argv = [
            *request.command_prefix,
            self.command,
            "exec",
            "--json",
            "--color",
            "never",
            "--sandbox",
            request.sandbox,
            "-C",
            str(request.worktree_argument or request.worktree),
        ]
        if request.model:
            argv.extend(["-m", request.model])
        if output_file is not None:
            argv.extend(["-o", str(output_file)])
        if schema_file is not None:
            argv.extend(["--output-schema", str(schema_file)])
        argv.append(request.prompt)
        return argv

    async def run(
        self,
        request: ExecutorRequest,
        on_event: EventCallback,
        on_process: ProcessCallback,
    ) -> ExecutorResult:
        artifact_path = request.artifact_path
        output_file = artifact_path / "final-output.txt" if artifact_path else None
        schema_file = artifact_path / "output-schema.json" if artifact_path and request.output_schema else None
        output_argument = (
            request.artifact_argument_root / "final-output.txt"
            if request.artifact_argument_root and output_file
            else output_file
        )
        schema_argument = (
            request.artifact_argument_root / "output-schema.json"
            if request.artifact_argument_root and schema_file
            else schema_file
        )
        if schema_file is not None:
            schema_file.write_text(
                json.dumps(request.output_schema, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        process = await asyncio.create_subprocess_exec(
            *self.command_for(
                request,
                output_file=output_argument,
                schema_file=schema_argument,
            ),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=SUBPROCESS_STREAM_LIMIT,
            cwd=request.worktree,
            env={
                **(os.environ if request.inherit_environment else {}),
                **request.environment,
            },
            start_new_session=os.name == "posix",
        )
        on_process(process)
        session_id: str | None = None
        final_message = ""
        final_payload: dict[str, Any] | None = None
        failure_reason: str | None = None
        failure_code: str | None = None
        turn_completed = False
        captured: dict[str, list[str]] = {"stdout": [], "stderr": []}

        async def read_stdout(stream: asyncio.StreamReader | None) -> None:
            nonlocal session_id, final_message, final_payload
            nonlocal failure_reason, failure_code, turn_completed
            if stream is None:
                return
            while raw := await stream.readline():
                line = raw.decode("utf-8", errors="replace").rstrip("\n")
                if line and len(captured["stdout"]) < 200:
                    captured["stdout"].append(line)
                try:
                    parsed = json.loads(line)
                    payload = parsed if isinstance(parsed, dict) else {"value": parsed}
                except json.JSONDecodeError:
                    payload = {"text": line}
                event_type = str(payload.get("type") or "codex.stdout")
                if event_type == "thread.started" and payload.get("thread_id"):
                    session_id = str(payload["thread_id"])
                item = payload.get("item")
                item_value = item if isinstance(item, dict) else {}
                if event_type == "item.completed" and item_value.get("type") == "agent_message":
                    final_message = str(item_value.get("text") or "")
                    try:
                        maybe_payload = json.loads(final_message)
                    except json.JSONDecodeError:
                        maybe_payload = None
                    if isinstance(maybe_payload, dict):
                        final_payload = maybe_payload
                if event_type == "turn.completed":
                    turn_completed = True
                if event_type == "error":
                    failure_reason = _codex_summary(payload, event_type)
                    failure_code = classify_failure(failure_reason)
                await on_event(
                    {
                        "event_type": event_type,
                        "source": self.name,
                        "channel": "stdout",
                        "summary": _codex_summary(payload, event_type),
                        "payload": payload,
                    }
                )

        async def read_stderr(stream: asyncio.StreamReader | None) -> None:
            if stream is None:
                return
            while raw := await stream.readline():
                line = raw.decode("utf-8", errors="replace").rstrip("\n")
                if not line:
                    continue
                if len(captured["stderr"]) < 200:
                    captured["stderr"].append(line)
                await on_event(
                    {
                        "event_type": "executor.diagnostic",
                        "source": self.name,
                        "channel": "stderr",
                        "summary": line,
                        "payload": {"text": line},
                    }
                )

        readers = [
            asyncio.create_task(read_stdout(process.stdout)),
            asyncio.create_task(read_stderr(process.stderr)),
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

        if output_file is not None and output_file.exists():
            output_text = output_file.read_text(encoding="utf-8").strip()
            if output_text:
                final_message = output_text
                try:
                    maybe_payload = json.loads(output_text)
                except json.JSONDecodeError:
                    maybe_payload = None
                if isinstance(maybe_payload, dict):
                    final_payload = maybe_payload

        if exit_code != 0 and not failure_reason:
            failure_reason = "\n".join(captured["stderr"] or captured["stdout"]).strip()
            failure_reason = failure_reason or f"Codex 退出码 {exit_code}"
            failure_code = classify_failure(failure_reason)
        elif exit_code == 0 and not turn_completed and not failure_reason:
            failure_reason = "Codex 退出码为 0，但没有收到 turn.completed"
            failure_code = "executor_error"

        return ExecutorResult(
            executor=self.name,
            exit_code=exit_code,
            session_id=session_id,
            final_message=final_message,
            final_payload=final_payload,
            failure_code=failure_code,
            failure_reason=failure_reason,
        )
