#!/usr/bin/env python3
"""Drive a recoverable complete, focused, or code-writeback knowledge workbench.

The tool keeps deterministic source identity and small recoverable state. It does
not decide knowledge truth, write domain content, or replace human review.
"""

from __future__ import annotations

import argparse
import ast
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


SCHEMA_VERSION = "1.5"
CASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
QUESTION_ID_RE = re.compile(r"^q-[0-9]{3}$")
UNIT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
LINK_RE = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", re.DOTALL)
FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):", re.MULTILINE)
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
MAX_KNOWLEDGE_UNITS_PER_QUESTION = 4
MAX_MATERIAL_GROUP_MEMBERS = 12
MAX_MATERIAL_GROUP_BYTES = 100_000
NARRATIVE_SUFFIXES = {".md", ".rst", ".txt"}
INGESTION_MODES = {"focused", "complete", "writeback"}
SYSTEM_RELATIONSHIPS = {"same_system", "new_system", "uncertain"}
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
WRITEBACK_IMPACTS = {
    "outcome",
    "current_state",
    "semantics",
    "software",
    "compatibility",
    "shared",
    "evidence",
    "navigation",
}
MANDATORY_WRITEBACK_IMPACTS = {
    "outcome",
    "current_state",
    "software",
    "evidence",
    "navigation",
}
WRITEBACK_IMPACT_KINDS = {
    "outcome": {"business", "identity"},
    "current_state": {"identity"},
    "semantics": {"business", "data"},
    "software": {"software"},
    "compatibility": {"compatibility", "software", "data"},
    "shared": {"shared"},
    "evidence": {"identity", "run"},
    "navigation": {"navigation"},
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


def knowledge_baseline() -> dict[str, Any]:
    """Snapshot the formal knowledge that a new candidate must inherit."""
    root = project_root()
    paths = sorted(path for path in (root / "knowledge").rglob("*") if path.is_file())
    domain_map = root / "config" / "knowledge-domains.yaml"
    if domain_map.is_file():
        paths.append(domain_map)
    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": digest_bytes(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(paths)
    ]
    substantive = [
        item for item in entries
        if item["path"].startswith("knowledge/")
        and not item["path"].endswith("/index.md")
        and item["path"] not in {"knowledge/index.md", "knowledge/log.md"}
    ]
    return {
        "files": entries,
        "file_count": len(entries),
        "substantive_file_count": len(substantive),
        "fingerprint": canonical_digest(entries),
    }


def baseline_paths(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["path"]: item for item in case.get("baseline", {}).get("files", [])}


def candidate_manifest(root: Path) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    paths = sorted(path for path in (root / "draft" / "knowledge").rglob("*") if path.is_file())
    domain_map = root / "draft" / "config" / "knowledge-domains.yaml"
    if domain_map.is_file():
        paths.append(domain_map)
    for path in sorted(paths):
        relative = path.relative_to(root / "draft").as_posix()
        entries[relative] = {
            "path": relative,
            "sha256": digest_bytes(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
    return entries


def candidate_changes(root: Path, case: dict[str, Any]) -> dict[str, list[str]]:
    before = baseline_paths(case)
    after = candidate_manifest(root)
    return {
        "added": sorted(set(after) - set(before)),
        "modified": sorted(
            path for path in set(before) & set(after)
            if before[path]["sha256"] != after[path]["sha256"]
        ),
        "deleted": sorted(set(before) - set(after)),
    }


def governed_candidate_path(path: str) -> bool:
    """Return whether a changed path must be owned by a planned topic or view."""
    if not path.startswith("knowledge/"):
        return False
    if path == "knowledge/log.md" or path.endswith("/index.md"):
        return False
    if path.startswith("knowledge/sources/"):
        return False
    return True


def governed_writeback_path(path: str) -> bool:
    """Code writeback plans source records as first-class knowledge units."""
    if not path.startswith("knowledge/"):
        return False
    if path == "knowledge/log.md" or path.endswith("/index.md"):
        return False
    return True


def frontmatter_keys(text: str) -> set[str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return set()
    return set(FRONTMATTER_KEY_RE.findall(match.group(1)))


def parent_content_regressions(path: str, parent: bytes, candidate: bytes) -> list[str]:
    """Detect silent loss that the first incremental slice does not authorize."""
    errors: list[str] = []
    if len(parent) >= 200 and len(candidate) < len(parent) * 0.9:
        errors.append(
            f"{path} 比父版本缩小超过 10%；当前增量切片不允许用整页重写或摘要静默删除父知识"
        )
    if path.endswith(".md"):
        parent_keys = frontmatter_keys(parent.decode("utf-8"))
        candidate_keys = frontmatter_keys(candidate.decode("utf-8"))
        missing = sorted(parent_keys - candidate_keys)
        if missing:
            errors.append(
                f"{path} 删除了父版本 frontmatter 字段：{', '.join(missing)}"
            )
    return errors


def incremental_parent_preservation_errors(
    root: Path, case: dict[str, Any], changes: dict[str, list[str]]
) -> list[str]:
    errors: list[str] = []
    baseline = baseline_paths(case)
    repository = project_root()
    for path in changes["modified"]:
        if not path.startswith("knowledge/") or path == "knowledge/log.md":
            continue
        original = baseline.get(path)
        parent_path = repository / path
        candidate_path = root / "draft" / path
        if original is None or not parent_path.is_file():
            continue
        parent = parent_path.read_bytes()
        if digest_bytes(parent) != original["sha256"]:
            errors.append(f"{path} 的正式父版本在摄入开始后发生变化；请先重建或变基候选")
            continue
        errors.extend(parent_content_regressions(path, parent, candidate_path.read_bytes()))
    return errors


def incremental_entrypoint_errors(
    case: dict[str, Any], changes: dict[str, list[str]]
) -> list[str]:
    """Require an increment to reconcile the public entry and append the change log."""
    if not case.get("baseline", {}).get("substantive_file_count", 0):
        return []
    changed = set(changes["added"] + changes["modified"] + changes["deleted"])
    baseline = baseline_paths(case)
    errors: list[str] = []
    requirements = {
        "knowledge/index.md": (
            "根知识入口未随增量更新；请修正当前范围、导航和仍缺内容，"
            "不要保留与已摄入内容冲突的父版本排除声明"
        ),
        "knowledge/log.md": (
            "知识操作日志未记录本次增量；请追加一条面向维护者的变更记录，"
            "保留既有历史记录"
        ),
    }
    for path, message in requirements.items():
        if path in baseline and path not in changed:
            errors.append(message)
    return errors


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
    if not isinstance(value, dict) or value.get("schema_version") not in {"1.3", "1.4", SCHEMA_VERSION}:
        raise IngestionError(f"不支持的摄入案状态：{path}")
    if value.get("schema_version") in {"1.3", "1.4"}:
        value["schema_version"] = SCHEMA_VERSION
        for question in value.get("questions", []):
            question.setdefault("contracts", [])
        if value.get("mode") == "writeback":
            value.setdefault(
                "writeback_impact_review",
                {"passed": False, "impacts": {}, "not_applicable": {}, "issues": ["升级后需要运行 impact-review"]},
            )
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
    branch_result = run_git(git_root, "symbolic-ref", "--quiet", "--short", "HEAD")
    return {
        "root": str(git_root),
        "commit": head.stdout.strip(),
        "branch": branch_result.stdout.strip() if branch_result.returncode == 0 else None,
        "scope": str(root.relative_to(git_root)) if root != git_root else ".",
        "dirty": bool(status.stdout.strip()),
    }


def writeback_change_hints(source: dict[str, Any], parent_commit: str | None) -> dict[str, Any]:
    """Return deterministic changed-path hints; never decide knowledge semantics."""
    if not parent_commit or not source.get("git"):
        return {
            "parent_commit": parent_commit,
            "changed_paths": [],
            "shared_dependencies": [],
            "compatibility_signals": [],
            "compatibility_probes": [],
            "fact_transitions": [],
        }
    git_root = Path(source["git"]["root"])
    head = source["git"]["commit"]
    parent = run_git(git_root, "rev-parse", parent_commit)
    if parent.returncode != 0:
        raise IngestionError(f"父提交不存在于来源仓库：{parent_commit}")
    parent_sha = parent.stdout.strip()
    ancestor = run_git(git_root, "merge-base", "--is-ancestor", parent_sha, head)
    if ancestor.returncode != 0:
        raise IngestionError(f"父提交不是固定来源 HEAD 的祖先：{parent_sha} -> {head}")
    names = run_git(git_root, "diff", "--name-only", parent_sha, head, "--")
    if names.returncode != 0:
        raise IngestionError("无法读取固定提交之间的变化路径")
    changed_paths = [item for item in names.stdout.splitlines() if item][:200]

    shared_dependencies: list[dict[str, str]] = []
    shared_markers = re.compile(r"(?:^|[/_.-])(shared|common|core|infra(?:structure)?|platform)(?:[/_.-]|$)", re.IGNORECASE)
    for relative in changed_paths:
        path = git_root / relative
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        modules = [match.group("module") for match in TS_IMPORT_RE.finditer(text)]
        modules.extend(match.group("module") for match in PYTHON_FROM_RE.finditer(text))
        modules.extend(match.group("module") for match in PYTHON_IMPORT_RE.finditer(text))
        for module in modules:
            if shared_markers.search(module):
                shared_dependencies.append({"path": relative, "module": module})

    compatibility_signals: list[dict[str, str]] = []
    fact_transitions: list[dict[str, str]] = []
    diff = run_git(git_root, "diff", "--unified=0", parent_sha, head, "--")
    compatibility_re = re.compile(
        r"兼容|旧(?:版|配置|数据|列)|列顺序|保存.{0,8}配置|backward|compatib|legacy|saved.{0,12}(?:config|view|column)",
        re.IGNORECASE,
    )
    current_path = ""
    if diff.returncode == 0:
        removed_assignments: dict[tuple[str, str], str] = {}
        for line in diff.stdout.splitlines():
            if line.startswith("+++ b/"):
                current_path = line[6:]
                continue
            if line.startswith("-") and not line.startswith("---"):
                assignment = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\d+)\b", line[1:])
                if assignment:
                    removed_assignments[(current_path, assignment.group(1))] = assignment.group(2)
                continue
            if line.startswith("+") and not line.startswith("+++") and compatibility_re.search(line):
                compatibility_signals.append({"path": current_path, "line": line[1:].strip()[:240]})
                if len(compatibility_signals) >= 12:
                    compatibility_signals = compatibility_signals[:12]
            if line.startswith("+") and not line.startswith("+++"):
                added = line[1:].strip()
                assignment = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\d+)\b", added)
                if assignment:
                    old = removed_assignments.get((current_path, assignment.group(1)))
                    new = assignment.group(2)
                    if old and old != new:
                        fact_transitions.append(
                            {
                                "path": current_path,
                                "old": old,
                                "new": new,
                                "context": f"{assignment.group(1)}: {old} -> {new}",
                            }
                        )
                for transition in re.finditer(
                    r"(?:由|从)\s*(\d+)\s*(?:个|项)?[^。；\n]{0,36}?(?:增至|增加到|变为|提高到|到)\s*(\d+)",
                    added,
                ):
                    old, new = transition.groups()
                    if old != new:
                        fact_transitions.append(
                            {
                                "path": current_path,
                                "old": old,
                                "new": new,
                                "context": added[:240],
                            }
                        )
    unique_transitions: list[dict[str, str]] = []
    seen_transitions: set[tuple[str, str, str]] = set()
    for item in fact_transitions:
        key = (item["path"], item["old"], item["new"])
        if key in seen_transitions:
            continue
        seen_transitions.add(key)
        unique_transitions.append(item)
    compatibility_probes: list[dict[str, Any]] = []
    for signal in compatibility_signals:
        line = signal["line"]
        if re.search(r"列顺序|新增列|saved.{0,16}column|column.{0,16}order", line, re.IGNORECASE):
            terms = ["columnOrder", "column_order", "applyState", "restore", "normalize"]
            kind = "saved_column_state"
        elif re.search(r"配置|config|setting|preference", line, re.IGNORECASE):
            terms = ["config", "legacy", "restore", "normalize", "fallback", "default"]
            kind = "saved_configuration"
        else:
            terms = ["legacy", "compat", "migrate", "normalize", "fallback", "default"]
            kind = "generic_compatibility"
        compatibility_probes.append(
            {"kind": kind, "source_path": signal["path"], "signal": line, "terms": terms}
        )
    return {
        "parent_commit": parent_sha,
        "current_commit": head,
        "changed_paths": changed_paths,
        "shared_dependencies": shared_dependencies[:20],
        "compatibility_signals": compatibility_signals,
        "compatibility_probes": compatibility_probes[:12],
        "fact_transitions": unique_transitions[:20],
    }


def stale_current_fact_candidates(root: Path, case: dict[str, Any]) -> list[dict[str, str | int]]:
    """Find high-confidence old numeric facts still presented as current in the draft."""
    hints = (case.get("writeback") or {}).get("change_hints") or {}
    transitions = hints.get("fact_transitions") or []
    if not transitions:
        return []
    current_markers = re.compile(
        r"当前|现在|现为|最多|上限|限制|允许|基础指标|返回|通过|拒绝|HTTP\s*(?:200|4\d\d)",
        re.IGNORECASE,
    )
    history_markers = re.compile(r"历史|此前|先前|父版本|旧版|原版本|曾经|当时")
    transition_markers = re.compile(r"(?:由|从).{0,20}(?:增至|增加到|变为|提高到|到)")
    candidates: list[dict[str, str | int]] = []
    knowledge_root = root / "draft" / "knowledge"
    if not knowledge_root.is_dir():
        return []
    for path in sorted(knowledge_root.rglob("*.md")):
        relative = path.relative_to(root / "draft").as_posix()
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not current_markers.search(line) or history_markers.search(line) or transition_markers.search(line):
                continue
            semantic_line = re.sub(r"^\s*\d+[.)]\s+", "", line)
            for transition in transitions:
                old = str(transition["old"])
                new = str(transition["new"])
                if not re.search(rf"(?<!\d){re.escape(old)}(?!\d)", semantic_line):
                    continue
                candidates.append(
                    {
                        "path": relative,
                        "line_number": line_number,
                        "line": line.strip()[:280],
                        "old": old,
                        "new": new,
                        "source_path": str(transition["path"]),
                    }
                )
                break
    return candidates[:30]


def compatibility_mechanism_errors(root: Path, case: dict[str, Any]) -> list[str]:
    """Require compatibility conclusions to cite implementation or focused test mechanics."""
    hints = (case.get("writeback") or {}).get("change_hints") or {}
    probes = hints.get("compatibility_probes") or []
    impact_review = case.get("writeback_impact_review") or {}
    compatibility_refs = impact_review.get("impacts", {}).get("compatibility", [])
    if not probes or not compatibility_refs:
        return []
    question_ids = {ref.split(":", 1)[0] for ref in compatibility_refs}
    evidence_refs = {
        evidence["ref"]
        for question in case.get("questions", [])
        if question.get("id") in question_ids
        for evidence in question.get("evidence", [])
    }
    sources = source_map(case)
    evidence_texts: list[tuple[str, str]] = []
    for ref in sorted(evidence_refs):
        source_id, separator, relative = ref.partition(":")
        source = sources.get(source_id)
        if not separator or source is None:
            continue
        path = Path(source["root"]) / relative
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            evidence_texts.append((ref, path.read_text(encoding="utf-8")[:1_000_000]))
        except (OSError, UnicodeError):
            continue
    errors: list[str] = []
    for probe in probes:
        terms = [str(term) for term in probe.get("terms", [])]
        if any(
            any(term.lower() in text.lower() for term in terms)
            for _, text in evidence_texts
        ):
            continue
        errors.append(
            "兼容结论只有结果信号，缺少恢复/归一化机制的实现或聚焦测试来源："
            f"{probe.get('signal')}；请在兼容问题登记包含 "
            + "/".join(terms)
            + " 等真实机制的源码或测试，并把旧输入、处理、结果和 owner 写入正文"
        )
    return errors


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
            "branch": git.get("branch"),
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


def scaffold_case(root: Path) -> dict[str, Any]:
    """Create an isolated candidate as an exact child of current formal knowledge."""
    baseline = knowledge_baseline()
    source_knowledge = project_root() / "knowledge"
    target_knowledge = root / "draft" / "knowledge"
    target_knowledge.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_knowledge, target_knowledge)
    domain_map = project_root() / "config" / "knowledge-domains.yaml"
    target = root / "draft" / "config" / "knowledge-domains.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(domain_map, target)
    return baseline


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
        "contracts": [],
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
    if args.mode in {"focused", "writeback"} and not questions:
        raise IngestionError("至少需要一个 --question；问题主线不能由工具猜测")
    sources, manifest = scan_sources(args.source)
    root.mkdir(parents=True, exist_ok=True)
    baseline = scaffold_case(root)
    now = utc_now()
    case = {
        "schema_version": SCHEMA_VERSION,
        "id": args.case_id,
        "mode": args.mode,
        "goal": args.goal.strip(),
        "target_reader": args.reader.strip(),
        "boundaries": [item.strip() for item in args.boundary if item.strip()],
        "sources": sources,
        "baseline": baseline,
        "questions": [new_question(index, text) for index, text in enumerate(questions, 1)],
        "stage": args.mode if args.mode in {"focused", "writeback"} else "mapping",
        "cursor": {"item_type": None, "item_id": None},
        "material_groups": [],
        "findings": [],
        "topics": [],
        "plan_review": {"passed": False, "lenses": {}, "not_applicable": {}, "issues": []},
        "writeback": (
            {
                "relationship": None,
                "reason": "",
                "source_path": None,
                "system_path": None,
                "decided_at": None,
            }
            if args.mode == "writeback"
            else None
        ),
        "writeback_impact_review": (
            {"passed": False, "impacts": {}, "not_applicable": {}, "issues": []}
            if args.mode == "writeback"
            else None
        ),
        "created_at": now,
        "updated_at": now,
        "next_action": (
            "先判断代码来源与既有系统知识的身份关系，再按影响面规划 q-001"
            if args.mode == "writeback"
            else "为 q-001 规划一至三个知识单元，再取得第一小批直接来源"
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
                "baseline": {
                    "file_count": baseline["file_count"],
                    "substantive_file_count": baseline["substantive_file_count"],
                    "fingerprint": baseline["fingerprint"],
                },
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


def set_writeback_identity(args: argparse.Namespace) -> int:
    """Record whether a fixed code source updates an existing system or introduces a new one."""
    root, case = load_case(args.cases_root, args.case_id)
    if case.get("mode") != "writeback":
        raise IngestionError("identity-set 只用于代码变化回写案")
    validate_id(args.case_id, "case id")
    relationship = args.relationship
    sources = {item["id"]: item for item in case.get("sources", [])}
    if args.source_id:
        if args.source_id not in sources:
            raise IngestionError(f"来源不存在：{args.source_id}")
        source = sources[args.source_id]
    elif len(sources) == 1:
        source = next(iter(sources.values()))
    else:
        source = None
        if args.parent_commit:
            raise IngestionError("存在多个来源时，--parent-commit 必须同时指定 --source-id")
    change_hints = writeback_change_hints(source, args.parent_commit) if source else {
        "parent_commit": args.parent_commit,
        "changed_paths": [],
        "shared_dependencies": [],
        "compatibility_signals": [],
        "compatibility_probes": [],
        "fact_transitions": [],
    }
    source_path = normalize_knowledge_path(args.source_path) if args.source_path else None
    system_path = normalize_knowledge_path(args.system_path) if args.system_path else None
    if relationship in {"same_system", "new_system"} and (not source_path or not system_path):
        raise IngestionError(
            f"{relationship} 必须同时声明独立的 --source-path 和 --system-path"
        )
    if source_path and not source_path.startswith("draft/knowledge/sources/"):
        raise IngestionError("--source-path 必须位于 draft/knowledge/sources/")
    if system_path and not system_path.startswith("draft/knowledge/systems/"):
        raise IngestionError("--system-path 必须位于 draft/knowledge/systems/")
    baseline = baseline_paths(case)
    canonical_source = source_path.removeprefix("draft/") if source_path else None
    canonical_system = system_path.removeprefix("draft/") if system_path else None
    if relationship == "new_system":
        existing = [
            path for path in (canonical_source, canonical_system)
            if path in baseline
        ]
        if existing:
            raise IngestionError(
                "new_system 必须使用父知识中不存在的独立来源/系统落点："
                + ", ".join(existing)
            )
    if relationship == "same_system":
        missing = [
            path for path in (canonical_source, canonical_system)
            if path not in baseline
        ]
        if missing:
            raise IngestionError(
                "same_system 必须更新父知识中已经存在的来源/系统落点："
                + ", ".join(missing)
            )
    current = case.get("writeback") or {}
    decision_fields = {
        "relationship": relationship,
        "reason": args.reason.strip(),
        "source_path": source_path,
        "system_path": system_path,
        "source_id": source.get("id") if source else None,
        "parent_commit": change_hints.get("parent_commit"),
        "change_hints": change_hints,
    }
    if all(current.get(key) == value for key, value in decision_fields.items()):
        print(
            json.dumps(
                {"writeback": current, "already_recorded": True, "next": case["next_action"]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    decided = {
        **decision_fields,
        "decided_at": utc_now(),
    }
    if current.get("relationship") and current != decided:
        started = any(
            question.get("evidence") or question.get("knowledge_paths")
            for question in case["questions"]
        )
        if started:
            raise IngestionError("已经形成来源或知识后不能改写系统身份；请新建回写案")
    case["writeback"] = decided
    case["next_action"] = (
        "按身份、业务/数据/规则、软件/运行和产品视图的实际影响规划读者问题；"
        "若下方存在固定验证报告，先把报告作为直接来源核对覆盖，再决定是否现场运行"
    )
    save_case(root, case)
    generate_review(root, case)
    print(
        json.dumps(
            {
                "writeback": decided,
                "existing_run_evidence_candidates": fixed_run_evidence_candidates(root, case),
                "change_hints": change_hints,
                "compatibility_followup": (
                    "兼容信号只给出结果。把它单独变成读者问题，继续定位旧输入或旧状态、"
                    "恢复/合并机制、可观察结果和长期 owner；若由共享能力承担，更新共享 owner。"
                    "最终审查要求兼容问题登记命中 compatibility_probes 的实现或聚焦测试，"
                    "不能只登记验证报告。"
                    if change_hints.get("compatibility_signals")
                    else None
                ),
                "evidence_rule": (
                    "候选报告属于冻结来源，不自动证明正文声明；先读取并核对 commit、环境和覆盖。"
                    "覆盖当前问题时作为直接来源登记，不机械重跑；不足时再运行来源项目。"
                ),
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
        raise IngestionError(
            "index.md 是最终导航同步，不是实质知识单元；"
            "请规划正文或受维护的产品视图，最后直接同步 index.md"
        )
    return normalized


def plan_unit(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    question = question_by_id(case, args.question_id)
    if case.get("mode") == "writeback" and not (case.get("writeback") or {}).get("relationship"):
        raise IngestionError("代码变化回写必须先运行 identity-set 判断系统身份")
    validate_id(args.unit_id, "unit id", UNIT_ID_RE)
    existing = next((item for item in question["expected_units"] if item["id"] == args.unit_id), None)
    if existing is None and len(question["expected_units"]) >= MAX_KNOWLEDGE_UNITS_PER_QUESTION:
        raise IngestionError(
            f"一个读者问题最多规划 {MAX_KNOWLEDGE_UNITS_PER_QUESTION} 个规范知识落点；"
            "导航、日志和来源清单应留到最终同步，超过上限时拆分读者问题"
        )
    path = normalize_knowledge_path(args.path)
    if any(item["path"] == path and item["id"] != args.unit_id for item in question["expected_units"]):
        raise IngestionError(f"知识路径已规划：{path}")
    unit = {
        "id": args.unit_id,
        "title": args.title.strip(),
        "kind": args.kind,
        "path": path,
        "status": "planned",
    }
    if existing:
        if question.get("evidence") or question.get("knowledge_paths"):
            raise IngestionError(f"知识单元 {args.unit_id} 已进入取源/写作，不能修改计划")
        existing.clear()
        existing.update(unit)
        unit = existing
        updated = True
    else:
        question["expected_units"].append(unit)
        updated = False
    if case.get("mode") == "writeback":
        case["writeback_impact_review"] = {
            "passed": False,
            "impacts": {},
            "not_applicable": {},
            "issues": ["知识单元发生变化，需要重新运行 impact-review"],
        }
    question["requires_run"] = bool(question["requires_run"] or args.require_run)
    question["updated_at"] = utc_now()
    question["next_action"] = "围绕当前问题取得第一小批直接来源"
    case["next_action"] = f"运行 next 为 {question['id']} 取得直接来源"
    save_case(root, case)
    payload: dict[str, Any] = {
        "unit": unit,
        "updated": updated,
        "requires_run": question["requires_run"],
        "next": case["next_action"],
    }
    if question["requires_run"]:
        payload["run_evidence_rule"] = (
            "下一次 next 会优先返回冻结来源内的验证报告。先核对其版本、环境和覆盖；"
            "报告足以回答时直接登记，只有覆盖不足时才现场运行。"
        )
    if unit["kind"] == "data":
        payload["data_contract_rule"] = (
            "若 packet 给出 contract_candidates，选择会影响读者/开发的契约运行 contract-inspect；"
            "知识页必须保留其完整字段，不得只概括字段组。"
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def review_writeback_impacts(args: argparse.Namespace) -> int:
    """Bind a code change's user-visible impact axes to planned knowledge owners."""
    root, case = load_case(args.cases_root, args.case_id)
    if case.get("mode") != "writeback":
        raise IngestionError("impact-review 只用于代码变化回写案")
    if not (case.get("writeback") or {}).get("relationship"):
        raise IngestionError("先运行 identity-set 判断系统身份")

    impact_values = parse_key_values(args.impact, "--impact")
    not_applicable = parse_key_values(args.not_applicable, "--not-applicable")
    unknown = (set(impact_values) | set(not_applicable)) - WRITEBACK_IMPACTS
    if unknown:
        raise IngestionError("未知变化影响角度：" + ", ".join(sorted(unknown)))
    overlap = set(impact_values) & set(not_applicable)
    if overlap:
        raise IngestionError("同一影响角度不能同时映射和排除：" + ", ".join(sorted(overlap)))

    missing = WRITEBACK_IMPACTS - set(impact_values) - set(not_applicable)
    errors: list[str] = []
    if missing:
        errors.append("以下变化影响尚未映射或说明不适用：" + ", ".join(sorted(missing)))
    forbidden_na = MANDATORY_WRITEBACK_IMPACTS & set(not_applicable)
    if forbidden_na:
        errors.append("以下回写影响不能标为不适用：" + ", ".join(sorted(forbidden_na)))
    for impact, reason in not_applicable.items():
        if len(reason) < 12:
            errors.append(f"影响角度 {impact} 的不适用依据过短，需说明代码事实和保持边界")
    hints = (case.get("writeback") or {}).get("change_hints") or {}
    if "shared" in not_applicable and hints.get("shared_dependencies"):
        errors.append(
            "固定代码变化涉及共享/公共依赖，shared 不能标为不适用："
            + "；".join(
                f"{item['path']} -> {item['module']}"
                for item in hints["shared_dependencies"][:6]
            )
        )
    if "compatibility" in not_applicable and hints.get("compatibility_signals"):
        errors.append(
            "固定 diff 或验证报告含兼容信号，compatibility 不能标为不适用："
            + "；".join(
                f"{item['path']} -> {item['line']}"
                for item in hints["compatibility_signals"][:6]
            )
        )

    unit_lookup: dict[str, dict[str, Any]] = {}
    for question in case["questions"]:
        for unit in question["expected_units"]:
            unit_lookup[f"{question['id']}:{unit['id']}"] = unit
    impact_units: dict[str, list[str]] = {
        impact: [item.strip() for item in value.split(",") if item.strip()]
        for impact, value in impact_values.items()
    }
    for impact, refs in impact_units.items():
        if not refs:
            errors.append(f"变化影响 {impact} 没有知识单元")
            continue
        for ref in refs:
            unit = unit_lookup.get(ref)
            if unit is None:
                errors.append(f"变化影响 {impact} 引用了未知知识单元：{ref}")
                continue
            allowed = WRITEBACK_IMPACT_KINDS[impact]
            if unit["kind"] not in allowed:
                errors.append(
                    f"变化影响 {impact} 的知识单元 {ref} 类型应为 "
                    + "/".join(sorted(allowed))
                    + f"，当前为 {unit['kind']}"
                )

    identity = case.get("writeback") or {}
    current_state_paths = {
        unit_lookup[ref]["path"]
        for ref in impact_units.get("current_state", [])
        if ref in unit_lookup
    }
    required_identity_paths = {
        path for path in (identity.get("source_path"), identity.get("system_path")) if path
    }
    if required_identity_paths - current_state_paths:
        errors.append(
            "current_state 必须同时覆盖来源页和系统页："
            + ", ".join(sorted(required_identity_paths - current_state_paths))
        )
    navigation_paths = {
        unit_lookup[ref]["path"]
        for ref in impact_units.get("navigation", [])
        if ref in unit_lookup
    }
    if navigation_paths and not all(path.startswith("draft/knowledge/views/") for path in navigation_paths):
        errors.append("navigation 只能映射到 draft/knowledge/views/ 下的受维护产品视图")

    report = {
        "passed": not errors,
        "impacts": impact_units,
        "not_applicable": not_applicable,
        "issues": errors,
        "reviewed_at": utc_now(),
    }
    case["writeback_impact_review"] = report
    case["next_action"] = (
        "按影响面逐题取源并形成知识；最终审查前复核版本、公式、数量限制和兼容行为的当前态一致性"
        if report["passed"]
        else "修正知识单元或变化影响映射后重新运行 impact-review"
    )
    save_case(root, case)
    generate_review(root, case)
    print(json.dumps({"impact_review": report, "next": case["next_action"]}, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


def default_query_terms(text: str) -> list[str]:
    terms = re.findall(r"[A-Za-z_][A-Za-z0-9_.-]{2,}", text)
    for chunk in re.split(r"[，。；：！？、,.;:!?\s/]+", text):
        chunk = chunk.strip()
        if 2 <= len(chunk) <= 12:
            terms.append(chunk)
    return list(dict.fromkeys(terms))[:12]


def normalize_query_terms(values: list[str]) -> list[str]:
    """Accept both repeated terms and a human-friendly whitespace-separated query."""
    terms: list[str] = []
    for value in values:
        value = value.strip()
        if not value:
            continue
        expanded = default_query_terms(value)
        terms.extend(expanded or [value])
    return list(dict.fromkeys(terms))[:24]


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
    if (
        lowered.endswith((".md", ".rst", ".txt", ".json", ".yaml", ".yml"))
        and any(
            marker in name
            for marker in (
                "verification-report", "validation-report", "test-report",
                "test-results", "run-report", "qa-report", "benchmark-report",
            )
        )
    ):
        return "run_evidence"
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


def python_contracts(path: Path) -> list[dict[str, Any]]:
    """Return annotated class fields, including local annotated bases.

    This deliberately supports one observable contract form rather than trying to
    infer an ontology from arbitrary source code. Other languages can add their
    own deterministic extractors when a real slice requires them.
    """
    if path.suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError):
        return []
    classes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }

    def fields_for(name: str, visiting: set[str] | None = None) -> list[str]:
        node = classes.get(name)
        if node is None:
            return []
        active = set(visiting or ())
        if name in active:
            return []
        active.add(name)
        fields: list[str] = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                fields.extend(fields_for(base.id, active))
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                fields.append(statement.target.id)
        return list(dict.fromkeys(fields))

    contracts = [
        {"symbol": name, "field_count": len(fields), "fields": fields}
        for name in classes
        if len(fields := fields_for(name)) >= 4
    ]
    contracts.sort(key=lambda item: (-item["field_count"], item["symbol"]))
    return contracts[:8]


def contract_candidates(case: dict[str, Any], reference: str) -> list[dict[str, Any]]:
    try:
        return python_contracts(resolve_source(case, reference))
    except IngestionError:
        return []


def fixed_run_evidence_candidates(
    root: Path, case: dict[str, Any], *, limit: int = 6
) -> list[dict[str, Any]]:
    sources = source_map(case)
    candidates: list[dict[str, Any]] = []
    for item in read_manifest(root):
        ref = manifest_ref(item)
        if candidate_role(ref) != "run_evidence":
            continue
        candidates.append(
            {
                "ref": ref,
                "role": "run_evidence",
                "absolute_path": str(Path(sources[item["source_id"]]["root"]) / item["path"]),
                "title": item.get("title"),
                "headings": item.get("headings", [])[:8],
            }
        )
    return candidates[:limit]


def prioritize_fixed_run_evidence(
    root: Path,
    case: dict[str, Any],
    question: dict[str, Any],
    queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not question.get("requires_run"):
        return queue
    seen = {item["ref"] for item in question.get("evidence", [])}
    for packet in question.get("dismissed_packets", []):
        seen.update(packet.get("refs", []))
    by_ref = {item["ref"]: item for item in queue}
    prioritized: list[dict[str, Any]] = []
    for item in fixed_run_evidence_candidates(root, case):
        if item["ref"] in seen:
            continue
        candidate = by_ref.pop(item["ref"], None) or {
            "ref": item["ref"],
            "score": 100,
            "reasons": ["固定来源包含现有验证报告；先核对覆盖范围，再决定是否重跑"],
        }
        candidate["score"] = max(100, int(candidate.get("score", 0)))
        candidate["reasons"] = list(dict.fromkeys([
            "固定来源包含现有验证报告；先核对覆盖范围，再决定是否重跑",
            *candidate.get("reasons", []),
        ]))[:6]
        prioritized.append(candidate)
    return [*prioritized, *sorted(by_ref.values(), key=lambda item: (-item["score"], item["ref"]))]


def take_diverse_packet(queue: list[dict[str, Any]], limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if len(queue) <= limit:
        return [
            {**item, "role": candidate_role(item["ref"])}
            for item in queue
        ], []
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
        "data_access", "data_schema", "run_evidence", "run_contract",
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
                "update/merge 必须通读最终整页并采用保守局部编辑：保留父页面已有 frontmatter、"
                "段落、图表、链接和技术细节，不得整页摘要重写；同时复核父版本的当前覆盖、缺口和未来补齐表述，"
                "确保它们仍成立、已按新证据更新，或已明确标成历史。"
                "不得在正文或产品视图追加按材料批次、本次增量或日期命名的分区。"
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
    raw_anchors = list(dict.fromkeys(item.strip() for item in args.anchor if item.strip()))
    if not raw_anchors:
        raise IngestionError("读后发现至少需要一项章节、表、符号或配置键 --anchor")
    unknown_sources = [item for item in sources if item not in group["members"]]
    if unknown_sources:
        raise IngestionError("读后发现来源不属于该材料组：" + ", ".join(unknown_sources))
    anchors: list[str] = []
    anchor_sources: list[str] = []
    for anchor in raw_anchors:
        ref, separator, locator = anchor.partition("#")
        if separator:
            if not ref.strip() or not locator.strip():
                raise IngestionError("--anchor 必须包含非空来源和定位")
            normalized = f"{ref.strip()}#{locator.strip()}"
            anchor_sources.append(ref.strip())
        else:
            if len(sources) != 1:
                raise IngestionError(
                    "发现有多个来源时，--anchor 必须使用 <source-ref>#<章节、表、符号或配置键>"
                )
            normalized = f"{sources[0]}#{anchor}"
            anchor_sources.append(sources[0])
        anchors.append(normalized)
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


def reopen_plan(args: argparse.Namespace) -> int:
    """Return a completed writing pass to planning without rereading materials."""
    root, case = load_case(args.cases_root, args.case_id)
    ensure_complete(case)
    if case["stage"] not in {"reviewing", "publish_ready"}:
        raise IngestionError("只在全部知识主题完成后的语义复核或最终审查阶段重新打开知识目录")
    previous = case.get("plan_review", {})
    reason = args.reason.strip()
    case["plan_review"] = {
        "passed": False,
        "lenses": previous.get("lenses", {}),
        "not_applicable": previous.get("not_applicable", {}),
        "issues": [reason],
        "reviewed_at": previous.get("reviewed_at"),
    }
    case["stage"] = "planning"
    case["plan_reopen_reason"] = reason
    case["cursor"] = {"item_type": None, "item_id": None}
    case["next_action"] = (
        "只补充最终审查暴露的知识主题或导航落点，再运行 plan-review；"
        "不重新读取已经审视完成的材料"
    )
    save_case(root, case)
    print(
        json.dumps(
            {
                "stage": case["stage"],
                "reason": reason,
                "last_review_issues": case.get("last_review_issues", []),
                "next": case["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def add_topic(args: argparse.Namespace) -> int:
    root, case = load_case(args.cases_root, args.case_id)
    ensure_complete(case)
    if case["stage"] != "planning":
        raise IngestionError("只有材料发现完成后才能规划知识主题")
    validate_id(args.topic_id, "topic id", UNIT_ID_RE)
    path = normalize_knowledge_path(args.path)
    canonical_path = path.removeprefix("draft/")
    existed_in_baseline = canonical_path in baseline_paths(case)
    if args.action == "create" and existed_in_baseline:
        raise IngestionError(
            f"create 只能用于父知识中不存在的落点；现有页面请使用 update 或 merge：{path}"
        )
    if args.action in {"update", "merge"} and not existed_in_baseline:
        raise IngestionError(
            f"{args.action} 只能用于父知识中已经存在的落点；新页面请使用 create：{path}"
        )
    finding_ids = list(dict.fromkeys(args.finding))
    parent_reconciliation = (
        args.action == "update"
        and bool(case.get("plan_reopen_reason"))
    )
    if not finding_ids and args.action != "view" and not parent_reconciliation:
        raise IngestionError("知识主题至少关联一个读后发现；发布前父级语义同步需先运行 plan-reopen")
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
    canonical_path = topic["path"].removeprefix("draft/")
    baseline = baseline_paths(case)
    if topic["action"] == "create" and canonical_path in baseline:
        raise IngestionError(f"create 落点已经存在于父知识：{topic['path']}")
    if topic["action"] in {"update", "merge"}:
        original = baseline.get(canonical_path)
        if original is None:
            raise IngestionError(f"{topic['action']} 落点不在父知识中：{topic['path']}")
        if digest_bytes(path.read_bytes()) == original["sha256"]:
            raise IngestionError(
                f"{topic['action']} 已声明，但候选正文与父知识完全相同：{topic['path']}"
            )
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
    terms = normalize_query_terms(args.query)
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
    question["candidate_queue"] = prioritize_fixed_run_evidence(
        root, case, question, question["candidate_queue"]
    )
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
        contracts = contract_candidates(case, item["ref"])
        output_packet.append(
            {
                **item,
                "absolute_path": str(Path(sources[source_id]["root"]) / relative),
                **({"contract_candidates": contracts} if contracts else {}),
            }
        )
    print(
        json.dumps(
            {
                "question": {"id": question["id"], "text": question["text"]},
                "query_terms": question["query_terms"],
                "packet": output_packet,
                "remaining_relevant_candidates": len(question["candidate_queue"]),
                "reading_rule": (
                    "优先只读取本 packet；读完立即更新规范知识并 record，不维护逐文件覆盖表。"
                    "代码回写中，固定 diff 或报告明确指向的其他冻结文件可以直接登记，"
                    "但不得借此无界通读来源。"
                    "run_evidence 先核对版本、环境和覆盖，足够时不要机械重跑。"
                    "当问题需要完整数据契约且 packet 给出 contract_candidates 时，"
                    "先运行 contract-inspect，再把返回字段完整写入规范知识。"
                ),
                "next": question["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def inspect_contract(args: argparse.Namespace) -> int:
    """Freeze a machine-readable source contract that must survive writeback."""
    root, case = load_case(args.cases_root, args.case_id)
    question = question_by_id(case, args.question_id)
    available = {
        item["ref"] for item in question.get("active_packet", [])
    } | {
        item["ref"] for item in question.get("evidence", [])
    }
    if args.source not in available:
        choices = ", ".join(sorted(available)) or "（先运行 next 取得包含契约的来源）"
        raise IngestionError(
            f"契约来源必须属于当前 packet 或本问题已登记证据：{args.source}；可用来源：{choices}"
        )
    contracts = {
        item["symbol"]: item
        for item in contract_candidates(case, args.source)
    }
    contract = contracts.get(args.symbol)
    if contract is None:
        choices = ", ".join(contracts) or "（该来源没有当前支持的 Python 注解类）"
        raise IngestionError(f"来源中没有可检查契约 {args.symbol}；可选：{choices}")
    frozen = {
        "source": args.source,
        "symbol": contract["symbol"],
        "field_count": contract["field_count"],
        "fields": contract["fields"],
        "purpose": args.purpose.strip(),
        "inspected_at": utc_now(),
    }
    existing = next(
        (
            item for item in question.setdefault("contracts", [])
            if item["source"] == frozen["source"] and item["symbol"] == frozen["symbol"]
        ),
        None,
    )
    if existing:
        if any(existing.get(key) != frozen[key] for key in ("field_count", "fields", "purpose")):
            raise IngestionError("同一来源契约已经冻结且内容不同；来源变化时请新建摄入案")
        frozen = existing
        already = True
    else:
        question["contracts"].append(frozen)
        question["updated_at"] = utc_now()
        save_case(root, case)
        already = False
    print(
        json.dumps(
            {
                "contract": frozen,
                "already_inspected": already,
                "writing_rule": (
                    f"在本问题的规范知识中逐项保留这 {frozen['field_count']} 个字段，"
                    "并说明粒度、嵌套对象、状态或兼容边界；check-unit 会核对字段名。"
                ),
                "next": "读取字段语义和嵌套契约，更新正文后运行 record",
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
    recorded = {item["ref"]: item for item in question["evidence"]}
    used = list(dict.fromkeys(args.source))
    if len(used) > 12:
        raise IngestionError("一次 record 最多登记 12 项直接来源；请按读者问题收束证据")
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
    manifest_by_ref = {
        source_ref(item["source_id"], item["path"]): item for item in read_manifest(root)
    }
    unknown = [
        item for item in used
        if item not in active
        and item not in recorded
        and not (case.get("mode") == "writeback" and item in manifest_by_ref)
    ]
    if unknown:
        available_refs = list(dict.fromkeys([*active, *recorded]))
        available = ", ".join(available_refs) or "（当前没有活动小批，请先 next）"
        raise IngestionError(
            "以下 --source 不在当前小批或本问题已登记证据中，不能登记："
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
        if ref in recorded:
            continue
        path = resolve_source(case, ref)
        actual = digest_bytes(path.read_bytes())
        manifest_item = manifest_by_ref[ref]
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


def contains_template_placeholder(text: str) -> bool:
    """Find unfilled prose/template markers without rejecting literal code examples."""
    without_fenced_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    without_code = re.sub(r"`[^`\n]+`", "", without_fenced_code)
    return bool(PLACEHOLDER_RE.search(without_code))


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
    if len(expected_paths) > MAX_KNOWLEDGE_UNITS_PER_QUESTION:
        errors.append(
            f"一个问题不能依赖超过 {MAX_KNOWLEDGE_UNITS_PER_QUESTION} 篇规范知识页"
        )
    linked = view_targets(root)
    source_index_targets = markdown_link_targets(
        root / "draft" / "knowledge" / "sources" / "index.md"
    )
    for unit in question["expected_units"]:
        path = root / unit["path"]
        if not path.is_file():
            errors.append(f"知识单元尚未形成：{unit['path']}")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 400:
            errors.append(f"知识单元内容过薄：{unit['path']}")
        if contains_template_placeholder(text):
            errors.append(f"知识单元仍含模板占位符：{unit['path']}")
        if unit["path"].startswith("draft/knowledge/views/"):
            pass
        elif unit["path"].startswith("draft/knowledge/sources/"):
            if path.resolve() not in source_index_targets:
                errors.append(f"来源导航尚未链接来源知识单元：{unit['path']}")
        elif path.resolve() not in linked:
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
    knowledge_text = "\n".join(
        (root / path).read_text(encoding="utf-8")
        for path in question.get("knowledge_paths", [])
        if (root / path).is_file()
    )
    for contract in question.get("contracts", []):
        missing_fields = [
            field for field in contract.get("fields", [])
            if not re.search(rf"(?<![A-Za-z0-9_]){re.escape(field)}(?![A-Za-z0-9_])", knowledge_text)
        ]
        if missing_fields:
            errors.append(
                f"源码契约 {contract['symbol']} 的字段未完整进入规范知识："
                + ", ".join(missing_fields)
            )
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
        fixed_reports = [
            item["ref"] for item in question.get("evidence", [])
            if candidate_role(item["ref"]) == "run_evidence"
        ]
        if not passed_runs and not fixed_reports:
            errors.append(
                "本问题要求当前行为证据，但既没有已核对的固定来源验证报告，"
                "也没有通过的隔离运行证据"
            )
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


CHINESE_COUNT = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}


def navigation_semantic_errors(root: Path, changed_paths: set[str]) -> list[str]:
    """Catch a few cheap navigation contradictions exposed by real trials."""
    errors: list[str] = []
    for relative in sorted(changed_paths):
        if not relative.startswith("knowledge/") or not relative.endswith(".md"):
            continue
        path = root / "draft" / relative
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            match = re.search(r"上面([一二三四五六七八九十]|\d+)项", line)
            if match:
                expected = CHINESE_COUNT.get(match.group(1), int(match.group(1)) if match.group(1).isdigit() else -1)
                cursor = index - 1
                while cursor >= 0 and not lines[cursor].strip():
                    cursor -= 1
                actual = 0
                while cursor >= 0 and re.match(r"^\s*[-*+]\s+", lines[cursor]):
                    actual += 1
                    cursor -= 1
                if actual and actual != expected:
                    errors.append(
                        f"导航数量表述与紧邻列表不一致：{relative}:{index + 1} "
                        f"写 {expected} 项，实际 {actual} 项"
                    )
        previous: tuple[str, int] | None = None
        for index, line in enumerate(lines):
            match = re.match(r"^(\s*)(\d+)\.\s+", line)
            if not match:
                if line.strip():
                    previous = None
                continue
            current = (match.group(1), int(match.group(2)))
            if previous == current and current[1] != 1:
                errors.append(
                    f"有序列表出现重复编号：{relative}:{index + 1} 重复 {current[1]}"
                )
            previous = current
    return errors


def writeback_review_errors(root: Path, case: dict[str, Any]) -> list[str]:
    """Validate the reusable boundaries of a code-to-knowledge candidate."""
    errors: list[str] = []
    identity = case.get("writeback") or {}
    relationship = identity.get("relationship")
    if not relationship:
        errors.append("尚未用 identity-set 判断代码来源与既有系统知识的身份关系")
    elif relationship == "uncertain":
        errors.append("系统身份仍为 uncertain；取得直接证据后改为 same_system 或 new_system")
    impact_review = case.get("writeback_impact_review") or {}
    if not impact_review.get("passed"):
        errors.append("代码变化影响尚未通过 impact-review：用户结果、当前态、语义、软件、兼容、公共能力、证据和导航未闭合")

    for question in case["questions"]:
        report = check_question(root, case, question)
        errors.extend(f"{question['id']}：{item}" for item in report["errors"])

    changes = candidate_changes(root, case)
    if changes["deleted"]:
        errors.append(
            "代码回写不得顺带删除父知识文件：" + ", ".join(changes["deleted"])
        )
    errors.extend(incremental_parent_preservation_errors(root, case, changes))
    errors.extend(incremental_entrypoint_errors(case, changes))
    errors.extend(compatibility_mechanism_errors(root, case))
    stale_candidates = stale_current_fact_candidates(root, case)
    if stale_candidates:
        errors.append(
            "固定提交已经替代以下数值，但候选仍把旧值写成当前事实；请原位更新，"
            "若确属历史则明确版本/时间范围："
            + "；".join(
                f"{item['path']}:{item['line_number']} ({item['old']} -> {item['new']}) {item['line']}"
                for item in stale_candidates[:12]
            )
        )

    changed = set(changes["added"] + changes["modified"] + changes["deleted"])
    errors.extend(navigation_semantic_errors(root, changed))
    planned_units = {
        unit["path"].removeprefix("draft/")
        for question in case["questions"]
        for unit in question["expected_units"]
    }
    unplanned = sorted(
        path for path in changes["added"] + changes["modified"]
        if governed_writeback_path(path) and path not in planned_units
    )
    if unplanned:
        errors.append(
            "以下规范正文或产品视图发生变化但没有读者问题/知识单元负责："
            + ", ".join(unplanned)
        )

    source_path = (identity.get("source_path") or "").removeprefix("draft/")
    system_path = (identity.get("system_path") or "").removeprefix("draft/")
    source_id = identity.get("source_id")
    source = next((item for item in case.get("sources", []) if item.get("id") == source_id), None)
    if source and source_path:
        source_document = root / "draft" / source_path
        if source_document.is_file():
            text = source_document.read_text(encoding="utf-8")
            required_identity_values = [source.get("root")]
            if source.get("git"):
                required_identity_values.append(source["git"].get("commit"))
                required_identity_values.append(source["git"].get("branch"))
            missing_identity_values = [value for value in required_identity_values if value and value not in text]
            if missing_identity_values:
                errors.append(
                    "来源规范页没有写入冻结来源的当前路径/branch/commit："
                    + ", ".join(missing_identity_values)
                )
    if relationship == "new_system":
        for path, label in ((source_path, "独立来源页"), (system_path, "独立系统页")):
            if path and path not in changes["added"]:
                errors.append(f"new_system 的{label}尚未作为新规范对象形成：{path}")
            if path and path not in planned_units:
                errors.append(f"new_system 的{label}没有知识单元负责：{path}")
        for path, label in (
            ("knowledge/sources/index.md", "来源导航"),
            ("knowledge/systems/index.md", "系统导航"),
        ):
            if path not in changed:
                errors.append(f"new_system 尚未同步{label}：{path}")
    elif relationship == "same_system":
        for path, label in ((source_path, "来源页"), (system_path, "系统页")):
            if path and path not in changes["modified"]:
                errors.append(f"same_system 的既有{label}尚未更新：{path}")

    if not any(path.startswith("knowledge/domains/") and not path.endswith("/index.md") for path in changed):
        errors.append("代码事实尚未原位进入受影响的业务、数据或规则知识")
    software_units = {
        unit["path"].removeprefix("draft/")
        for question in case["questions"]
        for unit in question["expected_units"]
        if unit["kind"] == "software"
    }
    if not software_units or not (software_units & changed):
        errors.append("尚未形成由 software 知识单元负责的系统结构、调用链或修改入口更新")
    if not any(
        path.startswith("knowledge/views/") and not path.endswith("/index.md")
        for path in changed
    ):
        errors.append("产品视图尚未同步受影响知识的稳定入口")
    return list(dict.fromkeys(errors))


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
    generate_complete_source_index(root, case)
    changes = candidate_changes(root, case)
    views = sorted(
        path for path in (root / "draft" / "knowledge" / "views").rglob("*.md")
        if path.name != "index.md"
    )
    lines = [
        "# 知识摄入审查",
        "",
        f"> **目标：** {case['goal']}",
        f"> **目标读者：** {case['target_reader']}",
        f"> **当前阶段：** {case['stage']}",
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
    if case.get("last_review_issues"):
        lines.extend(["", "## 当前审查未通过的原因", ""])
        lines.extend(f"- {item}" for item in case["last_review_issues"])
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

    lines.extend(
        [
            "",
            "## 父知识到候选知识的变化",
            "",
            f"- **父知识指纹：** `{case['baseline']['fingerprint']}`；"
            f"**父版本文件：** {case['baseline']['file_count']} 个。",
            f"- **实际变化：** 新增 {len(changes['added'])} 个，修改 {len(changes['modified'])} 个，"
            f"删除 {len(changes['deleted'])} 个。",
            "",
        ]
    )
    for label, key in (("新增", "added"), ("修改", "modified"), ("删除", "deleted")):
        values = changes[key]
        if values:
            lines.append(f"- **{label}：** " + "、".join(f"`{item}`" for item in values))
    if not any(changes.values()):
        lines.append("- 候选与父知识尚无内容变化。")

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


def generate_complete_source_index(root: Path, case: dict[str, Any]) -> None:
    """Build the user-facing provenance view from already validated finding state."""
    target = root / "draft" / "knowledge" / "sources" / "index.md"
    incremental = bool(case.get("baseline", {}).get("substantive_file_count", 0))
    section_start = f"<!-- omni-brain:provenance:{case['id']}:start -->"
    section_end = f"<!-- omni-brain:provenance:{case['id']}:end -->"
    if incremental and target.is_file():
        previous = target.read_text(encoding="utf-8")
        if section_start in previous:
            prefix, remainder = previous.split(section_start, 1)
            if section_end not in remainder:
                raise IngestionError(
                    f"来源目录中的本案增量标记不完整：{case['id']}"
                )
            _, suffix = remainder.split(section_end, 1)
            previous = (prefix.rstrip() + suffix).rstrip()
        # Legacy markers belong to an earlier published increment.  They are
        # deliberately left untouched; replacing them would erase parent
        # provenance when a second increment is prepared.
        lines = [*previous.splitlines(), "", section_start, ""]
    else:
        lines = [
            "# 直接材料与结论定位",
            "",
            "本页由摄入工作台从已校验的来源、读后结论和正文落点重建。它只用于追溯，不能代替规范正文。",
            "",
        ]
    lines.extend([
        "## 本次摄入的材料范围" if incremental else "## 固定材料范围",
        "",
        "| 来源 ID | 固定位置 | 文件数 | 指纹 |",
        "|---|---|---:|---|",
    ])
    for source in case["sources"]:
        lines.append(
            f"| `{source['id']}` | `{source['root']}` | {source['file_count']} | `{source['fingerprint']}` |"
        )
    if not case["sources"]:
        lines.append("| 无 | 无 | 0 | 无 |")

    lines.extend(["", "## 本次结论与规范知识落点" if incremental else "## 规范知识与直接材料", ""])
    for topic in case["topics"]:
        topic_path = root / topic["path"]
        topic_link = relative_link(target, topic_path) if topic_path.is_file() else topic["path"]
        lines.extend(
            [
                f"### [{topic['title']}]({topic_link})",
                "",
                "| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |",
                "|---|---|---|---|",
            ]
        )
        sections = topic.get("finding_sections", {})
        for finding_id in topic["finding_ids"]:
            finding = finding_by_id(case, finding_id)
            content = finding["content"].replace("|", "\\|")
            anchors = "<br>".join(
                f"`{item.replace('|', chr(92) + '|')}`"
                for item in finding.get("anchors", [])
            ) or "未登记精确定位"
            section = sections.get(finding_id, "写作中").replace("|", "\\|")
            lines.append(
                f"| {finding_id}：{content} | `{finding['reality']}` | {anchors} | {section} |"
            )
        if not topic["finding_ids"]:
            lines.append("| 无 | 无 | 无 | 无 |")
        lines.append("")
    if not case["topics"]:
        lines.append("知识目录尚未形成；当前只能在 `review.md` 查看已登记的直接材料结论。")
        lines.append("")

    lines.extend(
        [
            "## 使用边界",
            "",
            "- 路径和定位来自摄入开始时冻结并在登记时重新校验的来源；来源变化后必须重新摄入。",
            "- 当前实现、当前决定、目标设计、历史、冲突和未知不能互相替代。",
            "- 表中的正文落点只证明写作者完成了逐项对照，不自动证明业务结论正确；发布仍需人工审查。",
            "",
        ]
    )
    if incremental:
        lines.extend([section_end, ""])
    atomic_write_text(target, "\n".join(lines))


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
        f"> **目标：** {case['goal']}",
        f"> **目标读者：** {case['target_reader']}",
        f"> **当前阶段：** {case['stage']}",
        "> 正式知识尚未修改；本页只汇总候选知识、事实边界和需要人工决定的事项。",
        "",
    ]
    if case.get("mode") == "writeback":
        identity = case.get("writeback") or {}
        changes = candidate_changes(root, case)
        lines.extend(
            [
                "## 代码来源与知识身份",
                "",
                f"- **关系：** `{identity.get('relationship') or '尚未判断'}`。",
                f"- **判断依据：** {identity.get('reason') or '尚未登记'}。",
                f"- **来源规范页：** `{identity.get('source_path') or '尚未规划'}`。",
                f"- **系统规范页：** `{identity.get('system_path') or '尚未规划'}`。",
                "- **父知识到候选：** "
                f"新增 {len(changes['added'])}、修改 {len(changes['modified'])}、"
                f"删除 {len(changes['deleted'])} 个文件。",
                "",
            ]
        )
        if case.get("last_review_issues"):
            lines.extend(["## 当前审查未通过的原因", ""])
            lines.extend(f"- {item}" for item in case["last_review_issues"])
            lines.append("")
        impact_review = case.get("writeback_impact_review") or {}
        lines.extend(["## 代码变化影响", ""])
        if impact_review.get("passed"):
            for impact in sorted(impact_review.get("impacts", {})):
                refs = "、".join(f"`{item}`" for item in impact_review["impacts"][impact])
                lines.append(f"- **{impact}：** {refs}")
            for impact in sorted(impact_review.get("not_applicable", {})):
                lines.append(f"- **{impact}：** 不适用；{impact_review['not_applicable'][impact]}")
        else:
            lines.append("- 尚未通过 `impact-review`；不能只凭页面已修改进入发布审查。")
        lines.append("")
    lines.extend(["## 从这里开始看内容", ""])
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
    lines.extend(["", "## 直接依据与验证证据", ""])
    evidence_refs = {
        evidence["ref"]
        for question in case["questions"]
        for evidence in question["evidence"]
    }
    lines.append(f"- 已登记不重复直接来源：{len(evidence_refs)} 项。")
    fixed_reports = sorted(
        ref for ref in evidence_refs if candidate_role(ref) == "run_evidence"
    )
    if fixed_reports:
        lines.append(
            "- 已核对固定来源中的验证记录："
            + "、".join(f"`{ref}`" for ref in fixed_reports)
            + "。其版本、环境、覆盖范围和具体结果仍应在对应规范知识中说明。"
        )
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
        if fixed_reports:
            lines.append(
                "- 本案没有新增现场隔离运行；已有固定验证记录足以覆盖的问题无需机械重跑。"
            )
        else:
            lines.append("- 本案没有登记固定验证记录，也没有新增现场隔离运行。")
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
        lines.append(
            "- 当前问题状态没有登记会阻止本案继续的外部补知项；"
            "候选知识正文保留的长期未知、来源冲突和生产边界仍须随对应规范页审查。"
        )
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
    if case.get("mode") == "writeback":
        errors = writeback_review_errors(root, case)
        case["last_review_issues"] = errors
        if errors:
            case["stage"] = "reviewing"
            case["next_action"] = (
                "按 review.md 中的内容、身份、父知识保持和导航问题修正候选；"
                "只补受影响来源，不改写已确认的系统身份"
            )
        else:
            case["stage"] = "publish_ready"
            case["next_action"] = "请用户审查候选知识与 review.md，决定发布或退回"
        save_case(root, case)
        generate_review(root, case)
        print(
            json.dumps(
                {
                    "review": str(root / "review.md"),
                    "ready": not errors,
                    "errors": errors,
                    "candidate_changes": candidate_changes(root, case),
                    "next": case["next_action"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if not errors else 1
    if case.get("mode") == "complete":
        ensure_complete(case)
        errors: list[str] = []
        if case["stage"] not in {"reviewing", "publish_ready"}:
            errors.append(f"当前仍处于 {case['stage']}，尚未完成全部知识主题")
        unfinished = [item["id"] for item in case["topics"] if item["status"] != "ready"]
        if unfinished:
            errors.append("以下知识主题尚未完成：" + ", ".join(unfinished))
        changes = candidate_changes(root, case)
        if changes["deleted"]:
            errors.append(
                "当前增量切片不允许删除父知识文件；请恢复或提交新的退役方案："
                + ", ".join(changes["deleted"])
            )
        errors.extend(incremental_parent_preservation_errors(root, case, changes))
        errors.extend(incremental_entrypoint_errors(case, changes))
        planned = {topic["path"].removeprefix("draft/") for topic in case["topics"]}
        planned.update(
            path.removeprefix("draft/")
            for topic in case["topics"]
            for path in topic["view_paths"]
        )
        unplanned = sorted(
            path for path in changes["added"] + changes["modified"]
            if governed_candidate_path(path) and path not in planned
        )
        if unplanned:
            errors.append(
                "以下正文或产品视图发生变化但没有知识主题负责：" + ", ".join(unplanned)
            )
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
        case["last_review_issues"] = errors
        if not errors:
            case["stage"] = "publish_ready"
            case["next_action"] = "请用户审查候选知识、产品视图和 review.md，决定发布或退回"
        else:
            case["stage"] = "reviewing"
            case["cursor"] = {"item_type": None, "item_id": None}
            case["next_action"] = (
                "先按 last_review_issues 修正候选；若问题来自漏规划页面或导航，"
                "运行 plan-reopen 回到目录规划，不重读材料"
            )
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
            "last_review_issues": case.get("last_review_issues", []),
            "baseline": {
                "file_count": case["baseline"]["file_count"],
                "substantive_file_count": case["baseline"]["substantive_file_count"],
                "fingerprint": case["baseline"]["fingerprint"],
            },
            "candidate_changes": candidate_changes(root, case),
            "review": str(root / "review.md"),
            "next": case["next_action"],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    payload = {
        "case_id": case["id"],
        "mode": case.get("mode", "focused"),
        "stage": case.get("stage", "focused"),
        "goal": case["goal"],
        "target_reader": case["target_reader"],
        "writeback": case.get("writeback"),
        "writeback_impact_review": case.get("writeback_impact_review"),
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
        "candidate_changes": candidate_changes(root, case),
        "last_review_issues": case.get("last_review_issues", []),
        "review": str(root / "review.md"),
        "next": case["next_action"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-root", type=Path, default=default_cases_root())
    subparsers = parser.add_subparsers(dest="action", required=True)

    start = subparsers.add_parser("start", help="创建聚焦、代码回写或宽范围完整摄入案和后台来源基线")
    start.add_argument("case_id")
    start.add_argument("--mode", choices=sorted(INGESTION_MODES), default="focused")
    start.add_argument("--goal", required=True)
    start.add_argument("--reader", required=True)
    start.add_argument("--source", action="append", default=[])
    start.add_argument("--question", action="append", default=[])
    start.add_argument("--boundary", action="append", default=[])
    start.set_defaults(func=start_case)

    identity = subparsers.add_parser("identity-set", help="判断代码来源与既有系统知识的身份关系")
    identity.add_argument("case_id")
    identity.add_argument("--relationship", choices=sorted(SYSTEM_RELATIONSHIPS), required=True)
    identity.add_argument("--reason", required=True)
    identity.add_argument("--source-path")
    identity.add_argument("--system-path")
    identity.add_argument("--source-id")
    identity.add_argument("--parent-commit")
    identity.set_defaults(func=set_writeback_identity)

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
    unit.add_argument(
        "--kind",
        choices=("identity", "business", "data", "software", "compatibility", "shared", "run", "navigation", "other"),
        required=True,
    )
    unit.add_argument("--path", required=True)
    unit.add_argument("--require-run", action="store_true")
    unit.set_defaults(func=plan_unit)

    impact = subparsers.add_parser(
        "impact-review",
        help="把代码变化影响映射到计划知识单元，并显式处理兼容与公共能力",
    )
    impact.add_argument("case_id")
    impact.add_argument("--impact", action="append", default=[])
    impact.add_argument("--not-applicable", action="append", default=[])
    impact.set_defaults(func=review_writeback_impacts)

    next_command = subparsers.add_parser("next", help="取得当前材料组、知识主题或聚焦问题的小批来源")
    next_command.add_argument("case_id")
    next_command.add_argument("question_id", nargs="?")
    next_command.add_argument("--query", action="append", default=[])
    next_command.add_argument("--limit", type=int, choices=range(1, 9), default=6)
    next_command.set_defaults(func=next_sources)

    contract = subparsers.add_parser(
        "contract-inspect",
        help="冻结一个机器可读源码契约，并在知识单元检查中防止字段丢失",
    )
    contract.add_argument("case_id")
    contract.add_argument("question_id")
    contract.add_argument("--source", required=True)
    contract.add_argument("--symbol", required=True)
    contract.add_argument("--purpose", required=True)
    contract.set_defaults(func=inspect_contract)

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

    plan_reopen = subparsers.add_parser("plan-reopen", help="最终审查发现漏规划页面或视图时返回目录规划")
    plan_reopen.add_argument("case_id")
    plan_reopen.add_argument("--reason", required=True)
    plan_reopen.set_defaults(func=reopen_plan)

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
            "identity-set", "question-add", "plan-unit", "impact-review", "next", "contract-inspect", "finding-add", "record-material", "material-reopen", "plan-reopen",
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
