#!/usr/bin/env python3
"""Install one repository-owned skill and a small, reversible Codex entry point."""

from __future__ import annotations

import argparse
import json
import os
import stat
import tempfile
from pathlib import Path
from time import time_ns

START = "<!-- personal-workbench:begin -->"
END = "<!-- personal-workbench:end -->"


def entry(repo: Path, link: Path) -> str:
    return f"""{START}
## 个人工作台

用户要求记录想法、接续 YYH / Linear 事项、查个人工作台或金铲铲资料、审阅工作台成果时，使用 `personal-workbench`：先读 `{link / 'SKILL.md'}`，再读线上当前正文。普通仓库工作不自动创建事项。

工作台工具唯一维护仓：`{repo}`。共享首页：https://linear.app/yyhpokemonmaster/document/abed03cc1da2 。根据事项定位实际目标仓并遵守该仓规则，不把当前目录当成所有任务的实现位置。没有 MCP 或不能读本地文件时说明边界，不报告已同步。保留用户已经给出的任务授权，不因换会话重复要求批准。
{END}"""


def merge_entry(original: str, block: str) -> str:
    if START not in original and END not in original:
        return original + ("\n\n" if original and not original.endswith("\n") else "\n" if original else "") + block + "\n"
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError("入口标记不完整或重复；未改动已有 AGENTS.md")
    before, remainder = original.split(START, 1)
    old, after = remainder.split(END, 1)
    if END in before or START in old:
        raise ValueError("入口标记顺序错误；未改动已有 AGENTS.md")
    return before + block + after


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    staged = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        staged.chmod(mode)
        staged.replace(path)
    finally:
        staged.unlink(missing_ok=True)


def replace_link(link: Path, target: str) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{link.name}.", dir=link.parent)
    os.close(fd)
    staged = Path(temporary)
    staged.unlink()
    try:
        staged.symlink_to(target, target_is_directory=True)
        staged.replace(link)
    finally:
        staged.unlink(missing_ok=True)


def install(repo: Path, user_home: Path, codex_home: Path, *, check: bool = False,
            replace_existing_link: bool = False) -> dict:
    repo = repo.expanduser().resolve(strict=True)
    source = repo / ".agents/skills/personal-workbench"
    if not (source / "SKILL.md").is_file():
        raise ValueError(f"找不到 Skill：{source / 'SKILL.md'}")
    link = user_home.expanduser().absolute() / ".agents/skills/personal-workbench"
    codex_home = codex_home.expanduser().absolute()
    agents = codex_home / "AGENTS.md"
    override = codex_home / "AGENTS.override.md"
    if override.is_file() and override.read_bytes().strip():
        raise ValueError(f"{override} 会覆盖 AGENTS.md；请先合并该文件的入口，安装未写入")
    if agents.is_symlink() or (agents.exists() and not agents.is_file()):
        raise ValueError("AGENTS.md 不是普通文件，未写入")
    old_agents = agents.read_bytes() if agents.exists() else None
    desired = merge_entry((old_agents or b"").decode("utf-8"), entry(repo, link)).encode()
    old_target = os.readlink(link) if link.is_symlink() else None
    if old_target is None and link.exists():
        raise ValueError(f"{link} 已有独立内容，未覆盖")
    link_changed = old_target is None or link.resolve() != source.resolve()
    agents_changed = old_agents != desired
    result = {
        "repo": str(repo), "skill_link": str(link), "agents": str(agents),
        "skill_target": str(source), "installed": not (link_changed or agents_changed),
    }
    if check:
        return result
    if old_target is not None and link_changed and not replace_existing_link:
        raise ValueError("Skill 链接指向另一位置；核对后使用 --replace-link 切换，不会替换目录")
    if not link_changed and not agents_changed:
        return {**result, "changed": False}

    codex_home.mkdir(parents=True, exist_ok=True)
    link.parent.mkdir(parents=True, exist_ok=True)
    backups = codex_home / "backups/personal-workbench"
    backups.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = backups / f"{time_ns()}"
    backup.mkdir(mode=0o700)
    atomic_write(backup / "before.json", json.dumps({
        "agents_existed": old_agents is not None,
        "agents": str(agents), "skill_link": str(link), "skill_target": old_target,
    }, ensure_ascii=False, indent=2).encode())
    if old_agents is not None:
        atomic_write(backup / "AGENTS.md", old_agents)
    # Do not overwrite a user's edit made after we constructed the merged entry.
    if (agents.read_bytes() if agents.exists() else None) != old_agents:
        raise ValueError("安装期间 AGENTS.md 已变化，未覆盖；重新读取后再运行")
    if (os.readlink(link) if link.is_symlink() else None) != old_target or (not link.is_symlink() and link.exists()):
        raise ValueError("安装期间 Skill 入口已变化，未覆盖")
    try:
        if link_changed:
            replace_link(link, str(source))
        if agents_changed:
            mode = stat.S_IMODE(agents.stat().st_mode) if agents.exists() else 0o600
            atomic_write(agents, desired, mode)
    except Exception:
        if link_changed:
            if old_target is None:
                link.unlink(missing_ok=True)
            else:
                replace_link(link, old_target)
        raise
    return {**result, "installed": True, "changed": True, "backup": str(backup)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--user-home", type=Path, default=Path.home(), help="仅用于目标用户或隔离安装验证")
    parser.add_argument("--codex-home", type=Path, help="默认采用 CODEX_HOME，否则使用目标用户的 .codex")
    parser.add_argument("--check", action="store_true", help="只检查入口，不修改文件")
    parser.add_argument("--replace-link", action="store_true", help="显式把已有符号链接切到 --repo；不覆盖目录")
    args = parser.parse_args()
    codex_home = args.codex_home or Path(os.environ.get("CODEX_HOME", str(args.user_home / ".codex")))
    try:
        result = install(args.repo, args.user_home, codex_home, check=args.check,
                         replace_existing_link=args.replace_link)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["installed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
