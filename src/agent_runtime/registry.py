from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any

import yaml


ADOPTION_LABELS = {
    "verified": "已验证",
    "implemented": "已实现待验证",
    "approved": "已批准",
    "provisional": "试验中",
}


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"YAML 顶层必须是映射：{path}")
    return value


def _git(repository: Path, *args: str) -> str:
    import subprocess

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


def _adoption_label(value: str) -> str:
    for prefix, label in ADOPTION_LABELS.items():
        if value.startswith(prefix):
            return label
    return value.replace("_", " ")


class AgentRegistry:
    """Read the released Harness catalog once; execution is always OpenCode."""

    def __init__(self, registry_path: Path) -> None:
        self.registry_path = registry_path.resolve()
        self._lock = RLock()
        self._cache: list[dict[str, Any]] | None = None

    def _load(self) -> list[dict[str, Any]]:
        registry = _yaml(self.registry_path)
        source = registry.get("source", {})
        if not isinstance(source, dict):
            raise ValueError("Agent 注册表 source 必须是映射")
        project_root = self.registry_path.parent.parent
        repository = (project_root / str(source.get("repository", ""))).resolve()
        revision = str(source.get("revision", "HEAD"))
        manifest_path = repository / str(source.get("manifest", "harness.yaml"))
        manifest = _yaml(manifest_path)
        capabilities = manifest.get("capabilities", {})
        if not isinstance(capabilities, dict):
            capabilities = {}
        resolved_revision = _git(repository, "rev-parse", revision)

        result: list[dict[str, Any]] = []
        for raw in registry.get("agents", []):
            if not isinstance(raw, dict):
                continue
            capability_details: list[dict[str, Any]] = []
            adoptions: list[str] = []
            for key in raw.get("capability_keys", []):
                detail = capabilities.get(key, {})
                if not isinstance(detail, dict):
                    detail = {}
                adoption = str(detail.get("adoption", "unknown"))
                adoptions.append(adoption)
                capability_details.append(
                    {
                        "id": str(key),
                        "adoption": adoption,
                        "adoption_label": _adoption_label(adoption),
                        "entrypoints": detail.get("entrypoints", []),
                        "limits": detail.get("limits", []),
                    }
                )
            verified = bool(adoptions) and all(
                value.startswith("verified") for value in adoptions
            )
            implemented = bool(adoptions) and all(
                value.startswith(("verified", "implemented"))
                for value in adoptions
            )
            result.append(
                {
                    "id": str(raw["id"]),
                    "name": str(raw["name"]),
                    "category": str(raw.get("category", "未分类")),
                    "description": str(raw.get("description", "")),
                    "examples": [str(item) for item in raw.get("examples", [])],
                    "state": (
                        "verified"
                        if verified
                        else "implemented"
                        if implemented
                        else "experimental"
                    ),
                    "capabilities": capability_details,
                    "executor": "opencode",
                    "repository": str(repository),
                    "revision": resolved_revision,
                    "revision_short": resolved_revision[:7],
                    "release_channel": manifest.get("release_channel"),
                    "release_date": manifest.get("release_date"),
                }
            )
        return result

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            if self._cache is None:
                self._cache = self._load()
            return deepcopy(self._cache)

    def get(self, agent_id: str) -> dict[str, Any]:
        for agent in self.list():
            if agent["id"] == agent_id:
                return agent
        raise KeyError(agent_id)

    def refresh(self) -> list[dict[str, Any]]:
        with self._lock:
            candidate = self._load()
            self._cache = candidate
            return deepcopy(candidate)
