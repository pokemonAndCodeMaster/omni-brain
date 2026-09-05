from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import subprocess
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.agent_runtime import AgentExecutor

from .repository import GongzuoRuntimeRepository


TERMINAL_STATES = {"paused", "cancelled", "succeeded", "failed", "unavailable"}
ACTIVE_STATES = {"claimed", "running", "pause_requested", "cancelling"}
WORKSPACES = {"personal", "team"}


class GongzuoRuntimeService:
    def __init__(
        self,
        *,
        repository: GongzuoRuntimeRepository,
        gongzuo_service: Any,
        executors: Mapping[str, AgentExecutor],
        runtime_root: Path,
        repository_root: Path | None = None,
        registration_tokens: Mapping[str, str] | None = None,
        capability_provider: Callable[[str, str | None], list[dict[str, Any]]] | None = None,
        offline_after_seconds: int = 45,
    ) -> None:
        self.repository = repository
        self.gongzuo_service = gongzuo_service
        self.executors = dict(executors)
        self.runtime_root = runtime_root.resolve()
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.repository_root = repository_root.resolve() if repository_root else None
        self.registration_tokens = dict(registration_tokens or {})
        self.capability_provider = capability_provider
        self.offline_after_seconds = offline_after_seconds

    @staticmethod
    def _workspace(workspace: str) -> str:
        if workspace not in WORKSPACES:
            raise ValueError(f"未知工作空间：{workspace}")
        return workspace

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _authenticate_registration(self, workspace: str, token: str | None) -> None:
        expected = self.registration_tokens.get(workspace)
        if not expected:
            raise RuntimeError(f"{workspace} 执行机注册凭证未配置")
        if not token or not hmac.compare_digest(token, expected):
            raise PermissionError("执行机注册凭证无效")

    def authenticate_worker(self, workspace: str, machine_id: str, token: str | None) -> dict[str, Any]:
        workspace = self._workspace(workspace)
        row = self.repository.machine_credentials(workspace, machine_id)
        if row is None or not token or not hmac.compare_digest(
            str(row["token_hash"]), self._token_hash(token)
        ):
            raise PermissionError("执行机凭证无效或不属于当前空间")
        return row

    def register_machine(
        self,
        workspace: str,
        *,
        registration_token: str | None,
        name: str,
        capacity: int,
        engines: list[str],
        runtimes: list[str],
        images: list[str],
        labels: dict[str, str],
    ) -> dict[str, Any]:
        workspace = self._workspace(workspace)
        self._authenticate_registration(workspace, registration_token)
        engine_values = sorted(set(engines))
        runtime_values = sorted(set(runtimes))
        if not engine_values or set(engine_values) - set(self.executors):
            raise ValueError("执行机必须声明服务端已知的执行器")
        if not runtime_values or set(runtime_values) - {"native", "docker"}:
            raise ValueError("执行机 runtime 只能是 native/docker")
        if "docker" in runtime_values and not images:
            raise ValueError("声明 docker 能力时必须列出已验证可用的镜像")
        raw_token = secrets.token_urlsafe(32)
        machine_id = f"node-{workspace[:1]}-{uuid4().hex[:12]}"
        row = self.repository.register_machine(
            {
                "id": machine_id,
                "workspace": workspace,
                "name": name,
                "token_hash": self._token_hash(raw_token),
                "capacity": capacity,
                "capabilities": {
                    "engines": engine_values,
                    "runtimes": runtime_values,
                    "images": sorted(set(images)),
                    "labels": labels,
                },
            }
        )
        return {**self._format_machine(row), "worker_token": raw_token}

    def list_machines(self, workspace: str) -> list[dict[str, Any]]:
        workspace = self._workspace(workspace)
        return [
            self._format_machine(row)
            for row in self.repository.list_machines(
                workspace, offline_after_seconds=self.offline_after_seconds
            )
        ]

    def machine_action(self, workspace: str, machine_id: str, action: str) -> dict[str, Any]:
        workspace = self._workspace(workspace)
        status = {"enable": "online", "pause": "paused", "drain": "draining"}[action]
        row = self.repository.set_machine_status(workspace, machine_id, status)
        return self._format_machine(row)

    @staticmethod
    def _format_machine(row: dict[str, Any]) -> dict[str, Any]:
        return {
            **row,
            "active_runs": int(row.get("active_runs") or 0),
            "current_run_id": row.get("current_run_id"),
        }

    @staticmethod
    def _git_identity(directory: Path) -> tuple[str | None, str | None]:
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"工作来源目录不存在：{directory}")
        try:
            top = subprocess.run(
                ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            revision = subprocess.run(
                ["git", "-C", top, "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            return str(Path(top).resolve()), revision
        except (OSError, subprocess.SubprocessError):
            return str(directory.resolve()), None

    @staticmethod
    def _safe_branch(item_id: str, run_suffix: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", item_id).strip("-.") or "item"
        return f"gongzuo/{safe}-{run_suffix}"

    @staticmethod
    def _prompt(
        *,
        item: dict[str, Any],
        context: dict[str, Any],
        capabilities: list[dict[str, Any]],
        instruction: str,
    ) -> str:
        capability_text = "\n\n".join(
            f"### {'试验候选' if entry.get('isCandidate') else '已发布能力'} · "
            f"{entry.get('title') or entry.get('id')} @ {entry.get('version')}\n"
            f"目标/适用对象：{entry.get('target') or '未声明'}\n"
            f"{entry.get('content') or ''}"
            for entry in capabilities
        ) or "（没有发布能力附加材料）"
        return (
            "# 共作委托的不可变运行输入\n\n"
            f"工作事项：{item.get('id') or item.get('itemId')}\n"
            f"事项快照：\n```json\n{json.dumps(item, ensure_ascii=False, indent=2, default=str)}\n```\n\n"
            f"已接受上下文版本：{context.get('versionId')} / v{context.get('revisionNo')}\n"
            f"上下文内容：\n{context.get('content') or ''}\n\n"
            f"共同上下文来源事项：{context.get('inheritedFromItemId') or context.get('itemId')}\n"
            f"本贡献的局部目标与范围：\n{context.get('focus') or '同上'}\n\n"
            f"来源：\n```json\n{json.dumps(context.get('sources') or [], ensure_ascii=False, indent=2, default=str)}\n```\n\n"
            f"## 已发布能力与本次候选覆盖\n{capability_text}\n\n"
            f"## 本次具体任务\n{instruction}\n\n"
            "请交付实际结果、未覆盖范围与可核验证据。技术执行结束不代表事项已被业务接受。\n"
        )

    @staticmethod
    def _json_snapshot(value: Any) -> Any:
        """Detach database rows/datetimes into an immutable JSON value."""
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))

    def create_run(
        self,
        workspace: str,
        *,
        item_id: str,
        instruction: str,
        engine: str,
        runtime: str = "native",
        image: str | None = None,
        directory: str | None = None,
        branch: str | None = None,
        model: str | None = None,
        machine_id: str | None = None,
        permission: str = "read-only",
        capability_candidate_id: str | None = None,
        actor_id: str = "admin",
    ) -> dict[str, Any]:
        workspace = self._workspace(workspace)
        if engine not in self.executors:
            raise ValueError(f"执行器未登记：{engine}")
        if runtime == "docker" and not image:
            raise ValueError("Docker 运行必须指定镜像")
        if machine_id:
            machine = self.repository.machine_credentials(workspace, machine_id)
            if machine is None:
                raise ValueError("指定执行机不存在或不属于当前空间")
            capabilities = machine.get("capabilities") or {}
            if engine not in (capabilities.get("engines") or []):
                raise ValueError(f"指定执行机不支持执行器：{engine}")
            if runtime not in (capabilities.get("runtimes") or []):
                raise ValueError(f"指定执行机不支持运行环境：{runtime}")
            if runtime == "docker" and image not in (capabilities.get("images") or []):
                raise ValueError(f"指定执行机没有声明镜像：{image}")
        item = self.gongzuo_service.get_item(workspace, item_id)
        context = self.gongzuo_service.current_context_snapshot(workspace, item_id)
        capabilities = (
            self.capability_provider(workspace, capability_candidate_id)
            if self.capability_provider
            else []
        )
        item = self._json_snapshot(item)
        context = self._json_snapshot(context)
        capabilities = self._json_snapshot(capabilities)
        attempt = self.repository.next_attempt(workspace, item_id)
        source = Path(directory).expanduser() if directory else self.repository_root
        repository_path: str | None = None
        repository_revision: str | None = None
        if source:
            repository_path, repository_revision = self._git_identity(source.resolve())
        run_id = f"gzrun-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
        execution_directory = self.runtime_root / workspace / run_id / "repo"
        run = self.repository.create_run(
            {
                "id": run_id,
                "workspace": workspace,
                "item_id": item_id,
                "attempt": attempt,
                "retry_of": None,
                "actor_id": actor_id,
                "instruction": instruction,
                "prompt_snapshot": self._prompt(
                    item=item, context=context, capabilities=capabilities, instruction=instruction
                ),
                "item_snapshot": item,
                "context_snapshot": context,
                "capability_snapshot": capabilities,
                "capability_candidate_id": capability_candidate_id,
                "context_version_id": str(context["versionId"]),
                "context_revision_no": int(context["revisionNo"]),
                "engine": engine,
                "runtime": runtime,
                "image": image,
                "requested_machine_id": machine_id,
                "model": model,
                "sandbox": permission,
                "repository_path": repository_path,
                "repository_revision": repository_revision,
                "directory": str(execution_directory),
                "branch": branch or (
                    self._safe_branch(item_id, run_id.rsplit("-", 1)[-1])
                    if repository_revision
                    else None
                ),
                "environment_snapshot": {
                    "requestedRuntime": runtime,
                    "requestedImage": image,
                },
                "artifact_candidates": [],
                "evidence_candidates": [],
            }
        )
        self.gongzuo_service.append_activity(
            workspace,
            item_id,
            kind="run.created",
            body=f"已创建委托 {run_id}，冻结上下文 v{context['revisionNo']}",
            actor_id=actor_id,
            payload={
                "runId": run_id,
                "attempt": int(run["attempt"]),
                "contextVersionId": context["versionId"],
                "engine": engine,
                "runtime": runtime,
            },
        )
        return self.format_run(run)

    def retry_run(
        self,
        workspace: str,
        run_id: str,
        *,
        sync_context: bool,
        instruction: str | None = None,
        machine_id: str | None = None,
        actor_id: str = "admin",
    ) -> dict[str, Any]:
        workspace = self._workspace(workspace)
        old = self._required_run(workspace, run_id)
        if old["state"] not in TERMINAL_STATES:
            raise ValueError("只有已结束或已暂停的尝试才能创建新尝试")
        item = self.gongzuo_service.get_item(workspace, str(old["item_id"]))
        context = (
            self.gongzuo_service.current_context_snapshot(workspace, str(old["item_id"]))
            if sync_context
            else old["context_snapshot"]
        )
        capabilities = (
            self.capability_provider(workspace, old.get("capability_candidate_id"))
            if sync_context and self.capability_provider
            else list(old.get("capability_snapshot") or [])
        )
        item = self._json_snapshot(item)
        context = self._json_snapshot(context)
        capabilities = self._json_snapshot(capabilities)
        new_instruction = instruction or str(old["instruction"])
        attempt = self.repository.next_attempt(workspace, str(old["item_id"]))
        new_id = f"gzrun-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
        new_directory = self.runtime_root / workspace / new_id / "repo"
        row = self.repository.create_run(
            {
                "id": new_id,
                "workspace": workspace,
                "item_id": old["item_id"],
                "attempt": attempt,
                "retry_of": run_id,
                "actor_id": actor_id,
                "instruction": new_instruction,
                "prompt_snapshot": self._prompt(
                    item=item,
                    context=context,
                    capabilities=capabilities,
                    instruction=new_instruction,
                ),
                "item_snapshot": item if sync_context else old["item_snapshot"],
                "context_snapshot": context,
                "capability_snapshot": capabilities,
                "capability_candidate_id": old.get("capability_candidate_id"),
                "context_version_id": context["versionId"],
                "context_revision_no": int(context["revisionNo"]),
                "engine": old["engine"],
                "runtime": old["runtime"],
                "image": old.get("image"),
                "requested_machine_id": machine_id,
                "model": old.get("model"),
                "sandbox": old["sandbox"],
                "repository_path": old.get("repository_path"),
                "repository_revision": old.get("repository_revision"),
                "directory": str(new_directory),
                "branch": self._safe_branch(
                    str(old["item_id"]), new_id.rsplit("-", 1)[-1]
                )
                if old.get("repository_revision")
                else None,
                "environment_snapshot": {
                    "requestedRuntime": old["runtime"],
                    "requestedImage": old.get("image"),
                    "retriedFrom": run_id,
                    "contextSynced": sync_context,
                },
                "artifact_candidates": [],
                "evidence_candidates": [],
            }
        )
        self.gongzuo_service.append_activity(
            workspace,
            str(old["item_id"]),
            kind="run.retried",
            body=f"从 {run_id} 创建新尝试 {new_id}；{'同步最新上下文' if sync_context else '继续使用旧上下文'}",
            actor_id=actor_id,
            payload={
                "runId": new_id,
                "retryOf": run_id,
                "syncContext": sync_context,
                "attempt": int(row["attempt"]),
            },
        )
        return self.format_run(row)

    def list_runs(
        self,
        workspace: str,
        *,
        limit: int,
        offset: int,
        item_id: str | None = None,
        states: tuple[str, ...] = (),
    ) -> tuple[list[dict[str, Any]], int]:
        workspace = self._workspace(workspace)
        rows, total = self.repository.list_runs(
            workspace, limit=limit, offset=offset, item_id=item_id, states=states
        )
        return [self.format_run(row) for row in rows], total

    def get_run(self, workspace: str, run_id: str) -> dict[str, Any]:
        return self.format_run(self._required_run(self._workspace(workspace), run_id))

    def get_run_snapshot(self, workspace: str, run_id: str) -> dict[str, Any]:
        """Internal verification entry; returns the stored immutable attempt snapshot."""
        return self._required_run(self._workspace(workspace), run_id)

    def _required_run(self, workspace: str, run_id: str) -> dict[str, Any]:
        row = self.repository.get_run(workspace, run_id)
        if row is None:
            raise KeyError(run_id)
        return row

    def format_run(self, row: dict[str, Any]) -> dict[str, Any]:
        current_rev: int | None = None
        stale_context = False
        try:
            current = self.gongzuo_service.current_context_snapshot(
                str(row["workspace"]), str(row["item_id"])
            )
            current_rev = int(current["revisionNo"])
            stale_context = (
                current["versionId"] != row["context_version_id"]
                or current.get("contextRefs") != (row.get("context_snapshot") or {}).get("contextRefs")
            )
        except (KeyError, ValueError):
            pass
        capabilities = [
            {
                key: entry.get(key)
                for key in ("id", "target", "title", "version", "verificationId", "isCandidate")
                if key in entry
            }
            for entry in (row.get("capability_snapshot") or [])
        ]
        return {
            **row,
            "machine": row.get("machine_id"),
            "session": row.get("session_id"),
            "rev": int(row["context_revision_no"]),
            "capabilities": capabilities,
            "stale_context": stale_context,
            "current_rev": current_rev,
            "business_accepted": False,
        }

    def events(self, workspace: str, run_id: str, *, after_sequence: int, limit: int) -> list[dict[str, Any]]:
        workspace = self._workspace(workspace)
        self._required_run(workspace, run_id)
        return self.repository.events(
            workspace, run_id, after_sequence=after_sequence, limit=limit
        )

    def request_cancel(self, workspace: str, run_id: str) -> dict[str, Any]:
        workspace = self._workspace(workspace)
        row = self.repository.request_stop(workspace, run_id, pause=False)
        self.repository.append_event(
            workspace=workspace,
            run_id=run_id,
            event_type="run.cancel_requested" if row["state"] == "cancelling" else "run.cancelled",
            source="platform",
            summary="用户请求取消；运行中任务等待 Worker 确认" if row["state"] == "cancelling" else "排队中的委托已取消",
            payload={},
        )
        return self.format_run(row)

    def request_pause(self, workspace: str, run_id: str) -> dict[str, Any]:
        workspace = self._workspace(workspace)
        row = self.repository.request_stop(workspace, run_id, pause=True)
        self.repository.append_event(
            workspace=workspace,
            run_id=run_id,
            event_type="run.pause_requested" if row["state"] == "pause_requested" else "run.paused",
            source="platform",
            summary="用户请求暂停；运行中任务等待 Worker 停止" if row["state"] == "pause_requested" else "排队中的委托已暂停",
            payload={},
        )
        return self.format_run(row)

    def claim(self, workspace: str, machine_id: str, token: str | None, *, lease_seconds: int) -> dict[str, Any] | None:
        self.authenticate_worker(workspace, machine_id, token)
        lease_id = secrets.token_urlsafe(24)
        return self.repository.claim_next(
            workspace=workspace,
            machine_id=machine_id,
            lease_id=lease_id,
            lease_seconds=lease_seconds,
        )

    def heartbeat(
        self,
        workspace: str,
        machine_id: str,
        token: str | None,
        *,
        leases: list[dict[str, str]],
        lease_seconds: int,
    ) -> dict[str, Any]:
        self.authenticate_worker(workspace, machine_id, token)
        commands = self.repository.heartbeat(
            workspace=workspace,
            machine_id=machine_id,
            leases=leases,
            lease_seconds=lease_seconds,
        )
        return {"commands": commands, "serverTime": datetime.now(timezone.utc).isoformat()}

    def worker_event(
        self,
        workspace: str,
        machine_id: str,
        token: str | None,
        run_id: str,
        *,
        lease_id: str,
        event_type: str,
        source: str,
        channel: str | None,
        summary: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self.authenticate_worker(workspace, machine_id, token)
        return self.repository.append_event(
            workspace=workspace,
            run_id=run_id,
            event_type=event_type,
            source=source,
            channel=channel,
            summary=summary,
            payload=payload,
            machine_id=machine_id,
            lease_id=lease_id,
        )

    def worker_report(
        self,
        workspace: str,
        machine_id: str,
        token: str | None,
        run_id: str,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        self.authenticate_worker(workspace, machine_id, token)
        existing = self._required_run(workspace, run_id)
        outcome = str(report["outcome"])
        if outcome == "running" and existing["state"] != "claimed":
            raise ValueError("只有已领取的 Run 可以进入 running")
        if outcome in {"cancelled", "paused"}:
            expected = "cancelling" if outcome == "cancelled" else "pause_requested"
            if existing["state"] != expected:
                raise ValueError(f"Run 未处于 {expected}，不能回报 {outcome}")
        if outcome == "succeeded" and report.get("exit_code") not in {None, 0}:
            raise ValueError("非零退出码不能回报 succeeded")
        now = datetime.now(timezone.utc)
        changes: dict[str, Any] = {
            "state": outcome,
            "session_id": report.get("session_id"),
            "environment_snapshot": report.get("environment") or existing.get("environment_snapshot") or {},
        }
        if outcome == "running":
            changes["started_at"] = now
        else:
            changes.update(
                {
                    "finished_at": now,
                    "exit_code": report.get("exit_code"),
                    "result": report.get("result"),
                    "result_payload": report.get("result_payload"),
                    "artifact_candidates": report.get("artifacts") or [],
                    "evidence_candidates": report.get("evidence") or [],
                    "failure_code": report.get("failure_code"),
                    "error": report.get("error"),
                }
            )
        row = self.repository.worker_report(
            workspace=workspace,
            machine_id=machine_id,
            run_id=run_id,
            lease_id=str(report["lease_id"]),
            changes=changes,
        )
        effective_outcome = str(row["state"])
        self.repository.append_event(
            workspace=workspace,
            run_id=run_id,
            event_type=f"run.{effective_outcome}",
            source="worker",
            summary=(
                "执行器已启动" if effective_outcome == "running"
                else "取消请求已生效；迟到输出已保留为候选" if effective_outcome == "cancelled"
                else "暂停请求已生效；迟到输出已保留为候选" if effective_outcome == "paused"
                else "技术执行已结束，结果等待人工判断" if effective_outcome == "succeeded"
                else report.get("error") or f"运行状态：{effective_outcome}"
            ),
            payload={
                "exitCode": report.get("exit_code"),
                "machineId": machine_id,
                "reportedOutcome": outcome,
                "effectiveOutcome": effective_outcome,
            },
        )
        if effective_outcome in TERMINAL_STATES:
            self.gongzuo_service.append_activity(
                workspace,
                str(row["item_id"]),
                kind=f"run.{effective_outcome}",
                body=(
                    f"委托 {run_id} 技术执行完成，已形成待审结果"
                    if effective_outcome == "succeeded"
                    else f"委托 {run_id} 结束：{effective_outcome}"
                ),
                actor_id="worker",
                payload={
                    "runId": run_id,
                    "state": effective_outcome,
                    "reportedOutcome": outcome,
                    "exitCode": report.get("exit_code"),
                },
            )
            artifacts = report.get("artifacts") or []
            if artifacts:
                artifact = artifacts[0]
                artifact_ref = artifact.get("ref")
                artifact_version = artifact.get("version")
                environment_ref = (report.get("environment") or {}).get("identity")
                if artifact_ref and artifact_version and environment_ref:
                    self.gongzuo_service.add_run_evidence_link(
                        workspace,
                        str(row["item_id"]),
                        run_id=run_id,
                        artifact_ref=str(artifact_ref),
                        artifact_version=str(artifact_version),
                        environment_ref=str(environment_ref),
                        actor_id="worker",
                        summary="技术执行产物候选；仍需按事项验收标准人工接受",
                    )
        return self.format_run(row)

    def recover_expired_leases(self) -> int:
        return self.repository.recover_expired_leases()
