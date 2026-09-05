from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Protocol

from src.agent_runtime import CodexExecutor, ExecutorRequest, OpenCodeExecutor
from src.agent_runtime.executor import AgentExecutor, terminate_process


class WorkerClient(Protocol):
    async def claim(self, lease_seconds: int) -> dict[str, Any] | None: ...
    async def heartbeat(self, leases: list[dict[str, str]], lease_seconds: int) -> dict[str, Any]: ...
    async def event(self, run_id: str, payload: dict[str, Any]) -> None: ...
    async def report(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class ServiceWorkerClient:
    """In-process transport used by tests and a colocated worker."""

    def __init__(self, service: Any, workspace: str, machine_id: str, token: str) -> None:
        self.service = service
        self.workspace = workspace
        self.machine_id = machine_id
        self.token = token

    async def claim(self, lease_seconds: int) -> dict[str, Any] | None:
        return self.service.claim(
            self.workspace, self.machine_id, self.token, lease_seconds=lease_seconds
        )

    async def heartbeat(self, leases: list[dict[str, str]], lease_seconds: int) -> dict[str, Any]:
        return self.service.heartbeat(
            self.workspace,
            self.machine_id,
            self.token,
            leases=leases,
            lease_seconds=lease_seconds,
        )

    async def event(self, run_id: str, payload: dict[str, Any]) -> None:
        self.service.worker_event(
            self.workspace, self.machine_id, self.token, run_id, **payload
        )

    async def report(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.service.worker_report(
            self.workspace, self.machine_id, self.token, run_id, payload
        )


class HttpWorkerClient:
    """Same worker protocol over HTTP for a separate or remote execution node."""

    def __init__(self, server: str, workspace: str, machine_id: str, token: str) -> None:
        self.server = server.rstrip("/")
        self.workspace = workspace
        self.machine_id = machine_id
        self.token = token
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _request(self, suffix: str, payload: dict[str, Any]) -> Any:
        url = f"{self.server}/api/gongzuo/{self.workspace}/worker/{self.machine_id}{suffix}"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Gongzuo-Worker-Token": self.token,
            },
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Worker API {exc.code}: {detail}") from exc

    async def claim(self, lease_seconds: int) -> dict[str, Any] | None:
        return await asyncio.to_thread(
            self._request, "/claim", {"leaseSeconds": lease_seconds}
        )

    async def heartbeat(self, leases: list[dict[str, str]], lease_seconds: int) -> dict[str, Any]:
        values = [
            {"runId": lease["run_id"], "leaseId": lease["lease_id"]}
            for lease in leases
        ]
        return await asyncio.to_thread(
            self._request,
            "/heartbeat",
            {"leases": values, "leaseSeconds": lease_seconds},
        )

    async def event(self, run_id: str, payload: dict[str, Any]) -> None:
        body = {
            "leaseId": payload["lease_id"],
            "eventType": payload["event_type"],
            "source": payload.get("source", "worker"),
            "channel": payload.get("channel"),
            "summary": payload.get("summary", ""),
            "payload": payload.get("payload") or {},
        }
        await asyncio.to_thread(self._request, f"/runs/{run_id}/events", body)

    async def report(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "leaseId": payload["lease_id"],
            "outcome": payload["outcome"],
            "sessionId": payload.get("session_id"),
            "exitCode": payload.get("exit_code"),
            "result": payload.get("result"),
            "resultPayload": payload.get("result_payload"),
            "artifacts": payload.get("artifacts") or [],
            "evidence": payload.get("evidence") or [],
            "environment": payload.get("environment") or {},
            "failureCode": payload.get("failure_code"),
            "error": payload.get("error"),
        }
        return await asyncio.to_thread(self._request, f"/runs/{run_id}/report", body)


class GongzuoWorker:
    def __init__(
        self,
        *,
        client: WorkerClient,
        executors: dict[str, AgentExecutor],
        runtime_root: Path,
        machine_id: str,
        lease_seconds: int = 30,
        heartbeat_seconds: float = 5,
        concurrency: int = 1,
        repository_map: dict[str, str] | None = None,
    ) -> None:
        self.client = client
        self.executors = executors
        self.runtime_root = runtime_root.resolve()
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.machine_id = machine_id
        self.lease_seconds = lease_seconds
        self.heartbeat_seconds = heartbeat_seconds
        self.concurrency = concurrency
        self.repository_map = {
            str(Path(source)): str(Path(destination).expanduser().resolve())
            for source, destination in (repository_map or {}).items()
        }

    @staticmethod
    def _copy_auth_file(source: Path, destination: Path) -> None:
        if not source.is_file():
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        destination.chmod(0o600)

    @staticmethod
    def _copy_config_tree(source: Path, destination: Path) -> None:
        if not source.is_dir():
            return
        shutil.copytree(source, destination, dirs_exist_ok=True)

    def _isolated_environment(
        self,
        home: Path,
        *,
        workspace: str,
        engine: str,
    ) -> tuple[dict[str, str], bool]:
        home.mkdir(parents=True, exist_ok=True)
        config_home = home / ".config"
        data_home = home / ".local" / "share"
        inherit_environment = workspace == "personal"
        extra: dict[str, str] = {}
        if workspace == "team":
            allowlist = {
                name.strip()
                for name in os.environ.get("GONGZUO_TEAM_ENV_ALLOWLIST", "").split(",")
                if name.strip()
            }
            safe_names = {
                "PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ",
                "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
                "http_proxy", "https_proxy", "no_proxy",
            }
            extra.update(
                {name: value for name, value in os.environ.items() if name in safe_names | allowlist}
            )
        if engine == "codex":
            configured = os.environ.get("GONGZUO_TEAM_CODEX_HOME") if workspace == "team" else None
            if workspace == "team" and not configured:
                raise FileNotFoundError(
                    "团队 Codex 凭证未配置：必须设置 GONGZUO_TEAM_CODEX_HOME"
                )
            codex_source = Path(
                configured or os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
            )
            if workspace == "team" and not codex_source.is_dir():
                raise FileNotFoundError(f"团队 Codex 配置目录不可用：{codex_source}")
            for name in ("auth.json", "config.toml"):
                self._copy_auth_file(codex_source / name, home / ".codex" / name)
        elif engine == "opencode":
            if workspace == "team":
                data_source_value = os.environ.get("GONGZUO_TEAM_OPENCODE_DATA_HOME")
                config_source_value = os.environ.get("GONGZUO_TEAM_OPENCODE_CONFIG_HOME")
                explicit_config = os.environ.get("GONGZUO_TEAM_OPENCODE_CONFIG")
                if not data_source_value or not (config_source_value or explicit_config):
                    raise FileNotFoundError(
                        "团队 OpenCode 必须显式配置 GONGZUO_TEAM_OPENCODE_DATA_HOME，"
                        "以及 GONGZUO_TEAM_OPENCODE_CONFIG_HOME 或 GONGZUO_TEAM_OPENCODE_CONFIG"
                    )
                data_source = Path(data_source_value)
                config_source = Path(config_source_value) if config_source_value else None
            else:
                data_source = Path(
                    os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
                )
                config_source = Path(
                    os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
                )
                explicit_config = None
            if workspace == "team" and not data_source.is_dir():
                raise FileNotFoundError(f"团队 OpenCode data home 不可用：{data_source}")
            self._copy_auth_file(
                data_source / "opencode" / "auth.json",
                data_home / "opencode" / "auth.json",
            )
            if config_source:
                self._copy_config_tree(config_source / "opencode", config_home / "opencode")
            if explicit_config:
                config_file = Path(explicit_config)
                if not config_file.is_file():
                    raise FileNotFoundError(f"团队 OpenCode 配置文件不可用：{config_file}")
                destination = config_home / "opencode" / config_file.name
                self._copy_auth_file(config_file, destination)
                extra["OPENCODE_CONFIG"] = str(destination)
        return {
            **extra,
            "HOME": str(home),
            "CODEX_HOME": str(home / ".codex"),
            "XDG_CONFIG_HOME": str(config_home),
            "XDG_DATA_HOME": str(data_home),
            "XDG_STATE_HOME": str(home / ".local" / "state"),
            "XDG_CACHE_HOME": str(home / ".cache"),
        }, inherit_environment

    def _prepare_worktree(self, run: dict[str, Any]) -> tuple[Path, Path, Path]:
        run_root = self.runtime_root / str(run["workspace"]) / str(run["id"])
        worktree = run_root / "repo"
        artifacts = run_root / "artifacts"
        home = run_root / "home"
        artifacts.mkdir(parents=True, exist_ok=True)
        source_identity = run.get("repository_path")
        source_value = self.repository_map.get(str(source_identity), source_identity)
        revision = run.get("repository_revision")
        if source_identity and not Path(str(source_value)).is_dir():
            raise FileNotFoundError(
                f"执行机找不到仓库身份 {source_identity}；请配置 --repository-map"
            )
        if source_value and revision:
            commit = subprocess.run(
                ["git", "-C", str(source_value), "cat-file", "-e", f"{revision}^{{commit}}"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if commit.returncode != 0:
                raise FileNotFoundError(
                    f"执行机仓库缺少固定提交：{revision}（身份 {source_identity}）"
                )
        if worktree.exists():
            if any(worktree.iterdir()):
                raise RuntimeError(f"运行目录已经存在且非空：{worktree}")
        elif source_value and revision:
            worktree.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "-C", str(source_value), "worktree", "add", "--detach", str(worktree), str(revision)],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if run.get("sandbox") == "workspace-write" and run.get("branch"):
                subprocess.run(
                    ["git", "-C", str(worktree), "switch", "-c", str(run["branch"])],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
        elif source_value:
            shutil.copytree(str(source_value), worktree)
        else:
            worktree.mkdir(parents=True, exist_ok=True)
        return worktree, artifacts, home

    @staticmethod
    def _safe_capability_id(value: Any) -> str:
        cleaned = "".join(
            char if char.isalnum() or char in "._-" else "-" for char in str(value)
        ).strip(".-")
        return cleaned or "capability"

    def _materialize_capabilities(self, run: dict[str, Any], worktree: Path) -> list[str]:
        written: list[str] = []
        manifest: list[dict[str, Any]] = []
        for entry in run.get("capability_snapshot") or []:
            capability_id = self._safe_capability_id(entry.get("id"))
            target = str(entry.get("target") or "guidance").casefold()
            if target == "skill":
                destination = worktree / ".agents" / "skills" / capability_id / "SKILL.md"
            elif target == "knowledge":
                destination = worktree / ".gongzuo" / "knowledge" / f"{capability_id}.md"
            else:
                destination = worktree / ".gongzuo" / "runtime-guidance" / f"{capability_id}.md"
            destination.parent.mkdir(parents=True, exist_ok=True)
            status = "trial-candidate" if entry.get("isCandidate") else "published"
            content = str(entry.get("content") or "")
            if target == "skill":
                # A SKILL.md is executable input. Preserve its own frontmatter exactly;
                # Gongzuo provenance belongs in the adjacent manifest.
                destination.write_text(content.rstrip() + "\n", encoding="utf-8")
            else:
                destination.write_text(
                    f"<!-- gongzuo: {status}; version: {entry.get('version') or 'unknown'} -->\n\n"
                    f"{content.rstrip()}\n",
                    encoding="utf-8",
                )
            written.append(str(destination.relative_to(worktree)))
            manifest.append(
                {
                    "id": entry.get("id"),
                    "version": entry.get("version"),
                    "target": entry.get("target"),
                    "status": status,
                    "path": str(destination.relative_to(worktree)),
                }
            )
        if manifest:
            manifest_path = worktree / ".gongzuo" / "capability-manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        return written

    def _docker_prefix(self, run: dict[str, Any], worktree: Path, artifacts: Path, home: Path) -> tuple[str, ...]:
        docker = shutil.which("docker")
        image = run.get("image")
        if not docker:
            raise FileNotFoundError("Docker runtime 不可用：找不到 docker 命令")
        if not image:
            raise ValueError("Docker Run 没有固定镜像")
        inspected = subprocess.run(
            [docker, "image", "inspect", str(image)],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if inspected.returncode != 0:
            raise FileNotFoundError(f"Docker 镜像不可用：{image}")
        name = "gongzuo-" + "".join(
            char if char.isalnum() or char in "_.-" else "-" for char in str(run["id"])
        )
        return (
            docker,
            "run",
            "--rm",
            "--name",
            name,
            "--mount",
            f"type=bind,src={worktree},dst=/workspace",
            "--mount",
            f"type=bind,src={artifacts},dst=/artifacts",
            "--mount",
            f"type=bind,src={home},dst=/runner-home",
            "--workdir",
            "/workspace",
            "--env",
            "HOME=/runner-home",
            "--env",
            "CODEX_HOME=/runner-home/.codex",
            "--env",
            "XDG_DATA_HOME=/runner-home/.local/share",
            "--env",
            "XDG_STATE_HOME=/runner-home/.local/state",
            "--env",
            "XDG_CACHE_HOME=/runner-home/.cache",
            str(image),
        )

    @staticmethod
    def _environment_identity(values: dict[str, Any]) -> str:
        encoded = json.dumps(values, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    async def execute_once(self) -> bool:
        run = await self.client.claim(self.lease_seconds)
        if run is None:
            return False
        run_id = str(run["id"])
        lease_id = str(run["lease_id"])
        process: asyncio.subprocess.Process | None = None
        stop_outcome: str | None = None
        heartbeat_stop = asyncio.Event()
        heartbeat_task: asyncio.Task[None] | None = None

        async def heartbeat_loop() -> None:
            nonlocal stop_outcome
            while not heartbeat_stop.is_set():
                try:
                    await asyncio.wait_for(heartbeat_stop.wait(), timeout=self.heartbeat_seconds)
                    break
                except asyncio.TimeoutError:
                    response = await self.client.heartbeat(
                        [{"run_id": run_id, "lease_id": lease_id}], self.lease_seconds
                    )
                    command = next(
                        (entry for entry in response.get("commands", []) if entry.get("runId") == run_id),
                        None,
                    )
                    if not command or not command.get("leaseValid", False):
                        stop_outcome = "cancelled"
                    elif command.get("cancelRequested"):
                        stop_outcome = "cancelled"
                    elif command.get("pauseRequested"):
                        stop_outcome = "paused"
                    if stop_outcome and process is not None:
                        await terminate_process(process)
                        return

        try:
            executor = self.executors.get(str(run["engine"]))
            if executor is None:
                raise FileNotFoundError(f"Worker 未配置执行器：{run['engine']}")
            health = executor.health()
            if not health.available:
                raise FileNotFoundError(health.reason or f"执行器不可用：{run['engine']}")
            worktree, artifacts, home = self._prepare_worktree(run)
            materialized = self._materialize_capabilities(run, worktree)
            environment, inherit_environment = self._isolated_environment(
                home,
                workspace=str(run["workspace"]),
                engine=str(run["engine"]),
            )
            prefix: tuple[str, ...] = ()
            worktree_argument: Path | None = None
            artifact_argument_root: Path | None = None
            if run["runtime"] == "docker":
                prefix = self._docker_prefix(run, worktree, artifacts, home)
                worktree_argument = Path("/workspace")
                artifact_argument_root = Path("/artifacts")
            environment_snapshot: dict[str, Any] = {
                "machineId": self.machine_id,
                "hostname": socket.gethostname(),
                "runtime": run["runtime"],
                "image": run.get("image"),
                "executor": run["engine"],
                "executorCommand": health.command,
                "executorVersion": health.version,
                "repositoryRevision": run.get("repository_revision"),
                "actualDirectory": str(worktree),
                "sessionHome": str(home),
                "materializedCapabilities": materialized,
            }
            environment_snapshot["identity"] = self._environment_identity(environment_snapshot)
            initial_heartbeat = await self.client.heartbeat(
                [{"run_id": run_id, "lease_id": lease_id}], self.lease_seconds
            )
            initial_command = next(
                (
                    entry
                    for entry in initial_heartbeat.get("commands", [])
                    if entry.get("runId") == run_id
                ),
                None,
            )
            requested_outcome = (
                "cancelled"
                if initial_command and initial_command.get("cancelRequested")
                else "paused"
                if initial_command and initial_command.get("pauseRequested")
                else None
            )
            if requested_outcome:
                await self.client.report(
                    run_id,
                    {
                        "lease_id": lease_id,
                        "outcome": requested_outcome,
                        "environment": environment_snapshot,
                        "error": "执行器启动前已按控制端请求停止",
                    },
                )
                return True
            await self.client.report(
                run_id,
                {
                    "lease_id": lease_id,
                    "outcome": "running",
                    "environment": environment_snapshot,
                },
            )
            heartbeat_task = asyncio.create_task(heartbeat_loop())

            async def on_event(event: dict[str, Any]) -> None:
                await self.client.event(run_id, {"lease_id": lease_id, **event})

            def on_process(value: asyncio.subprocess.Process) -> None:
                nonlocal process
                process = value

            result = await executor.run(
                ExecutorRequest(
                    worktree=worktree,
                    prompt=str(run["prompt_snapshot"]),
                    run_id=run_id,
                    model=run.get("model"),
                    sandbox=str(run.get("sandbox") or "read-only"),
                    artifact_path=artifacts,
                    environment=environment,
                    command_prefix=prefix,
                    worktree_argument=worktree_argument,
                    artifact_argument_root=artifact_argument_root,
                    inherit_environment=inherit_environment,
                ),
                on_event,
                on_process,
            )
            heartbeat_stop.set()
            await heartbeat_task
            if stop_outcome:
                await self.client.report(
                    run_id,
                    {
                        "lease_id": lease_id,
                        "outcome": stop_outcome,
                        "session_id": result.session_id,
                        "exit_code": result.exit_code,
                        "environment": environment_snapshot,
                        "error": "运行已按控制端请求停止",
                    },
                )
                return True
            result_file = artifacts / "result.txt"
            result_file.write_text(result.final_message, encoding="utf-8")
            result_hash = "sha256:" + hashlib.sha256(result_file.read_bytes()).hexdigest()
            artifact_values = [
                {
                    "kind": "executor-result",
                    "ref": f"/api/gongzuo/{run['workspace']}/runs/{run_id}/artifacts/result",
                    "version": result_hash,
                    "mediaType": "text/plain",
                }
            ]
            succeeded = result.exit_code == 0 and not result.failure_reason
            await self.client.report(
                run_id,
                {
                    "lease_id": lease_id,
                    "outcome": "succeeded" if succeeded else "failed",
                    "session_id": result.session_id,
                    "exit_code": result.exit_code,
                    "result": result.final_message,
                    "result_payload": result.final_payload,
                    "artifacts": artifact_values,
                    "evidence": [
                        {
                            "kind": "technical-execution",
                            "executorCompleted": succeeded,
                            "exitCode": result.exit_code,
                            "artifactVersion": result_hash,
                            "environmentRef": environment_snapshot["identity"],
                            "businessAccepted": False,
                        }
                    ],
                    "environment": environment_snapshot,
                    "failure_code": result.failure_code,
                    "error": result.failure_reason,
                },
            )
            return True
        except asyncio.CancelledError:
            if process is not None:
                await terminate_process(process)
            raise
        except Exception as exc:
            heartbeat_stop.set()
            if heartbeat_task is not None:
                heartbeat_task.cancel()
                await asyncio.gather(heartbeat_task, return_exceptions=True)
            outcome = "unavailable" if isinstance(exc, FileNotFoundError) else "failed"
            try:
                await self.client.report(
                    run_id,
                    {
                        "lease_id": lease_id,
                        "outcome": outcome,
                        "failure_code": "runtime_unavailable" if outcome == "unavailable" else "worker_error",
                        "error": str(exc),
                        "environment": {
                            "machineId": self.machine_id,
                            "runtime": run.get("runtime"),
                            "image": run.get("image"),
                        },
                    },
                )
            except Exception:
                pass
            return True

    async def run_forever(self, poll_seconds: float = 2) -> None:
        while True:
            worked = await asyncio.gather(
                *(self.execute_once() for _ in range(self.concurrency))
            )
            if not any(worked):
                await asyncio.sleep(poll_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="共作远程/本地执行节点")
    parser.add_argument("--server", required=True)
    parser.add_argument("--workspace", choices=("personal", "team"))
    parser.add_argument("--machine-id")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--token-env", default="GONGZUO_WORKER_TOKEN")
    parser.add_argument(
        "--credential-file",
        type=Path,
        help="0600 私有 JSON（注册响应），可提供 workspace/id/workerToken",
    )
    parser.add_argument("--capacity", type=int, default=1)
    parser.add_argument(
        "--repository-map",
        type=Path,
        help="私有 JSON：控制端仓库身份绝对路径到本机 checkout 的映射",
    )
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    credential: dict[str, Any] = {}
    if args.credential_file:
        if args.credential_file.stat().st_mode & 0o077:
            parser.error("--credential-file 必须仅当前用户可读写（chmod 600）")
        parsed_credential = json.loads(args.credential_file.read_text(encoding="utf-8"))
        if not isinstance(parsed_credential, dict):
            parser.error("--credential-file 必须是 JSON 对象")
        credential = parsed_credential
    workspace = args.workspace or credential.get("workspace")
    machine_id = args.machine_id or credential.get("id")
    if workspace not in {"personal", "team"} or not machine_id:
        parser.error("必须通过参数或 credential file 提供 workspace 和 machine id")
    token = os.environ.get(args.token_env) or credential.get("workerToken")
    if not token:
        parser.error(f"环境变量 {args.token_env} 或 credential file 未提供 token")
    client = HttpWorkerClient(args.server, workspace, machine_id, str(token))
    repository_map: dict[str, str] = {}
    if args.repository_map:
        parsed = json.loads(args.repository_map.read_text(encoding="utf-8"))
        if not isinstance(parsed, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in parsed.items()
        ):
            parser.error("--repository-map 必须是字符串到字符串的 JSON 对象")
        repository_map = parsed
    worker = GongzuoWorker(
        client=client,
        executors={"codex": CodexExecutor(), "opencode": OpenCodeExecutor()},
        runtime_root=args.runtime_root,
        machine_id=str(machine_id),
        concurrency=args.capacity,
        repository_map=repository_map,
    )
    if args.once:
        return 0 if asyncio.run(worker.execute_once()) else 2
    asyncio.run(worker.run_forever())
    return 0


if __name__ == "__main__":
    sys.exit(main())
