#!/usr/bin/env python3
"""Record deterministic, recoverable observations of task-local Git sources.

This tool owns source identity, scope, version, coverage, evidence manifests, and
incremental state. It deliberately does not summarize source content, answer task
questions, or advance knowledge-readiness gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised in real environments
    raise SystemExit(
        "缺少依赖 PyYAML。请按 environment.yml 安装环境，或运行："
        "python -m pip install 'pyyaml>=6.0.1'"
    ) from exc


SCHEMA_VERSION = "0.1"
TOOL_VERSION = "0.1"
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
RUN_ID_PATTERN = re.compile(r"^[0-9]{8}T[0-9]{12}Z-[a-f0-9]{8}$")
SOURCE_RUN_URI_PATTERN = re.compile(
    r"^source-run://(?P<case>[a-z0-9][a-z0-9-]{0,62})/"
    r"(?P<source>[a-z0-9][a-z0-9-]{0,62})/(?P<run>[0-9A-Za-z._-]+)$"
)
AUTHORITIES = {"primary", "secondary", "contextual"}


class SourceRunError(Exception):
    """A user-actionable source-run error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_cases_root() -> Path:
    return Path(__file__).resolve().parents[1] / "workspaces" / "task-cases"


def default_workspace() -> Path:
    return Path(__file__).resolve().parents[1]


def validate_id(value: str, label: str) -> None:
    if not ID_PATTERN.fullmatch(value):
        raise SourceRunError(
            f"{label} 只能包含小写字母、数字和连字符，长度 1-63，且必须以字母或数字开头"
        )


def ensure_case(cases_root: Path, case_id: str) -> Path:
    validate_id(case_id, "case id")
    directory = cases_root.resolve() / case_id
    if not (directory / "case.yaml").is_file():
        raise SourceRunError(f"任务案不存在：{directory / 'case.yaml'}")
    return directory


def source_directory(cases_root: Path, case_id: str, source_id: str) -> Path:
    validate_id(source_id, "source id")
    return ensure_case(cases_root, case_id) / "source-runs" / source_id


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


def atomic_write_yaml(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(
        path,
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=100),
    )


def load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise SourceRunError(f"{label} 不存在：{path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise SourceRunError(f"无法读取 {label} {path}：{exc}") from exc
    if not isinstance(value, dict):
        raise SourceRunError(f"{label} 顶层必须是 YAML mapping：{path}")
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def normalize_source_root(workspace: Path, root_value: str) -> tuple[Path, str]:
    declared = Path(root_value)
    if declared.is_absolute():
        raise SourceRunError("来源 root 必须是相对 workspace 的路径，绝对路径属于越界输入")
    workspace = workspace.resolve()
    resolved = (workspace / declared).resolve()
    if not is_inside(resolved, workspace):
        raise SourceRunError("来源 root 越界：必须位于已授权 workspace 内")
    if not resolved.is_dir():
        raise SourceRunError(f"来源 root 不是目录：{resolved}")
    top_level = run_git(resolved, "rev-parse", "--show-toplevel", check=False)
    if top_level.returncode != 0:
        raise SourceRunError(f"来源 root 不是 Git 仓库：{resolved}")
    try:
        git_root = Path(top_level.stdout.strip()).resolve()
    except OSError as exc:
        raise SourceRunError(f"无法解析 Git root：{exc}") from exc
    if git_root != resolved:
        raise SourceRunError(
            f"首轮 local_git 要求 root 为 Git 顶层目录；当前顶层为 {git_root}"
        )
    relative = resolved.relative_to(workspace)
    normalized = "." if not relative.parts else relative.as_posix()
    return resolved, normalized


def normalize_include_path(source_root: Path, value: str) -> str:
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise SourceRunError(f"include path 越界或无效：{value}")
    normalized_parts = tuple(part for part in candidate.parts if part not in {"", "."})
    if not normalized_parts:
        raise SourceRunError(f"include path 必须指向文件：{value}")
    normalized = PurePosixPath(*normalized_parts).as_posix()
    current = source_root
    for part in normalized_parts:
        current = current / part
        if current.is_symlink():
            raise SourceRunError(f"include path 包含符号链接，拒绝潜在逃逸：{normalized}")
    resolved = (source_root / normalized).resolve(strict=False)
    if not is_inside(resolved, source_root):
        raise SourceRunError(f"include path 越界：{normalized}")
    if resolved.exists() and resolved.is_dir():
        raise SourceRunError(f"首轮 include path 只允许文件，不允许目录：{normalized}")
    return normalized


def run_git(
    repository: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise SourceRunError(f"Git 命令失败（git {' '.join(arguments)}）：{detail}")
    return result


def source_config_payload(
    source_id: str,
    kind: str,
    root: str,
    authority: str,
    purpose: str,
    includes: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": source_id,
        "kind": kind,
        "root": root,
        "authority": authority,
        "purpose": purpose,
        "scope": {"include_paths": includes},
        "access": "read_only",
    }


def validate_source_instance(source: dict[str, Any]) -> None:
    scope = source.get("scope")
    includes = scope.get("include_paths") if isinstance(scope, dict) else None
    if not isinstance(includes, list) or not all(isinstance(item, str) for item in includes):
        raise SourceRunError("SourceInstance.scope.include_paths 必须是字符串列表")
    payload = source_config_payload(
        str(source.get("id", "")),
        str(source.get("kind", "")),
        str(source.get("root", "")),
        str(source.get("authority", "")),
        str(source.get("purpose", "")),
        includes,
    )
    if source.get("config_fingerprint") != digest_value(payload):
        raise SourceRunError("SourceInstance config_fingerprint 校验失败")


def source_state(source_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id,
        "last_complete_run_id": None,
        "last_scoped_fingerprint": None,
        "last_config_fingerprint": None,
        "updated_at": None,
    }


def register_source(args: argparse.Namespace) -> int:
    cases_root = args.cases_root.resolve()
    workspace = args.workspace.resolve()
    source_dir = source_directory(cases_root, args.case_id, args.source_id)
    if args.kind != "local_git":
        raise SourceRunError("首轮只支持 kind=local_git")
    if args.authority not in AUTHORITIES:
        raise SourceRunError(f"无效 authority：{args.authority}")
    source_root, normalized_root = normalize_source_root(workspace, args.source_root)
    includes = sorted(
        {normalize_include_path(source_root, value) for value in args.includes}
    )
    if not includes:
        raise SourceRunError("至少需要一个 --include")

    payload = source_config_payload(
        args.source_id,
        args.kind,
        normalized_root,
        args.authority,
        args.purpose.strip(),
        includes,
    )
    fingerprint = digest_value(payload)
    source_path = source_dir / "source.yaml"
    existed = source_path.exists()
    if existed:
        existing = load_yaml(source_path, "SourceInstance")
        validate_source_instance(existing)
        if existing.get("config_fingerprint") == fingerprint:
            print(
                json.dumps(
                    {
                        "case_id": args.case_id,
                        "source_id": args.source_id,
                        "created": False,
                        "config_fingerprint": fingerprint,
                        "path": str(source_path),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if not args.replace:
            raise SourceRunError(
                "SourceInstance 配置已存在且不同；如需显式改变范围请使用 --replace"
            )
        registered_at = existing.get("registered_at") or utc_now()
    else:
        registered_at = utc_now()

    source = {
        **payload,
        "registered_at": registered_at,
        "updated_at": utc_now(),
        "config_fingerprint": fingerprint,
    }
    source_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_yaml(source_path, source)
    state_path = source_dir / "state.yaml"
    if not state_path.exists():
        atomic_write_yaml(state_path, source_state(args.source_id))
    print(
        json.dumps(
            {
                "case_id": args.case_id,
                "source_id": args.source_id,
                "created": not existed,
                "replaced": existed,
                "config_fingerprint": fingerprint,
                "path": str(source_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def create_run_id(source_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    suffix = hashlib.sha256(f"{source_id}:{timestamp}:{os.getpid()}".encode()).hexdigest()[:8]
    return f"{timestamp}-{suffix}"


def write_manifest(path: Path, entries: list[dict[str, Any]]) -> str:
    content = "".join(
        json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in entries
    )
    path.write_text(content, encoding="utf-8")
    return digest_bytes(content.encode("utf-8"))


def file_snapshot_path(staging: Path, relative_path: str) -> tuple[Path, str]:
    snapshot = PurePosixPath("raw") / PurePosixPath(relative_path)
    target = staging.joinpath(*snapshot.parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target, snapshot.as_posix()


def observe_path(repository: Path, relative_path: str, staging: Path) -> dict[str, Any]:
    normalized = normalize_include_path(repository, relative_path)
    file_path = repository / normalized
    if not file_path.exists():
        return {
            "path": normalized,
            "state": "missing",
            "git_blob": None,
            "sha256": None,
            "bytes": None,
            "snapshot": None,
        }
    try:
        content = file_path.read_bytes()
    except OSError:
        return {
            "path": normalized,
            "state": "unreadable",
            "git_blob": None,
            "sha256": None,
            "bytes": None,
            "snapshot": None,
        }

    tracked = (
        run_git(repository, "ls-files", "--error-unmatch", "--", normalized, check=False).returncode
        == 0
    )
    status = run_git(
        repository,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        normalized,
    ).stdout.strip()
    if tracked and not status:
        state = "tracked_clean"
        git_blob = run_git(repository, "rev-parse", f"HEAD:{normalized}").stdout.strip()
        snapshot = None
    else:
        state = "tracked_dirty" if tracked else "untracked"
        git_blob = None
        snapshot_file, snapshot = file_snapshot_path(staging, normalized)
        snapshot_file.write_bytes(content)
    return {
        "path": normalized,
        "state": state,
        "git_blob": git_blob,
        "sha256": digest_bytes(content),
        "bytes": len(content),
        "snapshot": snapshot,
    }


def fingerprint_entries(entries: list[dict[str, Any]]) -> str:
    identity = [
        {
            "path": entry.get("path"),
            "state": entry.get("state"),
            "git_blob": entry.get("git_blob"),
            "sha256": entry.get("sha256"),
            "bytes": entry.get("bytes"),
        }
        for entry in entries
    ]
    return digest_value(identity)


def load_manifest(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.is_file():
        raise SourceRunError(f"manifest 不存在：{path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SourceRunError(f"{path}:{line_number} 不是有效 JSONL：{exc}") from exc
        if not isinstance(value, dict):
            raise SourceRunError(f"{path}:{line_number} 必须是 JSON object")
        records.append(value)
    return records


def comparable_entry(entry: dict[str, Any]) -> tuple[Any, ...]:
    return (
        entry.get("state"),
        entry.get("git_blob"),
        entry.get("sha256"),
        entry.get("bytes"),
    )


def changed_paths(
    entries: list[dict[str, Any]], previous_entries: list[dict[str, Any]] | None
) -> list[str]:
    current = {str(entry.get("path")): comparable_entry(entry) for entry in entries}
    if previous_entries is None:
        return sorted(current)
    previous = {
        str(entry.get("path")): comparable_entry(entry) for entry in previous_entries
    }
    return sorted(
        path for path in current.keys() | previous.keys() if current.get(path) != previous.get(path)
    )


def load_state(source_dir: Path, source_id: str) -> dict[str, Any]:
    path = source_dir / "state.yaml"
    if not path.exists():
        return source_state(source_id)
    return load_yaml(path, "Source state")


def state_consistency_errors(source_dir: Path, state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append("state.yaml schema_version 不支持")
    if state.get("source_id") != source_dir.name:
        errors.append("state.yaml source_id 与目录不一致")
    run_id = state.get("last_complete_run_id")
    if not run_id:
        if state.get("last_scoped_fingerprint") is not None:
            errors.append("state.yaml 无 last_complete_run_id 却存在 scoped fingerprint")
        if state.get("last_config_fingerprint") is not None:
            errors.append("state.yaml 无 last_complete_run_id 却存在 config fingerprint")
        return errors
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        errors.append("state.yaml last_complete_run_id 无效")
        return errors
    run_dir = source_dir / "runs" / run_id
    if not run_dir.is_dir():
        errors.append("state.yaml 指向的完整 SourceRun 不存在")
        return errors
    result = verify_run_directory(run_dir, source_dir.name, run_id)
    if not result["valid"]:
        errors.append("state.yaml 指向的 SourceRun 校验失败")
        return errors
    run = result["run"]
    if run.get("execution") != "completed" or run.get("coverage") != "complete":
        errors.append("state.yaml 只能指向 execution=completed 且 coverage=complete 的 run")
    if state.get("last_scoped_fingerprint") != run.get("revision", {}).get(
        "scoped_fingerprint"
    ):
        errors.append("state.yaml scoped fingerprint 与 SourceRun 不一致")
    if state.get("last_config_fingerprint") != run.get("config_fingerprint"):
        errors.append("state.yaml config fingerprint 与 SourceRun 不一致")
    return errors


def previous_complete_manifest(
    source_dir: Path, state: dict[str, Any]
) -> list[dict[str, Any]] | None:
    run_id = state.get("last_complete_run_id")
    if not run_id:
        return None
    path = source_dir / "runs" / str(run_id) / "manifest.jsonl"
    try:
        return load_manifest(path)
    except SourceRunError:
        return None


def run_uri(case_id: str, source_id: str, run_id: str) -> str:
    return f"source-run://{case_id}/{source_id}/{run_id}"


def execute_source(args: argparse.Namespace) -> int:
    cases_root = args.cases_root.resolve()
    workspace = args.workspace.resolve()
    source_dir = source_directory(cases_root, args.case_id, args.source_id)
    source = load_yaml(source_dir / "source.yaml", "SourceInstance")
    validate_source_instance(source)
    if source.get("kind") != "local_git":
        raise SourceRunError(f"不支持来源 kind：{source.get('kind')}")
    includes = source.get("scope", {}).get("include_paths", [])
    if not isinstance(includes, list) or not includes:
        raise SourceRunError("SourceInstance.scope.include_paths 必须是非空列表")

    runs_dir = source_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    state = load_state(source_dir, args.source_id)
    state_errors = state_consistency_errors(source_dir, state)
    if state_errors:
        raise SourceRunError("Source state 校验失败：" + "；".join(state_errors))
    run_id = create_run_id(args.source_id)
    staging = runs_dir / f".staging-{run_id}"
    staging.mkdir()
    started_at = utc_now()
    cursor_before = state.get("last_scoped_fingerprint")
    config_fingerprint = str(source.get("config_fingerprint", ""))
    try:
        repository, normalized_root = normalize_source_root(
            workspace, str(source.get("root", ""))
        )
        if normalized_root != source.get("root"):
            raise SourceRunError("SourceInstance root 规范化结果发生变化，拒绝运行")
        head = run_git(repository, "rev-parse", "HEAD").stdout.strip()
        entries = sorted(
            (observe_path(repository, str(relative_path), staging) for relative_path in includes),
            key=lambda item: str(item["path"]),
        )
    except SourceRunError as exc:
        manifest_hash = write_manifest(staging / "manifest.jsonl", [])
        failed_run = {
            "schema_version": SCHEMA_VERSION,
            "id": run_id,
            "source_id": args.source_id,
            "started_at": started_at,
            "completed_at": utc_now(),
            "execution": "failed",
            "comparison": "unknown",
            "coverage": "unknown",
            "config_fingerprint": config_fingerprint,
            "cursor_before": cursor_before,
            "cursor_after": None,
            "revision": {"git_head": None, "scoped_fingerprint": None},
            "manifest_path": "manifest.jsonl",
            "manifest_sha256": manifest_hash,
            "changed_paths": [],
            "change_reasons": [],
            "warnings": [],
            "error": str(exc),
            "tool": {"name": "source_run.py", "version": TOOL_VERSION},
            "semantic_assessment": "not_performed",
            "task_state_changed": False,
            "uri": run_uri(args.case_id, args.source_id, run_id),
        }
        failed_run["envelope_sha256"] = digest_value(failed_run)
        atomic_write_yaml(staging / "run.yaml", failed_run)
        validity = verify_run_directory(staging, args.source_id, run_id)
        if not validity["valid"]:
            raise SourceRunError(
                "失败 SourceRun 发布前校验失败：" + "；".join(validity["errors"])
            ) from exc
        os.replace(staging, runs_dir / run_id)
        print(json.dumps(failed_run, ensure_ascii=False, indent=2))
        return 2

    warnings = [
        f"{entry['path']}: {entry['state']}"
        for entry in entries
        if entry.get("state") in {"missing", "unreadable"}
    ]
    coverage = "partial" if warnings else "complete"
    scoped_fingerprint = fingerprint_entries(entries)
    previous_manifest = previous_complete_manifest(source_dir, state)
    previous_config = state.get("last_config_fingerprint")
    reasons: list[str] = []
    if coverage != "complete":
        comparison = "unknown"
    elif not state.get("last_complete_run_id"):
        comparison = "initial"
    elif previous_config != config_fingerprint:
        comparison = "changed"
        reasons.append("config_changed")
    elif cursor_before == scoped_fingerprint:
        comparison = "unchanged"
    else:
        comparison = "changed"
        reasons.append("content_changed")
    paths_changed = changed_paths(entries, previous_manifest)
    if comparison == "changed" and paths_changed and "content_changed" not in reasons:
        reasons.append("content_changed")
    cursor_after = scoped_fingerprint if coverage == "complete" else None

    manifest_hash = write_manifest(staging / "manifest.jsonl", entries)
    run = {
        "schema_version": SCHEMA_VERSION,
        "id": run_id,
        "source_id": args.source_id,
        "started_at": started_at,
        "completed_at": utc_now(),
        "execution": "completed",
        "comparison": comparison,
        "coverage": coverage,
        "config_fingerprint": config_fingerprint,
        "cursor_before": cursor_before,
        "cursor_after": cursor_after,
        "revision": {"git_head": head, "scoped_fingerprint": scoped_fingerprint},
        "manifest_path": "manifest.jsonl",
        "manifest_sha256": manifest_hash,
        "changed_paths": paths_changed,
        "change_reasons": reasons,
        "warnings": warnings,
        "error": None,
        "tool": {"name": "source_run.py", "version": TOOL_VERSION},
        "semantic_assessment": "not_performed",
        "task_state_changed": False,
        "uri": run_uri(args.case_id, args.source_id, run_id),
    }
    run["envelope_sha256"] = digest_value(run)
    atomic_write_yaml(staging / "run.yaml", run)
    validity = verify_run_directory(staging, args.source_id, run_id)
    if not validity["valid"]:
        raise SourceRunError("发布前 SourceRun 校验失败：" + "；".join(validity["errors"]))
    if os.environ.get("SOURCE_RUN_TEST_FAILPOINT") == "before_publish":
        raise SourceRunError("触发测试故障点 before_publish")
    final = runs_dir / run_id
    os.replace(staging, final)

    if coverage == "complete":
        next_state = {
            "schema_version": SCHEMA_VERSION,
            "source_id": args.source_id,
            "last_complete_run_id": run_id,
            "last_scoped_fingerprint": scoped_fingerprint,
            "last_config_fingerprint": config_fingerprint,
            "updated_at": utc_now(),
        }
        atomic_write_yaml(source_dir / "state.yaml", next_state)

    print(json.dumps(run, ensure_ascii=False, indent=2))
    return 0


def safe_snapshot_path(run_dir: Path, snapshot: str) -> Path | None:
    candidate = PurePosixPath(snapshot)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = run_dir.joinpath(*candidate.parts).resolve(strict=False)
    return resolved if is_inside(resolved, run_dir.resolve()) else None


def verify_run_directory(run_dir: Path, source_id: str, run_id: str) -> dict[str, Any]:
    errors: list[str] = []
    try:
        run = load_yaml(run_dir / "run.yaml", "SourceRun")
    except SourceRunError as exc:
        return {"valid": False, "errors": [str(exc)], "run": None}
    if run.get("schema_version") != SCHEMA_VERSION:
        errors.append("run.yaml schema_version 不支持")
    if run.get("id") != run_id:
        errors.append("run.yaml id 与目录不一致")
    if run.get("source_id") != source_id:
        errors.append("run.yaml source_id 与目录不一致")
    stored_envelope_hash = run.get("envelope_sha256")
    envelope_payload = dict(run)
    envelope_payload.pop("envelope_sha256", None)
    if stored_envelope_hash != digest_value(envelope_payload):
        errors.append("run.yaml envelope sha256 不匹配")
    manifest_path = run_dir / str(run.get("manifest_path", "manifest.jsonl"))
    if not manifest_path.is_file():
        errors.append("manifest 不存在")
        entries: list[dict[str, Any]] = []
    else:
        content = manifest_path.read_bytes()
        if digest_bytes(content) != run.get("manifest_sha256"):
            errors.append("manifest sha256 不匹配")
        try:
            entries = load_manifest(manifest_path)
        except SourceRunError as exc:
            errors.append(str(exc))
            entries = []
    for entry in entries:
        state = entry.get("state")
        snapshot = entry.get("snapshot")
        if state in {"tracked_dirty", "untracked"} and not snapshot:
            errors.append(f"{entry.get('path')}: 不可重现内容缺少 snapshot")
            continue
        if snapshot:
            snapshot_path = safe_snapshot_path(run_dir, str(snapshot))
            if snapshot_path is None:
                errors.append(f"{entry.get('path')}: snapshot 越界")
            elif not snapshot_path.is_file():
                errors.append(f"{entry.get('path')}: snapshot 不存在")
            elif digest_bytes(snapshot_path.read_bytes()) != entry.get("sha256"):
                errors.append(f"{entry.get('path')}: snapshot sha256 不匹配")
    return {"valid": not errors, "errors": errors, "run": run}


def verify_published_run(
    cases_root: Path, case_id: str, source_id: str, run_id: str
) -> dict[str, Any]:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise SourceRunError(f"无效 SourceRun id：{run_id}")
    source_dir = source_directory(cases_root.resolve(), case_id, source_id)
    run_dir = source_dir / "runs" / run_id
    if not run_dir.is_dir():
        raise SourceRunError(f"SourceRun 不存在：{run_uri(case_id, source_id, run_id)}")
    result = verify_run_directory(run_dir, source_id, run_id)
    if not result["valid"]:
        raise SourceRunError(
            f"SourceRun 校验失败 {run_uri(case_id, source_id, run_id)}："
            + "；".join(result["errors"])
        )
    run = result["run"]
    if run.get("execution") != "completed":
        raise SourceRunError(f"SourceRun 未完成：{run_uri(case_id, source_id, run_id)}")
    return run


def validate_source_run_uri(
    uri: str, cases_root: Path, expected_case_id: str | None = None
) -> dict[str, Any]:
    match = SOURCE_RUN_URI_PATTERN.fullmatch(uri)
    if not match:
        raise SourceRunError(f"无效 SourceRun URI：{uri}")
    case_id = match.group("case")
    source_id = match.group("source")
    run_id = match.group("run")
    if expected_case_id is not None and case_id != expected_case_id:
        raise SourceRunError(
            f"SourceRun 属于其他 task case：{case_id}，当前为 {expected_case_id}"
        )
    return verify_published_run(cases_root, case_id, source_id, run_id)


def verify_command(args: argparse.Namespace) -> int:
    try:
        if not RUN_ID_PATTERN.fullmatch(args.run_id):
            raise SourceRunError(f"无效 SourceRun id：{args.run_id}")
        source_dir = source_directory(
            args.cases_root.resolve(), args.case_id, args.source_id
        )
        run_dir = source_dir / "runs" / args.run_id
        if not run_dir.is_dir():
            raise SourceRunError(
                f"SourceRun 不存在：{run_uri(args.case_id, args.source_id, args.run_id)}"
            )
        result = verify_run_directory(run_dir, args.source_id, args.run_id)
        if not result["valid"]:
            raise SourceRunError("；".join(result["errors"]))
        run = result["run"]
    except SourceRunError as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "uri": run_uri(args.case_id, args.source_id, args.run_id),
                    "errors": [str(exc)],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    print(
        json.dumps(
            {"valid": True, "uri": run.get("uri"), "errors": [], "run": run},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def latest_run(source_dir: Path) -> dict[str, Any] | None:
    runs_dir = source_dir / "runs"
    if not runs_dir.is_dir():
        return None
    candidates = sorted(
        (path for path in runs_dir.iterdir() if path.is_dir() and not path.name.startswith(".")),
        key=lambda path: path.name,
    )
    if not candidates:
        return None
    return load_yaml(candidates[-1] / "run.yaml", "SourceRun")


def status_command(args: argparse.Namespace) -> int:
    source_dir = source_directory(args.cases_root.resolve(), args.case_id, args.source_id)
    source = load_yaml(source_dir / "source.yaml", "SourceInstance")
    validate_source_instance(source)
    state = load_state(source_dir, args.source_id)
    state_errors = state_consistency_errors(source_dir, state)
    runs_dir = source_dir / "runs"
    orphaned = (
        sorted(path.name for path in runs_dir.iterdir() if path.name.startswith(".staging-"))
        if runs_dir.is_dir()
        else []
    )
    if args.run_id:
        if not RUN_ID_PATTERN.fullmatch(args.run_id):
            raise SourceRunError(f"无效 SourceRun id：{args.run_id}")
        requested = load_yaml(runs_dir / args.run_id / "run.yaml", "SourceRun")
    else:
        requested = latest_run(source_dir)
    if state_errors:
        next_actions = ["修复 state 与已发布 run 的一致性后再运行来源"]
    elif requested is None:
        next_actions = ["运行该来源以建立 initial 观察"]
    elif requested.get("execution") == "failed":
        next_actions = ["修复运行错误后重新观察；失败 run 未推进完整游标"]
    elif requested.get("coverage") != "complete":
        next_actions = ["处理 coverage warnings 后重新运行；当前结果不推进完整游标"]
    elif requested.get("comparison") in {"initial", "changed"}:
        next_actions = ["按任务问题检查 manifest 与必要证据；来源变化不等于知识充分"]
    else:
        next_actions = ["来源声明范围未变化；任务问题和知识状态仍以 task case 为准"]
    output = {
        "case_id": args.case_id,
        "source": source,
        "state": state,
        "state_valid": not state_errors,
        "state_errors": state_errors,
        "latest_run": requested,
        "orphaned_staging": orphaned,
        "semantic_assessment": "not_performed",
        "task_state_changed": False,
        "next_actions": next_actions,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="管理 task-local 来源运行信封")
    parser.add_argument("--cases-root", type=Path, default=default_cases_root())
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    subparsers = parser.add_subparsers(dest="command", required=True)

    register = subparsers.add_parser("register", help="登记一个只读 local_git 来源")
    register.add_argument("case_id")
    register.add_argument("source_id")
    register.add_argument("--kind", default="local_git")
    register.add_argument("--root", dest="source_root", required=True)
    register.add_argument("--authority", default="contextual", choices=sorted(AUTHORITIES))
    register.add_argument("--purpose", default="")
    register.add_argument("--include", dest="includes", action="append", required=True)
    register.add_argument("--replace", action="store_true")
    register.set_defaults(func=register_source)

    execute = subparsers.add_parser("run", help="观察来源并原子发布 SourceRun")
    execute.add_argument("case_id")
    execute.add_argument("source_id")
    execute.set_defaults(func=execute_source)

    status = subparsers.add_parser("status", help="不读取来源地恢复最近运行状态")
    status.add_argument("case_id")
    status.add_argument("source_id")
    status.add_argument("--run-id")
    status.set_defaults(func=status_command)

    verify = subparsers.add_parser("verify", help="校验已发布 SourceRun 的内部完整性")
    verify.add_argument("case_id")
    verify.add_argument("source_id")
    verify.add_argument("run_id")
    verify.set_defaults(func=verify_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SourceRunError as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
