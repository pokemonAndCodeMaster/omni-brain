from __future__ import annotations

from typing import Any, Iterable

from psycopg.types.json import Jsonb

from src.database import PGConnector


RUN_COLUMNS = """
    id, agent_id, agent_name, title, prompt, actor_id, status, model,
    repository_path, base_revision, worktree_path, branch_name,
    executor, executor_session_id, opencode_session_id,
    subject_type, subject_id, thread_id, trigger_action,
    work_id, plan_step_id,
    exit_code, result_summary, result_payload, failure_code,
    failure_reason, artifact_path, created_at, started_at, finished_at, updated_at
"""

RUN_SUMMARY_COLUMNS = """
    id, agent_id, agent_name, title, actor_id, status, model,
    branch_name, executor, executor_session_id,
    subject_type, subject_id, thread_id, trigger_action,
    work_id, plan_step_id,
    exit_code, failure_code,
    created_at, started_at, finished_at, updated_at
"""


class AgentRunRepository:
    """PostgreSQL source of truth for Run metadata and normalized events."""

    _UPDATABLE = {
        "status",
        "worktree_path",
        "branch_name",
        "executor_session_id",
        "opencode_session_id",
        "result_payload",
        "exit_code",
        "result_summary",
        "failure_code",
        "failure_reason",
        "artifact_path",
        "started_at",
        "finished_at",
    }

    def __init__(self, postgres: PGConnector) -> None:
        self._postgres = postgres
        self._runs = f"{postgres.schema}.t_agent_run"
        self._events = f"{postgres.schema}.t_agent_run_event"

    def create(self, run: dict[str, Any]) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        INSERT INTO {self._runs} (
                            id, agent_id, agent_name, title, prompt, actor_id, status,
                            model, repository_path, base_revision, artifact_path,
                            worktree_path, branch_name, executor,
                            subject_type, subject_id, thread_id, trigger_action,
                            work_id, plan_step_id
                        ) VALUES (
                            %(id)s, %(agent_id)s, %(agent_name)s, %(title)s,
                            %(prompt)s, %(actor_id)s, 'queued', %(model)s,
                            %(repository_path)s, %(base_revision)s, %(artifact_path)s,
                            %(worktree_path)s, %(branch_name)s, %(executor)s,
                            %(subject_type)s, %(subject_id)s,
                            %(thread_id)s, %(trigger_action)s,
                            %(work_id)s, %(plan_step_id)s
                        )
                        RETURNING {RUN_COLUMNS}
                    """,
                    run,
                )
                row = cursor.fetchone()
                cursor.execute(
                    f"""
                        INSERT INTO {self._events} (
                            run_id, sequence, event_type, source, summary, payload
                        ) VALUES (
                            %(id)s, 1, 'run.queued', 'platform',
                            %(summary)s, %(payload)s
                        )
                    """,
                    {
                        "id": run["id"],
                        "summary": f"任务已进入 {run['executor']} 执行队列",
                        "payload": Jsonb(
                            {
                                "agent_id": run["agent_id"],
                                "executor": run["executor"],
                                "subject_type": run.get("subject_type"),
                                "subject_id": run.get("subject_id"),
                                "work_id": run.get("work_id"),
                                "plan_step_id": run.get("plan_step_id"),
                            }
                        ),
                    },
                )
        if row is None:
            raise RuntimeError("创建 Run 后未返回记录")
        return row

    def get(self, run_id: str) -> dict[str, Any] | None:
        return self._postgres.fetch_one(
            f"SELECT {RUN_COLUMNS} FROM {self._runs} WHERE id = %(id)s",
            {"id": run_id},
        )

    def update(self, run_id: str, **changes: Any) -> dict[str, Any]:
        unknown = set(changes) - self._UPDATABLE
        if unknown:
            raise ValueError(f"不允许更新 Run 字段：{', '.join(sorted(unknown))}")
        if not changes:
            row = self.get(run_id)
            if row is None:
                raise KeyError(run_id)
            return row
        if isinstance(changes.get("result_payload"), dict):
            changes["result_payload"] = Jsonb(changes["result_payload"])
        assignments = [f"{key} = %({key})s" for key in changes]
        params = {"id": run_id, **changes}
        row = self._postgres.fetch_one(
            f"""
                UPDATE {self._runs}
                SET {', '.join(assignments)}, updated_at = now()
                WHERE id = %(id)s
                RETURNING {RUN_COLUMNS}
            """,
            params,
        )
        if row is None:
            raise KeyError(run_id)
        return row

    def list(
        self,
        *,
        limit: int,
        offset: int,
        agent_id: str | None = None,
        executor: str | None = None,
        subject_type: str | None = None,
        subject_id: str | None = None,
        statuses: Iterable[str] = (),
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if agent_id:
            clauses.append("agent_id = %(agent_id)s")
            params["agent_id"] = agent_id
        if executor:
            clauses.append("executor = %(executor)s")
            params["executor"] = executor
        if subject_type:
            clauses.append("subject_type = %(subject_type)s")
            params["subject_type"] = subject_type
        if subject_id:
            clauses.append("subject_id = %(subject_id)s")
            params["subject_id"] = subject_id
        status_values = tuple(statuses)
        if status_values:
            clauses.append("status = ANY(%(statuses)s)")
            params["statuses"] = list(status_values)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._postgres.fetch_all(
            f"""
                SELECT {RUN_SUMMARY_COLUMNS}, COUNT(*) OVER()::integer AS total_count
                FROM {self._runs}
                {where}
                ORDER BY created_at DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        total = int(rows[0]["total_count"]) if rows else 0
        for row in rows:
            row.pop("total_count", None)
        return rows, total

    def counts_by_agent(self) -> dict[str, dict[str, int]]:
        rows = self._postgres.fetch_all(
            f"""
                SELECT agent_id,
                       COUNT(*)::integer AS total,
                       COUNT(*) FILTER (
                           WHERE status IN ('queued', 'running')
                       )::integer AS active,
                       COUNT(*) FILTER (
                           WHERE status = 'succeeded'
                       )::integer AS succeeded,
                       COUNT(*) FILTER (
                           WHERE status = 'failed'
                       )::integer AS failed
                FROM {self._runs}
                GROUP BY agent_id
            """
        )
        return {
            str(row["agent_id"]): {
                "total": int(row["total"]),
                "active": int(row["active"]),
                "succeeded": int(row["succeeded"]),
                "failed": int(row["failed"]),
            }
            for row in rows
        }

    def append_event(
        self,
        *,
        run_id: str,
        event_type: str,
        summary: str,
        payload: dict[str, Any],
        source: str = "platform",
        channel: str | None = None,
    ) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s::text))",
                (run_id,),
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        INSERT INTO {self._events} (
                            run_id, sequence, event_type, source,
                            channel, summary, payload
                        )
                        SELECT %(run_id)s::varchar(64),
                               COALESCE(MAX(sequence), 0) + 1,
                               %(event_type)s, %(source)s, %(channel)s,
                               %(summary)s, %(payload)s
                        FROM {self._events}
                        WHERE run_id = %(run_id)s
                        RETURNING id, run_id, sequence, occurred_at,
                                  event_type, source, channel, summary, payload
                    """,
                    {
                        "run_id": run_id,
                        "event_type": event_type,
                        "source": source,
                        "channel": channel,
                        "summary": summary,
                        "payload": Jsonb(payload),
                    },
                )
                row = cursor.fetchone()
        if row is None:
            raise RuntimeError("写入 Run 事件后未返回记录")
        return row

    def events(
        self,
        run_id: str,
        *,
        after_sequence: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        return self._postgres.fetch_all(
            f"""
                SELECT id, run_id, sequence, occurred_at, event_type,
                       source, channel, summary, payload
                FROM {self._events}
                WHERE run_id = %(run_id)s
                  AND sequence > %(after_sequence)s
                ORDER BY sequence
                LIMIT %(limit)s
            """,
            {
                "run_id": run_id,
                "after_sequence": after_sequence,
                "limit": limit,
            },
        )

    def fail_interrupted(self) -> int:
        return self._postgres.execute(
            f"""
                UPDATE {self._runs}
                SET status = 'failed',
                    failure_code = 'platform_restarted',
                    failure_reason = '平台重启，原执行器进程已无法继续跟踪',
                    finished_at = now(),
                    updated_at = now()
                WHERE status IN ('queued', 'running')
            """
        )
