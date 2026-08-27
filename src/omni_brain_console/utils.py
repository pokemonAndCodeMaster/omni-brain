from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=False) + "\n")


def run_command(argv: list[str], cwd: Path | None = None) -> str:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def safe_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._")
    if not normalized:
        raise ValueError("标识不能为空")
    return normalized[:120]


def nested_value(value: Any, names: set[str]) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in names and isinstance(child, (str, int)):
                return str(child)
        for child in value.values():
            found = nested_value(child, names)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = nested_value(child, names)
            if found:
                return found
    return None


def first_text(value: Any) -> str | None:
    preferred = {"text", "message", "summary", "title", "command", "name"}
    if isinstance(value, dict):
        for key, child in value.items():
            if key in preferred and isinstance(child, str) and child.strip():
                return child.strip()
        for child in value.values():
            found = first_text(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = first_text(child)
            if found:
                return found
    return None
