from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.api.schemas.work import WorkCreate, WorkEvidenceCreate, WorkUpdate
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
