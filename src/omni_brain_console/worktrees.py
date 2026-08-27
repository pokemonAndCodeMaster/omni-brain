from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import run_command, safe_id


class WorktreeManager:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, run_id: str, repository: Path, revision: str) -> dict[str, str]:
        run_id = safe_id(run_id)
        target = (self.root / run_id).resolve()
        try:
            target.relative_to(self.root.resolve())
        except ValueError as exc:
            raise ValueError("Worktree 路径越界") from exc
        if target.exists():
            raise FileExistsError(f"Worktree 已存在：{target}")
        branch = f"agent-console/{run_id}"
        existing = run_command(["git", "-C", str(repository), "branch", "--list", branch])
        if existing:
            raise FileExistsError(f"运行分支已存在：{branch}")
        run_command(
            [
                "git",
                "-C",
                str(repository),
                "worktree",
                "add",
                "-b",
                branch,
                str(target),
                revision,
            ]
        )
        head = run_command(["git", "-C", str(target), "rev-parse", "HEAD"])
        return {"path": str(target), "branch": branch, "base_revision": head}

    def snapshot(self, path: Path) -> dict[str, Any]:
        status = run_command(["git", "-C", str(path), "status", "--short"])
        diff = run_command(["git", "-C", str(path), "diff", "--no-ext-diff", "--binary"])
        staged = run_command(["git", "-C", str(path), "diff", "--cached", "--no-ext-diff", "--binary"])
        head = run_command(["git", "-C", str(path), "rev-parse", "HEAD"])
        return {
            "status": status,
            "diff": "\n".join(part for part in (diff, staged) if part),
            "head": head,
        }

    def commit(self, path: Path, message: str) -> str:
        run_command(["git", "-C", str(path), "add", "-A"])
        run_command(["git", "-C", str(path), "commit", "-m", message])
        return run_command(["git", "-C", str(path), "rev-parse", "HEAD"])

    def release(self, path: Path) -> None:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.root.resolve())
        except ValueError as exc:
            raise ValueError("Worktree 路径越界") from exc
        if not resolved.is_dir():
            raise FileNotFoundError(str(resolved))
        status = run_command(["git", "-C", str(resolved), "status", "--short"])
        if status:
            raise RuntimeError("Worktree 仍有未提交变化，请先提交或人工处理")
        run_command(["git", "-C", str(resolved), "worktree", "remove", str(resolved)])
