from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from psycopg.types.json import Jsonb

from src.database.pg_connector import PGConnector


RUN_COLUMNS = """
    id, workspace, item_id, attempt, retry_of, actor_id, instruction,
    prompt_snapshot, item_snapshot, context_snapshot, capability_snapshot,
    capability_candidate_id, context_version_id, context_revision_no, state, engine, runtime, image,
    requested_machine_id, machine_id, lease_id, lease_expires_at, model,
    sandbox, session_id, repository_path, repository_revision, directory,
    branch, environment_snapshot, result, result_payload, artifact_candidates,
    evidence_candidates, exit_code, failure_code, error,
    cancellation_requested_at, created_at, claimed_at, started_at,
    finished_at, updated_at
"""


class GongzuoRuntimeRepository:
    """PostgreSQL owner for execution nodes, immutable attempts, leases and events."""

    def __init__(self, postgres: PGConnector) -> None:
        schema = postgres.schema
        self._postgres = postgres
        self._machines = f"{schema}.t_gongzuo_machine"
        self._runs = f"{schema}.t_gongzuo_run"
        self._events = f"{schema}.t_gongzuo_run_event"

    def register_machine(self, machine: dict[str, Any]) -> dict[str, Any]:
        row = self._postgres.fetch_one(
            f"""
                INSERT INTO {self._machines} (
                    id, workspace, name, token_hash, capacity, capabilities
                ) VALUES (
                    %(id)s, %(workspace)s, %(name)s, %(token_hash)s,
                    %(capacity)s, %(capabilities)s
                )
                RETURNING id, workspace, name, status, capacity, capabilities,
                          last_seen_at, created_at, updated_at
            """,
            {**machine, "capabilities": Jsonb(machine["capabilities"])},
        )
        if row is None:
            raise RuntimeError("注册执行机后未返回记录")
        return row

    def machine_credentials(self, workspace: str, machine_id: str) -> dict[str, Any] | None:
        return self._postgres.fetch_one(
            f"""
                SELECT id, workspace, token_hash, status, capacity, capabilities,
                       last_seen_at
                FROM {self._machines}
                WHERE workspace = %(workspace)s AND id = %(id)s
            """,
            {"workspace": workspace, "id": machine_id},
        )

    def list_machines(self, workspace: str, *, offline_after_seconds: int) -> list[dict[str, Any]]:
        return self._postgres.fetch_all(
            f"""
                SELECT m.id, m.workspace, m.name,
                       CASE
                           WHEN m.last_seen_at < now() - (%(offline)s * interval '1 second')
                           THEN 'offline'
                           ELSE m.status
                       END AS status,
                       m.capacity, m.capabilities, m.last_seen_at,
                       COUNT(r.id) FILTER (
                           WHERE r.state IN ('claimed', 'running', 'pause_requested', 'cancelling')
                             AND r.lease_expires_at > now()
                       )::integer AS active_runs,
                       MIN(r.id) FILTER (
                           WHERE r.state IN ('claimed', 'running', 'pause_requested', 'cancelling')
                             AND r.lease_expires_at > now()
                       ) AS current_run_id
                FROM {self._machines} m
                LEFT JOIN {self._runs} r ON r.machine_id = m.id
                WHERE m.workspace = %(workspace)s
                GROUP BY m.id
                ORDER BY m.created_at
            """,
            {"workspace": workspace, "offline": offline_after_seconds},
        )

    def set_machine_status(self, workspace: str, machine_id: str, status: str) -> dict[str, Any]:
        row = self._postgres.fetch_one(
            f"""
                UPDATE {self._machines}
                SET status = %(status)s, updated_at = now()
                WHERE workspace = %(workspace)s AND id = %(id)s
                RETURNING id, workspace, name, status, capacity, capabilities,
                          last_seen_at, created_at, updated_at
            """,
            {"workspace": workspace, "id": machine_id, "status": status},
        )
        if row is None:
            raise KeyError(machine_id)
        return row

    def create_run(self, run: dict[str, Any]) -> dict[str, Any]:
        json_fields = {
            "item_snapshot",
            "context_snapshot",
            "capability_snapshot",
            "environment_snapshot",
            "artifact_candidates",
            "evidence_candidates",
        }
        params = {
            key: Jsonb(value) if key in json_fields else value
            for key, value in run.items()
        }
        with self._postgres.transaction() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s::text))",
                (f"{run['workspace']}:{run['item_id']}",),
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        SELECT COALESCE(MAX(attempt), 0)::integer + 1 AS attempt
                        FROM {self._runs}
                        WHERE workspace = %(workspace)s AND item_id = %(item_id)s
                    """,
                    {"workspace": run["workspace"], "item_id": run["item_id"]},
                )
                params["attempt"] = int(cursor.fetchone()["attempt"])
                cursor.execute(
                    f"""
                        INSERT INTO {self._runs} (
                            id, workspace, item_id, attempt, retry_of, actor_id,
                            instruction, prompt_snapshot, item_snapshot,
                            context_snapshot, capability_snapshot, capability_candidate_id,
                            context_version_id, context_revision_no, state,
                            engine, runtime, image, requested_machine_id, model,
                            sandbox, repository_path, repository_revision,
                            directory, branch, environment_snapshot,
                            artifact_candidates, evidence_candidates
                        ) VALUES (
                            %(id)s, %(workspace)s, %(item_id)s, %(attempt)s,
                            %(retry_of)s, %(actor_id)s, %(instruction)s,
                            %(prompt_snapshot)s, %(item_snapshot)s,
                            %(context_snapshot)s, %(capability_snapshot)s, %(capability_candidate_id)s,
                            %(context_version_id)s, %(context_revision_no)s,
                            'queued', %(engine)s, %(runtime)s, %(image)s,
                            %(requested_machine_id)s, %(model)s, %(sandbox)s,
                            %(repository_path)s, %(repository_revision)s,
                            %(directory)s, %(branch)s, %(environment_snapshot)s,
                            %(artifact_candidates)s, %(evidence_candidates)s
                        ) RETURNING {RUN_COLUMNS}
                    """,
                    params,
                )
                row = cursor.fetchone()
                cursor.execute(
                    f"""
                        INSERT INTO {self._events} (
                            run_id, sequence, event_type, source, summary, payload
                        ) VALUES (
                            %(id)s, 1, 'run.queued', 'platform',
                            '委托已进入执行队列', %(payload)s
                        )
                    """,
                    {
                        "id": run["id"],
                        "payload": Jsonb(
                            {
                                "itemId": run["item_id"],
                                "attempt": params["attempt"],
                                "contextVersionId": run["context_version_id"],
                                "contextRevisionNo": run["context_revision_no"],
                                "engine": run["engine"],
                                "runtime": run["runtime"],
                            }
                        ),
                    },
                )
        if row is None:
            raise RuntimeError("创建 Run 后未返回记录")
        return row

    def next_attempt(self, workspace: str, item_id: str) -> int:
        row = self._postgres.fetch_one(
            f"""
                SELECT COALESCE(MAX(attempt), 0)::integer + 1 AS next_attempt
                FROM {self._runs}
                WHERE workspace = %(workspace)s AND item_id = %(item_id)s
            """,
            {"workspace": workspace, "item_id": item_id},
        )
        return int(row["next_attempt"]) if row else 1

    def get_run(self, workspace: str, run_id: str) -> dict[str, Any] | None:
        return self._postgres.fetch_one(
            f"SELECT {RUN_COLUMNS} FROM {self._runs} WHERE workspace = %(workspace)s AND id = %(id)s",
            {"workspace": workspace, "id": run_id},
        )

    def list_runs(
        self,
        workspace: str,
        *,
        limit: int,
        offset: int,
        item_id: str | None = None,
        states: Iterable[str] = (),
    ) -> tuple[list[dict[str, Any]], int]:
        clauses = ["workspace = %(workspace)s"]
        params: dict[str, Any] = {"workspace": workspace, "limit": limit, "offset": offset}
        if item_id:
            clauses.append("item_id = %(item_id)s")
            params["item_id"] = item_id
        state_values = list(states)
        if state_values:
            clauses.append("state = ANY(%(states)s)")
            params["states"] = state_values
        rows = self._postgres.fetch_all(
            f"""
                SELECT {RUN_COLUMNS}, COUNT(*) OVER()::integer AS total_count
                FROM {self._runs}
                WHERE {' AND '.join(clauses)}
                ORDER BY created_at DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        total = int(rows[0]["total_count"]) if rows else 0
        for row in rows:
            row.pop("total_count", None)
        return rows, total

    def events(self, workspace: str, run_id: str, *, after_sequence: int, limit: int) -> list[dict[str, Any]]:
        return self._postgres.fetch_all(
            f"""
                SELECT e.id, e.run_id, e.sequence, e.occurred_at, e.event_type,
                       e.source, e.channel, e.summary, e.payload
                FROM {self._events} e
                JOIN {self._runs} r ON r.id = e.run_id
                WHERE r.workspace = %(workspace)s AND e.run_id = %(run_id)s
                  AND e.sequence > %(after)s
                ORDER BY e.sequence
                LIMIT %(limit)s
            """,
            {"workspace": workspace, "run_id": run_id, "after": after_sequence, "limit": limit},
        )

    def append_event(
        self,
        *,
        workspace: str,
        run_id: str,
        event_type: str,
        source: str,
        summary: str,
        payload: dict[str, Any],
        channel: str | None = None,
        machine_id: str | None = None,
        lease_id: str | None = None,
    ) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s::text))", (run_id,))
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        INSERT INTO {self._events} (
                            run_id, sequence, event_type, source, channel, summary, payload
                        )
                        SELECT r.id, COALESCE(MAX(e.sequence), 0) + 1,
                               %(event_type)s, %(source)s, %(channel)s,
                               %(summary)s, %(payload)s
                        FROM {self._runs} r
                        LEFT JOIN {self._events} e ON e.run_id = r.id
                        WHERE r.workspace = %(workspace)s AND r.id = %(run_id)s
                          AND (%(machine_id)s::varchar(64) IS NULL OR r.machine_id = %(machine_id)s::varchar(64))
                          AND (%(lease_id)s::varchar(64) IS NULL OR r.lease_id = %(lease_id)s::varchar(64))
                        GROUP BY r.id
                        RETURNING id, run_id, sequence, occurred_at, event_type,
                                  source, channel, summary, payload
                    """,
                    {
                        "workspace": workspace,
                        "run_id": run_id,
                        "event_type": event_type,
                        "source": source,
                        "channel": channel,
                        "summary": summary,
                        "payload": Jsonb(payload),
                        "machine_id": machine_id,
                        "lease_id": lease_id,
                    },
                )
                row = cursor.fetchone()
        if row is None:
            raise PermissionError("Run 不存在，或机器租约不匹配")
        return row

    def claim_next(
        self,
        *,
        workspace: str,
        machine_id: str,
        lease_id: str,
        lease_seconds: int,
    ) -> dict[str, Any] | None:
        with self._postgres.transaction() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        SELECT id, status, capacity, capabilities
                        FROM {self._machines}
                        WHERE workspace = %(workspace)s AND id = %(machine_id)s
                        FOR UPDATE
                    """,
                    {"workspace": workspace, "machine_id": machine_id},
                )
                machine = cursor.fetchone()
                if machine is None:
                    raise KeyError(machine_id)
                cursor.execute(
                    f"UPDATE {self._machines} SET last_seen_at = now(), updated_at = now() WHERE id = %(id)s",
                    {"id": machine_id},
                )
                if machine["status"] != "online":
                    return None
                cursor.execute(
                    f"""
                        SELECT COUNT(*)::integer AS active
                        FROM {self._runs}
                        WHERE machine_id = %(machine_id)s
                          AND state IN ('claimed', 'running', 'pause_requested', 'cancelling')
                          AND lease_expires_at > now()
                    """,
                    {"machine_id": machine_id},
                )
                active = cursor.fetchone()
                if active and int(active["active"]) >= int(machine["capacity"]):
                    return None
                capabilities = machine["capabilities"] or {}
                engines = list(capabilities.get("engines") or [])
                runtimes = list(capabilities.get("runtimes") or [])
                images = list(capabilities.get("images") or [])
                cursor.execute(
                    f"""
                        SELECT id
                        FROM {self._runs}
                        WHERE workspace = %(workspace)s AND state = 'queued'
                          AND engine = ANY(%(engines)s)
                          AND runtime = ANY(%(runtimes)s)
                          AND (requested_machine_id IS NULL OR requested_machine_id = %(machine_id)s)
                          AND (runtime <> 'docker' OR image IS NULL OR image = ANY(%(images)s))
                        ORDER BY created_at
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    """,
                    {
                        "workspace": workspace,
                        "machine_id": machine_id,
                        "engines": engines,
                        "runtimes": runtimes,
                        "images": images,
                    },
                )
                selected = cursor.fetchone()
                if selected is None:
                    return None
                cursor.execute(
                    f"""
                        UPDATE {self._runs}
                        SET state = 'claimed', machine_id = %(machine_id)s,
                            lease_id = %(lease_id)s,
                            lease_expires_at = now() + (%(lease_seconds)s * interval '1 second'),
                            claimed_at = now(), updated_at = now()
                        WHERE id = %(id)s
                        RETURNING {RUN_COLUMNS}
                    """,
                    {
                        "id": selected["id"],
                        "machine_id": machine_id,
                        "lease_id": lease_id,
                        "lease_seconds": lease_seconds,
                    },
                )
                row = cursor.fetchone()
                cursor.execute(
                    f"""
                        INSERT INTO {self._events} (
                            run_id, sequence, event_type, source, summary, payload
                        )
                        SELECT %(id)s::varchar(64), COALESCE(MAX(sequence), 0) + 1,
                               'run.claimed', 'worker', '执行机已取得租约', %(payload)s
                        FROM {self._events} WHERE run_id = %(id)s
                    """,
                    {
                        "id": selected["id"],
                        "payload": Jsonb({"machineId": machine_id, "leaseSeconds": lease_seconds}),
                    },
                )
        return row

    def heartbeat(
        self,
        *,
        workspace: str,
        machine_id: str,
        leases: list[dict[str, str]],
        lease_seconds: int,
    ) -> list[dict[str, Any]]:
        commands: list[dict[str, Any]] = []
        with self._postgres.transaction() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        UPDATE {self._machines}
                        SET last_seen_at = now(), updated_at = now()
                        WHERE workspace = %(workspace)s AND id = %(machine_id)s
                    """,
                    {"workspace": workspace, "machine_id": machine_id},
                )
                if cursor.rowcount != 1:
                    raise KeyError(machine_id)
                for lease in leases:
                    cursor.execute(
                        f"""
                            UPDATE {self._runs}
                            SET lease_expires_at = now() + (%(lease_seconds)s * interval '1 second'),
                                updated_at = now()
                            WHERE workspace = %(workspace)s AND id = %(run_id)s
                              AND machine_id = %(machine_id)s AND lease_id = %(lease_id)s
                              AND state IN ('claimed', 'running', 'pause_requested', 'cancelling')
                            RETURNING state
                        """,
                        {
                            "workspace": workspace,
                            "run_id": lease["run_id"],
                            "machine_id": machine_id,
                            "lease_id": lease["lease_id"],
                            "lease_seconds": lease_seconds,
                        },
                    )
                    row = cursor.fetchone()
                    if row is None:
                        commands.append({"runId": lease["run_id"], "leaseValid": False})
                    else:
                        commands.append(
                            {
                                "runId": lease["run_id"],
                                "leaseValid": True,
                                "cancelRequested": row["state"] == "cancelling",
                                "pauseRequested": row["state"] == "pause_requested",
                            }
                        )
        return commands

    def worker_report(
        self,
        *,
        workspace: str,
        machine_id: str,
        run_id: str,
        lease_id: str,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        allowed = {
            "state", "session_id", "exit_code", "result", "result_payload",
            "artifact_candidates", "evidence_candidates", "environment_snapshot",
            "failure_code", "error", "started_at", "finished_at",
        }
        if set(changes) - allowed:
            raise ValueError("Worker 回报包含不允许更新的字段")
        json_fields = {"result_payload", "artifact_candidates", "evidence_candidates", "environment_snapshot"}
        params: dict[str, Any] = {
            key: Jsonb(value) if key in json_fields and value is not None else value
            for key, value in changes.items()
        }
        identifiers = {
            "workspace": workspace,
            "machine_id": machine_id,
            "run_id": run_id,
            "lease_id": lease_id,
        }
        with self._postgres.transaction() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        SELECT state
                        FROM {self._runs}
                        WHERE workspace = %(workspace)s AND id = %(run_id)s
                          AND machine_id = %(machine_id)s AND lease_id = %(lease_id)s
                          AND state IN ('claimed', 'running', 'pause_requested', 'cancelling')
                        FOR UPDATE
                    """,
                    identifiers,
                )
                current = cursor.fetchone()
                if current is None:
                    raise PermissionError("租约已失效，拒绝接收 Worker 回报")
                current_state = str(current["state"])
                reported_state = str(changes["state"])
                if current_state == "cancelling":
                    effective_state = "cancelling" if reported_state == "running" else "cancelled"
                elif current_state == "pause_requested":
                    effective_state = "pause_requested" if reported_state == "running" else "paused"
                else:
                    effective_state = reported_state
                params["state"] = effective_state
                assignments = [f"{key} = %({key})s" for key in params]
                terminal = effective_state in {
                    "paused", "cancelled", "succeeded", "failed", "unavailable"
                }
                if terminal:
                    assignments.extend(["lease_id = NULL", "lease_expires_at = NULL"])
                cursor.execute(
                    f"""
                        UPDATE {self._runs}
                        SET {', '.join(assignments)}, updated_at = now()
                        WHERE workspace = %(workspace)s AND id = %(run_id)s
                          AND machine_id = %(machine_id)s AND lease_id = %(lease_id)s
                        RETURNING {RUN_COLUMNS}
                    """,
                    {**params, **identifiers},
                )
                row = cursor.fetchone()
        if row is None:
            raise PermissionError("租约已失效，拒绝接收 Worker 回报")
        row["reported_state"] = changes["state"]
        return row

    def request_stop(self, workspace: str, run_id: str, *, pause: bool) -> dict[str, Any]:
        target = "paused" if pause else "cancelled"
        pending = "pause_requested" if pause else "cancelling"
        row = self._postgres.fetch_one(
            f"""
                UPDATE {self._runs}
                SET state = CASE WHEN state = 'queued' THEN %(target)s ELSE %(pending)s END,
                    cancellation_requested_at = now(),
                    finished_at = CASE WHEN state = 'queued' THEN now() ELSE finished_at END,
                    updated_at = now()
                WHERE workspace = %(workspace)s AND id = %(run_id)s
                  AND state IN ('queued', 'claimed', 'running')
                RETURNING {RUN_COLUMNS}
            """,
            {"workspace": workspace, "run_id": run_id, "target": target, "pending": pending},
        )
        if row is None:
            existing = self.get_run(workspace, run_id)
            if existing is None:
                raise KeyError(run_id)
            raise ValueError(f"当前状态不能{'暂停' if pause else '取消'}：{existing['state']}")
        return row

    def recover_expired_leases(self) -> int:
        now = datetime.now(timezone.utc)
        with self._postgres.transaction() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                        UPDATE {self._runs}
                        SET state = 'failed', failure_code = 'lease_expired',
                            error = '执行机租约过期；为避免重复副作用，本次尝试不会自动重跑',
                            finished_at = %(now)s, lease_id = NULL, lease_expires_at = NULL,
                            updated_at = %(now)s
                        WHERE state IN ('claimed', 'running', 'pause_requested', 'cancelling')
                          AND lease_expires_at <= %(now)s
                        RETURNING id, workspace
                    """,
                    {"now": now},
                )
                rows = list(cursor.fetchall())
        for row in rows:
            self.append_event(
                workspace=str(row["workspace"]),
                run_id=str(row["id"]),
                event_type="run.lease_expired",
                source="platform",
                summary="执行机租约已过期，本次尝试终止",
                payload={},
            )
        return len(rows)
