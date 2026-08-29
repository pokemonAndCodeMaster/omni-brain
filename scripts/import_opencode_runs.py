#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.agent_runtime.opencode_executor import classify_failure  # noqa: E402
from src.config import ConfigManager  # noqa: E402
from src.database import DatabaseManager  # noqa: E402


STATUS_MAP = {
    "completed": "succeeded",
    "succeeded": "succeeded",
    "failed": "failed",
    "blocked": "failed",
    "cancelled": "cancelled",
    "queued": "queued",
    "running": "running",
}


def nested_message(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "message" and isinstance(item, str) and item.strip():
                return item.strip()
            found = nested_message(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = nested_message(item)
            if found:
                return found
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-time import of historical OpenCode runs into PostgreSQL",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=PROJECT_ROOT.parent / "omni-brain" / ".derived" / "agent-console" / "agent-console.sqlite3",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    if not source.is_file():
        raise SystemExit(f"SQLite 历史库不存在：{source}")

    legacy = sqlite3.connect(source)
    legacy.row_factory = sqlite3.Row
    config = ConfigManager(project_root=PROJECT_ROOT)
    manager = DatabaseManager(config)
    postgres = manager.postgres()
    runs_table = f"{postgres.schema}.t_agent_run"
    events_table = f"{postgres.schema}.t_agent_run_event"
    imported = 0
    skipped = 0
    try:
        rows = legacy.execute(
            """
            SELECT payload_json
            FROM runs
            WHERE json_extract(payload_json, '$.executor') = 'opencode'
            ORDER BY created_at
            """
        ).fetchall()
        for row in rows:
            run = json.loads(str(row["payload_json"]))
            run_id = str(run["id"])
            legacy_events = [
                json.loads(str(event["payload_json"]))
                for event in legacy.execute(
                    """
                    SELECT payload_json
                    FROM run_events
                    WHERE run_id = ?
                    ORDER BY seq
                    """,
                    (run_id,),
                ).fetchall()
            ]
            failure_reason = str(run.get("error") or "").strip() or None
            if not failure_reason:
                for event in legacy_events:
                    if str(event.get("type", "")).casefold() == "error":
                        failure_reason = nested_message(event.get("payload"))
                        if failure_reason:
                            break
            status = STATUS_MAP.get(str(run.get("status")), "failed")
            failure_code = run.get("failure_code")
            if status == "failed" and not failure_code:
                failure_code = classify_failure(failure_reason or "OpenCode 历史运行失败")
            if str(run.get("status")) == "blocked" and not failure_code:
                failure_code = "blocked"

            with postgres.transaction() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        INSERT INTO {runs_table} (
                            id, agent_id, agent_name, title, prompt, actor_id,
                            status, model, repository_path, base_revision,
                            worktree_path, branch_name, opencode_session_id,
                            exit_code, result_summary, failure_code, failure_reason,
                            artifact_path, created_at, started_at, finished_at, updated_at
                        ) VALUES (
                            %(id)s, %(agent_id)s, %(agent_name)s, %(title)s,
                            %(prompt)s, 'legacy-local-user', %(status)s, %(model)s,
                            %(repository_path)s, %(base_revision)s, %(worktree_path)s,
                            %(branch_name)s, %(session_id)s, %(exit_code)s,
                            %(result_summary)s, %(failure_code)s, %(failure_reason)s,
                            %(artifact_path)s, %(created_at)s, %(started_at)s,
                            %(finished_at)s, %(updated_at)s
                        )
                        ON CONFLICT (id) DO NOTHING
                        RETURNING id
                        """,
                        {
                            "id": run_id,
                            "agent_id": run.get("agent_id") or "unknown-agent",
                            "agent_name": run.get("agent_name") or run.get("agent_id") or "未知 Agent",
                            "title": str(run.get("prompt") or run_id).strip().splitlines()[0][:256],
                            "prompt": run.get("prompt") or "",
                            "status": status,
                            "model": run.get("model"),
                            "repository_path": run.get("repository") or "",
                            "base_revision": run.get("base_revision") or run.get("agent_revision") or "unknown",
                            "worktree_path": run.get("worktree"),
                            "branch_name": run.get("branch"),
                            "session_id": run.get("session_id"),
                            "exit_code": run.get("exit_code"),
                            "result_summary": (
                                run.get("final_preview")
                                if status == "succeeded"
                                else None
                            ),
                            "failure_code": failure_code,
                            "failure_reason": failure_reason,
                            "artifact_path": str(source.parent / "runs" / run_id),
                            "created_at": run.get("created_at"),
                            "started_at": run.get("created_at"),
                            "finished_at": (
                                run.get("updated_at")
                                if status in {"succeeded", "failed", "cancelled"}
                                else None
                            ),
                            "updated_at": run.get("updated_at") or run.get("created_at"),
                        },
                    )
                    inserted = cursor.fetchone()
                    if inserted is None:
                        skipped += 1
                        continue
                    imported += 1
                    for index, event in enumerate(legacy_events, 1):
                        payload = event.get("payload")
                        cursor.execute(
                            f"""
                            INSERT INTO {events_table} (
                                run_id, sequence, occurred_at, event_type,
                                source, channel, summary, payload
                            ) VALUES (
                                %(run_id)s, %(sequence)s, %(occurred_at)s,
                                %(event_type)s, %(source)s, %(channel)s,
                                %(summary)s, %(payload)s
                            )
                            """,
                            {
                                "run_id": run_id,
                                "sequence": int(event.get("seq") or index),
                                "occurred_at": event.get("timestamp") or run.get("created_at"),
                                "event_type": event.get("type") or "legacy.event",
                                "source": event.get("source") or "legacy",
                                "channel": event.get("channel"),
                                "summary": event.get("summary") or event.get("type") or "legacy.event",
                                "payload": Jsonb(payload if isinstance(payload, dict) else {"value": payload}),
                            },
                        )
    finally:
        legacy.close()
        manager.close()

    print(
        json.dumps(
            {
                "source": str(source),
                "executor": "opencode",
                "imported": imported,
                "skipped": skipped,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
