#!/usr/bin/env python3
"""Create and validate a deterministic knowledge-ingestion workbench."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml

from knowledge_check import markdown_table_errors, validate_bundle


SCHEMA_VERSION = "0.4"
CASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
SOURCE_ID_RE = CASE_ID_RE
LINK_RE = re.compile(r"(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)")
SOURCE_READ_MAX_LINES = 80
SOURCE_READ_MAX_CHARS = 6000
REQUIRED_ROOT_FILES = {
    "case.yaml",
    "brief.md",
    "reader-answers.md",
    "inventory.md",
    "questions.md",
    "completion.yaml",
    "coverage.yaml",
    "source-manifest.jsonl",
    "source-summary.md",
    "review.md",
}
WORKBENCH_ENTRY_FILES = {
    "brief.md",
    "reader-answers.md",
    "inventory.md",
    "questions.md",
    "review.md",
}
COVERAGE_STATES = {
    "unreviewed",
    "screened",
    "read_full",
    "read_targeted",
    "excluded",
    "duplicate",
    "unread_blocked",
}
STRONG_READ_STATES = {"read_full", "read_targeted"}
COMPLETION_STATES = {"covered", "partial", "unknown", "not_applicable"}
COMPLETION_DIMENSIONS = {
    "operating_model",
    "information_model",
    "system_and_software",
    "rules_and_mechanisms",
    "shared_dependencies",
    "history_conflicts_and_unknowns",
}
KNOWLEDGE_LEVELS = {"parent", "subject", "focus"}


class IngestionWorkspaceError(Exception):
    """A user-actionable workbench error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_cases_root() -> Path:
    return project_root() / "workspaces" / "knowledge-ingestion"


def validate_id(value: str, label: str) -> None:
    if not CASE_ID_RE.fullmatch(value):
        raise IngestionWorkspaceError(
            f"{label} 只能包含小写字母、数字和连字符，长度 1-63"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, check=False, capture_output=True, text=True
    )


def git_identity(root: Path) -> dict[str, Any] | None:
    top = run_git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root:
        return None
    head = run_git(root, "rev-parse", "HEAD")
    status = run_git(root, "status", "--short")
    if head.returncode != 0 or status.returncode != 0:
        raise IngestionWorkspaceError(f"无法读取 Git 来源基线：{root}")
    return {
        "commit": head.stdout.strip(),
        "status": [line for line in status.stdout.splitlines() if line],
    }


def source_paths(root: Path, is_git: bool) -> list[Path]:
    if is_git:
        result = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            raise IngestionWorkspaceError(f"无法枚举 Git 来源：{root}")
        candidates = [root / os.fsdecode(item) for item in result.stdout.split(b"\0") if item]
    else:
        candidates = [
            path
            for path in root.rglob("*")
            if ".git" not in path.relative_to(root).parts
        ]
    return sorted(
        (path for path in candidates if path.is_file() and not path.is_symlink()),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def scan_source(source_id: str, value: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_id(source_id, "source id")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise IngestionWorkspaceError(f"来源目录不存在：{root}")
    git = git_identity(root)
    entries: list[dict[str, Any]] = []
    for path in source_paths(root, git is not None):
        relative = path.relative_to(root).as_posix()
        try:
            size = path.stat().st_size
            digest = sha256_file(path)
        except OSError as exc:
            raise IngestionWorkspaceError(f"无法读取来源文件 {path}：{exc}") from exc
        entries.append(
            {
                "source_id": source_id,
                "path": relative,
                "bytes": size,
                "sha256": digest,
            }
        )
    fingerprint = canonical_digest(entries)
    summary = {
        "id": source_id,
        "root": str(root),
        "kind": "git" if git is not None else "directory",
        "git": git,
        "file_count": len(entries),
        "fingerprint": fingerprint,
    }
    return summary, entries


def parse_sources(values: list[str]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for value in values:
        source_id, separator, path = value.partition("=")
        if not separator or not path:
            raise IngestionWorkspaceError("--source 必须使用 <id>=<directory> 格式")
        validate_id(source_id, "source id")
        if source_id in seen:
            raise IngestionWorkspaceError(f"重复 source id：{source_id}")
        seen.add(source_id)
        result.append((source_id, path))
    if not result:
        raise IngestionWorkspaceError("至少需要一个 --source")
    return result


def dump_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )


def load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise IngestionWorkspaceError(f"{label} 不存在：{path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise IngestionWorkspaceError(f"无法读取 {label}：{exc}") from exc
    if not isinstance(value, dict):
        raise IngestionWorkspaceError(f"{label} 顶层必须是 mapping")
    return value


def formal_surface_fingerprint(root: Path) -> str:
    entries: list[dict[str, Any]] = []
    for base in (root / "knowledge", root / "config"):
        if not base.exists():
            continue
        for path in sorted(item for item in base.rglob("*") if item.is_file()):
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256_file(path),
                }
            )
    return canonical_digest(entries)


def copy_asset(name: str, target: Path) -> None:
    source = project_root() / ".agents" / "skills" / "ingest-knowledge" / "assets" / name
    shutil.copyfile(source, target)


def render_source_summary(case_id: str, sources: list[dict[str, Any]]) -> str:
    lines = [
        "# 来源机器盘点",
        "",
        "> 本页由 `ingestion_workspace.py` 生成。不要手工修改数量或指纹；语义判断写入 `inventory.md`。",
        "",
        f"- **Case ID**：`{case_id}`",
        "",
        "| 来源 ID | 授权根目录 | 类型 | 文件数 | Git/指纹 |",
        "|---|---|---|---:|---|",
    ]
    for source in sources:
        git = source.get("git")
        identity = git.get("commit")[:12] if isinstance(git, dict) else source["fingerprint"][:12]
        lines.append(
            f"| `{source['id']}` | `{source['root']}` | {source['kind']} | "
            f"{source['file_count']} | `{identity}` |"
        )
    lines.extend(
        [
            "",
            "完整逐文件身份记录见 [source-manifest.jsonl](source-manifest.jsonl)；"
            "Agent 的筛查/理解声明与脚本的展示进度见 [coverage.yaml](coverage.yaml)。",
            "",
        ]
    )
    return "\n".join(lines)


def init_case(args: argparse.Namespace) -> int:
    validate_id(args.case_id, "case id")
    root = args.cases_root.resolve() / args.case_id
    if root.exists():
        raise IngestionWorkspaceError(f"摄入工作台已存在：{root}")
    source_pairs = parse_sources(args.source)
    sources: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    for source_id, source_path in source_pairs:
        summary, entries = scan_source(source_id, source_path)
        sources.append(summary)
        manifest.extend(entries)

    root.mkdir(parents=True)
    created_at = utc_now()
    case = {
        "schema_version": SCHEMA_VERSION,
        "case_id": args.case_id,
        "status": "preparing",
        "created_at": created_at,
        "goal": args.goal.strip(),
        "harness": {
            "root": str(project_root()),
            "git_head": run_git(project_root(), "rev-parse", "HEAD").stdout.strip(),
            "formal_surface_fingerprint": formal_surface_fingerprint(project_root()),
        },
        "sources": sources,
    }
    dump_yaml(root / "case.yaml", case)
    with (root / "source-manifest.jsonl").open("w", encoding="utf-8") as handle:
        for entry in manifest:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    coverage = {
        "schema_version": SCHEMA_VERSION,
        "case_id": args.case_id,
        "semantics": "agent declarations; not machine-observed reading",
        "display_semantics": (
            "machine-observed script output; proves complete display, not agent comprehension"
        ),
        "files": [
            {
                "source_id": entry["source_id"],
                "path": entry["path"],
                "status": "unreviewed",
                "reason": "",
                "evidence": [],
            }
            for entry in manifest
        ],
    }
    dump_yaml(root / "coverage.yaml", coverage)
    (root / "source-summary.md").write_text(
        render_source_summary(args.case_id, sources), encoding="utf-8"
    )
    for name in (
        "brief.md",
        "reader-answers.md",
        "inventory.md",
        "questions.md",
        "review.md",
    ):
        copy_asset(name, root / name)
    copy_asset("completion.yaml", root / "completion.yaml")
    brief = (root / "brief.md").read_text(encoding="utf-8")
    brief = brief.replace("- **Case ID**：", f"- **Case ID**：`{args.case_id}`")
    brief = brief.replace(
        "- **用户最终要得到什么**：",
        f"- **用户最终要得到什么**：{args.goal.strip()}",
    )
    brief = brief.replace(
        "- **材料位置与版本**：",
        "- **材料位置与版本**："
        + "；".join(f"`{item['root']}`" for item in sources),
    )
    (root / "brief.md").write_text(brief, encoding="utf-8")
    draft = root / "draft"
    shutil.copytree(project_root() / "knowledge", draft / "knowledge")
    (draft / "config").mkdir(parents=True)
    shutil.copyfile(
        project_root() / "config" / "knowledge-domains.yaml",
        draft / "config" / "knowledge-domains.yaml",
    )
    print(
        json.dumps(
            {
                "case_id": args.case_id,
                "workbench": str(root),
                "sources": [
                    {"id": item["id"], "file_count": item["file_count"]}
                    for item in sources
                ],
                "next": "fill brief.md; read by question; write candidate pages and reader-answers.md",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def case_root(args: argparse.Namespace) -> Path:
    validate_id(args.case_id, "case id")
    root = args.cases_root.resolve() / args.case_id
    if not (root / "case.yaml").is_file():
        raise IngestionWorkspaceError(f"摄入工作台不存在：{root}")
    return root


def find_manifest_entry(
    root: Path, source_id: str, relative_path: str
) -> dict[str, Any]:
    matches = [
        item
        for item in read_manifest(root / "source-manifest.jsonl")
        if item.get("source_id") == source_id and item.get("path") == relative_path
    ]
    if len(matches) != 1:
        raise IngestionWorkspaceError(
            f"来源清单中不存在唯一精确路径：{source_id}={relative_path}"
        )
    return matches[0]


def find_source_root(root: Path, source_id: str) -> Path:
    case = load_yaml(root / "case.yaml", "case.yaml")
    matches = [
        item
        for item in case.get("sources", [])
        if isinstance(item, dict) and item.get("id") == source_id
    ]
    if len(matches) != 1:
        raise IngestionWorkspaceError(f"case.yaml 中不存在唯一来源：{source_id}")
    source_root = Path(str(matches[0].get("root", ""))).resolve()
    if not source_root.is_dir():
        raise IngestionWorkspaceError(f"来源目录不存在：{source_root}")
    return source_root


def find_coverage_entry(
    coverage: dict[str, Any], source_id: str, relative_path: str
) -> dict[str, Any]:
    files = coverage.get("files")
    if not isinstance(files, list):
        raise IngestionWorkspaceError("coverage.yaml files 必须是列表")
    matches = [
        item
        for item in files
        if isinstance(item, dict)
        and item.get("source_id") == source_id
        and item.get("path") == relative_path
    ]
    if len(matches) != 1:
        raise IngestionWorkspaceError(
            f"coverage.yaml 中不存在唯一精确路径：{source_id}={relative_path}"
        )
    return matches[0]


def resolve_registered_source_file(
    root: Path, source_id: str, relative_path: str
) -> tuple[Path, dict[str, Any]]:
    validate_id(source_id, "source id")
    manifest_entry = find_manifest_entry(root, source_id, relative_path)
    source_root = find_source_root(root, source_id)
    source_path = (source_root / relative_path).resolve()
    try:
        source_path.relative_to(source_root)
    except ValueError as exc:
        raise IngestionWorkspaceError(f"来源路径逃逸授权目录：{relative_path}") from exc
    if not source_path.is_file() or source_path.is_symlink():
        raise IngestionWorkspaceError(f"来源文件不存在或不再是普通文件：{source_path}")
    current_sha256 = sha256_file(source_path)
    if current_sha256 != manifest_entry.get("sha256"):
        raise IngestionWorkspaceError(
            f"来源文件已变化，停止读取并重新建立摄入案：{source_id}={relative_path}"
        )
    return source_path, manifest_entry


def source_read(args: argparse.Namespace) -> int:
    root = case_root(args)
    source_path, manifest_entry = resolve_registered_source_file(
        root, args.source_id, args.path
    )
    try:
        text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise IngestionWorkspaceError(
            f"source-read 只支持可按 UTF-8 展示的文本文件：{source_path}：{exc}"
        ) from exc
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        if len(line) > SOURCE_READ_MAX_CHARS:
            raise IngestionWorkspaceError(
                f"第 {number} 行超过 {SOURCE_READ_MAX_CHARS} 字符，"
                "无法保证单次输出有界；请人工处理或先提供可读文本版本"
            )

    coverage = load_yaml(root / "coverage.yaml", "coverage.yaml")
    item = find_coverage_entry(coverage, args.source_id, args.path)
    display = item.get("display")
    if display is None:
        display = {
            "assertion": "machine_emitted",
            "source_sha256": manifest_entry["sha256"],
            "total_lines": len(lines),
            "displayed_through_line": 0,
            "displayed_complete": False,
        }
    if not isinstance(display, dict):
        raise IngestionWorkspaceError("coverage.yaml display 必须是 mapping")
    if (
        display.get("source_sha256") != manifest_entry["sha256"]
        or display.get("total_lines") != len(lines)
    ):
        raise IngestionWorkspaceError(
            f"既有展示进度与当前来源不一致，停止读取：{args.source_id}={args.path}"
        )
    through = display.get("displayed_through_line", 0)
    if not isinstance(through, int) or through < 0 or through > len(lines):
        raise IngestionWorkspaceError("coverage.yaml displayed_through_line 无效")

    start = through
    end = start
    emitted_chars = 0
    while end < len(lines) and end - start < SOURCE_READ_MAX_LINES:
        next_size = len(lines[end]) + 10
        if end > start and emitted_chars + next_size > SOURCE_READ_MAX_CHARS:
            break
        emitted_chars += next_size
        end += 1

    display.update(
        {
            "assertion": "machine_emitted",
            "source_sha256": manifest_entry["sha256"],
            "total_lines": len(lines),
            "displayed_through_line": end,
            "displayed_complete": end == len(lines),
            "updated_at": utc_now(),
        }
    )
    item["display"] = display
    dump_yaml(root / "coverage.yaml", coverage)

    if start < end:
        shown = f"{start + 1}-{end}/{len(lines)}"
    else:
        shown = f"complete/{len(lines)}"
    print(
        f"SOURCE_READ source={args.source_id} path={args.path} "
        f"sha256={manifest_entry['sha256']} lines={shown} "
        f"displayed_complete={str(end == len(lines)).lower()}"
    )
    for number in range(start, end):
        print(f"{number + 1:06d} | {lines[number]}")
    print("END_SOURCE_READ")
    if end < len(lines):
        command = [
            "python",
            "scripts/ingestion_workspace.py",
            "source-read",
            args.case_id,
            args.source_id,
            "--path",
            args.path,
        ]
        print("next: " + " ".join(shlex.quote(value) for value in command))
    else:
        print(
            "next: 全文已由脚本分块展示；理解内容后再登记 read_full，"
            "不要把 displayed_complete 解释为已经理解"
        )
    return 0


def select_source(args: argparse.Namespace) -> int:
    root = case_root(args)
    validate_id(args.source_id, "source id")
    resolve_registered_source_file(root, args.source_id, args.path)
    levels = set(args.level)
    if not levels:
        raise IngestionWorkspaceError("source-select 至少需要一个 --level")
    if not args.reason.strip():
        raise IngestionWorkspaceError("--reason 不能为空")

    coverage = load_yaml(root / "coverage.yaml", "coverage.yaml")
    item = find_coverage_entry(coverage, args.source_id, args.path)
    current_key = (args.source_id, args.path)
    coverage_files = coverage.get("files")
    if not isinstance(coverage_files, list):
        raise IngestionWorkspaceError("coverage.yaml files 必须是列表")
    pending_selections: list[tuple[str, str]] = []
    for candidate in coverage_files:
        if not isinstance(candidate, dict):
            continue
        key = (str(candidate.get("source_id")), str(candidate.get("path")))
        if (
            key != current_key
            and isinstance(candidate.get("selection"), dict)
            and candidate.get("status") not in {"read_full", "unread_blocked"}
        ):
            pending_selections.append(key)
    if pending_selections:
        source_id, path = pending_selections[0]
        raise IngestionWorkspaceError(
            "已有选中来源尚未完成读取或明确阻塞："
            f"{source_id}:{path}。先用 source-read 完整展示并登记 read_full；"
            "若确实无法读取则登记 unread_blocked，之后再选择下一份来源。"
        )
    selection = item.get("selection")
    if selection is None:
        selection = {
            "assertion": "agent_declared",
            "levels": [],
            "reasons": [],
        }
    if not isinstance(selection, dict):
        raise IngestionWorkspaceError("coverage.yaml selection 必须是 mapping")
    existing = selection.get("levels")
    reasons = selection.get("reasons")
    if not isinstance(existing, list) or not isinstance(reasons, list):
        raise IngestionWorkspaceError(
            "coverage.yaml selection.levels/reasons 必须是列表"
        )
    selection.update(
        {
            "assertion": "agent_declared",
            "levels": sorted({str(value) for value in existing} | levels),
            "reasons": list(dict.fromkeys([*(str(value) for value in reasons), args.reason.strip()])),
            "updated_at": utc_now(),
        }
    )
    item["selection"] = selection
    dump_yaml(root / "coverage.yaml", coverage)
    print(
        json.dumps(
            {
                "case_id": args.case_id,
                "source_id": args.source_id,
                "path": args.path,
                "levels": selection["levels"],
                "assertion": "agent_declared",
                "next": "use source-read, then mark read_full or unread_blocked",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def mark_coverage(args: argparse.Namespace) -> int:
    root = case_root(args)
    validate_id(args.source_id, "source id")
    if args.status not in COVERAGE_STATES - {"unreviewed"}:
        raise IngestionWorkspaceError(f"不可写入 coverage status：{args.status}")
    if not args.reason.strip():
        raise IngestionWorkspaceError("--reason 不能为空")
    if args.status in STRONG_READ_STATES:
        if args.glob or args.all_unreviewed:
            raise IngestionWorkspaceError(
                "read_full/read_targeted 只能使用一个精确 --path；"
                "批量 glob 或 --all-unreviewed 只能登记 screened/excluded 等弱状态"
            )
        if len(args.path) != 1:
            raise IngestionWorkspaceError(
                "read_full/read_targeted 每次必须且只能登记一个精确 --path"
            )
        if not args.evidence:
            raise IngestionWorkspaceError("read_full/read_targeted 必须提供直接 --evidence 定位")
        selected_path = args.path[0]
        if args.status == "read_full":
            expected = f"{selected_path}#full-file"
            if expected not in args.evidence:
                raise IngestionWorkspaceError(
                    f"read_full 必须包含 --evidence '{expected}'"
                )
        elif not any(
            evidence.startswith(f"{selected_path}#")
            or evidence.startswith(f"{selected_path}:")
            for evidence in args.evidence
        ):
            raise IngestionWorkspaceError(
                "read_targeted 的 --evidence 必须以精确文件路径开头并包含标题、行号或符号定位"
            )
    coverage = load_yaml(root / "coverage.yaml", "coverage.yaml")
    files = coverage.get("files")
    if not isinstance(files, list):
        raise IngestionWorkspaceError("coverage.yaml files 必须是列表")
    selected: list[dict[str, Any]] = []
    exact = set(args.path)
    patterns = args.glob
    for item in files:
        if not isinstance(item, dict) or item.get("source_id") != args.source_id:
            continue
        path = str(item.get("path", ""))
        matches = path in exact or any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)
        if args.all_unreviewed and item.get("status") == "unreviewed":
            matches = True
        if matches:
            selected.append(item)
    if not selected:
        raise IngestionWorkspaceError("没有 coverage 条目匹配本次选择")
    if args.status == "read_full":
        selected_item = selected[0]
        display = selected_item.get("display")
        if not isinstance(display, dict) or display.get("displayed_complete") is not True:
            raise IngestionWorkspaceError(
                "read_full 需要先用 source-read 完整展示该文件；"
                "displayed_complete 只证明展示完成，仍需 Agent 实际理解"
            )
        _, manifest_entry = resolve_registered_source_file(
            root, args.source_id, args.path[0]
        )
        if (
            display.get("assertion") != "machine_emitted"
            or display.get("source_sha256") != manifest_entry.get("sha256")
        ):
            raise IngestionWorkspaceError("read_full 的机器展示事实与来源版本不一致")
    for item in selected:
        item["status"] = args.status
        item["assertion"] = "agent_declared"
        item["reason"] = args.reason.strip()
        item["evidence"] = list(args.evidence)
        item["updated_at"] = utc_now()
    dump_yaml(root / "coverage.yaml", coverage)
    print(
        json.dumps(
            {
                "case_id": args.case_id,
                "source_id": args.source_id,
                "updated": len(selected),
                "status": args.status,
                "assertion": "agent_declared",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def read_manifest(path: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    try:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("record is not an object")
            result.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise IngestionWorkspaceError(f"无效 source-manifest.jsonl：{exc}") from exc
    return result


def list_files(args: argparse.Namespace) -> int:
    root = case_root(args)
    validate_id(args.source_id, "source id")
    if not 1 <= args.limit <= 500:
        raise IngestionWorkspaceError("--limit 必须在 1-500 之间")
    records = [
        item
        for item in read_manifest(root / "source-manifest.jsonl")
        if item.get("source_id") == args.source_id
    ]
    if args.glob:
        records = [
            item
            for item in records
            if any(
                fnmatch.fnmatchcase(str(item.get("path", "")), pattern)
                for pattern in args.glob
            )
        ]
    total = len(records)
    shown = records[: args.limit]
    print(
        json.dumps(
            {
                "case_id": args.case_id,
                "source_id": args.source_id,
                "matched": total,
                "shown": len(shown),
                "truncated": total > len(shown),
                "files": [item.get("path") for item in shown],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def validate_review_links(root: Path, errors: list[str]) -> None:
    review_path = root / "review.md"
    text = review_path.read_text(encoding="utf-8")
    required_targets = {
        "brief.md",
        "reader-answers.md",
        "inventory.md",
        "questions.md",
        "completion.yaml",
        "source-summary.md",
    }
    seen: set[str] = set()
    for _, raw in LINK_RE.findall(text):
        target = unquote(raw.strip().strip("<>"))
        path_part = target.partition("#")[0]
        scheme = urlsplit(path_part).scheme.lower()
        if scheme in {"http", "https", "mailto"}:
            continue
        if scheme == "file" or path_part.startswith("/"):
            errors.append(f"review.md 使用不可移植链接：{raw}")
            continue
        resolved = (root / path_part).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            errors.append(f"review.md 链接逃逸工作台：{raw}")
            continue
        if not resolved.is_file():
            errors.append(f"review.md 存在坏链：{raw}")
        seen.add(path_part)
    missing = sorted(required_targets - seen)
    if missing:
        errors.append(f"review.md 缺少固定审查入口链接：{', '.join(missing)}")
    if re.search(r"<[^>\n]+>", text):
        errors.append("review.md 仍包含模板占位符")
    for heading in ("Agent 内容声明（待人工审查）", "结构门禁", "人工门禁"):
        if not re.search(rf"^##\s+{re.escape(heading)}\s*$", text, flags=re.MULTILINE):
            errors.append(f"review.md 缺少固定分层标题：{heading}")


def candidate_concepts_exist(root: Path) -> bool:
    knowledge = root / "draft" / "knowledge"
    for area in ("domains", "capabilities", "systems"):
        base = knowledge / area
        if not base.exists():
            continue
        if any(path.name not in {"index.md", "log.md"} for path in base.rglob("*.md")):
            return True
    return False


def named_candidate_view_links(root: Path, document: str, errors: list[str]) -> set[str]:
    path = root / document
    text = path.read_text(encoding="utf-8")
    views: set[str] = set()
    for _, raw in LINK_RE.findall(text):
        target = unquote(raw.strip().strip("<>"))
        path_part = target.partition("#")[0]
        scheme = urlsplit(path_part).scheme.lower()
        if scheme in {"http", "https", "mailto"}:
            continue
        if scheme == "file" or path_part.startswith("/"):
            errors.append(f"{document} 使用不可移植链接：{raw}")
            continue
        resolved = (root / path_part).resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError:
            errors.append(f"{document} 链接逃逸工作台：{raw}")
            continue
        if relative.startswith("draft/views/"):
            errors.append(
                f"{document} 使用已废弃的候选视图路径：{raw}；"
                "请统一链接 draft/knowledge/views/ 下的具名视图"
            )
        if (
            relative.startswith("draft/knowledge/views/")
            and resolved.name != "index.md"
        ):
            views.add(relative)
        if path_part.startswith("draft/") and not resolved.is_file():
            errors.append(f"{document} 存在坏的候选链接：{raw}")
    return views


def validate_candidate_view_surface(root: Path, errors: list[str]) -> None:
    draft = root / "draft"
    if draft.is_dir():
        unexpected = sorted(
            path.name for path in draft.iterdir() if path.name not in {"knowledge", "config"}
        )
        if unexpected:
            errors.append(
                "draft/ 只允许 knowledge/ 和 config/；"
                f"发现多余候选目录或文件：{', '.join(unexpected)}"
            )

    if not candidate_concepts_exist(root):
        return
    review_views = named_candidate_view_links(root, "review.md", errors)
    reader_views = named_candidate_view_links(root, "reader-answers.md", errors)
    if not any(path.startswith("draft/knowledge/views/by-domain/") for path in review_views):
        errors.append("review.md 必须链接一个具名领域产品视图，不能只链接 index.md")
    if not any(path.startswith("draft/knowledge/views/by-journey/") for path in review_views):
        errors.append("review.md 必须链接一个具名旅程/学习产品视图，不能只链接 index.md")
    if not any(path.startswith("draft/knowledge/views/by-journey/") for path in reader_views):
        errors.append(
            "reader-answers.md 必须链接实际消费的具名旅程/学习产品视图"
        )


def validate_completion(
    root: Path, errors: list[str], coverage_files: list[dict[str, Any]]
) -> None:
    value = load_yaml(root / "completion.yaml", "completion.yaml")
    if value.get("claim_owner") != "agent":
        errors.append("completion.yaml claim_owner 必须保持为 agent")
    if value.get("human_review_status") != "pending":
        errors.append("人工审查前 completion.yaml human_review_status 必须保持为 pending")
    for field in ("target_reader", "intended_outcome"):
        current = value.get(field)
        if not isinstance(current, str) or not current.strip() or current.startswith("<"):
            errors.append(f"completion.yaml {field} 未填写")
    knowledge_path = value.get("knowledge_path")
    if not isinstance(knowledge_path, list):
        errors.append("completion.yaml knowledge_path 必须是列表")
        knowledge_path = []
    coverage_by_key = {
        (item.get("source_id"), item.get("path")): item
        for item in coverage_files
        if isinstance(item, dict)
    }
    found_levels: set[str] = set()
    knowledge_root = (root / "draft" / "knowledge").resolve()
    for item in knowledge_path:
        if not isinstance(item, dict):
            errors.append("completion.yaml knowledge_path 条目必须是 mapping")
            continue
        level = str(item.get("level", ""))
        if level not in KNOWLEDGE_LEVELS:
            errors.append(f"completion.yaml knowledge_path 无效层次：{level!r}")
            continue
        if level in found_levels:
            errors.append(f"completion.yaml knowledge_path 重复层次：{level}")
            continue
        found_levels.add(level)
        status = item.get("status")
        if status not in COMPLETION_STATES:
            errors.append(f"completion.yaml knowledge_path {level} 未完成：{status}")
            continue
        topic = item.get("topic")
        if not isinstance(topic, str) or not topic.strip() or topic.startswith("<"):
            errors.append(f"completion.yaml knowledge_path {level} 未填写 topic")
        if status in {"covered", "partial"}:
            source_files = item.get("source_files")
            if not isinstance(source_files, list) or not source_files:
                errors.append(
                    f"completion.yaml knowledge_path {level} {status} 但没有 source_files"
                )
            else:
                for raw_source in source_files:
                    if not isinstance(raw_source, dict):
                        errors.append(
                            f"completion.yaml knowledge_path {level} source_files 条目必须是 mapping"
                        )
                        continue
                    key = (raw_source.get("source_id"), raw_source.get("path"))
                    coverage_item = coverage_by_key.get(key)
                    if coverage_item is None:
                        errors.append(
                            f"completion.yaml knowledge_path {level} 来源不存在：{key}"
                        )
                        continue
                    selection = coverage_item.get("selection")
                    selected_levels = (
                        selection.get("levels") if isinstance(selection, dict) else None
                    )
                    if (
                        not isinstance(selected_levels, list)
                        or level not in selected_levels
                    ):
                        errors.append(
                            f"completion.yaml knowledge_path {level} 来源未用 "
                            f"source-select 绑定该层次：{key}"
                        )
                    if coverage_item.get("status") != "read_full":
                        errors.append(
                            f"completion.yaml knowledge_path {level} 来源没有完成全文阅读：{key}"
                        )
            primary_page = item.get("primary_page")
            if not isinstance(primary_page, str) or not primary_page.strip():
                errors.append(
                    f"completion.yaml knowledge_path {level} {status} 但没有 primary_page"
                )
            else:
                target = (knowledge_root / primary_page).resolve()
                try:
                    target.relative_to(knowledge_root)
                except ValueError:
                    errors.append(
                        f"completion.yaml knowledge_path {level} 主落点逃逸知识 Bundle："
                        f"{primary_page}"
                    )
                else:
                    if not target.is_file():
                        errors.append(
                            f"completion.yaml knowledge_path {level} 主落点不存在："
                            f"{primary_page}"
                        )
            if level != "focus":
                relation = item.get("relation_to_next")
                if not isinstance(relation, str) or not relation.strip():
                    errors.append(
                        f"completion.yaml knowledge_path {level} 缺少 relation_to_next"
                    )
            if status == "partial":
                rationale = item.get("rationale")
                if not isinstance(rationale, str) or not rationale.strip():
                    errors.append(
                        f"completion.yaml knowledge_path {level} partial "
                        "需要同时说明已覆盖和仍缺范围"
                    )
        else:
            rationale = item.get("rationale")
            if not isinstance(rationale, str) or not rationale.strip():
                errors.append(
                    f"completion.yaml knowledge_path {level} 需要说明 {status} 理由"
                )
    missing_levels = sorted(KNOWLEDGE_LEVELS - found_levels)
    if missing_levels:
        errors.append(
            "completion.yaml knowledge_path 缺少层次："
            + ", ".join(missing_levels)
        )
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, list):
        errors.append("completion.yaml dimensions 必须是列表")
        return
    found: set[str] = set()
    for item in dimensions:
        if not isinstance(item, dict):
            errors.append("completion.yaml dimension 必须是 mapping")
            continue
        dimension_id = item.get("id")
        if dimension_id in found:
            errors.append(f"completion.yaml 重复 dimension：{dimension_id}")
            continue
        found.add(str(dimension_id))
        status = item.get("status")
        if status not in COMPLETION_STATES:
            errors.append(f"completion.yaml {dimension_id} 仍未完成：{status}")
            continue
        evidence = item.get("evidence_pages")
        if status in {"covered", "partial"}:
            if not isinstance(evidence, list) or not evidence:
                errors.append(
                    f"completion.yaml {dimension_id} {status} 但没有 evidence_pages"
                )
            else:
                knowledge_root = (root / "draft" / "knowledge").resolve()
                for raw in evidence:
                    target = (knowledge_root / str(raw)).resolve()
                    try:
                        target.relative_to(knowledge_root)
                    except ValueError:
                        errors.append(
                            f"completion.yaml {dimension_id} 证据页逃逸知识 Bundle：{raw}"
                        )
                        continue
                    if not target.is_file():
                        errors.append(
                            f"completion.yaml {dimension_id} 证据页不存在：{raw}"
                        )
            if status == "partial":
                rationale = item.get("rationale")
                if not isinstance(rationale, str) or not rationale.strip():
                    errors.append(
                        f"completion.yaml {dimension_id} partial "
                        "需要同时说明已覆盖和仍缺范围"
                    )
        else:
            rationale = item.get("rationale")
            if not isinstance(rationale, str) or not rationale.strip():
                errors.append(f"completion.yaml {dimension_id} 需要说明 {status} 理由")
    missing = sorted(COMPLETION_DIMENSIONS - found)
    if missing:
        errors.append(f"completion.yaml 缺少 dimension：{', '.join(missing)}")
    visuals = value.get("visuals")
    if not isinstance(visuals, dict):
        errors.append("completion.yaml visuals 必须是 mapping")
        return
    visual_status = visuals.get("status")
    if visual_status == "provided":
        pages = visuals.get("evidence_pages")
        if not isinstance(pages, list) or not pages:
            errors.append("completion.yaml visuals=provided 但没有 evidence_pages")
        else:
            has_mermaid = False
            knowledge_root = (root / "draft" / "knowledge").resolve()
            for raw in pages:
                target = (knowledge_root / str(raw)).resolve()
                try:
                    target.relative_to(knowledge_root)
                except ValueError:
                    errors.append(f"completion.yaml 图表证据页逃逸知识 Bundle：{raw}")
                    continue
                if not target.is_file():
                    errors.append(f"completion.yaml 图表证据页不存在：{raw}")
                    continue
                if "```mermaid" in target.read_text(encoding="utf-8"):
                    has_mermaid = True
            if not has_mermaid:
                errors.append("completion.yaml 声明已提供图表，但证据页没有 Mermaid")
    elif visual_status == "not_applicable":
        rationale = visuals.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append("completion.yaml visuals=not_applicable 必须说明理由")
    else:
        errors.append(f"completion.yaml visuals 仍未完成：{visual_status}")


def check_case(args: argparse.Namespace) -> int:
    root = case_root(args)
    errors: list[str] = []
    missing = sorted(name for name in REQUIRED_ROOT_FILES if not (root / name).is_file())
    if missing:
        errors.append(f"工作台缺少根文件：{', '.join(missing)}")
    for name in WORKBENCH_ENTRY_FILES:
        if (root / "assets" / name).exists():
            errors.append(f"固定入口被错误放入 assets/：{name}")

    case = load_yaml(root / "case.yaml", "case.yaml")
    manifest = read_manifest(root / "source-manifest.jsonl")
    expected_keys = {(item.get("source_id"), item.get("path")) for item in manifest}
    if len(expected_keys) != len(manifest):
        errors.append("source-manifest.jsonl 存在重复来源路径")
    coverage = load_yaml(root / "coverage.yaml", "coverage.yaml")
    if coverage.get("semantics") != "agent declarations; not machine-observed reading":
        errors.append("coverage.yaml 缺少 Agent 声明语义标记")
    if coverage.get("display_semantics") != (
        "machine-observed script output; proves complete display, not agent comprehension"
    ):
        errors.append("coverage.yaml 缺少机器展示事实语义标记")
    coverage_files = coverage.get("files")
    if not isinstance(coverage_files, list):
        errors.append("coverage.yaml files 必须是列表")
        coverage_files = []
    coverage_keys: set[tuple[Any, Any]] = set()
    unreviewed: list[tuple[Any, Any]] = []
    invalid_states: list[tuple[tuple[Any, Any], Any]] = []
    missing_reasons: list[tuple[Any, Any]] = []
    missing_evidence: list[tuple[Any, Any]] = []
    missing_assertions: list[tuple[Any, Any]] = []
    unbound_read_evidence: list[tuple[Any, Any]] = []
    unverified_full_reads: list[tuple[Any, Any]] = []
    selected_unresolved: list[tuple[Any, Any]] = []
    invalid_selections: list[tuple[Any, Any]] = []
    for item in coverage_files:
        if not isinstance(item, dict):
            errors.append("coverage.yaml file entry 必须是 mapping")
            continue
        key = (item.get("source_id"), item.get("path"))
        if key in coverage_keys:
            errors.append(f"coverage.yaml 重复条目：{key}")
        coverage_keys.add(key)
        status = item.get("status")
        if status not in COVERAGE_STATES:
            invalid_states.append((key, status))
        elif status == "unreviewed":
            unreviewed.append(key)
        reason = item.get("reason")
        if status != "unreviewed" and (not isinstance(reason, str) or not reason.strip()):
            missing_reasons.append(key)
        if status != "unreviewed" and item.get("assertion") != "agent_declared":
            missing_assertions.append(key)
        if status in {"read_full", "read_targeted"}:
            evidence = item.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                missing_evidence.append(key)
            else:
                path = str(item.get("path", ""))
                if status == "read_full":
                    bound = f"{path}#full-file" in evidence
                else:
                    bound = any(
                        str(value).startswith(f"{path}#")
                        or str(value).startswith(f"{path}:")
                        for value in evidence
                    )
                if not bound:
                    unbound_read_evidence.append(key)
            if status == "read_full":
                display = item.get("display")
                if (
                    not isinstance(display, dict)
                    or display.get("assertion") != "machine_emitted"
                    or display.get("displayed_complete") is not True
                ):
                    unverified_full_reads.append(key)
        selection = item.get("selection")
        if selection is not None:
            if not isinstance(selection, dict):
                invalid_selections.append(key)
            else:
                levels = selection.get("levels")
                reasons = selection.get("reasons")
                valid_levels = (
                    isinstance(levels, list)
                    and bool(levels)
                    and all(level in KNOWLEDGE_LEVELS for level in levels)
                )
                if (
                    selection.get("assertion") != "agent_declared"
                    or not valid_levels
                    or not isinstance(reasons, list)
                    or not reasons
                    or any(not isinstance(reason, str) or not reason.strip() for reason in reasons)
                ):
                    invalid_selections.append(key)
                if status not in {"read_full", "unread_blocked"}:
                    selected_unresolved.append(key)
    if unreviewed:
        errors.append(
            f"coverage.yaml 尚未分类 {len(unreviewed)} 项；示例：{unreviewed[:10]}"
        )
    if invalid_states:
        errors.append(
            f"coverage.yaml 存在 {len(invalid_states)} 个无效状态；示例：{invalid_states[:10]}"
        )
    if missing_reasons:
        errors.append(
            f"coverage.yaml 有 {len(missing_reasons)} 项缺少处理理由；示例：{missing_reasons[:10]}"
        )
    if missing_evidence:
        errors.append(
            f"coverage.yaml 有 {len(missing_evidence)} 个已读取项缺少证据定位；示例：{missing_evidence[:10]}"
        )
    if missing_assertions:
        errors.append(
            f"coverage.yaml 有 {len(missing_assertions)} 项未标记为 Agent 声明；"
            f"示例：{missing_assertions[:10]}"
        )
    if unbound_read_evidence:
        errors.append(
            f"coverage.yaml 有 {len(unbound_read_evidence)} 个强阅读声明没有逐文件绑定证据；"
            f"示例：{unbound_read_evidence[:10]}"
        )
    if unverified_full_reads:
        errors.append(
            f"coverage.yaml 有 {len(unverified_full_reads)} 个 read_full "
            "没有完整机器展示事实；"
            f"示例：{unverified_full_reads[:10]}"
        )
    if invalid_selections:
        errors.append(
            f"coverage.yaml 有 {len(invalid_selections)} 个无效来源选择声明；"
            f"示例：{invalid_selections[:10]}"
        )
    if selected_unresolved:
        errors.append(
            f"coverage.yaml 有 {len(selected_unresolved)} 个已选择关键来源尚未阅读或阻塞；"
            f"示例：{selected_unresolved[:10]}"
        )
    if coverage_keys != expected_keys:
        missing_coverage = expected_keys - coverage_keys
        extra_coverage = coverage_keys - expected_keys
        if missing_coverage:
            errors.append(f"coverage.yaml 缺少 {len(missing_coverage)} 个来源文件")
        if extra_coverage:
            errors.append(f"coverage.yaml 多出 {len(extra_coverage)} 个来源文件")

    for source in case.get("sources", []):
        if not isinstance(source, dict):
            errors.append("case.yaml source 必须是 mapping")
            continue
        current, _ = scan_source(str(source.get("id", "")), str(source.get("root", "")))
        if current["file_count"] != source.get("file_count"):
            errors.append(
                f"来源 {source.get('id')} 文件数已变化："
                f"{source.get('file_count')} -> {current['file_count']}"
            )
        if current["fingerprint"] != source.get("fingerprint"):
            errors.append(f"来源 {source.get('id')} 内容指纹已变化")

    harness = case.get("harness")
    expected_surface = harness.get("formal_surface_fingerprint") if isinstance(harness, dict) else None
    if expected_surface != formal_surface_fingerprint(project_root()):
        errors.append("正式 knowledge/ 或 config/ 在人工批准前发生变化")

    if all((root / name).is_file() for name in ("completion.yaml", "review.md")):
        validate_completion(root, errors, coverage_files)
        validate_review_links(root, errors)
        validate_candidate_view_surface(root, errors)
    errors.extend(markdown_table_errors(list(root.glob("*.md")), root))

    knowledge_report = validate_bundle(
        root / "draft" / "knowledge",
        root / "draft" / "config" / "knowledge-domains.yaml",
    )
    errors.extend(f"knowledge bundle: {item}" for item in knowledge_report.errors)

    counts = Counter(
        str(item.get("status")) for item in coverage_files if isinstance(item, dict)
    )
    result = {
        "status": "passed" if not errors else "failed",
        "structural_gate": "passed" if not errors else "failed",
        "content_review": "pending_human",
        "case_id": args.case_id,
        "workbench": str(root),
        "machine_source_files": len(manifest),
        "agent_coverage_claims": dict(sorted(counts.items())),
        "machine_displayed_complete": sum(
            1
            for item in coverage_files
            if isinstance(item, dict)
            and isinstance(item.get("display"), dict)
            and item["display"].get("displayed_complete") is True
        ),
        "knowledge_files": knowledge_report.files_checked,
        "knowledge_concepts": knowledge_report.concepts_checked,
        "errors": errors,
    }
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ingestion-structure-check: {'PASS' if not errors else 'FAIL'}")
        print("content-review: PENDING_HUMAN")
        print(f"case: {args.case_id}")
        print(f"machine source files: {len(manifest)}")
        print(f"agent coverage claims: {dict(sorted(counts.items()))}")
        print(f"machine displayed complete: {result['machine_displayed_complete']}")
        print(
            f"knowledge files: {knowledge_report.files_checked}; "
            f"concepts: {knowledge_report.concepts_checked}"
        )
        if errors:
            print("errors:")
            for error in errors:
                print(f"- {error}")
    return 0 if not errors else 1


def status_case(args: argparse.Namespace) -> int:
    root = case_root(args)
    case = load_yaml(root / "case.yaml", "case.yaml")
    coverage = load_yaml(root / "coverage.yaml", "coverage.yaml")
    files = coverage.get("files") if isinstance(coverage.get("files"), list) else []
    counts = Counter(str(item.get("status")) for item in files if isinstance(item, dict))
    displayed_complete = sum(
        1
        for item in files
        if isinstance(item, dict)
        and isinstance(item.get("display"), dict)
        and item["display"].get("displayed_complete") is True
    )
    selected_sources = sum(
        1
        for item in files
        if isinstance(item, dict) and isinstance(item.get("selection"), dict)
    )
    print(
        json.dumps(
            {
                "case_id": args.case_id,
                "goal": case.get("goal"),
                "sources": [
                    {
                        "id": item.get("id"),
                        "root": item.get("root"),
                        "file_count": item.get("file_count"),
                    }
                    for item in case.get("sources", [])
                    if isinstance(item, dict)
                ],
                "machine_source_files": sum(
                    int(item.get("file_count", 0))
                    for item in case.get("sources", [])
                    if isinstance(item, dict)
                ),
                "agent_coverage_claims": dict(sorted(counts.items())),
                "machine_displayed_complete": displayed_complete,
                "selected_sources": selected_sources,
                "content_review": "pending_human",
                "review": str(root / "review.md"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "公开契约：source-manifest/source-summary 是来源机器事实；coverage 的 status "
            "是 Agent 声明，display 是脚本输出事实。"
            "check 只判定结构是否可交人工审查，不判定内容真实、充分或已经完成。"
        ),
    )
    parser.add_argument("--cases-root", type=Path, default=default_cases_root())
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="创建摄入工作台并确定性盘点授权来源")
    init.add_argument("case_id")
    init.add_argument("--goal", required=True)
    init.add_argument("--source", action="append", default=[], metavar="ID=DIR")
    init.set_defaults(func=init_case)

    mark = subparsers.add_parser(
        "mark",
        help="登记 Agent 的逐文件筛查、读取或排除声明",
        description=(
            "screened/excluded 等弱状态可批量登记；read_full/read_targeted "
            "每次只能使用一个精确 --path，并提供与该路径绑定的定位。"
        ),
    )
    mark.add_argument("case_id")
    mark.add_argument("source_id")
    mark.add_argument("--status", required=True, choices=sorted(COVERAGE_STATES - {"unreviewed"}))
    mark.add_argument("--reason", required=True)
    mark.add_argument("--evidence", action="append", default=[])
    mark.add_argument("--path", action="append", default=[])
    mark.add_argument("--glob", action="append", default=[])
    mark.add_argument("--all-unreviewed", action="store_true")
    mark.set_defaults(func=mark_coverage)

    status = subparsers.add_parser("status", help="显示来源数量、覆盖状态和审查入口")
    status.add_argument("case_id")
    status.set_defaults(func=status_case)

    files = subparsers.add_parser("files", help="按来源和 glob 有界查看机器文件清单")
    files.add_argument("case_id")
    files.add_argument("source_id")
    files.add_argument("--glob", action="append", default=[])
    files.add_argument("--limit", type=int, default=100)
    files.set_defaults(func=list_files)

    read = subparsers.add_parser(
        "source-read",
        help="逐块展示一个已登记 UTF-8 来源文件，并记录机器展示进度",
        description=(
            "每次只输出一个固定上限、带行号的连续片段；重复同一命令自动续读。"
            "displayed_complete 只证明脚本已完整输出，不证明 Agent 已理解。"
        ),
    )
    read.add_argument("case_id")
    read.add_argument("source_id")
    read.add_argument("--path", required=True)
    read.set_defaults(func=source_read)

    select = subparsers.add_parser(
        "source-select",
        help="把一个精确来源绑定为三层知识主线的必读依据",
        description=(
            "选择是 Agent 的注意力契约，不判断来源是否正确。"
            "一次只能有一份尚未处理的已选来源；完成 read_full 或明确 "
            "unread_blocked 后才能选择下一份。"
        ),
    )
    select.add_argument("case_id")
    select.add_argument("source_id")
    select.add_argument("--path", required=True)
    select.add_argument(
        "--level",
        action="append",
        default=[],
        choices=sorted(KNOWLEDGE_LEVELS),
    )
    select.add_argument("--reason", required=True)
    select.set_defaults(func=select_source)

    check = subparsers.add_parser(
        "check",
        help="验证工作台结构是否可交人工审查；不判定内容质量",
    )
    check.add_argument("case_id")
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.set_defaults(func=check_case)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except IngestionWorkspaceError as exc:
        print(f"ingestion-workspace: ERROR\n- {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
