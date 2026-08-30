from __future__ import annotations

import re
import subprocess
from pathlib import Path


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        reason = (result.stderr or result.stdout).strip()
        raise RuntimeError(reason or f"git {' '.join(args)} 执行失败")
    return result.stdout.strip()


class WorktreeManager:
    """Use a worktree only for code and file isolation."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _create(
        self,
        identity: str,
        repository: Path,
        revision: str,
        *,
        branch_prefix: str,
    ) -> dict[str, str]:
        if not _SAFE_ID.fullmatch(identity):
            raise ValueError(f"不安全的工作区 ID：{identity}")
        target = (self.root / identity).resolve()
        target.relative_to(self.root)
        if target.exists():
            raise FileExistsError(f"Worktree 已存在：{target}")
        branch = f"{branch_prefix}/{identity}"
        if _git(repository, "branch", "--list", branch):
            raise FileExistsError(f"运行分支已存在：{branch}")
        _git(repository, "worktree", "add", "-b", branch, str(target), revision)
        return {
            "path": str(target),
            "branch": branch,
            "base_revision": _git(target, "rev-parse", "HEAD"),
        }

    def create(self, run_id: str, repository: Path, revision: str) -> dict[str, str]:
        return self._create(
            run_id,
            repository,
            revision,
            branch_prefix="agent-run",
        )

    def create_work(
        self,
        work_id: str,
        repository: Path,
        revision: str,
    ) -> dict[str, str]:
        return self._create(
            work_id,
            repository,
            revision,
            branch_prefix="agent-work",
        )

    def discard(
        self,
        *,
        repository: Path,
        path: Path,
        branch: str,
    ) -> None:
        """Clean up a just-created workspace when its owning DB transaction fails."""

        resolved = path.resolve()
        resolved.relative_to(self.root)
        _git(repository, "worktree", "remove", "--force", str(resolved))
        _git(repository, "branch", "-D", branch)

    def snapshot(self, path: Path) -> dict[str, str]:
        return {
            "head": _git(path, "rev-parse", "HEAD"),
            "status": _git(path, "status", "--short"),
            "diff": _git(path, "diff", "--no-ext-diff", "--binary"),
        }

    def delivery_evidence(self, path: Path, base_commit: str) -> dict[str, str]:
        head = _git(path, "rev-parse", "HEAD")
        return {
            "head_commit": head,
            "branch_name": _git(path, "branch", "--show-current"),
            "worktree_status": _git(path, "status", "--short"),
            "diff_summary": _git(path, "diff", "--stat", f"{base_commit}..{head}"),
        }
