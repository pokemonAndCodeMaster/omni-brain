from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .utils import run_command


ADOPTION_LABELS = {
    "verified": "已验证",
    "implemented": "已实现待验证",
    "approved": "已批准",
    "provisional": "试验中",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML 顶层必须是 mapping：{path}")
    return data


def _adoption_label(value: str) -> str:
    for prefix, label in ADOPTION_LABELS.items():
        if value.startswith(prefix):
            return label
    return value.replace("_", " ")


class AgentRegistry:
    def __init__(self, project_root: Path, registry_path: Path) -> None:
        self.project_root = project_root
        self.registry_path = registry_path

    def _documents(self) -> tuple[dict[str, Any], dict[str, Any], Path, str]:
        registry = _load_yaml(self.registry_path)
        source = registry.get("source", {})
        repository = (self.project_root / str(source.get("repository", ""))).resolve()
        revision = str(source.get("revision", "HEAD"))
        manifest_path = repository / str(source.get("manifest", "harness.yaml"))
        manifest = _load_yaml(manifest_path)
        resolved_revision = run_command(["git", "-C", str(repository), "rev-parse", revision])
        return registry, manifest, repository, resolved_revision

    def list_agents(self, run_counts: dict[str, int] | None = None) -> list[dict[str, Any]]:
        registry, manifest, repository, resolved_revision = self._documents()
        capabilities = manifest.get("capabilities", {})
        result: list[dict[str, Any]] = []
        for spec in registry.get("agents", []):
            capability_details: list[dict[str, Any]] = []
            statuses: list[str] = []
            for key in spec.get("capability_keys", []):
                detail = capabilities.get(key, {})
                adoption = str(detail.get("adoption", "unknown"))
                statuses.append(adoption)
                capability_details.append(
                    {
                        "id": key,
                        "adoption": adoption,
                        "adoption_label": _adoption_label(adoption),
                        "entrypoints": detail.get("entrypoints", []),
                        "limits": detail.get("limits", []),
                    }
                )
            verified = bool(statuses) and all(status.startswith("verified") for status in statuses)
            implemented = bool(statuses) and all(
                status.startswith(("verified", "implemented")) for status in statuses
            )
            state = "verified" if verified else "implemented" if implemented else "experimental"
            item = dict(spec)
            item.update(
                {
                    "repository": str(repository),
                    "revision": resolved_revision,
                    "revision_short": resolved_revision[:7],
                    "release_channel": manifest.get("release_channel"),
                    "release_date": manifest.get("release_date"),
                    "state": state,
                    "capabilities": capability_details,
                    "run_count": (run_counts or {}).get(str(spec["id"]), 0),
                }
            )
            result.append(item)
        return result

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        for agent in self.list_agents():
            if agent["id"] == agent_id:
                return agent
        raise KeyError(agent_id)

    def list_eval_cases(self) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        datasets_root = self.project_root / "eval" / "datasets"
        for path in sorted(datasets_root.rglob("*.yaml")):
            try:
                data = _load_yaml(path)
            except (OSError, ValueError, yaml.YAMLError):
                continue
            parent_id = str(
                data.get("id")
                or data.get("dataset_id")
                or data.get("task", {}).get("id")
                or path.stem
            )
            category = path.relative_to(datasets_root).parts[0]
            child_cases = data.get("cases")
            if isinstance(child_cases, list):
                for child in child_cases:
                    if not isinstance(child, dict) or not child.get("prompt"):
                        continue
                    cases.append(
                        {
                            "id": f"{parent_id}:{child.get('id', len(cases) + 1)}",
                            "dataset_id": parent_id,
                            "name": str(child.get("id", parent_id)).replace("-", " "),
                            "title": data.get("title", data.get("name", parent_id)),
                            "category": category,
                            "kind": child.get("kind", "case"),
                            "prompt": child["prompt"],
                            "expected": child.get("expected"),
                            "path": str(path),
                            "launchable": True,
                        }
                    )
                continue
            prompt = data.get("instruction", {}).get("prompt")
            if not prompt:
                fixture_value = data.get("input", {}).get("fixture")
                if fixture_value:
                    fixture_path = self.project_root / str(fixture_value) / "initial-request.md"
                    if fixture_path.is_file():
                        prompt = fixture_path.read_text(encoding="utf-8")
            title = data.get("title") or data.get("name") or data.get("task", {}).get("name") or parent_id
            cases.append(
                {
                    "id": parent_id,
                    "dataset_id": parent_id,
                    "name": title,
                    "title": title,
                    "category": category,
                    "kind": data.get("status", "dataset"),
                    "prompt": prompt,
                    "expected": data.get("expected"),
                    "path": str(path),
                    "launchable": bool(prompt),
                }
            )
        return cases

    def get_eval_case(self, case_id: str) -> dict[str, Any]:
        for case in self.list_eval_cases():
            if case["id"] == case_id:
                return case
        raise KeyError(case_id)

    def list_archived_trials(self) -> list[dict[str, Any]]:
        trials: list[dict[str, Any]] = []
        for manifest_path in (self.project_root / "eval" / "trials").rglob("manifest.yaml"):
            try:
                manifest = _load_yaml(manifest_path)
            except (OSError, ValueError, yaml.YAMLError):
                continue
            outcome = {}
            artifact = manifest.get("artifacts", {}).get("outcome", {})
            if isinstance(artifact, dict) and artifact.get("path"):
                outcome_path = manifest_path.parent / str(artifact["path"])
                if outcome_path.is_file():
                    try:
                        outcome = _load_yaml(outcome_path)
                    except (OSError, ValueError, yaml.YAMLError):
                        outcome = {}
            trials.append(
                {
                    "id": manifest.get("trial_id", manifest_path.parent.name),
                    "task_id": manifest.get("task_id"),
                    "record_kind": manifest.get("record_kind"),
                    "identity": manifest.get("identity", {}),
                    "started_at": manifest.get("started_at"),
                    "ended_at": manifest.get("ended_at"),
                    "outcome": outcome,
                    "path": str(manifest_path.parent),
                }
            )
        return sorted(trials, key=lambda item: item.get("started_at") or "", reverse=True)
