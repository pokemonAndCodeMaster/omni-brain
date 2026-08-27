from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from .utils import append_jsonl, read_json, write_json


class RunStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.runs_root = root / "runs"
        self.evolutions_root = root / "evolutions"
        self._lock = threading.RLock()
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self.evolutions_root.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        return self.runs_root / run_id

    def create_run(self, record: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            run_dir = self.run_dir(record["id"])
            if run_dir.exists():
                raise FileExistsError(f"Run 已存在：{record['id']}")
            run_dir.mkdir(parents=True)
            write_json(run_dir / "run.json", record)
            return record

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            return read_json(self.run_dir(run_id) / "run.json")

    def update_run(self, run_id: str, **changes: Any) -> dict[str, Any]:
        with self._lock:
            record = self.get_run(run_id)
            if record is None:
                raise KeyError(run_id)
            record.update(changes)
            write_json(self.run_dir(run_id) / "run.json", record)
            return record

    def list_runs(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        with self._lock:
            for path in self.runs_root.glob("*/run.json"):
                record = read_json(path)
                if isinstance(record, dict):
                    records.append(record)
        return sorted(records, key=lambda item: item.get("created_at", ""), reverse=True)

    def append_event(self, run_id: str, event: dict[str, Any]) -> None:
        with self._lock:
            append_jsonl(self.run_dir(run_id) / "events.jsonl", event)

    def events(self, run_id: str, after: int = 0) -> list[dict[str, Any]]:
        path = self.run_dir(run_id) / "events.jsonl"
        if not path.is_file():
            return []
        events: list[dict[str, Any]] = []
        with self._lock, path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = __import__("json").loads(line)
                if int(event.get("seq", 0)) > after:
                    events.append(event)
        return events

    def write_artifact(self, run_id: str, name: str, content: str) -> Path:
        path = self.run_dir(run_id) / name
        path.write_text(content, encoding="utf-8")
        return path

    def artifact_text(self, run_id: str, name: str, limit: int = 200_000) -> str:
        path = self.run_dir(run_id) / name
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")[:limit]

    def create_evolution(self, record: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            target = self.evolutions_root / f"{record['id']}.json"
            if target.exists():
                raise FileExistsError(record["id"])
            write_json(target, record)
            return record

    def update_evolution(self, evolution_id: str, **changes: Any) -> dict[str, Any]:
        with self._lock:
            target = self.evolutions_root / f"{evolution_id}.json"
            record = read_json(target)
            if not isinstance(record, dict):
                raise KeyError(evolution_id)
            record.update(changes)
            write_json(target, record)
            return record

    def list_evolutions(self) -> list[dict[str, Any]]:
        records = [read_json(path) for path in self.evolutions_root.glob("*.json")]
        return sorted(
            [record for record in records if isinstance(record, dict)],
            key=lambda item: item.get("created_at", ""),
            reverse=True,
        )

    def get_evolution(self, evolution_id: str) -> dict[str, Any] | None:
        return read_json(self.evolutions_root / f"{evolution_id}.json")
