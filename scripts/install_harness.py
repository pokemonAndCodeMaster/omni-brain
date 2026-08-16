#!/usr/bin/env python3
"""Copy the released Omni-Brain Harness into an existing project.

This is deliberately an overlay installer: Harness-owned Skills and scripts are
updated in place, while an existing project AGENTS.md and knowledge content are
kept.  The caller supplies the target project root.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
BLOCK_START = "<!-- omni-brain-harness:start -->"
BLOCK_END = "<!-- omni-brain-harness:end -->"


class InstallError(RuntimeError):
    pass


def release_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(SOURCE_ROOT), "rev-parse", "--short", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def copy_tree(source: Path, target: Path) -> None:
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def merge_agents(path: Path, commit: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    block = f"""{BLOCK_START}
## Omni-Brain Harness

- 整理、摄入或归并材料时加载 `ingest-knowledge`；查询、学习已有知识或取得任务背景时加载 `answer-from-knowledge`。
- 复杂软件诉求尚未形成获批方案时加载 `form-solution`；已有获批方案的跨层开发、真实运行验证或知识变化交接加载 `develop-with-knowledge`；复杂软件成果需要人工验收时加载 `review-work`。
- 目标明确、范围局部、风险低且易回滚的任务直接执行，不机械启动完整流程。能力范围和限制见 `harness.yaml`；当前 Release：`{commit}`。
{BLOCK_END}
"""
    if (BLOCK_START in current) != (BLOCK_END in current):
        raise InstallError(f"{path} 中的 Omni-Brain 区块不完整，请先人工修复")
    if BLOCK_START in current:
        start = current.index(BLOCK_START)
        end = current.index(BLOCK_END, start) + len(BLOCK_END)
        updated = current[:start].rstrip() + "\n\n" + block.rstrip() + "\n" + current[end:].lstrip()
    else:
        updated = current.rstrip() + "\n\n" + block
    path.write_text(updated, encoding="utf-8")


def copy_if_missing(source: Path, target: Path) -> None:
    """Install an empty knowledge scaffold without replacing existing knowledge."""

    if source.is_dir():
        for child in source.iterdir():
            copy_if_missing(child, target / child.name)
        return
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="一键把 Omni-Brain Release 覆盖安装到目标项目")
    parser.add_argument("target", type=Path, help="目标项目根目录")
    args = parser.parse_args(argv)

    target = args.target.expanduser().resolve()
    if not target.is_dir():
        raise InstallError(f"目标项目目录不存在：{target}")
    if target == SOURCE_ROOT.resolve():
        raise InstallError("不能安装到 Harness Release 自身")

    # 这些路径是 Harness 的正式运行实体，直接以当前 Release 覆盖更新。
    copy_tree(SOURCE_ROOT / ".agents" / "skills", target / ".agents" / "skills")
    for filename in ("ingestion_workspace.py", "knowledge_check.py"):
        source = SOURCE_ROOT / "scripts" / filename
        destination = target / "scripts" / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    shutil.copy2(SOURCE_ROOT / "harness.yaml", target / "harness.yaml")
    shutil.copy2(SOURCE_ROOT / "requirements.txt", target / "requirements-omni-brain.txt")

    # 知识内容属于目标项目；首次安装补齐空骨架，已有知识绝不被空骨架覆盖。
    copy_if_missing(SOURCE_ROOT / "knowledge", target / "knowledge")
    copy_if_missing(
        SOURCE_ROOT / "config" / "knowledge-domains.yaml",
        target / "config" / "knowledge-domains.yaml",
    )
    (target / "workspaces" / "knowledge-ingestion").mkdir(parents=True, exist_ok=True)
    merge_agents(target / "AGENTS.md", release_commit())

    print(f"已安装 Omni-Brain Harness：{target}")
    print("已覆盖：.agents/skills/、scripts/ingestion_workspace.py、scripts/knowledge_check.py、harness.yaml")
    print("已保留：目标项目既有知识、配置和 AGENTS.md 正文")
    print("如当前 Python 缺少依赖：python -m pip install -r requirements-omni-brain.txt")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InstallError as error:
        print(f"安装失败：{error}", file=sys.stderr)
        raise SystemExit(2)
