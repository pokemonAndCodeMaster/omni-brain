from __future__ import annotations

import asyncio
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from src.agent_runtime import ExecutorHealth, ExecutorResult
from src.gongzuo_runtime.service import GongzuoRuntimeService
from src.gongzuo_runtime.worker import GongzuoWorker, ServiceWorkerClient


def now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryRuntimeRepository:
    def __init__(self) -> None:
        self.machines: dict[str, dict[str, Any]] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.run_events: dict[str, list[dict[str, Any]]] = {}

    def register_machine(self, machine: dict[str, Any]) -> dict[str, Any]:
        row = {
            **machine,
            "status": "online",
            "last_seen_at": now(),
            "created_at": now(),
            "updated_at": now(),
        }
        self.machines[str(row["id"])] = row
        return {key: value for key, value in row.items() if key != "token_hash"}

    def machine_credentials(self, workspace: str, machine_id: str) -> dict[str, Any] | None:
        row = self.machines.get(machine_id)
        return dict(row) if row and row["workspace"] == workspace else None

    def list_machines(self, workspace: str, *, offline_after_seconds: int) -> list[dict[str, Any]]:
        rows = []
        for machine in self.machines.values():
            if machine["workspace"] != workspace:
                continue
            active = [
                run for run in self.runs.values()
                if run.get("machine_id") == machine["id"]
                and run["state"] in {"claimed", "running", "pause_requested", "cancelling"}
                and run.get("lease_expires_at", now() - timedelta(seconds=1)) > now()
            ]
            status = machine["status"]
            if machine["last_seen_at"] < now() - timedelta(seconds=offline_after_seconds):
                status = "offline"
            rows.append(
                {
                    **{key: value for key, value in machine.items() if key != "token_hash"},
                    "status": status,
                    "active_runs": len(active),
                    "current_run_id": active[0]["id"] if active else None,
                }
            )
        return rows

    def set_machine_status(self, workspace: str, machine_id: str, status: str) -> dict[str, Any]:
        row = self.machine_credentials(workspace, machine_id)
        if row is None:
            raise KeyError(machine_id)
        self.machines[machine_id]["status"] = status
        return {key: value for key, value in self.machines[machine_id].items() if key != "token_hash"}

    def next_attempt(self, workspace: str, item_id: str) -> int:
        attempts = [
            int(run["attempt"]) for run in self.runs.values()
            if run["workspace"] == workspace and run["item_id"] == item_id
        ]
        return max(attempts, default=0) + 1

    def create_run(self, run: dict[str, Any]) -> dict[str, Any]:
        row = {
            **run,
            "state": "queued",
            "machine_id": None,
            "lease_id": None,
            "lease_expires_at": None,
            "session_id": None,
            "result": None,
            "result_payload": None,
            "exit_code": None,
            "failure_code": None,
            "error": None,
            "cancellation_requested_at": None,
            "created_at": now(),
            "claimed_at": None,
            "started_at": None,
            "finished_at": None,
            "updated_at": now(),
        }
        self.runs[str(row["id"])] = row
        self.run_events[str(row["id"])] = []
        self.append_event(
            workspace=str(row["workspace"]), run_id=str(row["id"]),
            event_type="run.queued", source="platform", summary="queued", payload={}
        )
        return dict(row)

    def get_run(self, workspace: str, run_id: str) -> dict[str, Any] | None:
        row = self.runs.get(run_id)
        return dict(row) if row and row["workspace"] == workspace else None

    def list_runs(self, workspace: str, *, limit: int, offset: int, item_id=None, states=()):
        rows = [run for run in self.runs.values() if run["workspace"] == workspace]
        if item_id:
            rows = [run for run in rows if run["item_id"] == item_id]
        if states:
            rows = [run for run in rows if run["state"] in states]
        return [dict(run) for run in rows[offset:offset + limit]], len(rows)

    def append_event(self, *, workspace: str, run_id: str, event_type: str, source: str,
                     summary: str, payload: dict[str, Any], channel=None, machine_id=None,
                     lease_id=None) -> dict[str, Any]:
        run = self.get_run(workspace, run_id)
        if run is None or (machine_id and run["machine_id"] != machine_id) or (
            lease_id and run["lease_id"] != lease_id
        ):
            raise PermissionError("lease mismatch")
        events = self.run_events[run_id]
        row = {
            "id": len(events) + 1,
            "run_id": run_id,
            "sequence": len(events) + 1,
            "occurred_at": now(),
            "event_type": event_type,
            "source": source,
            "channel": channel,
            "summary": summary,
            "payload": payload,
        }
        events.append(row)
        return row

    def events(self, workspace: str, run_id: str, *, after_sequence: int, limit: int):
        if self.get_run(workspace, run_id) is None:
            return []
        return [e for e in self.run_events[run_id] if e["sequence"] > after_sequence][:limit]

    def claim_next(self, *, workspace: str, machine_id: str, lease_id: str, lease_seconds: int):
        machine = self.machine_credentials(workspace, machine_id)
        if machine is None:
            raise KeyError(machine_id)
        self.machines[machine_id]["last_seen_at"] = now()
        if machine["status"] != "online":
            return None
        active = [
            run for run in self.runs.values()
            if run.get("machine_id") == machine_id
            and run["state"] in {"claimed", "running", "pause_requested", "cancelling"}
            and run.get("lease_expires_at", now() - timedelta(seconds=1)) > now()
        ]
        if len(active) >= machine["capacity"]:
            return None
        caps = machine["capabilities"]
        for run in self.runs.values():
            if run["workspace"] != workspace or run["state"] != "queued":
                continue
            if run["engine"] not in caps["engines"] or run["runtime"] not in caps["runtimes"]:
                continue
            if run.get("requested_machine_id") not in {None, machine_id}:
                continue
            if run["runtime"] == "docker" and run.get("image") not in caps["images"]:
                continue
            run.update(
                state="claimed", machine_id=machine_id, lease_id=lease_id,
                lease_expires_at=now() + timedelta(seconds=lease_seconds), claimed_at=now()
            )
            self.append_event(
                workspace=workspace, run_id=run["id"], event_type="run.claimed",
                source="worker", summary="claimed", payload={}
            )
            return dict(run)
        return None

    def heartbeat(self, *, workspace: str, machine_id: str, leases: list[dict[str, str]], lease_seconds: int):
        if self.machine_credentials(workspace, machine_id) is None:
            raise KeyError(machine_id)
        self.machines[machine_id]["last_seen_at"] = now()
        commands = []
        for lease in leases:
            run = self.runs.get(lease["run_id"])
            valid = bool(
                run and run.get("machine_id") == machine_id
                and run.get("lease_id") == lease["lease_id"]
                and run["state"] in {"claimed", "running", "pause_requested", "cancelling"}
            )
            if valid:
                run["lease_expires_at"] = now() + timedelta(seconds=lease_seconds)
            commands.append(
                {
                    "runId": lease["run_id"], "leaseValid": valid,
                    "cancelRequested": valid and run["state"] == "cancelling",
                    "pauseRequested": valid and run["state"] == "pause_requested",
                }
            )
        return commands

    def worker_report(self, *, workspace: str, machine_id: str, run_id: str,
                      lease_id: str, changes: dict[str, Any]):
        run = self.runs.get(run_id)
        if not run or run["workspace"] != workspace or run["machine_id"] != machine_id or run["lease_id"] != lease_id:
            raise PermissionError("lease mismatch")
        reported_state = changes["state"]
        if run["state"] == "cancelling":
            changes = {
                **changes,
                "state": "cancelling" if reported_state == "running" else "cancelled",
            }
        elif run["state"] == "pause_requested":
            changes = {
                **changes,
                "state": "pause_requested" if reported_state == "running" else "paused",
            }
        run.update(changes, updated_at=now())
        if changes["state"] in {"paused", "cancelled", "succeeded", "failed", "unavailable"}:
            run["lease_id"] = None
            run["lease_expires_at"] = None
        return {**run, "reported_state": reported_state}

    def request_stop(self, workspace: str, run_id: str, *, pause: bool):
        run = self.runs.get(run_id)
        if not run or run["workspace"] != workspace:
            raise KeyError(run_id)
        if run["state"] not in {"queued", "claimed", "running"}:
            raise ValueError("invalid state")
        run["state"] = ("paused" if pause else "cancelled") if run["state"] == "queued" else (
            "pause_requested" if pause else "cancelling"
        )
        run["cancellation_requested_at"] = now()
        return dict(run)

    def recover_expired_leases(self) -> int:
        count = 0
        for run in self.runs.values():
            if run["state"] in {"claimed", "running", "pause_requested", "cancelling"} and run["lease_expires_at"] <= now():
                run.update(state="failed", failure_code="lease_expired", lease_id=None)
                count += 1
        return count


class FakeGongzuo:
    def __init__(self) -> None:
        self.revision = 1
        self.activities: list[dict[str, Any]] = []
        self.evidence: list[dict[str, Any]] = []

    def get_item(self, workspace: str, item_id: str) -> dict[str, Any]:
        return {"id": item_id, "workspace": workspace, "title": "真实运行测试", "goal": "产出可核验结果"}

    def current_context_snapshot(self, workspace: str, item_id: str) -> dict[str, Any]:
        return {
            "itemId": item_id, "contextId": f"ctx-{item_id}",
            "versionId": f"ctxv-{self.revision}", "revisionNo": self.revision,
            "content": f"accepted context {self.revision}", "acceptedAt": now(),
            "acceptedBy": "admin", "sources": [{"ref": "fixture", "version": str(self.revision)}],
        }

    def append_activity(self, workspace: str, item_id: str, **payload: Any) -> dict[str, Any]:
        self.activities.append({"workspace": workspace, "itemId": item_id, **payload})
        return self.activities[-1]

    def add_run_evidence_link(self, workspace: str, item_id: str, **payload: Any) -> dict[str, Any]:
        row = {"workspace": workspace, "itemId": item_id, "status": "submitted", **payload}
        self.evidence.append(row)
        return row


class ShellExecutor:
    name = "codex"

    def __init__(self, *, block: bool = False) -> None:
        self.block = block
        self.started = asyncio.Event()
        self.processes: list[asyncio.subprocess.Process] = []
        self.requests: list[Any] = []

    def health(self) -> ExecutorHealth:
        return ExecutorHealth(name="codex", available=True, command="fixture-shell", version="1")

    async def run(self, request, on_event, on_process):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        command = "sleep 30" if self.block else "printf '%s' \"$HOME\""
        process = await asyncio.create_subprocess_exec(
            "bash", "-lc", command,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **request.environment}, start_new_session=True,
        )
        self.processes.append(process)
        on_process(process)
        self.started.set()
        stdout, _ = await process.communicate()
        text = stdout.decode() or "stopped"
        await on_event(
            {"event_type": "fixture.output", "source": "codex", "channel": "stdout", "summary": text, "payload": {}}
        )
        return ExecutorResult(
            executor="codex", exit_code=int(process.returncode or 0),
            session_id=f"session-{Path(request.environment.get('HOME', 'none')).parent.name}",
            final_message=text,
            failure_code=None if process.returncode == 0 else "terminated",
            failure_reason=None if process.returncode == 0 else "terminated",
        )


def service(tmp_path: Path, executor: ShellExecutor, *, repository_root: Path | None = None):
    repo = MemoryRuntimeRepository()
    core = FakeGongzuo()
    capabilities = [
        {
            "id": "candidate-check", "target": "skill", "title": "候选检查",
            "version": "v2", "content": "执行候选规则", "isCandidate": True,
        }
    ]
    runtime = GongzuoRuntimeService(
        repository=repo,  # type: ignore[arg-type]
        gongzuo_service=core,
        executors={"codex": executor},
        runtime_root=tmp_path / "control-runtime",
        repository_root=repository_root,
        registration_tokens={"personal": "personal-registration", "team": "team-registration"},
        capability_provider=lambda workspace, candidate_id: capabilities if candidate_id else [],
        offline_after_seconds=10,
    )
    return runtime, repo, core


def register(runtime: GongzuoRuntimeService, workspace: str = "personal", *, capacity: int = 1,
             runtimes: list[str] | None = None, images: list[str] | None = None):
    return runtime.register_machine(
        workspace,
        registration_token=f"{workspace}-registration",
        name=f"{workspace} worker",
        capacity=capacity,
        engines=["codex"],
        runtimes=runtimes or ["native"],
        images=images or [],
        labels={"fixture": "true"},
    )


def test_run_pins_repository_context_and_capability_and_retry_never_mutates_old_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=source, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=source, check=True)
    (source / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=source, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=source, check=True, capture_output=True)
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source, check=True, capture_output=True, text=True
    ).stdout.strip()
    runtime, repo, core = service(tmp_path, ShellExecutor(), repository_root=source)

    first = runtime.create_run(
        "personal", item_id="P-1", instruction="检查结果", engine="codex",
        permission="read-only", capability_candidate_id="candidate-check",
    )
    raw_first = runtime.get_run_snapshot("personal", first["id"])
    assert raw_first["repository_revision"] == revision
    assert raw_first["context_version_id"] == "ctxv-1"
    assert raw_first["capability_snapshot"][0]["version"] == "v2"
    assert "试验候选" in raw_first["prompt_snapshot"]

    core.revision = 2
    repo.runs[first["id"]]["state"] = "failed"
    old_context_retry = runtime.retry_run("personal", first["id"], sync_context=False)
    synced_retry = runtime.retry_run("personal", first["id"], sync_context=True)

    assert runtime.get_run("personal", first["id"])["stale_context"] is True
    assert runtime.get_run_snapshot("personal", first["id"])["context_version_id"] == "ctxv-1"
    assert runtime.get_run_snapshot("personal", old_context_retry["id"])["context_version_id"] == "ctxv-1"
    assert runtime.get_run_snapshot("personal", synced_retry["id"])["context_version_id"] == "ctxv-2"
    assert len({first["directory"], old_context_retry["directory"], synced_retry["directory"]}) == 3



def test_child_delegation_prompt_keeps_local_goal_and_pins_parent_context(tmp_path: Path) -> None:
    from copy import deepcopy
    from test_gongzuo import service as core_service

    core, core_repo = core_service()
    parent = core.create_item(
        "personal", item_type="requirement", title="改善验收体验", status="open",
        payload={"goal": "让验收人员看懂结果", "scope": "不改变分配规则"}, actor_id="admin",
    )
    child = core.create_item(
        "personal", item_type="research", title="解释分配缺口", status="open",
        payload={"goal": "说明每个未分配原因", "parentId": parent["id"]}, actor_id="admin",
    )
    core.create_context("personal", parent["id"], content={"goal": "父背景第一版"}, provenance=[], actor_id="admin")
    core.create_context("personal", child["id"], content={"goal": "子事项独立目标"}, provenance=[], actor_id="admin")
    core_repo.relation_rows.append({
        "fromKind": "item", "fromId": child["id"], "toKind": "item",
        "toId": parent["id"], "relationType": "contributes_to",
    })
    runtime, _, _ = service(tmp_path, ShellExecutor())
    runtime.gongzuo_service = core
    first = runtime.create_run(
        "personal", item_id=child["id"], instruction="核查本次缺口解释", engine="codex",
    )
    snapshot = deepcopy(runtime.get_run_snapshot("personal", first["id"]))
    assert snapshot["item_id"] == child["id"]
    assert snapshot["item_snapshot"]["id"] == child["id"]
    assert snapshot["context_snapshot"]["inheritedFromItemId"] == parent["id"]
    assert snapshot["context_snapshot"]["focus"]["goal"] == "子事项独立目标"
    assert snapshot["context_snapshot"]["content"]["goal"] == "父背景第一版"
    assert f'工作事项：{child["id"]}' in snapshot["prompt_snapshot"]
    for expected in ("子事项独立目标", "父背景第一版", "核查本次缺口解释", "说明每个未分配原因"):
        assert expected in snapshot["prompt_snapshot"]

    parent_context = core_repo.contexts["personal", parent["id"]]
    parent_context.update(currentVersionId="parent-version-2", revisionNo=2, version=2, content={"goal": "父背景第二版"})
    next_run = runtime.create_run(
        "personal", item_id=child["id"], instruction="继续核查", engine="codex",
    )
    next_snapshot = runtime.get_run_snapshot("personal", next_run["id"])
    assert next_snapshot["context_snapshot"]["content"]["goal"] == "父背景第二版"
    assert next_snapshot["context_snapshot"]["focus"]["goal"] == "子事项独立目标"
    assert runtime.get_run_snapshot("personal", first["id"])["prompt_snapshot"] == snapshot["prompt_snapshot"]
    assert runtime.get_run_snapshot("personal", first["id"])["context_snapshot"] == snapshot["context_snapshot"]
    assert runtime.get_run("personal", first["id"])["stale_context"] is True

    parent_run = runtime.create_run(
        "personal", item_id=parent["id"], instruction="检查整体效果", engine="codex",
    )
    assert runtime.get_run_snapshot("personal", parent_run["id"])["item_id"] == parent["id"]
    assert "inheritedFromItemId" not in runtime.get_run_snapshot("personal", parent_run["id"])["context_snapshot"]


def test_context_identity_change_at_same_revision_marks_run_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime, _, core = service(tmp_path, ShellExecutor())
    first = runtime.create_run("personal", item_id="P-1", instruction="one", engine="codex")
    changed = core.current_context_snapshot("personal", "P-1")
    changed["versionId"] = "another-parent-v1"
    monkeypatch.setattr(core, "current_context_snapshot", lambda *_: changed)
    assert runtime.get_run("personal", first["id"])["stale_context"] is True
    assert runtime.get_run_snapshot("personal", first["id"])["context_version_id"] == "ctxv-1"


def test_machine_credentials_workspace_capacity_pause_and_lease_commands(tmp_path: Path) -> None:
    runtime, repo, _ = service(tmp_path, ShellExecutor())
    personal = register(runtime, capacity=1)
    team = register(runtime, "team")
    assert personal["worker_token"] != team["worker_token"]
    assert "token_hash" not in runtime.list_machines("personal")[0]
    with pytest.raises(PermissionError):
        runtime.authenticate_worker("team", personal["id"], personal["worker_token"])

    one = runtime.create_run("personal", item_id="P-1", instruction="one", engine="codex")
    two = runtime.create_run("personal", item_id="P-2", instruction="two", engine="codex")
    claimed = runtime.claim("personal", personal["id"], personal["worker_token"], lease_seconds=30)
    assert claimed and claimed["id"] == one["id"]
    assert runtime.claim("personal", personal["id"], personal["worker_token"], lease_seconds=30) is None
    repo.runs[one["id"]]["state"] = "running"
    paused = runtime.request_pause("personal", one["id"])
    assert paused["state"] == "pause_requested"
    heartbeat = runtime.heartbeat(
        "personal", personal["id"], personal["worker_token"],
        leases=[{"run_id": one["id"], "lease_id": claimed["lease_id"]}], lease_seconds=30,
    )
    assert heartbeat["commands"] == [
        {"runId": one["id"], "leaseValid": True, "cancelRequested": False, "pauseRequested": True}
    ]
    runtime.machine_action("personal", personal["id"], "drain")
    assert runtime.claim("personal", personal["id"], personal["worker_token"], lease_seconds=30) is None
    assert repo.runs[two["id"]]["state"] == "queued"


@pytest.mark.parametrize(
    ("stop", "requested_state", "final_state", "event_type"),
    [
        ("cancel", "cancelling", "cancelled", "run.cancelled"),
        ("pause", "pause_requested", "paused", "run.paused"),
    ],
)
def test_persisted_stop_intent_wins_over_late_worker_success_but_keeps_output(
    tmp_path: Path,
    stop: str,
    requested_state: str,
    final_state: str,
    event_type: str,
) -> None:
    runtime, repo, _ = service(tmp_path, ShellExecutor())
    machine = register(runtime)
    run = runtime.create_run("personal", item_id="P-race", instruction="race", engine="codex")
    claimed = runtime.claim(
        "personal", machine["id"], machine["worker_token"], lease_seconds=30
    )
    assert claimed is not None
    runtime.worker_report(
        "personal",
        machine["id"],
        machine["worker_token"],
        run["id"],
        {"lease_id": claimed["lease_id"], "outcome": "running", "environment": {}},
    )
    requested = (
        runtime.request_cancel("personal", run["id"])
        if stop == "cancel"
        else runtime.request_pause("personal", run["id"])
    )
    assert requested["state"] == requested_state

    final = runtime.worker_report(
        "personal",
        machine["id"],
        machine["worker_token"],
        run["id"],
        {
            "lease_id": claimed["lease_id"],
            "outcome": "succeeded",
            "exit_code": 0,
            "result": "late but real output",
            "artifacts": [
                {
                    "kind": "executor-result",
                    "ref": f"/api/gongzuo/personal/runs/{run['id']}/artifacts/result",
                    "version": "sha256:late",
                }
            ],
            "evidence": [{"kind": "late-output", "businessAccepted": False}],
            "environment": {"identity": "fixture:race"},
        },
    )

    assert final["state"] == final_state
    assert final["result"] == "late but real output"
    assert final["artifact_candidates"][0]["version"] == "sha256:late"
    assert repo.run_events[run["id"]][-1]["event_type"] == event_type
    assert repo.run_events[run["id"]][-1]["payload"] == {
        "exitCode": 0,
        "machineId": machine["id"],
        "reportedOutcome": "succeeded",
        "effectiveOutcome": final_state,
    }


def test_expired_lease_rejects_late_success_and_keeps_lease_failure(tmp_path: Path) -> None:
    runtime, repo, _ = service(tmp_path, ShellExecutor())
    machine = register(runtime)
    run = runtime.create_run("personal", item_id="P-expired", instruction="expire", engine="codex")
    claimed = runtime.claim(
        "personal", machine["id"], machine["worker_token"], lease_seconds=30
    )
    assert claimed is not None
    repo.runs[run["id"]]["lease_expires_at"] = now() - timedelta(seconds=1)
    assert runtime.recover_expired_leases() == 1

    with pytest.raises(PermissionError, match="lease"):
        runtime.worker_report(
            "personal",
            machine["id"],
            machine["worker_token"],
            run["id"],
            {
                "lease_id": claimed["lease_id"],
                "outcome": "succeeded",
                "exit_code": 0,
                "result": "too late",
                "environment": {},
            },
        )
    assert runtime.get_run("personal", run["id"])["state"] == "failed"
    assert runtime.get_run("personal", run["id"])["failure_code"] == "lease_expired"


def test_worker_runs_real_subprocess_retains_artifact_and_isolates_sessions(tmp_path: Path) -> None:
    executor = ShellExecutor()
    runtime, _, core = service(tmp_path, executor)
    machine = register(runtime, capacity=1)
    client = ServiceWorkerClient(runtime, "personal", machine["id"], machine["worker_token"])
    worker = GongzuoWorker(
        client=client,
        executors={"codex": executor},
        runtime_root=tmp_path / "worker-runtime",
        machine_id=machine["id"],
        heartbeat_seconds=0.02,
    )
    first = runtime.create_run(
        "personal", item_id="P-1", instruction="return home", engine="codex",
        capability_candidate_id="candidate-check",
    )
    assert asyncio.run(worker.execute_once()) is True
    first_done = runtime.get_run("personal", first["id"])
    assert first_done["state"] == "succeeded"
    assert first_done["business_accepted"] is False
    assert first_done["artifact_candidates"][0]["ref"].endswith("/artifacts/result")
    assert first_done["artifact_candidates"][0]["version"].startswith("sha256:")
    assert first_done["result"]
    assert first_done["artifact_candidates"][0]["version"] == (
        "sha256:" + __import__("hashlib").sha256(first_done["result"].encode()).hexdigest()
    )
    assert first_done["environment_snapshot"]["materializedCapabilities"] == [
        ".agents/skills/candidate-check/SKILL.md"
    ]
    assert core.evidence[0]["status"] == "submitted"

    second = runtime.create_run("personal", item_id="P-2", instruction="return home", engine="codex")
    assert asyncio.run(worker.execute_once()) is True
    second_done = runtime.get_run("personal", second["id"])
    assert first_done["session"] != second_done["session"]
    assert first_done["environment_snapshot"]["sessionHome"] != second_done["environment_snapshot"]["sessionHome"]


def test_worker_cancellation_terminates_process_before_truthful_cancelled_state(tmp_path: Path) -> None:
    executor = ShellExecutor(block=True)
    runtime, _, _ = service(tmp_path, executor)
    machine = register(runtime)
    client = ServiceWorkerClient(runtime, "personal", machine["id"], machine["worker_token"])
    worker = GongzuoWorker(
        client=client, executors={"codex": executor},
        runtime_root=tmp_path / "worker-runtime", machine_id=machine["id"],
        heartbeat_seconds=0.02,
    )
    run = runtime.create_run("personal", item_id="P-1", instruction="block", engine="codex")

    async def scenario() -> None:
        task = asyncio.create_task(worker.execute_once())
        await asyncio.wait_for(executor.started.wait(), timeout=3)
        requested = runtime.request_cancel("personal", run["id"])
        assert requested["state"] == "cancelling"
        await asyncio.wait_for(task, timeout=3)

    asyncio.run(scenario())
    assert runtime.get_run("personal", run["id"])["state"] == "cancelled"
    assert executor.processes[0].returncode is not None


def test_docker_request_reports_unavailable_when_runtime_does_not_exist(tmp_path: Path, monkeypatch) -> None:
    executor = ShellExecutor()
    runtime, _, _ = service(tmp_path, executor)
    machine = register(runtime, runtimes=["docker"], images=["fixture/image:1"])
    client = ServiceWorkerClient(runtime, "personal", machine["id"], machine["worker_token"])
    worker = GongzuoWorker(
        client=client, executors={"codex": executor}, runtime_root=tmp_path / "worker-runtime",
        machine_id=machine["id"], heartbeat_seconds=0.02,
    )
    run = runtime.create_run(
        "personal", item_id="P-1", instruction="docker", engine="codex",
        runtime="docker", image="fixture/image:1",
    )
    original_which = __import__("shutil").which
    monkeypatch.setattr(
        "src.gongzuo_runtime.worker.shutil.which",
        lambda command: None if command == "docker" else original_which(command),
    )
    assert asyncio.run(worker.execute_once()) is True
    done = runtime.get_run("personal", run["id"])
    assert done["state"] == "unavailable"
    assert done["failure_code"] == "runtime_unavailable"
    assert "docker" in done["error"].lower()


def test_worker_maps_remote_repository_identity_and_requires_fixed_commit(tmp_path: Path) -> None:
    source = tmp_path / "local-checkout"
    source.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=source, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=source, check=True)
    (source / "README.md").write_text("mapped\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=source, check=True)
    subprocess.run(["git", "commit", "-m", "mapped"], cwd=source, check=True, capture_output=True)
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source, check=True, capture_output=True, text=True
    ).stdout.strip()
    executor = ShellExecutor()
    runtime, _, _ = service(tmp_path, executor)
    worker = GongzuoWorker(
        client=None,  # type: ignore[arg-type]
        executors={"codex": executor},
        runtime_root=tmp_path / "worker-runtime",
        machine_id="node",
        repository_map={"/center/repos/product": str(source)},
    )
    run = {
        "workspace": "team", "id": "run-mapped", "repository_path": "/center/repos/product",
        "repository_revision": revision, "sandbox": "read-only", "branch": None,
    }
    worktree, _, _ = worker._prepare_worktree(run)
    assert (worktree / "README.md").read_text(encoding="utf-8") == "mapped\n"
    with pytest.raises(FileNotFoundError, match="缺少固定提交"):
        worker._prepare_worktree({**run, "id": "run-missing", "repository_revision": "0" * 40})


def test_team_worker_never_falls_back_to_personal_auth_or_provider_environment(
    tmp_path: Path, monkeypatch
) -> None:
    personal_codex = tmp_path / "personal-codex"
    personal_codex.mkdir()
    (personal_codex / "auth.json").write_text("personal-secret", encoding="utf-8")
    team_codex = tmp_path / "team-codex"
    team_codex.mkdir()
    (team_codex / "auth.json").write_text("team-secret", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(personal_codex))
    monkeypatch.setenv("OPENAI_API_KEY", "personal-provider-secret")
    monkeypatch.delenv("GONGZUO_TEAM_CODEX_HOME", raising=False)
    executor = ShellExecutor()
    runtime, _, _ = service(tmp_path, executor)
    worker = GongzuoWorker(
        client=None,  # type: ignore[arg-type]
        executors={"codex": executor},
        runtime_root=tmp_path / "worker-runtime",
        machine_id="node",
    )

    with pytest.raises(FileNotFoundError, match="GONGZUO_TEAM_CODEX_HOME"):
        worker._isolated_environment(
            tmp_path / "team-missing-home", workspace="team", engine="codex"
        )
    assert not (tmp_path / "team-missing-home" / ".codex" / "auth.json").exists()

    monkeypatch.setenv("GONGZUO_TEAM_CODEX_HOME", str(team_codex))
    team_env, team_inherits = worker._isolated_environment(
        tmp_path / "team-home", workspace="team", engine="codex"
    )
    personal_env, personal_inherits = worker._isolated_environment(
        tmp_path / "personal-home", workspace="personal", engine="codex"
    )
    assert team_inherits is False
    assert personal_inherits is True
    assert "OPENAI_API_KEY" not in team_env
    assert (Path(team_env["CODEX_HOME"]) / "auth.json").read_text() == "team-secret"
    assert (Path(personal_env["CODEX_HOME"]) / "auth.json").read_text() == "personal-secret"
    assert team_env["HOME"] != personal_env["HOME"]
