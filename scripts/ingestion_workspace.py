#!/usr/bin/env python3
"""Drive a recoverable complete or focused knowledge-ingestion workbench.

The tool keeps deterministic source identity and small recoverable state. It does
not decide knowledge truth, write domain content, or replace human review.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from knowledge_check import validate_bundle


SCHEMA_VERSION = "1.2"
CASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
QUESTION_ID_RE = re.compile(r"^q-[0-9]{3}$")
UNIT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
LINK_RE = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
TS_IMPORT_RE = re.compile(
    r"(?:from\s+|import\s*\()\s*['\"](?P<module>(?:\.{1,2}/|@/)[^'\"]+)['\"]"
)
PYTHON_FROM_RE = re.compile(r"^\s*from\s+(?P<module>\.*[A-Za-z_][\w.]*)\s+import\s+", re.MULTILINE)
PYTHON_IMPORT_RE = re.compile(r"^\s*import\s+(?P<module>[A-Za-z_][\w.]*)", re.MULTILINE)
PATH_LITERAL_RE = re.compile(r"['\"](?P<path>/(?:api/)?[A-Za-z0-9_./{}:-]{4,})['\"]")
STALE_MARKERS = ("待核实", "待补充", "TODO", "TBD")
PLACEHOLDER_RE = re.compile(
    r"<(?:case-id|question-id|source-id|unit-id|area|page|path|slug|"
    r"[^>\n]*[\u4e00-\u9fff][^>\n]*)>"
)
TEXT_SUFFIXES = {
    ".c", ".cc", ".cfg", ".conf", ".cpp", ".css", ".csv", ".go",
    ".h", ".hpp", ".html", ".ini", ".java", ".js", ".json", ".jsx",
    ".md", ".mjs", ".py", ".rst", ".scss", ".sh", ".sql", ".toml",
    ".ts", ".tsx", ".txt", ".vue", ".xml", ".yaml", ".yml",
}
IGNORED_DIRECTORIES = {
    ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv",
    ".runtime", "__pycache__", "build", "dist", "node_modules",
}
IGNORED_FILENAMES = {".env", "SHA256SUMS"}
QUESTION_STATES = {"working", "answered", "partial", "external_missing", "conflict"}
QUESTION_STATUS_LABELS = {
    "working": "处理中",
    "answered": "已回答",
    "partial": "部分回答",
    "external_missing": "外部缺失",
    "conflict": "冲突待确认",
}
RUN_KINDS = {"health", "api", "sql", "page", "other"}
MAX_CANDIDATE_POOL = 24
MAX_MATERIAL_GROUP_MEMBERS = 12
MAX_MATERIAL_GROUP_BYTES = 100_000
NARRATIVE_SUFFIXES = {".md", ".rst", ".txt"}
INGESTION_MODES = {"focused", "complete"}
MATERIAL_GROUP_STATES = {"unreviewed", "partial", "reviewed", "irrelevant", "external"}
REALITY_STATES = {
    "current_implementation",
    "current_decision",
    "target_design",
    "historical",
    "conflict",
    "unknown",
}
PLAN_LENSES = {
    "position",
    "lifecycle",
    "data",
    "rules",
    "software",
    "shared",
    "reality",
    "navigation",
}


class IngestionError(Exception):
    """An actionable ingestion-workbench error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_cases_root() -> Path:
    return project_root() / "workspaces" / "knowledge-ingestion"


def validate_id(value: str, label: str, pattern: re.Pattern[str] = CASE_ID_RE) -> None:
    if not pattern.fullmatch(value):
        raise IngestionError(f"{label} 格式无效：{value}")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, prefix=f".{path.name}."
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return digest_bytes(encoded)


def case_root(cases_root: Path, case_id: str, must_exist: bool = True) -> Path:
    validate_id(case_id, "case id")
    root = cases_root.resolve() / case_id
    if must_exist and not (root / ".state" / "case.json").is_file():
        raise IngestionError(f"摄入案不存在：{root}")
    return root


def load_case(cases_root: Path, case_id: str) -> tuple[Path, dict[str, Any]]:
    root = case_root(cases_root, case_id)
    path = root / ".state" / "case.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IngestionError(f"无法读取摄入案状态 {path}：{exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise IngestionError(f"不支持的摄入案状态：{path}")
    return root, value


def save_case(root: Path, case: dict[str, Any]) -> None:
    case["updated_at"] = utc_now()
    atomic_write_json(root / ".state" / "case.json", case)


@contextmanager
def case_state_lock(cases_root: Path, case_id: str):
    """Serialize mutations without adding another workbench state file."""
    root = case_root(cases_root, case_id)
    descriptor = os.open(root / ".state", os.O_RDONLY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def question_by_id(case: dict[str, Any], question_id: str) -> dict[str, Any]:
    validate_id(question_id, "question id", QUESTION_ID_RE)
    for question in case.get("questions", []):
        if question.get("id") == question_id:
            return question
    raise IngestionError(f"问题不存在：{question_id}")


def parse_source(value: str) -> tuple[str, Path]:
    source_id, separator, raw_path = value.partition("=")
    if not separator:
        raise IngestionError("--source 必须使用 <id>=<directory> 格式")
    validate_id(source_id, "source id")
    root = Path(raw_path).expanduser().resolve()
    if not root.is_dir():
        raise IngestionError(f"来源目录不存在：{root}")
    return source_id, root


def run_git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=False, capture_output=True, text=True
    )


def git_identity(root: Path) -> dict[str, Any] | None:
    top = run_git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return None
    git_root = Path(top.stdout.strip()).resolve()
    head = run_git(git_root, "rev-parse", "HEAD")
    status = run_git(git_root, "status", "--short", "--", str(root))
    if head.returncode != 0 or status.returncode != 0:
        return None
    return {
        "root": str(git_root),
        "commit": head.stdout.strip(),
        "scope": str(root.relative_to(git_root)) if root != git_root else ".",
        "dirty": bool(status.stdout.strip()),
    }


def source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, directories, names in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in IGNORED_DIRECTORIES)
        current_path = Path(current)
        for name in sorted(names):
            if name in IGNORED_FILENAMES:
                continue
            path = current_path / name
            if path.is_symlink() or not path.is_file():
                continue
            files.append(path)
    return files


def text_metadata(path: Path, content: bytes) -> dict[str, Any]:
    if path.suffix.lower() not in TEXT_SUFFIXES and b"\0" in content[:8192]:
        return {"text": False, "title": None, "headings": []}
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return {"text": False, "title": None, "headings": []}
    headings = [item.strip()[:160] for item in HEADING_RE.findall(text[:524288])]
    title = headings[0] if headings else None
    return {"text": True, "title": title, "headings": headings[:24]}


def scan_sources(values: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not values:
        raise IngestionError("至少需要一个 --source")
    sources: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for value in values:
        source_id, root = parse_source(value)
        if source_id in seen_ids:
            raise IngestionError(f"重复 source id：{source_id}")
        seen_ids.add(source_id)
        entries: list[dict[str, Any]] = []
        for path in source_files(root):
            try:
                content = path.read_bytes()
            except OSError as exc:
                raise IngestionError(f"无法盘点来源文件 {path}：{exc}") from exc
            relative = path.relative_to(root).as_posix()
            entry = {
                "source_id": source_id,
                "path": relative,
                "bytes": len(content),
                "sha256": digest_bytes(content),
                "suffix": path.suffix.lower(),
                **text_metadata(path, content),
            }
            entries.append(entry)
            manifest.append(entry)
        identity = git_identity(root)
        sources.append(
            {
                "id": source_id,
                "root": str(root),
                "kind": "local_git" if identity else "local_directory",
                "git": identity,
                "file_count": len(entries),
                "fingerprint": canonical_digest(
                    [{"path": item["path"], "sha256": item["sha256"]} for item in entries]
                ),
            }
        )
    manifest.sort(key=lambda item: (item["source_id"], item["path"]))
    return sources, manifest


def write_manifest(path: Path, records: list[dict[str, Any]]) -> None:
    content = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in records)
    atomic_write_text(path, content)


def read_manifest(root: Path) -> list[dict[str, Any]]:
    path = root / ".state" / "source-manifest.jsonl"
    try:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IngestionError(f"无法读取来源基线 {path}：{exc}") from exc
    if not all(isinstance(item, dict) for item in records):
        raise IngestionError(f"来源基线损坏：{path}")
    return records


def manifest_ref(item: dict[str, Any]) -> str:
    return source_ref(item["source_id"], item["path"])


def split_path_cluster(
    source_id: str,
    records: list[dict[str, Any]],
    prefix: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """Split one source by observable path structure without assigning meaning."""
    if (
        len(records) <= MAX_MATERIAL_GROUP_MEMBERS
        and sum(item["bytes"] for item in records) <= MAX_MATERIAL_GROUP_BYTES
    ):
        return [{"source_id": source_id, "prefix": prefix, "records": records}]

    direct: list[dict[str, Any]] = []
    children: dict[str, list[dict[str, Any]]] = defaultdict(list)
    depth = len(prefix)
    for item in records:
        parts = PurePosixPath(item["path"]).parts
        if len(parts) <= depth + 1:
            direct.append(item)
        else:
            children[parts[depth]].append(item)

    clusters: list[dict[str, Any]] = []
    if direct:
        chunks: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        current_bytes = 0
        for item in direct:
            if current and (
                len(current) >= MAX_MATERIAL_GROUP_MEMBERS
                or current_bytes + item["bytes"] > MAX_MATERIAL_GROUP_BYTES
            ):
                chunks.append(current)
                current = []
                current_bytes = 0
            current.append(item)
            current_bytes += item["bytes"]
        if current:
            chunks.append(current)
        for chunk in chunks:
            clusters.append(
                {
                    "source_id": source_id,
                    "prefix": prefix,
                    "records": chunk,
                }
            )
    for name in sorted(children):
        clusters.extend(split_path_cluster(source_id, children[name], (*prefix, name)))
    return clusters


def material_group_label(source_id: str, prefix: tuple[str, ...], part: int | None = None) -> str:
    location = "/".join(prefix) if prefix else "根目录"
    suffix = f"（第 {part} 组）" if part is not None else ""
    return f"{source_id}:{location}{suffix}"


def build_material_groups(
    case: dict[str, Any], manifest: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Build non-overlapping groups from paths and exact hashes only."""
    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in manifest:
        by_hash[item["sha256"]].append(item)

    clusters: list[dict[str, Any]] = []
    duplicate_refs: set[str] = set()
    for digest, records in sorted(by_hash.items()):
        if len(records) < 2:
            continue
        duplicate_refs.update(manifest_ref(item) for item in records)
        clusters.append(
            {
                "kind": "exact_duplicate",
                "label": f"完全重复内容 {digest[:8]}",
                "basis": "sha256 完全相同；只需完整读取一个代表文件，其余用于确认重复位置",
                "records": sorted(records, key=manifest_ref),
            }
        )

    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in manifest:
        if manifest_ref(item) not in duplicate_refs:
            by_source[item["source_id"]].append(item)
    for source_id in sorted(by_source):
        source_records = sorted(by_source[source_id], key=lambda item: item["path"])
        narrative_records = [
            item for item in source_records if item["suffix"] in NARRATIVE_SUFFIXES
        ]
        implementation_records = [
            item for item in source_records if item["suffix"] not in NARRATIVE_SUFFIXES
        ]
        for item in narrative_records:
            clusters.append(
                {
                    "kind": "narrative_document",
                    "label": f"{source_id}:{item['path']}",
                    "basis": (
                        "独立叙述文档；文档链接只形成地图关系，不把多份长文合并为一次阅读任务"
                    ),
                    "records": [item],
                }
            )
        path_clusters = (
            split_path_cluster(source_id, implementation_records)
            if implementation_records
            else []
        )
        label_counts = Counter(tuple(item["prefix"]) for item in path_clusters)
        label_seen: Counter[tuple[str, ...]] = Counter()
        for cluster in path_clusters:
            prefix = tuple(cluster["prefix"])
            label_seen[prefix] += 1
            part = label_seen[prefix] if label_counts[prefix] > 1 else None
            clusters.append(
                {
                    "kind": "path_cluster",
                    "label": material_group_label(source_id, prefix, part),
                    "basis": "同一授权来源中的共同路径前缀",
                    "records": cluster["records"],
                }
            )

    groups: list[dict[str, Any]] = []
    ref_to_group: dict[str, str] = {}
    for number, cluster in enumerate(clusters, 1):
        group_id = f"group-{number:03d}"
        records = cluster.pop("records")
        members = [manifest_ref(item) for item in records]
        for ref in members:
            ref_to_group[ref] = group_id
        groups.append(
            {
                "id": group_id,
                "kind": cluster["kind"],
                "label": cluster["label"],
                "basis": cluster["basis"],
                "members": members,
                "member_count": len(members),
                "total_bytes": sum(item["bytes"] for item in records),
                "suffixes": dict(sorted(Counter(item["suffix"] or "[none]" for item in records).items())),
                "representative_paths": [item["path"] for item in records[:5]],
                "related_groups": [],
                "status": "unreviewed",
                "summary": "",
                "finding_ids": [],
                "updated_at": None,
            }
        )

    # Relations remain observable: direct code imports and relative Markdown links.
    by_ref = {manifest_ref(item): item for item in manifest}
    relation_bases: dict[tuple[str, str], set[str]] = defaultdict(set)
    for ref, item in by_ref.items():
        origin = ref_to_group[ref]
        text = read_source_text(case, item)
        if not text:
            continue
        targets = direct_import_refs(item, text, by_ref)
        if item["suffix"] in {".md", ".txt", ".rst"}:
            parent = PurePosixPath(item["path"]).parent
            for raw in LINK_RE.findall(text):
                target = raw.split("#", 1)[0].split("?", 1)[0]
                if not target or "://" in target or target.startswith("#"):
                    continue
                candidate = parent / target
                parts: list[str] = []
                valid = True
                for part in candidate.parts:
                    if part == "..":
                        if not parts:
                            valid = False
                            break
                        parts.pop()
                    elif part != ".":
                        parts.append(part)
                if valid:
                    linked = source_ref(item["source_id"], PurePosixPath(*parts).as_posix())
                    if linked in by_ref:
                        targets.add(linked)
        for target in targets:
            destination = ref_to_group.get(target)
            if destination and destination != origin:
                basis = "code_import" if item["suffix"] in {".py", ".ts", ".tsx", ".js", ".jsx", ".vue"} else "document_link"
                relation_bases[(origin, destination)].add(basis)

    by_group = {item["id"]: item for item in groups}
    for (origin, destination), bases in sorted(relation_bases.items()):
        by_group[origin]["related_groups"].append(
            {"group_id": destination, "basis": sorted(bases)}
        )
    return groups


def group_by_id(case: dict[str, Any], group_id: str) -> dict[str, Any]:
    for group in case.get("material_groups", []):
        if group.get("id") == group_id:
            return group
    raise IngestionError(f"材料组不存在：{group_id}")


def finding_by_id(case: dict[str, Any], finding_id: str) -> dict[str, Any]:
    for finding in case.get("findings", []):
        if finding.get("id") == finding_id:
            return finding
    raise IngestionError(f"读后发现不存在：{finding_id}")


def topic_by_id(case: dict[str, Any], topic_id: str) -> dict[str, Any]:
    for topic in case.get("topics", []):
        if topic.get("id") == topic_id:
            return topic
    raise IngestionError(f"知识主题不存在：{topic_id}")


def ensure_complete(case: dict[str, Any]) -> None:
    if case.get("mode") != "complete":
        raise IngestionError("该命令只用于宽范围完整整理；聚焦整理继续使用问题驱动命令")


def refresh_complete_cursor(case: dict[str, Any]) -> None:
    """Move to the first unfinished item; repeated reads never advance it."""
    ensure_complete(case)
    if case.get("stage") == "publish_ready":
        case["cursor"] = {"item_type": None, "item_id": None}
        case["next_action"] = "请用户审查候选知识、产品视图和 review.md，决定发布或退回"
        return
    for group in case.get("material_groups", []):
        if group["status"] in {"unreviewed", "partial"}:
            case["stage"] = "discovering"
            case["cursor"] = {"item_type": "material_group", "item_id": group["id"]}
            case["next_action"] = f"运行 next 取得并审视材料组 {group['id']}"
            return
    if not case.get("plan_review", {}).get("passed"):
        case["stage"] = "planning"
        case["cursor"] = {"item_type": None, "item_id": None}
        case["next_action"] = "根据读后发现规划知识主题，再运行 plan-review 复核目录"
        return
    for topic in case.get("topics", []):
        if topic["status"] != "ready":
            case["stage"] = "writing"
            case["cursor"] = {"item_type": "knowledge_topic", "item_id": topic["id"]}
            case["next_action"] = f"形成知识主题 {topic['id']} 的正文与产品视图，再运行 record-topic"
            return
    case["stage"] = "reviewing"
    case["cursor"] = {"item_type": None, "item_id": None}
    case["next_action"] = "运行 review 重建人工审查页并检查候选知识"


def public_material_group(
    case: dict[str, Any], manifest: list[dict[str, Any]], group: dict[str, Any], *, members: bool
) -> dict[str, Any]:
    payload = {key: value for key, value in group.items() if key != "members"}
    if members:
        manifest_by_ref = {manifest_ref(item): item for item in manifest}
        sources = source_map(case)
        payload["members"] = []
        for ref in group["members"]:
            item = manifest_by_ref[ref]
            source_id, relative = split_source_ref(ref)
            payload["members"].append(
                {
                    "ref": ref,
                    "absolute_path": str(Path(sources[source_id]["root"]) / relative),
                    "bytes": item["bytes"],
                    "suffix": item["suffix"],
                    "title": item.get("title"),
                    "headings": item.get("headings", []),
                }
            )
    return payload


def source_map(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in case.get("sources", [])}


def public_source_identity(item: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "id": item["id"],
        "root": item["root"],
        "kind": item["kind"],
        "file_count": item["file_count"],
        "fingerprint": item["fingerprint"],
    }
    git = item.get("git")
    if isinstance(git, dict):
        payload["git"] = {
            "commit": git["commit"],
            "scope": git["scope"],
            "dirty": git["dirty"],
        }
    return payload


def source_ref(source_id: str, path: str) -> str:
    return f"{source_id}:{path}"


def split_source_ref(value: str) -> tuple[str, str]:
    source_id, separator, relative = value.partition(":")
    if not separator:
        raise IngestionError(f"来源引用必须使用 <source-id>:<path>：{value}")
    validate_id(source_id, "source id")
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise IngestionError(f"来源路径越界：{value}")
    return source_id, candidate.as_posix()


def resolve_source(case: dict[str, Any], value: str) -> Path:
    source_id, relative = split_source_ref(value)
    source = source_map(case).get(source_id)
    if source is None:
        raise IngestionError(f"来源不存在：{source_id}")
    root = Path(source["root"]).resolve()
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise IngestionError(f"来源路径越界：{value}") from exc
    if not resolved.is_file():
        raise IngestionError(f"来源文件不存在：{resolved}")
    return resolved


def scaffold_case(root: Path) -> None:
    knowledge = root / "draft" / "knowledge"
    for relative, title in (
        ("index.md", "# 候选知识入口\n"),
        ("domains/index.md", "# 领域知识\n"),
        ("capabilities/index.md", "# 公共能力\n"),
        ("systems/index.md", "# 系统知识\n"),
        ("sources/index.md", "# 来源记录\n"),
        ("views/index.md", "# 产品视图\n"),
        ("views/by-domain/index.md", "# 领域视图\n"),
        ("views/by-journey/index.md", "# 旅程与任务视图\n"),
    ):
        atomic_write_text(knowledge / relative, title + "\n")
    domain_map = project_root() / "config" / "knowledge-domains.yaml"
    target = root / "draft" / "config" / "knowledge-domains.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(domain_map, target)


def new_question(number: int, text: str) -> dict[str, Any]:
    return {
        "id": f"q-{number:03d}",
        "text": text,
        "status": "working",
        "summary": "",
        "missing": [],
        "expected_units": [],
        "knowledge_paths": [],
        "requires_run": False,
        "run_ids": [],
        "pending_run_ids": [],
        "integrated_run_ids": [],
        "evidence": [],
        "query_terms": [],
        "candidate_queue": [],
        "active_packet": [],
        "dismissed_packets": [],
        "candidate_closure": None,
        "next_action": "规划本问题的知识单元并取得第一小批直接来源",
        "updated_at": utc_now(),
    }


def start_case(args: argparse.Namespace) -> int:
    root = case_root(args.cases_root, args.case_id, must_exist=False)
    if root.exists() and any(root.iterdir()):
        raise IngestionError(f"摄入案目录已存在且非空：{root}")
    questions = [item.strip() for item in args.question if item.strip()]
    if args.mode == "focused" and not questions:
        raise IngestionError("至少需要一个 --question；问题主线不能由工具猜测")
    sources, manifest = scan_sources(args.source)
    root.mkdir(parents=True, exist_ok=True)
    scaffold_case(root)
    now = utc_now()
    case = {
        "schema_version": SCHEMA_VERSION,
        "id": args.case_id,
        "mode": args.mode,
        "goal": args.goal.strip(),
        "target_reader": args.reader.strip(),
        "boundaries": [item.strip() for item in args.boundary if item.strip()],
        "sources": sources,
        "questions": [new_question(index, text) for index, text in enumerate(questions, 1)],
        "stage": "focused" if args.mode == "focused" else "mapping",
        "cursor": {"item_type": None, "item_id": None},
        "material_groups": [],
        "findings": [],
        "topics": [],
        "plan_review": {"passed": False, "lenses": {}, "not_applicable": {}, "issues": []},
        "created_at": now,
        "updated_at": now,
        "next_action": (
            "为 q-001 规划一至三个知识单元，再取得第一小批直接来源"
            if args.mode == "focused"
            else "查看材料地图，再从第一个材料组开始读后发现"
        ),
    }
    if args.mode == "complete":
        case["material_groups"] = build_material_groups(case, manifest)
        refresh_complete_cursor(case)
    write_manifest(root / ".state" / "source-manifest.jsonl", manifest)
    save_case(root, case)
    generate_review(root, case)
    print(
        json.dumps(
            {
                "case_id": args.case_id,
                "mode": case["mode"],
                "goal": case["goal"],
                "questions": [{"id": item["id"], "text": item["text"]} for item in case["questions"]],
                "sources": [public_source_identity(item) for item in case["sources"]],
                "source_files": len(manifest),
                "material_groups": len(case["material_groups"]),
                "user_visible": ["draft/knowledge/", "review.md"],
                "internal_state": [".state/case.json", ".state/source-manifest.jsonl"],
                "next": case["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def add_question(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    number = len(case["questions"]) + 1
    question = new_question(number, args.text.strip())
    case["questions"].append(question)
    case["next_action"] = f"为 {question['id']} 规划知识单元或继续当前问题"
    save_case(root, case)
    generate_review(root, case)
    print(json.dumps({"added": question, "next": case["next_action"]}, ensure_ascii=False, indent=2))
    return 0


def normalize_knowledge_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise IngestionError(f"知识路径越界：{value}")
    normalized = candidate.as_posix()
    if not normalized.startswith("draft/knowledge/") or not normalized.endswith(".md"):
        raise IngestionError("知识路径必须位于 draft/knowledge/ 且使用 .md")
    if Path(normalized).name == "index.md":
        raise IngestionError("知识单元不能以 index.md 作为实质落点")
    return normalized


def plan_unit(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    question = question_by_id(case, args.question_id)
    validate_id(args.unit_id, "unit id", UNIT_ID_RE)
    if any(item["id"] == args.unit_id for item in question["expected_units"]):
        raise IngestionError(f"知识单元已存在：{args.unit_id}")
    if len(question["expected_units"]) >= 3:
        raise IngestionError("一个读者问题最多规划三个规范知识落点")
    path = normalize_knowledge_path(args.path)
    if any(item["path"] == path for item in question["expected_units"]):
        raise IngestionError(f"知识路径已规划：{path}")
    unit = {
        "id": args.unit_id,
        "title": args.title.strip(),
        "kind": args.kind,
        "path": path,
        "status": "planned",
    }
    question["expected_units"].append(unit)
    question["requires_run"] = bool(question["requires_run"] or args.require_run)
    question["updated_at"] = utc_now()
    question["next_action"] = "围绕当前问题取得第一小批直接来源"
    case["next_action"] = f"运行 next 为 {question['id']} 取得直接来源"
    save_case(root, case)
    print(json.dumps({"unit": unit, "requires_run": question["requires_run"], "next": case["next_action"]}, ensure_ascii=False, indent=2))
    return 0


def default_query_terms(text: str) -> list[str]:
    terms = re.findall(r"[A-Za-z_][A-Za-z0-9_.-]{2,}", text)
    for chunk in re.split(r"[，。；：！？、,.;:!?\s/]+", text):
        chunk = chunk.strip()
        if 2 <= len(chunk) <= 12:
            terms.append(chunk)
    return list(dict.fromkeys(terms))[:12]


def read_source_text(case: dict[str, Any], item: dict[str, Any]) -> str:
    if not item.get("text"):
        return ""
    path = resolve_source(case, source_ref(item["source_id"], item["path"]))
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def initial_rank(case: dict[str, Any], manifest: list[dict[str, Any]], terms: list[str]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for item in manifest:
        if not item.get("text"):
            continue
        path_text = item["path"].lower()
        outline = "\n".join([item.get("title") or "", *item.get("headings", [])]).lower()
        content: str | None = None
        score = 0
        reasons: list[str] = []
        for term in terms:
            needle = term.lower().strip()
            if not needle:
                continue
            if needle in path_text:
                score += 12
                reasons.append(f"路径命中 {term}")
            if needle in outline:
                score += 8
                reasons.append(f"标题/章节命中 {term}")
            if content is None:
                content = read_source_text(case, item).lower()
            count = content.count(needle)
            if count:
                score += min(5, count)
                if item["suffix"] in {".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".sql"}:
                    score += 2
                reasons.append(f"正文命中 {term}")
        if score:
            role = candidate_role(source_ref(item["source_id"], item["path"]))
            if role == "test":
                score = max(1, score - 8)
                reasons.append("测试文件降权：用于验证而非首要实现入口")
            if "/archive/" in f"/{item['path'].lower()}/":
                score = max(1, score - 10)
                reasons.append("归档材料降权：只用于历史取舍")
            ranked.append(
                {
                    "ref": source_ref(item["source_id"], item["path"]),
                    "score": score,
                    "reasons": list(dict.fromkeys(reasons))[:6],
                }
            )
    ranked.sort(key=lambda item: (-item["score"], item["ref"]))
    return ranked


def resolve_ts_import(importer: dict[str, Any], module: str, manifest_by_ref: dict[str, dict[str, Any]]) -> str | None:
    source_id = importer["source_id"]
    if module.startswith("@/"):
        tail = module[2:]
        candidate_suffixes = [
            f"/src/{tail}",
            *[f"/src/{tail}{suffix}" for suffix in (".ts", ".tsx", ".js", ".jsx", ".vue")],
            *[f"/src/{tail}/index{suffix}" for suffix in (".ts", ".tsx", ".js", ".jsx", ".vue")],
        ]
        matches = sorted(
            ref
            for ref, item in manifest_by_ref.items()
            if item["source_id"] == source_id
            and any(f"/{item['path']}".endswith(suffix) for suffix in candidate_suffixes)
        )
        return matches[0] if len(matches) == 1 else None
    base = PurePosixPath(importer["path"]).parent / module
    normalized = PurePosixPath(*[part for part in base.parts if part != "."])
    candidates = [
        normalized,
        *[PurePosixPath(str(normalized) + suffix) for suffix in (".ts", ".tsx", ".js", ".jsx", ".vue")],
        *[normalized / ("index" + suffix) for suffix in (".ts", ".tsx", ".js", ".jsx", ".vue")],
    ]
    for candidate in candidates:
        parts: list[str] = []
        valid = True
        for part in candidate.parts:
            if part == "..":
                if not parts:
                    valid = False
                    break
                parts.pop()
            else:
                parts.append(part)
        if valid:
            ref = source_ref(source_id, PurePosixPath(*parts).as_posix())
            if ref in manifest_by_ref:
                return ref
    return None


def resolve_python_import(
    importer: dict[str, Any], module: str, manifest_by_ref: dict[str, dict[str, Any]]
) -> str | None:
    source_id = importer["source_id"]
    if module.startswith("."):
        level = len(module) - len(module.lstrip("."))
        remainder = module[level:]
        parts = list(PurePosixPath(importer["path"]).parent.parts)
        for _ in range(max(0, level - 1)):
            if parts:
                parts.pop()
        if remainder:
            parts.extend(remainder.split("."))
        base = PurePosixPath(*parts).as_posix()
    else:
        base = module.replace(".", "/")
    for suffix in (".py", "/__init__.py"):
        ref = source_ref(source_id, base + suffix)
        if ref in manifest_by_ref:
            return ref
    return None


def direct_import_refs(
    importer: dict[str, Any], text: str, manifest_by_ref: dict[str, dict[str, Any]]
) -> set[str]:
    refs: set[str] = set()
    for match in TS_IMPORT_RE.finditer(text):
        resolved = resolve_ts_import(importer, match.group("module"), manifest_by_ref)
        if resolved:
            refs.add(resolved)
    if importer["suffix"] == ".py":
        modules = [match.group("module") for match in PYTHON_FROM_RE.finditer(text)]
        modules += [match.group("module") for match in PYTHON_IMPORT_RE.finditer(text)]
        for module in modules:
            resolved = resolve_python_import(importer, module, manifest_by_ref)
            if resolved:
                refs.add(resolved)
    return refs


def endpoint_router_refs(
    importer: dict[str, Any], text: str, manifest_by_ref: dict[str, dict[str, Any]], case: dict[str, Any]
) -> set[str]:
    endpoints = [match.group("path") for match in PATH_LITERAL_RE.finditer(text)]
    if not endpoints:
        return set()
    result: set[str] = set()
    for endpoint in endpoints:
        segments = [item.replace("-", "_") for item in endpoint.strip("/").split("/") if item not in {"api"}]
        if len(segments) < 2:
            continue
        decisive = segments[-2:]
        for ref, item in manifest_by_ref.items():
            lowered_path = item["path"].lower()
            if item["source_id"] != importer["source_id"] or "/api/routers/" not in f"/{lowered_path}/":
                continue
            candidate_text = read_source_text(case, item).lower().replace("-", "_")
            if all(segment.lower() in candidate_text for segment in decisive):
                result.add(ref)
    return result


def import_neighbours(case: dict[str, Any], manifest: list[dict[str, Any]], ranked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_ref = {source_ref(item["source_id"], item["path"]): item for item in manifest}
    existing = {item["ref"]: item for item in ranked}
    frontier = [item["ref"] for item in ranked[:10]]
    traversed: set[str] = set()
    for depth in range(3):
        next_frontier: list[str] = []
        bonus = 8 - (depth * 2)
        for importer_ref in frontier:
            if importer_ref in traversed or importer_ref not in by_ref:
                continue
            traversed.add(importer_ref)
            importer = by_ref[importer_ref]
            text = read_source_text(case, importer)
            imported = direct_import_refs(importer, text, by_ref)
            bridged = endpoint_router_refs(importer, text, by_ref, case)
            for ref in sorted(imported | bridged):
                if ref == importer_ref:
                    continue
                relation = "接口路径连接" if ref in bridged else "直接导入"
                reason = f"由 {importer_ref} {relation}"
                if ref in existing:
                    accumulated = int(existing[ref].get("_relation_bonus", 0))
                    delta = min(bonus, max(0, 8 - accumulated))
                    existing[ref]["score"] += delta
                    existing[ref]["_relation_bonus"] = accumulated + delta
                    existing[ref]["reasons"].append(reason)
                else:
                    existing[ref] = {
                        "ref": ref,
                        "score": bonus,
                        "reasons": [reason],
                        "_relation_bonus": bonus,
                    }
                next_frontier.append(ref)
        frontier = next_frontier
    values = list(existing.values())
    for item in values:
        item["reasons"] = list(dict.fromkeys(item["reasons"]))[:6]
        item.pop("_relation_bonus", None)
    values.sort(key=lambda item: (-item["score"], item["ref"]))
    selected, _ = take_diverse_packet(values, MAX_CANDIDATE_POOL)
    for item in selected:
        item.pop("role", None)
    selected.sort(key=lambda item: (-item["score"], item["ref"]))
    return selected


def candidate_role(reference: str) -> str:
    _, relative = split_source_ref(reference)
    lowered = relative.lower()
    name = PurePosixPath(relative).name.lower()
    if ".test." in name or ".spec." in name or "/tests/" in f"/{lowered}/":
        return "test"
    if name in {"agents.md", "readme.md", "handoff.md"} or lowered.startswith("docs/handoff"):
        return "run_contract"
    if lowered.endswith(".vue"):
        return "frontend_view"
    if "/frontend/" in f"/{lowered}/" and "/api/" in f"/{lowered}/":
        return "frontend_api"
    if "/frontend/" in f"/{lowered}/" or lowered.endswith((".ts", ".tsx", ".js", ".jsx")):
        return "frontend_logic"
    if lowered.startswith(("migrations/", "seeds/")) or lowered.endswith(".sql"):
        return "data_schema"
    if "repository" in lowered or "/database/" in f"/{lowered}/" or "connector" in lowered:
        return "data_access"
    if "/api/" in f"/{lowered}/":
        return "api"
    if lowered.endswith((".py", ".go", ".java")):
        return "backend_logic"
    if lowered.endswith((".md", ".txt", ".rst")):
        return "document"
    return "other"


def take_diverse_packet(queue: list[dict[str, Any]], limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if len(queue) <= limit:
        return queue[:], []
    chosen: list[dict[str, Any]] = []
    chosen_refs: set[str] = set()

    def choose(item: dict[str, Any]) -> None:
        if item["ref"] in chosen_refs or len(chosen) >= limit:
            return
        copy = {**item, "role": candidate_role(item["ref"])}
        chosen.append(copy)
        chosen_refs.add(item["ref"])

    choose(queue[0])
    role_order = (
        "frontend_view", "frontend_logic", "frontend_api", "api", "backend_logic",
        "data_access", "data_schema", "run_contract",
    )
    for role in role_order:
        candidate = next((item for item in queue if candidate_role(item["ref"]) == role), None)
        if candidate is not None:
            choose(candidate)
    for item in queue:
        choose(item)
    remaining = [item for item in queue if item["ref"] not in chosen_refs]
    return chosen, remaining


def survey_materials(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    ensure_complete(case)
    manifest = read_manifest(root)
    print(
        json.dumps(
            {
                "case_id": case["id"],
                "mode": case["mode"],
                "source_collections": [public_source_identity(item) for item in case["sources"]],
                "group_count": len(case["material_groups"]),
                "groups": [
                    public_material_group(case, manifest, item, members=args.members)
                    for item in case["material_groups"]
                ],
                "boundary": (
                    "分组只来自路径、完全重复、文档链接和代码导入；"
                    "title/headings 只作为阅读导航，不代表现状、历史或目标身份"
                ),
                "next": case["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def next_complete_item(root: Path, case: dict[str, Any]) -> int:
    refresh_complete_cursor(case)
    save_case(root, case)
    cursor = case["cursor"]
    if cursor["item_type"] == "material_group":
        manifest = read_manifest(root)
        group = group_by_id(case, cursor["item_id"])
        payload = {
            "stage": case["stage"],
            "current": public_material_group(case, manifest, group, members=True),
            "reading_rule": (
                "先用路径、标题和章节建立本单元概要；若与用户目标相关，完整读取会改变结论的成员。"
                "每项发现只表达一个可独立复用的结论，并保留关键细节与章节、表、符号或配置键定位；"
                "一个来源有多个独立结论时分别登记。不要由文件名推断现实身份"
            ),
            "next": case["next_action"],
        }
    elif cursor["item_type"] == "knowledge_topic":
        topic = topic_by_id(case, cursor["item_id"])
        findings = [finding_by_id(case, item) for item in topic["finding_ids"]]
        payload = {
            "stage": case["stage"],
            "current": topic,
            "findings": findings,
            "writing_rule": (
                "逐项比较每条直接材料结论、关键细节和边界，把它们充分内化到唯一规范落点，"
                "并同步形成计划中的产品视图；引用负责追溯，不能代替正文。"
                "结束主题时用 record-topic 的 --section 把每项发现定位到正文真实章节"
            ),
            "next": case["next_action"],
        }
    elif case["stage"] == "planning":
        payload = {
            "stage": case["stage"],
            "current": {
                "material_groups": [
                    {
                        "id": item["id"],
                        "label": item["label"],
                        "status": item["status"],
                        "summary": item["summary"],
                        "finding_ids": item["finding_ids"],
                    }
                    for item in case["material_groups"]
                ],
                "findings": case["findings"],
                "planned_topics": case["topics"],
                "last_review_issues": case["plan_review"].get("issues", []),
            },
            "planning_rule": (
                "先让每项读后发现进入一个长期可维护主题，再从读者心智模型、材料覆盖和唯一规范落点"
                "做第二遍目录复核；不要按来源目录直接建页"
            ),
            "next": case["next_action"],
        }
    else:
        payload = {
            "stage": case["stage"],
            "current": None,
            "next": case["next_action"],
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def add_finding(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    ensure_complete(case)
    validate_id(args.finding_id, "finding id", UNIT_ID_RE)
    group = group_by_id(case, args.group_id)
    sources = list(dict.fromkeys(args.source))
    if not sources:
        raise IngestionError("读后发现至少需要一项精确 --source")
    details = list(dict.fromkeys(item.strip() for item in args.detail if item.strip()))
    if not details:
        raise IngestionError("读后发现至少需要一项决定理解或行动的 --detail")
    anchors = list(dict.fromkeys(item.strip() for item in args.anchor if item.strip()))
    if not anchors:
        raise IngestionError("读后发现至少需要一项 <source-ref>#<章节或符号> 形式的 --anchor")
    unknown_sources = [item for item in sources if item not in group["members"]]
    if unknown_sources:
        raise IngestionError("读后发现来源不属于该材料组：" + ", ".join(unknown_sources))
    anchor_sources: list[str] = []
    for anchor in anchors:
        ref, separator, locator = anchor.partition("#")
        if not separator or not ref.strip() or not locator.strip():
            raise IngestionError("--anchor 必须使用 <source-ref>#<章节、表、符号或配置键>")
        anchor_sources.append(ref.strip())
    unknown_anchor_sources = [item for item in anchor_sources if item not in sources]
    if unknown_anchor_sources:
        raise IngestionError("定位引用必须先登记为本发现来源：" + ", ".join(unknown_anchor_sources))
    for ref in sources:
        path = resolve_source(case, ref)
        manifest_item = next(item for item in read_manifest(root) if manifest_ref(item) == ref)
        if digest_bytes(path.read_bytes()) != manifest_item["sha256"]:
            raise IngestionError(f"来源自摄入案开始后发生变化：{ref}")
    finding = {
        "id": args.finding_id,
        "group_id": args.group_id,
        "content": args.content.strip(),
        "details": details,
        "reality": args.reality,
        "sources": sources,
        "anchors": anchors,
        "scope": args.scope.strip(),
        "limits": [item.strip() for item in args.limit if item.strip()],
        "candidate_topics": [item.strip() for item in args.topic if item.strip()],
    }
    existing = next((item for item in case["findings"] if item["id"] == args.finding_id), None)
    if existing:
        comparable = {key: existing[key] for key in finding}
        if comparable != finding:
            raise IngestionError(f"读后发现 {args.finding_id} 已存在且内容不同")
        print(json.dumps({"finding": existing, "already_recorded": True, "next": case["next_action"]}, ensure_ascii=False, indent=2))
        return 0
    if group["status"] not in {"unreviewed", "partial"}:
        raise IngestionError(f"材料组 {group['id']} 已结束，不能追加新的读后发现")
    finding["recorded_at"] = utc_now()
    case["findings"].append(finding)
    group["finding_ids"].append(finding["id"])
    save_case(root, case)
    print(json.dumps({"finding": finding, "already_recorded": False, "next": f"登记材料组 {group['id']} 的审视结果"}, ensure_ascii=False, indent=2))
    return 0


def record_material(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    ensure_complete(case)
    group = group_by_id(case, args.group_id)
    if group["status"] == args.status and group["summary"] == args.summary.strip():
        print(json.dumps({"group_id": group["id"], "status": group["status"], "already_recorded": True, "next": case["next_action"]}, ensure_ascii=False, indent=2))
        return 0
    if args.status == "reviewed" and not group["finding_ids"]:
        raise IngestionError("相关材料组标为 reviewed 前必须先形成至少一个读后发现")
    if args.status == "irrelevant" and group["finding_ids"]:
        raise IngestionError("已有读后发现的材料组不能标为 irrelevant")
    if group["status"] not in {"unreviewed", "partial"}:
        raise IngestionError(f"材料组 {group['id']} 已登记且本次内容不同")
    current = case.get("cursor", {})
    if current.get("item_type") != "material_group" or current.get("item_id") != group["id"]:
        raise IngestionError(f"当前应处理 {current.get('item_id') or '无'}，不能跳到 {group['id']}")
    group["status"] = args.status
    group["summary"] = args.summary.strip()
    group["updated_at"] = utc_now()
    refresh_complete_cursor(case)
    save_case(root, case)
    print(json.dumps({"group_id": group["id"], "status": group["status"], "finding_ids": group["finding_ids"], "already_recorded": False, "stage": case["stage"], "next": case["next_action"]}, ensure_ascii=False, indent=2))
    return 0


def reopen_material(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    ensure_complete(case)
    if case["stage"] != "planning":
        raise IngestionError("只在知识目录规划阶段重新打开已经审视的材料组")
    group = group_by_id(case, args.group_id)
    if group["status"] in {"unreviewed", "partial"}:
        if group["status"] == "partial" and group.get("reopen_reason") == args.reason.strip():
            print(json.dumps({"group_id": group["id"], "already_reopened": True, "next": case["next_action"]}, ensure_ascii=False, indent=2))
            return 0
        raise IngestionError(f"材料组 {group['id']} 尚未结束，不需要重新打开")
    group["status"] = "partial"
    group["reopen_reason"] = args.reason.strip()
    group["updated_at"] = utc_now()
    case["plan_review"] = {"passed": False, "lenses": {}, "not_applicable": {}, "issues": []}
    refresh_complete_cursor(case)
    save_case(root, case)
    print(json.dumps({"group_id": group["id"], "already_reopened": False, "stage": case["stage"], "next": case["next_action"]}, ensure_ascii=False, indent=2))
    return 0


def add_topic(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    ensure_complete(case)
    if case["stage"] != "planning":
        raise IngestionError("只有材料发现完成后才能规划知识主题")
    validate_id(args.topic_id, "topic id", UNIT_ID_RE)
    path = normalize_knowledge_path(args.path)
    finding_ids = list(dict.fromkeys(args.finding))
    if not finding_ids:
        raise IngestionError("知识主题至少关联一个读后发现")
    for finding_id in finding_ids:
        finding_by_id(case, finding_id)
    view_paths = [normalize_knowledge_path(item) for item in args.view]
    topic = {
        "id": args.topic_id,
        "title": args.title.strip(),
        "purpose": args.purpose.strip(),
        "action": args.action,
        "path": path,
        "finding_ids": finding_ids,
        "view_paths": view_paths,
        "status": "planned",
    }
    existing = next((item for item in case["topics"] if item["id"] == args.topic_id), None)
    if existing:
        if existing == topic:
            print(json.dumps({"topic": existing, "already_recorded": True, "next": case["next_action"]}, ensure_ascii=False, indent=2))
            return 0
        if existing["status"] != "planned" or case["plan_review"].get("passed"):
            raise IngestionError(f"知识主题 {args.topic_id} 已进入写作，不能修改计划")
        if any(item["id"] != args.topic_id and item["path"] == path for item in case["topics"]):
            raise IngestionError(f"规范知识落点已由其他主题使用：{path}")
        existing.clear()
        existing.update(topic)
        case["plan_review"] = {"passed": False, "lenses": {}, "not_applicable": {}, "issues": []}
        save_case(root, case)
        print(json.dumps({"topic": existing, "already_recorded": False, "updated": True, "next": "继续补全目录；完成后运行 plan-review"}, ensure_ascii=False, indent=2))
        return 0
    if any(item["path"] == path for item in case["topics"]):
        raise IngestionError(f"规范知识落点已由其他主题使用：{path}")
    case["topics"].append(topic)
    save_case(root, case)
    print(json.dumps({"topic": topic, "already_recorded": False, "next": "继续补全目录；完成后运行 plan-review"}, ensure_ascii=False, indent=2))
    return 0


def parse_key_values(values: list[str], label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key, separator, content = value.partition("=")
        if not separator or not key.strip() or not content.strip():
            raise IngestionError(f"{label} 必须使用 <name>=<value>：{value}")
        key = key.strip()
        if key in result:
            raise IngestionError(f"{label} 重复：{key}")
        result[key] = content.strip()
    return result


def review_knowledge_plan(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    ensure_complete(case)
    if case["stage"] != "planning":
        raise IngestionError("当前尚未进入知识目录复核阶段")
    lens_values = parse_key_values(args.lens, "--lens")
    not_applicable = parse_key_values(args.not_applicable, "--not-applicable")
    unknown_lenses = (set(lens_values) | set(not_applicable)) - PLAN_LENSES
    if unknown_lenses:
        raise IngestionError("未知复核角度：" + ", ".join(sorted(unknown_lenses)))
    overlap = set(lens_values) & set(not_applicable)
    if overlap:
        raise IngestionError("同一复核角度不能同时映射和排除：" + ", ".join(sorted(overlap)))
    lens_topics = {
        lens: [item.strip() for item in value.split(",") if item.strip()]
        for lens, value in lens_values.items()
    }
    topic_ids = {item["id"] for item in case["topics"]}
    errors: list[str] = []
    if not case["topics"]:
        errors.append("尚未规划任何知识主题")
    unfinished = [item["id"] for item in case["material_groups"] if item["status"] in {"unreviewed", "partial"}]
    if unfinished:
        errors.append("以下材料组尚未完成审视：" + ", ".join(unfinished))
    empty_relevant = [item["id"] for item in case["material_groups"] if item["status"] == "reviewed" and not item["finding_ids"]]
    if empty_relevant:
        errors.append("以下相关材料组没有读后发现：" + ", ".join(empty_relevant))
    mapped_findings = {finding_id for topic in case["topics"] for finding_id in topic["finding_ids"]}
    missing_findings = [item["id"] for item in case["findings"] if item["id"] not in mapped_findings]
    if missing_findings:
        errors.append("以下读后发现尚未进入任何知识主题：" + ", ".join(missing_findings))
    finding_owners: dict[str, list[str]] = defaultdict(list)
    for topic in case["topics"]:
        if topic["action"] == "view":
            continue
        for finding_id in topic["finding_ids"]:
            finding_owners[finding_id].append(topic["id"])
    duplicate_findings = {
        finding_id: owners
        for finding_id, owners in finding_owners.items()
        if len(owners) > 1
    }
    if duplicate_findings:
        errors.append(
            "以下读后发现被多个规范主题重复维护："
            + "；".join(
                f"{finding_id} -> {', '.join(owners)}"
                for finding_id, owners in sorted(duplicate_findings.items())
            )
        )
    missing_lenses = PLAN_LENSES - set(lens_topics) - set(not_applicable)
    if missing_lenses:
        errors.append("以下读者理解角度尚未映射或说明不适用：" + ", ".join(sorted(missing_lenses)))
    for lens, values in lens_topics.items():
        unknown_topics = [item for item in values if item not in topic_ids]
        if unknown_topics:
            errors.append(f"复核角度 {lens} 引用了未知主题：" + ", ".join(unknown_topics))
        if not values:
            errors.append(f"复核角度 {lens} 没有主题")
    report = {
        "passed": not errors,
        "lenses": lens_topics,
        "not_applicable": not_applicable,
        "issues": errors,
        "reviewed_at": utc_now(),
    }
    case["plan_review"] = report
    if report["passed"]:
        refresh_complete_cursor(case)
    else:
        case["next_action"] = "修正知识目录或复核映射后重新运行 plan-review"
    save_case(root, case)
    print(json.dumps({"plan_review": report, "stage": case["stage"], "next": case["next_action"]}, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


def record_topic(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    ensure_complete(case)
    topic = topic_by_id(case, args.topic_id)
    if topic["status"] == "ready":
        print(json.dumps({"topic_id": topic["id"], "already_recorded": True, "stage": case["stage"], "next": case["next_action"]}, ensure_ascii=False, indent=2))
        return 0
    current = case.get("cursor", {})
    if current.get("item_type") != "knowledge_topic" or current.get("item_id") != topic["id"]:
        raise IngestionError(f"当前应形成 {current.get('item_id') or '无'}，不能跳到 {topic['id']}")
    path = root / topic["path"]
    if not path.is_file():
        raise IngestionError(f"计划的规范知识尚未形成：{topic['path']}")
    finding_sections = parse_key_values(args.section, "--section")
    assigned_findings = set(topic["finding_ids"])
    unknown_findings = set(finding_sections) - assigned_findings
    if unknown_findings:
        raise IngestionError(
            "章节定位包含不属于当前主题的读后发现：" + ", ".join(sorted(unknown_findings))
        )
    missing_findings = assigned_findings - set(finding_sections)
    if missing_findings:
        raise IngestionError(
            "以下读后发现尚未定位到正文真实章节：" + ", ".join(sorted(missing_findings))
        )
    document_headings = {
        re.sub(r"[`*_~]", "", heading).strip().casefold()
        for heading in HEADING_RE.findall(path.read_text(encoding="utf-8"))
    }
    missing_headings = sorted(
        {
            heading
            for heading in finding_sections.values()
            if re.sub(r"[`*_~]", "", heading).strip().casefold() not in document_headings
        }
    )
    if missing_headings:
        raise IngestionError("以下章节定位在正文中不存在：" + "；".join(missing_headings))
    for view_path in topic["view_paths"]:
        view = root / view_path
        if not view.is_file():
            raise IngestionError(f"计划的产品视图尚未形成：{view_path}")
        if path.resolve() not in markdown_link_targets(view):
            raise IngestionError(f"计划产品视图 {view_path} 尚未链接规范知识：{topic['path']}")
    topic["status"] = "ready"
    topic["finding_sections"] = finding_sections
    topic["recorded_at"] = utc_now()
    refresh_complete_cursor(case)
    save_case(root, case)
    generate_review(root, case)
    print(json.dumps({"topic_id": topic["id"], "already_recorded": False, "stage": case["stage"], "next": case["next_action"]}, ensure_ascii=False, indent=2))
    return 0


def next_sources(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    if case.get("mode", "focused") == "complete":
        if args.question_id:
            raise IngestionError("宽范围完整整理的 next 不接收 question id")
        if args.query:
            raise IngestionError("宽范围完整整理按当前材料组推进，next 不接收 --query")
        return next_complete_item(root, case)
    if not args.question_id:
        raise IngestionError("聚焦整理的 next 需要 question id")
    question = question_by_id(case, args.question_id)
    if question["active_packet"]:
        raise IngestionError("当前小批来源尚未 record；先写知识并登记结果")
    terms = [item.strip() for item in args.query if item.strip()]
    if terms:
        manifest = read_manifest(root)
        ranked = import_neighbours(case, manifest, initial_rank(case, manifest, terms))
        seen = {item["ref"] for item in question["evidence"]}
        for packet in question["dismissed_packets"]:
            seen.update(packet.get("refs", []))
        question["candidate_queue"] = [item for item in ranked if item["ref"] not in seen]
        question["query_terms"] = terms
        question["candidate_closure"] = None
    elif not question["candidate_queue"]:
        terms = default_query_terms(question["text"])
        manifest = read_manifest(root)
        question["candidate_queue"] = import_neighbours(
            case, manifest, initial_rank(case, manifest, terms)
        )
        question["query_terms"] = terms
        question["candidate_closure"] = None
    limit = args.limit
    packet, remaining = take_diverse_packet(question["candidate_queue"], limit)
    question["candidate_queue"] = remaining
    question["active_packet"] = packet
    question["updated_at"] = utc_now()
    if packet:
        question["next_action"] = "只读取当前小批直接来源，立即更新规范知识，再运行 record"
    else:
        question["next_action"] = "当前查询没有库内候选；形成可靠局部或说明外部缺失"
    case["next_action"] = f"处理 {question['id']}：{question['next_action']}"
    save_case(root, case)
    sources = source_map(case)
    output_packet = []
    for item in packet:
        source_id, relative = split_source_ref(item["ref"])
        output_packet.append(
            {
                **item,
                "absolute_path": str(Path(sources[source_id]["root"]) / relative),
            }
        )
    print(
        json.dumps(
            {
                "question": {"id": question["id"], "text": question["text"]},
                "query_terms": question["query_terms"],
                "packet": output_packet,
                "remaining_relevant_candidates": len(question["candidate_queue"]),
                "reading_rule": "只读取本 packet；读完立即更新规范知识并 record，不维护逐文件覆盖表",
                "next": question["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def record_result(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    question = question_by_id(case, args.question_id)
    if args.status not in QUESTION_STATES - {"working"}:
        raise IngestionError(f"无效问题状态：{args.status}")
    active = {item["ref"]: item for item in question["active_packet"]}
    used = list(dict.fromkeys(args.source))
    used_runs = list(dict.fromkeys(args.run_id))
    runs_by_id = {item["id"]: item for item in case.get("runs", [])}
    unknown_runs = [item for item in used_runs if item not in runs_by_id]
    if unknown_runs:
        raise IngestionError("以下 --run-id 不属于本摄入案：" + ", ".join(unknown_runs))
    wrong_question_runs = [
        item for item in used_runs
        if runs_by_id[item].get("question_id") != question["id"]
    ]
    if wrong_question_runs:
        raise IngestionError("以下运行证据不属于当前问题：" + ", ".join(wrong_question_runs))
    unknown = [item for item in used if item not in active]
    if unknown:
        available = ", ".join(active) or "（当前没有活动小批，请先 next）"
        raise IngestionError(
            "以下 --source 不在当前小批，不能登记："
            + ", ".join(unknown)
            + "；当前可登记来源："
            + available
        )
    unused = [item for item in active if item not in used]
    if unused and not args.dismiss_unused:
        raise IngestionError("当前小批仍有未使用来源；提供 --dismiss-unused 说明整批剩余项为何不改变答案")
    if not used and not used_runs and args.status in {"answered", "partial", "conflict"}:
        raise IngestionError(f"{args.status} 至少需要一项当前直接来源或运行证据")
    if args.status == "answered" and args.missing:
        raise IngestionError("answered 不应同时登记 missing；应改为 partial")
    if args.status in {"partial", "external_missing", "conflict"} and not args.missing:
        raise IngestionError(f"{args.status} 必须说明缺失或冲突内容")
    knowledge_paths = [normalize_knowledge_path(item) for item in args.knowledge]
    if used_runs and not knowledge_paths:
        raise IngestionError("登记运行证据时必须用 --knowledge 指明已经写回的规范知识")
    for path in knowledge_paths:
        if not (root / path).is_file():
            raise IngestionError(f"规范知识尚未形成：{root / path}")
    for ref in used:
        item = active[ref]
        path = resolve_source(case, ref)
        actual = digest_bytes(path.read_bytes())
        manifest_item = next(
            entry for entry in read_manifest(root)
            if source_ref(entry["source_id"], entry["path"]) == ref
        )
        if actual != manifest_item["sha256"]:
            raise IngestionError(f"来源自摄入案开始后发生变化：{ref}")
        question["evidence"].append(
            {"ref": ref, "sha256": actual, "used_for": args.summary.strip(), "recorded_at": utc_now()}
        )
    if unused:
        question["dismissed_packets"].append(
            {"refs": unused, "reason": args.dismiss_unused.strip(), "recorded_at": utc_now()}
        )
    question["active_packet"] = []
    if args.close_candidates:
        remaining = [item["ref"] for item in question["candidate_queue"]]
        question["candidate_closure"] = {
            "reason": args.close_candidates.strip(),
            "remaining_refs": remaining,
            "recorded_at": utc_now(),
        }
        question["candidate_queue"] = []
    if args.status in {"answered", "external_missing"} and question["candidate_queue"]:
        raise IngestionError(
            f"{args.status} 前仍有 {len(question['candidate_queue'])} 项相关候选；继续 next 或用 --close-candidates 说明停止理由"
        )
    if args.status == "external_missing" and used:
        # Direct evidence may establish the reliable boundary before the external gap.
        pass
    failed_runs = [
        item for item in used_runs
        if not runs_by_id[item].get("evidence_complete", True)
        or runs_by_id[item].get("exit_code") != runs_by_id[item].get("expected_exit")
    ]
    if args.status == "answered" and failed_runs:
        raise IngestionError("失败或证据不完整的运行不能把问题登记为 answered：" + ", ".join(failed_runs))
    question["status"] = args.status
    question["summary"] = args.summary.strip()
    question["missing"] = [item.strip() for item in args.missing if item.strip()]
    question["knowledge_paths"] = list(dict.fromkeys([*question["knowledge_paths"], *knowledge_paths]))
    question.setdefault("integrated_run_ids", [])
    question["integrated_run_ids"] = list(
        dict.fromkeys([*question["integrated_run_ids"], *used_runs])
    )
    pending_runs = question.setdefault("pending_run_ids", [])
    question["pending_run_ids"] = [item for item in pending_runs if item not in used_runs]
    question["next_action"] = args.next_action.strip() if args.next_action else (
        "运行 check-unit 核对知识、候选来源、产品视图和运行证据"
        if args.status in {"answered", "external_missing"}
        else "按明确缺口取得下一小批来源或请求责任方补充"
    )
    question["updated_at"] = utc_now()
    case["next_action"] = f"处理 {question['id']}：{question['next_action']}"
    save_case(root, case)
    generate_review(root, case)
    print(
        json.dumps(
            {
                "question_id": question["id"],
                "status": question["status"],
                "used_sources": used,
                "integrated_run_ids": used_runs,
                "pending_run_ids": question["pending_run_ids"],
                "dismissed_as_packet": unused,
                "remaining_relevant_candidates": len(question["candidate_queue"]),
                "knowledge_paths": question["knowledge_paths"],
                "next": question["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def stop_search(args: argparse.Namespace) -> int:
    """Close the remaining candidate queue after useful knowledge is recorded."""
    root, case = load_case(args.cases_root, args.case_id)
    question = question_by_id(case, args.question_id)
    if question["active_packet"]:
        raise IngestionError("当前小批来源尚未 record；先写入知识并登记本批结果")
    if question["status"] == "working" or not question["knowledge_paths"]:
        raise IngestionError("停止继续取源前，必须先 record 已形成的规范知识和当前缺口")
    remaining = [item["ref"] for item in question["candidate_queue"]]
    question["candidate_closure"] = {
        "reason": args.reason.strip(),
        "remaining_refs": remaining,
        "recorded_at": utc_now(),
    }
    question["candidate_queue"] = []
    question["next_action"] = args.next_action.strip() if args.next_action else (
        "运行 check-unit 核对知识、产品视图、直接依据和运行证据"
    )
    question["updated_at"] = utc_now()
    case["next_action"] = f"处理 {question['id']}：{question['next_action']}"
    save_case(root, case)
    generate_review(root, case)
    print(
        json.dumps(
            {
                "question_id": question["id"],
                "stopped": True,
                "closed_candidate_count": len(remaining),
                "reason": question["candidate_closure"]["reason"],
                "next": question["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def markdown_link_targets(path: Path) -> set[Path]:
    targets: set[Path] = set()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return targets
    for raw in LINK_RE.findall(text):
        target = raw.split("#", 1)[0].split("?", 1)[0]
        if not target or "://" in target or target.startswith("#"):
            continue
        targets.add((path.parent / target).resolve())
    return targets


def view_targets(root: Path) -> set[Path]:
    targets: set[Path] = set()
    views = root / "draft" / "knowledge" / "views"
    if not views.is_dir():
        return targets
    for path in views.rglob("*.md"):
        targets.update(markdown_link_targets(path))
    return targets


def check_question(root: Path, case: dict[str, Any], question: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not question["expected_units"]:
        errors.append("尚未规划任何知识单元")
    expected_paths = [item["path"] for item in question["expected_units"]]
    if len(expected_paths) > 3:
        errors.append("一个问题不能依赖超过三篇规范知识页")
    linked = view_targets(root)
    for unit in question["expected_units"]:
        path = root / unit["path"]
        if not path.is_file():
            errors.append(f"知识单元尚未形成：{unit['path']}")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 400:
            errors.append(f"知识单元内容过薄：{unit['path']}")
        if PLACEHOLDER_RE.search(text):
            errors.append(f"知识单元仍含模板占位符：{unit['path']}")
        if path.resolve() not in linked:
            errors.append(f"产品视图尚未链接知识单元：{unit['path']}")
        if question["status"] == "answered":
            for marker in STALE_MARKERS:
                lines = [index for index, line in enumerate(text.splitlines(), 1) if marker in line]
                if lines:
                    errors.append(
                        f"已回答问题的知识页仍含 {marker}：{unit['path']} lines {lines[:5]}"
                    )
    missing_planned = sorted(set(expected_paths) - set(question["knowledge_paths"]))
    if missing_planned:
        errors.append("record 尚未登记计划知识单元：" + ", ".join(missing_planned))
    if question["active_packet"]:
        errors.append("当前小批来源尚未 record")
    if question["candidate_queue"]:
        errors.append(f"仍有 {len(question['candidate_queue'])} 项相关候选未处理或未说明停止理由")
    if question["status"] == "working":
        errors.append("问题仍处于处理中")
    if question["status"] in {"answered", "partial", "conflict"} and not question["evidence"]:
        errors.append("问题没有直接来源证据")
    if question["status"] in {"partial", "external_missing", "conflict"}:
        if not question["missing"]:
            errors.append("未说明缺失或冲突内容")
        if not question["next_action"]:
            errors.append("未说明下一补充动作")
    pending_runs = question.get("pending_run_ids", [])
    if pending_runs:
        errors.append(
            "以下运行结果尚未写回规范知识并用 record --run-id 登记："
            + ", ".join(pending_runs)
        )
    if question["requires_run"]:
        passed_runs = [
            item for item in case.get("runs", [])
            if item.get("id") in question["run_ids"]
            and item.get("exit_code") == item.get("expected_exit")
            and item.get("evidence_complete", True)
        ]
        if not passed_runs:
            errors.append("本问题要求真实运行，但尚无通过的隔离运行证据")
    report = validate_bundle(
        root / "draft" / "knowledge", root / "draft" / "config" / "knowledge-domains.yaml"
    )
    errors.extend(f"知识结构：{item}" for item in report.errors)
    if any(
        "domain[" in item or "domain map" in item or "directory is not declared" in item
        for item in report.errors
    ):
        errors.append(
            "知识结构：领域地图每项必须包含 id/title/parent/scope/excludes；"
            "可直接套用 .agents/skills/ingest-knowledge/assets/domain-overview.md 中的最小示例"
        )
    warnings.extend(f"知识结构：{item}" for item in report.warnings)
    return {
        "question_id": question["id"],
        "ready": not errors,
        "status": question["status"],
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def check_unit(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    question = question_by_id(case, args.question_id)
    report = check_question(root, case, question)
    if report["ready"]:
        for unit in question["expected_units"]:
            unit["status"] = "ready"
        question["next_action"] = "进入人工审查，或继续下一个读者问题"
        case["next_action"] = question["next_action"]
        save_case(root, case)
        generate_review(root, case)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"knowledge-unit-check: {'PASS' if report['ready'] else 'FAIL'}")
        for error in report["errors"]:
            print(f"- ERROR: {error}")
        for warning in report["warnings"]:
            print(f"- WARNING: {warning}")
    return 0 if report["ready"] else 1


def safe_mount(
    run_root: Path, source_root: Path, value: str, *, copy_input: bool
) -> dict[str, Any]:
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise IngestionError(f"--mount 必须是来源根内相对路径：{value}")
    source = (source_root / candidate.as_posix()).resolve()
    try:
        source.relative_to(source_root)
    except ValueError as exc:
        raise IngestionError(f"--mount 越界：{value}") from exc
    if not source.exists():
        raise IngestionError(f"--mount 来源不存在：{source}")
    target = run_root / candidate.as_posix()
    if target.exists() or target.is_symlink():
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    if copy_input:
        if source.is_dir():
            shutil.copytree(source, target, symlinks=True)
        else:
            shutil.copy2(source, target, follow_symlinks=False)
        mode = "private_copy"
    else:
        target.symlink_to(source, target_is_directory=source.is_dir())
        mode = "live_reference"
    return {
        "path": candidate.as_posix(),
        "mode": mode,
        "source": str(source),
        "run_path": str(target.resolve() if copy_input else target.absolute()),
    }


def run_project(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    question = question_by_id(case, args.question_id)
    source = source_map(case).get(args.source_id)
    if source is None:
        raise IngestionError(f"来源不存在：{args.source_id}")
    git = source.get("git")
    if not isinstance(git, dict):
        raise IngestionError("隔离运行首版只支持 Git 来源")
    source_root = Path(source["root"]).resolve()
    current = git_identity(source_root)
    if current is None or current["commit"] != git["commit"] or current["dirty"]:
        raise IngestionError("来源 Git 状态已变化或非干净状态；拒绝在不可重放版本上运行")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    evidence_dir = root / "evidence" / "runs" / run_id
    evidence_dir.mkdir(parents=True, exist_ok=False)
    git_root = Path(git["root"])
    scope = git["scope"]
    temporary = Path(tempfile.mkdtemp(prefix=f"omni-ingestion-{args.case_id}-"))
    worktree = temporary / "source"
    result: subprocess.CompletedProcess[str] | None = None
    try:
        added = run_git(git_root, "worktree", "add", "--detach", str(worktree), git["commit"])
        if added.returncode != 0:
            raise IngestionError(f"无法创建隔离 worktree：{added.stderr.strip()}")
        run_root = worktree if scope == "." else worktree / scope
        if not run_root.is_dir():
            raise IngestionError(f"隔离 worktree 中不存在来源范围：{run_root}")
        duplicates = sorted(set(args.mount) & set(args.copy_mount))
        if duplicates:
            raise IngestionError(
                "同一路径不能同时使用 --mount 和 --copy-mount：" + ", ".join(duplicates)
            )
        runtime_inputs: list[dict[str, Any]] = []
        for mount in args.mount:
            runtime_inputs.append(
                safe_mount(run_root, source_root, mount, copy_input=False)
            )
        for mount in args.copy_mount:
            runtime_inputs.append(
                safe_mount(run_root, source_root, mount, copy_input=True)
            )
        temp_runtime = temporary / "runtime"
        temp_runtime.mkdir()
        environment = os.environ.copy()
        environment.update(
            {
                "OMNI_SOURCE_ROOT": str(source_root),
                "OMNI_RUN_ROOT": str(run_root),
                "TMPDIR": str(temp_runtime),
                "XDG_CACHE_HOME": str(temp_runtime / "cache"),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        mount_environment: dict[str, str] = {}
        for index, runtime_input in enumerate(runtime_inputs, start=1):
            variable = f"OMNI_MOUNT_{index}"
            environment[variable] = runtime_input["run_path"]
            runtime_input["environment_variable"] = variable
            mount_environment[runtime_input["path"]] = runtime_input["run_path"]
        environment["OMNI_MOUNTS_JSON"] = json.dumps(
            mount_environment, ensure_ascii=False, sort_keys=True
        )
        command_file: str | None = None
        command_file_sha256: str | None = None
        if args.command_file:
            relative_command = PurePosixPath(args.command_file)
            if (
                relative_command.is_absolute()
                or ".." in relative_command.parts
                or relative_command.suffix != ".sh"
                or relative_command.parts[:2] != ("evidence", "recipes")
            ):
                raise IngestionError(
                    "--command-file 必须是摄入案 evidence/recipes/ 下的相对 .sh 文件"
                )
            source_command = (root / relative_command.as_posix()).resolve()
            try:
                source_command.relative_to(root.resolve())
            except ValueError as exc:
                raise IngestionError("--command-file 路径越界") from exc
            if not source_command.is_file() or source_command.is_symlink():
                raise IngestionError(f"--command-file 不存在或不是普通文件：{source_command}")
            command_copy = evidence_dir / "command.sh"
            shutil.copy2(source_command, command_copy)
            command_file = relative_command.as_posix()
            command_file_sha256 = digest_bytes(command_copy.read_bytes())
            command_argv = ["bash", "-euo", "pipefail", str(command_copy)]
            recorded_command = f"bash -euo pipefail {command_file}"
        else:
            command_argv = ["bash", "-lc", args.command]
            recorded_command = args.command
        result = subprocess.run(
            command_argv,
            cwd=run_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=args.timeout,
            env=environment,
        )
        runtime_scope = "git_only"
        if runtime_inputs or args.runtime_note:
            runtime_scope = (
                "environment_bound"
                if any(item["mode"] == "live_reference" for item in runtime_inputs)
                or args.runtime_note
                else "private_snapshot"
            )
        atomic_write_text(evidence_dir / "stdout.log", result.stdout)
        atomic_write_text(evidence_dir / "stderr.log", result.stderr)
        artifacts: list[str] = []
        artifact_errors: list[str] = []
        artifact_dir = evidence_dir / "artifacts"
        for raw in args.artifact:
            relative = PurePosixPath(raw)
            if relative.is_absolute() or ".." in relative.parts:
                raise IngestionError(f"artifact 路径越界：{raw}")
            candidate = (run_root / relative.as_posix()).resolve()
            try:
                candidate.relative_to(run_root.resolve())
            except ValueError as exc:
                raise IngestionError(f"artifact 路径越界：{raw}") from exc
            if not candidate.is_file():
                artifact_errors.append(f"声明的 artifact 不存在：{candidate}")
                continue
            target = artifact_dir / relative.as_posix()
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, target)
            artifacts.append(str(target.relative_to(root)))
        evidence_complete = not artifact_errors
        run_record = {
            "id": run_id,
            "question_id": question["id"],
            "source_id": args.source_id,
            "source_commit": git["commit"],
            "kind": args.kind,
            "purpose": args.purpose.strip(),
            "command": recorded_command,
            "command_file": command_file,
            "command_file_sha256": command_file_sha256,
            "expected_exit": args.expect_exit,
            "exit_code": result.returncode,
            "started_and_completed_at": utc_now(),
            "artifacts": artifacts,
            "artifact_errors": artifact_errors,
            "evidence_complete": evidence_complete,
            "stdout": str((evidence_dir / "stdout.log").relative_to(root)),
            "stderr": str((evidence_dir / "stderr.log").relative_to(root)),
            "isolation": "temporary_git_worktree",
            "mounts": args.mount,
            "copy_mounts": args.copy_mount,
            "runtime_scope": runtime_scope,
            "runtime_notes": args.runtime_note,
            "runtime_inputs": runtime_inputs,
        }
        atomic_write_json(evidence_dir / "run.json", run_record)
        case.setdefault("runs", []).append(run_record)
        question["run_ids"].append(run_id)
        question.setdefault("pending_run_ids", []).append(run_id)
        question["updated_at"] = utc_now()
        case["next_action"] = (
            f"先把 {args.kind} 运行结论写入规范知识，再用 record --run-id {run_id} 更新 {question['id']}"
            if result.returncode == args.expect_exit and evidence_complete
            else f"把运行失败或证据缺失写入规范知识，再用 record --run-id {run_id} 更新 {question['id']}"
        )
        save_case(root, case)
        generate_review(root, case)
        print(json.dumps(run_record, ensure_ascii=False, indent=2))
        return 0 if result.returncode == args.expect_exit and evidence_complete else 1
    except subprocess.TimeoutExpired as exc:
        atomic_write_text(evidence_dir / "stdout.log", exc.stdout or "")
        atomic_write_text(evidence_dir / "stderr.log", exc.stderr or "")
        raise IngestionError(f"隔离运行超过 {args.timeout}s；证据保存在 {evidence_dir}") from exc
    finally:
        if worktree.exists():
            run_git(git_root, "worktree", "remove", "--force", str(worktree))
        shutil.rmtree(temporary, ignore_errors=True)


def relative_link(from_path: Path, to_path: Path) -> str:
    return Path(os.path.relpath(to_path, from_path.parent)).as_posix()


def document_title(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return path.stem
    title_match = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    heading_match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    return heading_match.group(1).strip() if heading_match else path.stem


def generate_complete_review(root: Path, case: dict[str, Any]) -> None:
    views = sorted(
        path for path in (root / "draft" / "knowledge" / "views").rglob("*.md")
        if path.name != "index.md"
    )
    lines = [
        "# 知识摄入审查",
        "",
        f"> **目标：** {case['goal']}  ",
        f"> **目标读者：** {case['target_reader']}  ",
        f"> **当前阶段：** {case['stage']}  ",
        "> 正式知识尚未修改；本页只汇总候选知识、事实边界和需要人工决定的事项。",
        "",
        "## 从这里开始看内容",
        "",
    ]
    if views:
        lines.extend(
            f"- [{document_title(path)}]({relative_link(root / 'review.md', path)})"
            for path in views
        )
    else:
        lines.append("- 产品视图尚未形成。")
    lines.extend(
        [
            "",
            "## 知识目录与完成状态",
            "",
            "| 知识主题 | 读者用途 | 处理方式 | 规范落点 | 状态 |",
            "|---|---|---|---|---|",
        ]
    )
    for topic in case["topics"]:
        target = root / topic["path"]
        purpose = topic["purpose"].replace("|", "\\|")
        link = (
            f"[{topic['path']}]({relative_link(root / 'review.md', target)})"
            if target.is_file()
            else topic["path"]
        )
        located = len(topic.get("finding_sections", {}))
        expected = len(topic["finding_ids"])
        status = topic["status"]
        if status == "ready":
            status = f"{status}（直接材料结论 {located}/{expected} 已定位）"
        lines.append(
            f"| {topic['id']} {topic['title']} | {purpose} | "
            f"{topic['action']} | {link} | {status} |"
        )
    if not case["topics"]:
        lines.append("| 尚未形成 | 尚未形成知识目录 | - | - | - |")

    counts = Counter(item["status"] for item in case["material_groups"])
    lines.extend(
        [
            "",
            "## 材料范围与读后发现",
            "",
            f"- **材料集合：** {len(case['sources'])} 个；**材料组：** {len(case['material_groups'])} 个。",
            "- **材料组状态：** "
            + "；".join(f"{status} {count} 个" for status, count in sorted(counts.items()))
            + "。",
            f"- **带精确来源的读后发现：** {len(case['findings'])} 项。",
            "",
        ]
    )
    for finding in case["findings"]:
        sources = "、".join(f"`{item}`" for item in finding["sources"])
        anchors = "、".join(f"`{item}`" for item in finding.get("anchors", []))
        details = "；".join(finding.get("details", [])) or "未登记"
        limits = "；".join(finding["limits"]) or "无额外限制"
        lines.append(
            f"- **{finding['id']} · {finding['reality']}：** {finding['content']} "
            f"关键细节：{details}。适用范围：{finding['scope']}。限制：{limits}。"
            f"来源：{sources}。定位：{anchors}。"
        )

    lines.extend(["", "## 仍需补充或人工决定", ""])
    uncertain = [item for item in case["findings"] if item["reality"] in {"conflict", "unknown"}]
    if uncertain:
        for finding in uncertain:
            lines.append(f"- **{finding['id']}：** {finding['content']}（{finding['reality']}）。")
    else:
        lines.append("- 当前没有登记冲突或未知；这不代表材料之外不存在未知。")
    if case.get("plan_review", {}).get("issues"):
        for issue in case["plan_review"]["issues"]:
            lines.append(f"- **知识目录复核：** {issue}")

    lines.extend(
        [
            "",
            "## 发布决定",
            "",
            "- [ ] 候选知识的范围、事实和未知边界可以接受",
            "- [ ] 产品视图能够支持实际浏览和继续工作",
            "- [ ] 批准把候选变更合并到正式 `knowledge/` 和 `config/`",
            "",
        ]
    )
    atomic_write_text(root / "review.md", "\n".join(lines))


def generate_review(root: Path, case: dict[str, Any]) -> None:
    if case.get("mode") == "complete":
        generate_complete_review(root, case)
        return
    views = sorted(
        path for path in (root / "draft" / "knowledge" / "views").rglob("*.md")
        if path.name != "index.md"
    )
    lines = [
        "# 知识摄入审查",
        "",
        f"> **目标：** {case['goal']}  ",
        f"> **目标读者：** {case['target_reader']}  ",
        "> 正式知识尚未修改；本页只汇总候选知识、事实边界和需要人工决定的事项。",
        "",
        "## 从这里开始看内容",
        "",
    ]
    if views:
        for path in views:
            lines.append(f"- [{document_title(path)}]({relative_link(root / 'review.md', path)})")
    else:
        lines.append("- 产品视图尚未形成。")
    lines.extend(
        [
            "",
            "## 读者问题与知识结果",
            "",
            "| 问题 | 当前状态 | 结果摘要 | 规范知识 | 仍缺什么/下一动作 |",
            "|---|---|---|---|---|",
        ]
    )
    for question in case["questions"]:
        knowledge_links = []
        for value in question["knowledge_paths"]:
            target = root / value
            knowledge_links.append(f"[{document_title(target)}]({relative_link(root / 'review.md', target)})")
        missing = "；".join(question["missing"]) or "无"
        next_action = question["next_action"] or "无"
        lines.append(
            "| {id} {text} | {status} | {summary} | {knowledge} | {missing}；下一步：{next_action} |".format(
                id=question["id"],
                text=question["text"].replace("|", "\\|"),
                status=QUESTION_STATUS_LABELS.get(question["status"], question["status"]),
                summary=(question["summary"] or "尚未形成").replace("|", "\\|"),
                knowledge="；".join(knowledge_links) or "尚未形成",
                missing=missing.replace("|", "\\|"),
                next_action=next_action.replace("|", "\\|"),
            )
        )
    lines.extend(["", "## 直接依据与真实运行", ""])
    evidence_refs = {
        evidence["ref"]
        for question in case["questions"]
        for evidence in question["evidence"]
    }
    lines.append(f"- 已登记不重复直接来源：{len(evidence_refs)} 项。")
    if case.get("runs"):
        for run in case["runs"]:
            status = (
                "通过"
                if run["exit_code"] == run["expected_exit"] and run.get("evidence_complete", True)
                else "失败"
            )
            target = root / "evidence" / "runs" / run["id"] / "run.json"
            scope_label = {
                "git_only": "仅 Git 输入",
                "private_snapshot": "私有输入副本",
                "environment_bound": "环境绑定，不能当作固定基线",
            }.get(run.get("runtime_scope"), "旧版未声明")
            lines.append(
                f"- [{run['kind']}：{run['purpose']}]({relative_link(root / 'review.md', target)})："
                f"{status}；运行范围：{scope_label}。"
            )
    else:
        lines.append("- 本轮尚无真实运行证据。")
    pending_runs = [
        run_id
        for question in case["questions"]
        for run_id in question.get("pending_run_ids", [])
    ]
    if pending_runs:
        lines.append(
            "- **尚待写回知识的运行结果：** " + "、".join(pending_runs)
            + "。先更新对应规范页，再用 `record --run-id` 登记。"
        )
    lines.extend(["", "## 仍需补充或人工决定", ""])
    decisions = [
        item for item in case["questions"]
        if item["status"] in {"partial", "conflict", "external_missing"} and item["missing"]
    ]
    if decisions:
        for question in decisions:
            lines.append(f"- **{question['id']}：** {'；'.join(question['missing'])}。")
    else:
        lines.append("- 当前没有登记缺口、冲突或必须由外部责任方补充的事项。")
    lines.extend(
        [
            "",
            "## 发布决定",
            "",
            "- [ ] 候选知识的范围、事实和未知边界可以接受",
            "- [ ] 产品视图能够支持实际浏览和继续工作",
            "- [ ] 批准把候选变更合并到正式 `knowledge/` 和 `config/`",
            "",
        ]
    )
    atomic_write_text(root / "review.md", "\n".join(lines))


def review_case(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    if case.get("mode") == "complete":
        ensure_complete(case)
        errors: list[str] = []
        if case["stage"] not in {"reviewing", "publish_ready"}:
            errors.append(f"当前仍处于 {case['stage']}，尚未完成全部知识主题")
        unfinished = [item["id"] for item in case["topics"] if item["status"] != "ready"]
        if unfinished:
            errors.append("以下知识主题尚未完成：" + ", ".join(unfinished))
        report = validate_bundle(
            root / "draft" / "knowledge", root / "draft" / "config" / "knowledge-domains.yaml"
        )
        errors.extend(f"知识结构：{item}" for item in report.errors)
        for area, label in (("by-domain", "领域位置视图"), ("by-journey", "旅程/学习视图")):
            view_files = [
                path for path in (root / "draft" / "knowledge" / "views" / area).glob("*.md")
                if path.name != "index.md"
            ]
            if not view_files:
                errors.append(f"尚未形成{label}")
        if not errors:
            case["stage"] = "publish_ready"
            case["next_action"] = "请用户审查候选知识、产品视图和 review.md，决定发布或退回"
            save_case(root, case)
        generate_review(root, case)
        print(json.dumps({"review": str(root / "review.md"), "ready": not errors, "errors": errors, "next": case["next_action"]}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    generate_review(root, case)
    print(str(root / "review.md"))
    return 0


def status_case(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    if case.get("mode") == "complete":
        refresh_complete_cursor(case)
        save_case(root, case)
        group_counts = Counter(item["status"] for item in case["material_groups"])
        topic_counts = Counter(item["status"] for item in case["topics"])
        cursor = case["cursor"]
        current: dict[str, Any] | None = None
        if cursor["item_type"] == "material_group":
            group = group_by_id(case, cursor["item_id"])
            sources = source_map(case)
            current = {
                "id": group["id"],
                "label": group["label"],
                "open_paths": [
                    str(Path(sources[source_id]["root"]) / relative)
                    for source_id, relative in (split_source_ref(ref) for ref in group["members"])
                ],
            }
        elif cursor["item_type"] == "knowledge_topic":
            topic = topic_by_id(case, cursor["item_id"])
            current = {
                "id": topic["id"],
                "title": topic["title"],
                "open_paths": [str(root / topic["path"]), *[str(root / item) for item in topic["view_paths"]]],
            }
        payload = {
            "case_id": case["id"],
            "mode": case["mode"],
            "goal": case["goal"],
            "target_reader": case["target_reader"],
            "stage": case["stage"],
            "cursor": case["cursor"],
            "current": current,
            "sources": [public_source_identity(item) for item in case["sources"]],
            "material_groups": dict(sorted(group_counts.items())),
            "findings": len(case["findings"]),
            "knowledge_topics": dict(sorted(topic_counts.items())),
            "plan_review_passed": bool(case["plan_review"].get("passed")),
            "review": str(root / "review.md"),
            "next": case["next_action"],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    payload = {
        "case_id": case["id"],
        "goal": case["goal"],
        "target_reader": case["target_reader"],
        "sources": [public_source_identity(item) for item in case["sources"]],
        "questions": [
            {
                "id": item["id"],
                "text": item["text"],
                "status": item["status"],
                "active_packet": len(item["active_packet"]),
                "remaining_candidates": len(item["candidate_queue"]),
                "knowledge_paths": item["knowledge_paths"],
                "run_ids": item["run_ids"],
                "pending_run_ids": item.get("pending_run_ids", []),
                "next": item["next_action"],
            }
            for item in case["questions"]
        ],
        "review": str(root / "review.md"),
        "next": case["next_action"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-root", type=Path, default=default_cases_root())
    subparsers = parser.add_subparsers(dest="action", required=True)

    start = subparsers.add_parser("start", help="创建聚焦或宽范围完整摄入案和后台来源基线")
    start.add_argument("case_id")
    start.add_argument("--mode", choices=sorted(INGESTION_MODES), default="focused")
    start.add_argument("--goal", required=True)
    start.add_argument("--reader", required=True)
    start.add_argument("--source", action="append", default=[])
    start.add_argument("--question", action="append", default=[])
    start.add_argument("--boundary", action="append", default=[])
    start.set_defaults(func=start_case)

    survey = subparsers.add_parser("survey", help="查看完整整理的客观材料地图")
    survey.add_argument("case_id")
    survey.add_argument("--members", action="store_true", help="同时显示各组全部成员")
    survey.set_defaults(func=survey_materials)

    question = subparsers.add_parser("question-add", help="新增一个随证据出现的读者问题")
    question.add_argument("case_id")
    question.add_argument("--text", required=True)
    question.set_defaults(func=add_question)

    unit = subparsers.add_parser("plan-unit", help="为一个读者问题规划规范知识落点")
    unit.add_argument("case_id")
    unit.add_argument("question_id")
    unit.add_argument("unit_id")
    unit.add_argument("--title", required=True)
    unit.add_argument("--kind", choices=("business", "data", "software", "run", "other"), required=True)
    unit.add_argument("--path", required=True)
    unit.add_argument("--require-run", action="store_true")
    unit.set_defaults(func=plan_unit)

    next_command = subparsers.add_parser("next", help="取得当前材料组、知识主题或聚焦问题的小批来源")
    next_command.add_argument("case_id")
    next_command.add_argument("question_id", nargs="?")
    next_command.add_argument("--query", action="append", default=[])
    next_command.add_argument("--limit", type=int, choices=range(1, 9), default=6)
    next_command.set_defaults(func=next_sources)

    finding = subparsers.add_parser("finding-add", help="为当前材料组登记一项带精确来源的读后发现")
    finding.add_argument("case_id")
    finding.add_argument("finding_id")
    finding.add_argument("--group-id", required=True)
    finding.add_argument("--content", required=True)
    finding.add_argument("--detail", action="append", default=[])
    finding.add_argument("--reality", choices=sorted(REALITY_STATES), required=True)
    finding.add_argument("--source", action="append", default=[])
    finding.add_argument("--anchor", action="append", default=[])
    finding.add_argument("--scope", required=True)
    finding.add_argument("--limit", action="append", default=[])
    finding.add_argument("--topic", action="append", default=[])
    finding.set_defaults(func=add_finding)

    material = subparsers.add_parser("record-material", help="登记当前材料组的相关性与概要")
    material.add_argument("case_id")
    material.add_argument("group_id")
    material.add_argument("--status", choices=sorted(MATERIAL_GROUP_STATES - {"unreviewed"}), required=True)
    material.add_argument("--summary", required=True)
    material.set_defaults(func=record_material)

    reopen = subparsers.add_parser("material-reopen", help="目录规划发现漏读时重新审视一个已结束材料组")
    reopen.add_argument("case_id")
    reopen.add_argument("group_id")
    reopen.add_argument("--reason", required=True)
    reopen.set_defaults(func=reopen_material)

    topic = subparsers.add_parser("topic-add", help="根据读后发现规划一个规范知识主题")
    topic.add_argument("case_id")
    topic.add_argument("topic_id")
    topic.add_argument("--title", required=True)
    topic.add_argument("--purpose", required=True)
    topic.add_argument("--action", choices=("create", "update", "merge", "view"), required=True)
    topic.add_argument("--path", required=True)
    topic.add_argument("--finding", action="append", default=[])
    topic.add_argument("--view", action="append", default=[])
    topic.set_defaults(func=add_topic)

    plan_review = subparsers.add_parser("plan-review", help="写作前复核知识目录、材料覆盖和维护边界")
    plan_review.add_argument("case_id")
    plan_review.add_argument("--lens", action="append", default=[])
    plan_review.add_argument("--not-applicable", action="append", default=[])
    plan_review.set_defaults(func=review_knowledge_plan)

    topic_record = subparsers.add_parser("record-topic", help="登记当前知识主题正文和产品视图已经形成")
    topic_record.add_argument("case_id")
    topic_record.add_argument("topic_id")
    topic_record.add_argument(
        "--section",
        action="append",
        default=[],
        help="使用 <finding-id>=<正文标题> 定位每项直接材料结论",
    )
    topic_record.set_defaults(func=record_topic)

    record = subparsers.add_parser("record", help="登记当前小批来源形成的知识和缺口")
    record.add_argument("case_id")
    record.add_argument("question_id")
    record.add_argument("--status", required=True, choices=sorted(QUESTION_STATES - {"working"}))
    record.add_argument("--summary", required=True)
    record.add_argument("--source", action="append", default=[])
    record.add_argument("--run-id", action="append", default=[])
    record.add_argument("--knowledge", action="append", default=[])
    record.add_argument("--missing", action="append", default=[])
    record.add_argument("--dismiss-unused")
    record.add_argument("--close-candidates")
    record.add_argument("--next-action")
    record.set_defaults(func=record_result)

    stop = subparsers.add_parser(
        "stop-search", help="已有可用知识后，说明理由并停止为该问题继续选源"
    )
    stop.add_argument("case_id")
    stop.add_argument("question_id")
    stop.add_argument("--reason", required=True)
    stop.add_argument("--next-action")
    stop.set_defaults(func=stop_search)

    check = subparsers.add_parser("check-unit", help="核对一个问题的知识、候选、视图和运行证据")
    check.add_argument("case_id")
    check.add_argument("question_id")
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.set_defaults(func=check_unit)

    run = subparsers.add_parser("run", help="在临时 Git worktree 中执行来源项目验证")
    run.add_argument("case_id")
    run.add_argument("question_id")
    run.add_argument("--source-id", required=True)
    run.add_argument("--kind", choices=sorted(RUN_KINDS), required=True)
    run.add_argument("--purpose", required=True)
    command = run.add_mutually_exclusive_group(required=True)
    command.add_argument("--command")
    command.add_argument("--command-file")
    run.add_argument("--expect-exit", type=int, default=0)
    run.add_argument("--timeout", type=int, default=120)
    run.add_argument("--mount", action="append", default=[])
    run.add_argument("--copy-mount", action="append", default=[])
    run.add_argument("--runtime-note", action="append", default=[])
    run.add_argument("--artifact", action="append", default=[])
    run.set_defaults(func=run_project)

    review = subparsers.add_parser("review", help="重建唯一人工审查页")
    review.add_argument("case_id")
    review.set_defaults(func=review_case)

    status = subparsers.add_parser("status", help="恢复问题、知识、候选和下一动作")
    status.add_argument("case_id")
    status.set_defaults(func=status_case)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.action in {
            "question-add", "plan-unit", "next", "finding-add", "record-material", "material-reopen",
            "topic-add", "plan-review", "record-topic", "record", "stop-search",
            "check-unit", "run", "review",
        }:
            with case_state_lock(args.cases_root, args.case_id):
                return args.func(args)
        return args.func(args)
    except IngestionError as exc:
        print(f"ingestion-workspace: ERROR\n- {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
