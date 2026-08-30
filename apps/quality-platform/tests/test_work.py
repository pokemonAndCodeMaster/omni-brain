from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.api.schemas.work import WorkCreate, WorkEvidenceCreate, WorkUpdate
from src.agent_runtime.worktrees import WorktreeManager
from src.work.repository import WorkRepository
from src.work.service import STEP_DEFINITIONS, WorkService


def test_standard_development_v1_is_fixed_and_bounded() -> None:
    assert [definition[0] for definition in STEP_DEFINITIONS] == [
        "knowledge_context",
        "solution",
        "development",
        "verification",
        "review",
        "acceptance",
    ]
    assert len(STEP_DEFINITIONS) == 6
    assert STEP_DEFINITIONS[2][4:] == ("development-agent", "codex")
    assert STEP_DEFINITIONS[3][4:] == ("review-agent", "opencode")


def test_work_create_rejects_backwards_timebox() -> None:
    with pytest.raises(ValidationError, match="结束时间必须晚于开始时间"):
        WorkCreate.model_validate(
            {
                "timebox_start": "2026-08-31T12:00:00Z",
                "timebox_end": "2026-08-31T10:00:00Z",
            }
        )


def test_work_evidence_requires_a_human_evidence_field() -> None:
    with pytest.raises(ValidationError, match="至少补充一项"):
        WorkEvidenceCreate.model_validate({})


def test_work_update_requires_an_explicit_field() -> None:
    with pytest.raises(ValidationError, match="至少提交一项"):
        WorkUpdate.model_validate({})


@pytest.mark.parametrize(
    ("stored_status", "run_status", "expected"),
    [
        ("pending", None, "blocked"),
        ("ready", None, "ready"),
        ("ready", "running", "running"),
        ("ready", "succeeded", "awaiting_gate"),
        ("ready", "failed", "failed"),
        ("completed", "failed", "completed"),
    ],
)
def test_step_display_status_keeps_gate_separate_from_run_status(
    stored_status: str,
    run_status: str | None,
    expected: str,
) -> None:
    runs = [{"status": run_status}] if run_status else []
    assert WorkRepository._display_status({"status": stored_status, "runs": runs}) == expected


class FakeRegistry:
    def get(self, agent_id: str) -> dict:
        assert agent_id == "development-agent"
        return {"repository": "/tmp/repository", "revision": "base-sha"}


class FakeWorktrees:
    def __init__(self) -> None:
        self.discarded = False

    def create_work(self, work_id: str, repository: Path, revision: str) -> dict[str, str]:
        return {
            "path": f"/tmp/runs/{work_id}",
            "branch": f"agent-work/{work_id}",
            "base_revision": revision,
        }

    def discard(self, **_: object) -> None:
        self.discarded = True


class FailingRepository:
    def create(self, **_: object) -> dict:
        raise ValueError("Requirement 已有关联 Work")


def test_failed_db_creation_discards_just_created_worktree(monkeypatch: pytest.MonkeyPatch) -> None:
    worktrees = FakeWorktrees()
    service = WorkService(
        repository=FailingRepository(),  # type: ignore[arg-type]
        run_service=SimpleNamespace(registry=FakeRegistry()),  # type: ignore[arg-type]
        worktrees=worktrees,  # type: ignore[arg-type]
    )
    monkeypatch.setattr("src.work.service._git", lambda *_: "base-sha")
    monkeypatch.setattr(Path, "is_dir", lambda _: True)

    with pytest.raises(ValueError, match="已有关联 Work"):
        service.create_for_requirement(
            requirement_id="req-1",
            payload=WorkCreate(),
            actor_id="admin",
        )

    assert worktrees.discarded is True


class RequirementGateConnection:
    def __enter__(self) -> RequirementGateConnection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, query: str, _: object = None) -> SimpleNamespace:
        if "pg_advisory_xact_lock" in query:
            return SimpleNamespace()
        if "FROM manual_qc_lab.t_collab_requirement" in query:
            return SimpleNamespace(
                fetchone=lambda: {
                    "id": "req-later",
                    "title": "Later",
                    "status": "accepted",
                    "accepted_revision_id": "rev-later",
                    "commitment": "LATER",
                }
            )
        raise AssertionError(f"不应越过 NEXT 门禁继续写入：{query}")


class RequirementGatePostgres:
    schema = "manual_qc_lab"

    def transaction(self) -> RequirementGateConnection:
        return RequirementGateConnection()


def test_work_creation_requires_an_accepted_next_requirement() -> None:
    repository = WorkRepository(RequirementGatePostgres())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=r"accepted \+ NEXT"):
        repository.create(
            work_id="work-later",
            plan_id="plan-later",
            requirement_id="req-later",
            title=None,
            owner_id="admin",
            reviewer_id="admin",
            timebox_start=None,
            timebox_end=None,
            repository_path="/tmp/repository",
            base_commit="base-sha",
            worktree_path="/tmp/work-later",
            branch_name="agent-work/work-later",
            actor_id="admin",
            steps=[],
        )


class DecisionRepository:
    def __init__(self, evidence: dict[str, str]) -> None:
        self.evidence = evidence
        self.decisions: list[dict[str, object]] = []

    def detail(self, _: str) -> dict[str, object]:
        return {
            "worktree_path": "/tmp/work-1",
            "base_commit": "base-sha",
            "latest_evidence": {"payload": self.evidence},
        }

    def decide(self, **values: object) -> dict[str, str]:
        self.decisions.append(values)
        return {"id": "decision-1"}


class EvidenceWorktrees:
    def __init__(self, current: dict[str, str]) -> None:
        self.current = current

    def delivery_evidence(self, path: Path, base_commit: str) -> dict[str, str]:
        assert path == Path("/tmp/work-1")
        assert base_commit == "base-sha"
        return self.current


def test_accept_rejects_stale_git_evidence() -> None:
    recorded = {
        "head_commit": "commit-1",
        "branch_name": "agent-work/work-1",
        "worktree_status": "",
        "diff_summary": "",
    }
    repository = DecisionRepository(recorded)
    service = WorkService(
        repository=repository,  # type: ignore[arg-type]
        run_service=SimpleNamespace(),  # type: ignore[arg-type]
        worktrees=EvidenceWorktrees({**recorded, "worktree_status": " M changed.py"}),  # type: ignore[arg-type]
    )

    with pytest.raises(ValueError, match="Git 状态已变化"):
        service.decide(
            work_id="work-1",
            decision_type="accept",
            reason="接受",
            actor_id="admin",
        )

    assert repository.decisions == []


def test_accept_allows_current_git_evidence() -> None:
    evidence = {
        "head_commit": "commit-1",
        "branch_name": "agent-work/work-1",
        "worktree_status": "",
        "diff_summary": " changed.py | 1 +",
    }
    repository = DecisionRepository(evidence)
    service = WorkService(
        repository=repository,  # type: ignore[arg-type]
        run_service=SimpleNamespace(),  # type: ignore[arg-type]
        worktrees=EvidenceWorktrees(evidence),  # type: ignore[arg-type]
    )

    decision = service.decide(
        work_id="work-1",
        decision_type="accept",
        reason="接受",
        actor_id="admin",
    )

    assert decision == {"id": "decision-1"}
    assert repository.decisions[0]["work_id"] == "work-1"


def test_platform_commits_worktree_changes_without_exposing_git_metadata(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git_test(repository, "init", "-b", "main")
    (repository / "README.md").write_text("base\n", encoding="utf-8")
    _git_test(repository, "add", "README.md")
    _git_test(
        repository,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "base",
    )
    base_commit = _git_test(repository, "rev-parse", "HEAD")
    manager = WorktreeManager(tmp_path / "runs")
    workspace = manager.create_work("work-1", repository, base_commit)
    worktree = Path(workspace["path"])
    (worktree / "delivery.txt").write_text("delivered\n", encoding="utf-8")

    head = manager.commit_delivery(worktree, base_commit, "agent: complete development")

    assert head != base_commit
    assert _git_test(worktree, "status", "--short") == ""
    assert _git_test(worktree, "log", "-1", "--pretty=%s") == "agent: complete development"


def _git_test(repository: Path, *args: str) -> str:
    import subprocess

    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
