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

    def create(self, run_id: str, repository: Path, revision: str) -> dict[str, str]:
        if not _SAFE_ID.fullmatch(run_id):
            raise ValueError(f"不安全的 Run ID：{run_id}")
        target = (self.root / run_id).resolve()
        target.relative_to(self.root)
        if target.exists():
            raise FileExistsError(f"Worktree 已存在：{target}")
        branch = f"agent-run/{run_id}"
        if _git(repository, "branch", "--list", branch):
            raise FileExistsError(f"运行分支已存在：{branch}")
        _git(repository, "worktree", "add", "-b", branch, str(target), revision)
        return {
            "path": str(target),
            "branch": branch,
            "base_revision": _git(target, "rev-parse", "HEAD"),
        }

    def snapshot(self, path: Path) -> dict[str, str]:
        return {
            "head": _git(path, "rev-parse", "HEAD"),
            "status": _git(path, "status", "--short"),
            "diff": _git(path, "diff", "--no-ext-diff", "--binary"),
        }
