from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from psycopg.types.json import Jsonb

from src.database import PGConnector


WORK_COLUMNS = """
    work.id, work.requirement_id, work.requirement_revision_id,
    work.title, work.status, work.owner_id, work.reviewer_id,
    work.timebox_start, work.timebox_end, work.repository_path,
    work.base_commit, work.worktree_path, work.branch_name,
    work.created_by, work.created_at, work.updated_at, work.accepted_at
"""

RUN_SUMMARY_COLUMNS = """
    run.id, run.agent_id, run.agent_name, run.title, run.actor_id,
    run.status, run.model, run.branch_name, run.executor,
    run.executor_session_id, run.subject_type, run.subject_id,
    run.thread_id, run.trigger_action, run.work_id, run.plan_step_id,
    run.exit_code, run.failure_code, run.created_at, run.started_at,
    run.finished_at, run.updated_at
"""


class WorkRepository:
    def __init__(self, postgres: PGConnector) -> None:
        self._postgres = postgres
        schema = postgres.schema
        self._works = f"{schema}.t_collab_work"
        self._plans = f"{schema}.t_collab_work_plan"
        self._steps = f"{schema}.t_collab_plan_step"
        self._evidence = f"{schema}.t_collab_work_evidence"
        self._decisions = f"{schema}.t_collab_work_decision"
        self._requirements = f"{schema}.t_collab_requirement"
        self._revisions = f"{schema}.t_collab_requirement_revision"
        self._threads = f"{schema}.t_collab_thread"
        self._entries = f"{schema}.t_collab_thread_entry"
        self._runs = f"{schema}.t_agent_run"

    def create(
        self,
        *,
        work_id: str,
        plan_id: str,
        requirement_id: str,
        title: str | None,
        owner_id: str,
        reviewer_id: str,
        timebox_start: datetime | None,
        timebox_end: datetime | None,
        repository_path: str,
        base_commit: str,
        worktree_path: str,
        branch_name: str,
        actor_id: str,
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s::text))",
                (repository_path,),
            )
            requirement = connection.execute(
                f"""
                    SELECT id, title, status, commitment, accepted_revision_id
                    FROM {self._requirements}
                    WHERE id = %s
                    FOR UPDATE
                """,
                (requirement_id,),
            ).fetchone()
            if requirement is None:
                raise KeyError(requirement_id)
            if (
                requirement["status"] != "accepted"
                or not requirement["accepted_revision_id"]
                or requirement["commitment"] != "NEXT"
            ):
                raise ValueError("只有 accepted + NEXT 且冻结 Revision 的 Requirement 可以创建 Work")
            existing = connection.execute(
                f"SELECT id FROM {self._works} WHERE requirement_id = %s",
                (requirement_id,),
            ).fetchone()
            if existing is not None:
                raise ValueError(f"Requirement 已有关联 Work：{existing['id']}")
            active = connection.execute(
                f"""
                    SELECT id FROM {self._works}
                    WHERE repository_path = %s
                      AND status IN (
                          'planned', 'in_progress', 'in_review', 'revision_requested'
                      )
                """,
                (repository_path,),
            ).fetchone()
            if active is not None:
                raise ValueError(f"目标仓库已有写入型 Work：{active['id']}")

            connection.execute(
                f"""
                    INSERT INTO {self._works} (
                        id, requirement_id, requirement_revision_id, title,
                        owner_id, reviewer_id, timebox_start, timebox_end,
                        repository_path, base_commit, worktree_path, branch_name,
                        created_by
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                """,
                (
                    work_id,
                    requirement_id,
                    requirement["accepted_revision_id"],
                    title.strip() if title and title.strip() else requirement["title"],
                    owner_id,
                    reviewer_id,
                    timebox_start,
                    timebox_end,
                    repository_path,
                    base_commit,
                    worktree_path,
                    branch_name,
                    actor_id,
                ),
            )
            connection.execute(
                f"""
                    INSERT INTO {self._plans} (
                        id, work_id, recipe_key, created_by
                    ) VALUES (%s, %s, 'standard_development_v1', %s)
                """,
                (plan_id, work_id, actor_id),
            )
            with connection.cursor() as cursor:
                cursor.executemany(
                    f"""
                        INSERT INTO {self._steps} (
                            id, work_plan_id, position, step_key, title, description,
                            actor_kind, agent_id, default_executor, status
                        ) VALUES (
                            %(id)s, %(plan_id)s, %(position)s, %(step_key)s,
                            %(title)s, %(description)s, %(actor_kind)s,
                            %(agent_id)s, %(default_executor)s, %(status)s
                        )
                    """,
                    [{**step, "plan_id": plan_id} for step in steps],
                )
            connection.execute(
                f"""
                    UPDATE {self._requirements}
                    SET commitment = 'NOW', updated_at = now()
                    WHERE id = %s
                """,
                (requirement_id,),
            )
            thread = connection.execute(
                f"""
                    SELECT id FROM {self._threads}
                    WHERE subject_type = 'requirement' AND subject_id = %s
                """,
                (requirement_id,),
            ).fetchone()
            if thread is not None:
                connection.execute(
                    f"""
                        INSERT INTO {self._entries} (
                            thread_id, entry_type, actor_type, actor_id, body, payload
                        ) VALUES (%s, 'system', 'system', 'system', %s, %s)
                    """,
                    (
                        thread["id"],
                        "已创建首个 Work，Requirement 进入 NOW",
                        Jsonb({"action": "work.created", "work_id": work_id}),
                    ),
                )
        result = self.detail(work_id)
        if result is None:
            raise RuntimeError("创建 Work 后无法回读")
        return result

    def list(
        self,
        *,
        limit: int,
        offset: int,
        statuses: Iterable[str] = (),
    ) -> tuple[list[dict[str, Any]], int]:
        values = tuple(statuses)
        where = "WHERE work.status = ANY(%(statuses)s)" if values else ""
        rows = self._postgres.fetch_all(
            f"""
                SELECT work.id, work.requirement_id, work.requirement_revision_id,
                       requirement.title AS requirement_title, work.title,
                       work.status, work.owner_id, work.reviewer_id,
                       work.repository_path, work.base_commit, work.branch_name,
                       COUNT(DISTINCT run.id)::integer AS run_count,
                       COUNT(DISTINCT step.id) FILTER (
                           WHERE step.status = 'completed'
                       )::integer AS completed_step_count,
                       COUNT(DISTINCT step.id)::integer AS step_count,
                       work.created_at, work.updated_at,
                       COUNT(*) OVER()::integer AS total_count
                FROM {self._works} AS work
                JOIN {self._requirements} AS requirement
                  ON requirement.id = work.requirement_id
                JOIN {self._plans} AS plan ON plan.work_id = work.id
                JOIN {self._steps} AS step ON step.work_plan_id = plan.id
                LEFT JOIN {self._runs} AS run ON run.work_id = work.id
                {where}
                GROUP BY work.id, requirement.title
                ORDER BY work.updated_at DESC, work.id DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """,
            {"statuses": list(values), "limit": limit, "offset": offset},
        )
        total = int(rows[0]["total_count"]) if rows else 0
        for row in rows:
            row.pop("total_count", None)
        return rows, total

    @staticmethod
    def _display_status(step: dict[str, Any]) -> str:
        if step["status"] == "completed":
            return "completed"
        runs = step["runs"]
        if runs:
            latest = runs[0]
            if latest["status"] in {"queued", "running"}:
                return "running"
            if latest["status"] == "succeeded":
                return "awaiting_gate"
            return "failed"
        return "ready" if step["status"] == "ready" else "blocked"

    def detail(self, work_id: str) -> dict[str, Any] | None:
        work = self._postgres.fetch_one(
            f"""
                SELECT {WORK_COLUMNS},
                       requirement.title AS requirement_title,
                       requirement.status AS requirement_status,
                       plan.id AS plan_id, plan.recipe_key, plan.revision_no,
                       plan.status AS plan_status,
                       plan.created_by AS plan_created_by,
                       plan.created_at AS plan_created_at,
                       plan.completed_at AS plan_completed_at
                FROM {self._works} AS work
                JOIN {self._requirements} AS requirement
                  ON requirement.id = work.requirement_id
                JOIN {self._plans} AS plan ON plan.work_id = work.id
                WHERE work.id = %(id)s
            """,
            {"id": work_id},
        )
        if work is None:
            return None
        steps = self._postgres.fetch_all(
            f"""
                SELECT step.id, step.work_plan_id, step.position, step.step_key,
                       step.title, step.description, step.actor_kind, step.agent_id,
                       step.default_executor, step.status, step.completion_note,
                       step.completed_by, step.completed_at,
                       step.created_at, step.updated_at
                FROM {self._steps} AS step
                WHERE step.work_plan_id = %(plan_id)s
                ORDER BY step.position
            """,
            {"plan_id": work["plan_id"]},
        )
        runs = self._postgres.fetch_all(
            f"""
                SELECT {RUN_SUMMARY_COLUMNS}
                FROM {self._runs} AS run
                WHERE run.work_id = %(work_id)s
                ORDER BY run.created_at DESC, run.id DESC
            """,
            {"work_id": work_id},
        )
        runs_by_step: dict[str, list[dict[str, Any]]] = {}
        for run in runs:
            runs_by_step.setdefault(str(run["plan_step_id"]), []).append(run)
        for step in steps:
            step["runs"] = runs_by_step.get(str(step["id"]), [])
            step["display_status"] = self._display_status(step)

        evidence = self._postgres.fetch_one(
            f"""
                SELECT id, work_id, payload, created_by, created_at
                FROM {self._evidence}
                WHERE work_id = %(work_id)s
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            """,
            {"work_id": work_id},
        )
        decisions = self._postgres.fetch_all(
            f"""
                SELECT id, work_id, decision_type, reason, evidence_id,
                       commit_sha, actor_id, created_at
                FROM {self._decisions}
                WHERE work_id = %(work_id)s
                ORDER BY created_at DESC, id DESC
            """,
            {"work_id": work_id},
        )
        result = dict(work)
        result["run_count"] = len(runs)
        result["completed_step_count"] = sum(
            1 for step in steps if step["status"] == "completed"
        )
        result["step_count"] = len(steps)
        result["plan"] = {
            "id": result.pop("plan_id"),
            "work_id": work_id,
            "recipe_key": result.pop("recipe_key"),
            "revision_no": result.pop("revision_no"),
            "status": result.pop("plan_status"),
            "created_by": result.pop("plan_created_by"),
            "created_at": result.pop("plan_created_at"),
            "completed_at": result.pop("plan_completed_at"),
            "steps": steps,
        }
        result["latest_evidence"] = evidence
        result["decisions"] = decisions
        return result

    def mark_started(self, work_id: str) -> None:
        updated = self._postgres.execute(
            f"""
                UPDATE {self._works}
                SET status = CASE
                        WHEN status IN ('planned', 'revision_requested') THEN 'in_progress'
                        ELSE status
                    END,
                    updated_at = now()
                WHERE id = %(id)s AND status <> 'accepted'
            """,
            {"id": work_id},
        )
        if updated == 0:
            current = self.detail(work_id)
            if current is None:
                raise KeyError(work_id)
            raise ValueError(f"Work 当前状态不可启动步骤：{current['status']}")

    def update_metadata(
        self,
        *,
        work_id: str,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        allowed = {"owner_id", "reviewer_id", "timebox_start", "timebox_end"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"不允许更新 Work 字段：{', '.join(sorted(unknown))}")
        if not changes:
            raise ValueError("至少提交一项 Work 元数据")
        with self._postgres.transaction() as connection:
            current = connection.execute(
                f"SELECT * FROM {self._works} WHERE id = %s FOR UPDATE",
                (work_id,),
            ).fetchone()
            if current is None:
                raise KeyError(work_id)
            if current["status"] in {"accepted", "cancelled"}:
                raise ValueError(f"Work 当前状态不可更新：{current['status']}")
            start = changes.get("timebox_start", current["timebox_start"])
            end = changes.get("timebox_end", current["timebox_end"])
            if start is not None and end is not None and end <= start:
                raise ValueError("时间盒结束时间必须晚于开始时间")
            assignments = [f"{key} = %({key})s" for key in changes]
            connection.execute(
                f"""
                    UPDATE {self._works}
                    SET {', '.join(assignments)}, updated_at = now()
                    WHERE id = %(work_id)s
                """,
                {"work_id": work_id, **changes},
            )
        result = self.detail(work_id)
        if result is None:
            raise KeyError(work_id)
        return result

    def step_context(self, work_id: str, position: int) -> dict[str, Any]:
        revision = self._postgres.fetch_one(
            f"""
                SELECT revision.content
                FROM {self._works} AS work
                JOIN {self._revisions} AS revision
                  ON revision.id = work.requirement_revision_id
                WHERE work.id = %(work_id)s
            """,
            {"work_id": work_id},
        )
        if revision is None:
            raise KeyError(work_id)
        upstream = self._postgres.fetch_all(
            f"""
                SELECT step.step_key, step.completion_note,
                       latest.id AS latest_run_id,
                       left(latest.result_summary, 8000) AS latest_result_summary
                FROM {self._steps} AS step
                JOIN {self._plans} AS plan ON plan.id = step.work_plan_id
                LEFT JOIN LATERAL (
                    SELECT run.id, run.result_summary
                    FROM {self._runs} AS run
                    WHERE run.work_id = %(work_id)s
                      AND run.plan_step_id = step.id
                      AND run.status = 'succeeded'
                    ORDER BY run.created_at DESC, run.id DESC
                    LIMIT 1
                ) AS latest ON true
                WHERE plan.work_id = %(work_id)s
                  AND step.position < %(position)s
                ORDER BY step.position
            """,
            {"work_id": work_id, "position": position},
        )
        return {"requirement_content": revision["content"], "upstream": upstream}

    def complete_step(
        self,
        *,
        work_id: str,
        step_id: str,
        note: str,
        actor_id: str,
    ) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            work = connection.execute(
                f"SELECT id, status FROM {self._works} WHERE id = %s FOR UPDATE",
                (work_id,),
            ).fetchone()
            if work is None:
                raise KeyError(work_id)
            if work["status"] in {"accepted", "cancelled"}:
                raise ValueError(f"Work 当前状态不可确认步骤：{work['status']}")
            step = connection.execute(
                f"""
                    SELECT step.* FROM {self._steps} AS step
                    JOIN {self._plans} AS plan ON plan.id = step.work_plan_id
                    WHERE step.id = %s AND plan.work_id = %s
                    FOR UPDATE
                """,
                (step_id, work_id),
            ).fetchone()
            if step is None:
                raise KeyError(step_id)
            if step["actor_kind"] != "agent":
                raise ValueError("人工接受步骤只能通过 Work 决定完成")
            if step["status"] == "completed":
                raise ValueError("步骤已经完成")
            blocked = connection.execute(
                f"""
                    SELECT count(*)::integer AS count
                    FROM {self._steps}
                    WHERE work_plan_id = %s
                      AND position < %s
                      AND status <> 'completed'
                """,
                (step["work_plan_id"], step["position"]),
            ).fetchone()
            if blocked and blocked["count"]:
                raise ValueError("前序步骤尚未完成")
            latest = connection.execute(
                f"""
                    SELECT id, status FROM {self._runs}
                    WHERE work_id = %s AND plan_step_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                """,
                (work_id, step_id),
            ).fetchone()
            if latest is None or latest["status"] != "succeeded":
                raise ValueError("步骤需要最近一次 Run 成功后才能确认完成")
            connection.execute(
                f"""
                    UPDATE {self._steps}
                    SET status = 'completed', completion_note = %s,
                        completed_by = %s, completed_at = now(), updated_at = now()
                    WHERE id = %s
                """,
                (note.strip(), actor_id, step_id),
            )
            next_step = connection.execute(
                f"""
                    SELECT id, actor_kind FROM {self._steps}
                    WHERE work_plan_id = %s AND position = %s
                """,
                (step["work_plan_id"], step["position"] + 1),
            ).fetchone()
            if next_step is not None:
                connection.execute(
                    f"UPDATE {self._steps} SET status = 'ready', updated_at = now() WHERE id = %s",
                    (next_step["id"],),
                )
                if next_step["actor_kind"] == "human":
                    connection.execute(
                        f"UPDATE {self._works} SET status = 'in_review', updated_at = now() WHERE id = %s",
                        (work_id,),
                    )
                else:
                    connection.execute(
                        f"UPDATE {self._works} SET status = 'in_progress', updated_at = now() WHERE id = %s",
                        (work_id,),
                    )
        result = self.detail(work_id)
        if result is None:
            raise KeyError(work_id)
        return result

    def add_evidence(
        self,
        *,
        evidence_id: str,
        work_id: str,
        payload: dict[str, Any],
        actor_id: str,
    ) -> dict[str, Any]:
        row = self._postgres.fetch_one(
            f"""
                INSERT INTO {self._evidence} (id, work_id, payload, created_by)
                SELECT %(id)s, id, %(payload)s, %(actor_id)s
                FROM {self._works}
                WHERE id = %(work_id)s
                RETURNING id, work_id, payload, created_by, created_at
            """,
            {
                "id": evidence_id,
                "work_id": work_id,
                "payload": Jsonb(payload),
                "actor_id": actor_id,
            },
        )
        if row is None:
            raise KeyError(work_id)
        self._postgres.execute(
            f"UPDATE {self._works} SET updated_at = now() WHERE id = %(id)s",
            {"id": work_id},
        )
        return row

    def decide(
        self,
        *,
        decision_id: str,
        work_id: str,
        decision_type: str,
        reason: str,
        actor_id: str,
    ) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            work = connection.execute(
                f"SELECT * FROM {self._works} WHERE id = %s FOR UPDATE",
                (work_id,),
            ).fetchone()
            if work is None:
                raise KeyError(work_id)
            if work["status"] in {"accepted", "cancelled"}:
                raise ValueError(f"Work 当前状态不可决策：{work['status']}")
            evidence_id = None
            commit_sha = None
            if decision_type == "accept":
                incomplete = connection.execute(
                    f"""
                        SELECT count(*)::integer AS count
                        FROM {self._steps} AS step
                        JOIN {self._plans} AS plan ON plan.id = step.work_plan_id
                        WHERE plan.work_id = %s
                          AND step.actor_kind = 'agent'
                          AND step.status <> 'completed'
                    """,
                    (work_id,),
                ).fetchone()
                if incomplete and incomplete["count"]:
                    raise ValueError("前五个 Agent 步骤尚未全部确认完成")
                evidence = connection.execute(
                    f"""
                        SELECT id, payload FROM {self._evidence}
                        WHERE work_id = %s
                        ORDER BY created_at DESC, id DESC
                        LIMIT 1
                    """,
                    (work_id,),
                ).fetchone()
                if evidence is None:
                    raise ValueError("接受交付前必须保存交付证据")
                payload = evidence["payload"]
                required = {
                    "verification_summary": "验证摘要",
                    "review_summary": "审查摘要",
                    "head_commit": "最终 Commit",
                }
                missing = [label for key, label in required.items() if not payload.get(key)]
                if missing:
                    raise ValueError(f"接受交付前必须补齐：{'、'.join(missing)}")
                if payload.get("head_commit") == work["base_commit"]:
                    raise ValueError("最终 Commit 仍等于 base commit")
                if payload.get("worktree_status"):
                    raise ValueError("worktree 仍有未提交变更")
                evidence_id = evidence["id"]
                commit_sha = payload["head_commit"]
                connection.execute(
                    f"""
                        UPDATE {self._works}
                        SET status = 'accepted', accepted_at = now(), updated_at = now()
                        WHERE id = %s
                    """,
                    (work_id,),
                )
                connection.execute(
                    f"""
                        UPDATE {self._steps} AS step
                        SET status = 'completed', completion_note = %s,
                            completed_by = %s, completed_at = now(), updated_at = now()
                        FROM {self._plans} AS plan
                        WHERE plan.id = step.work_plan_id
                          AND plan.work_id = %s
                          AND step.step_key = 'acceptance'
                    """,
                    (reason.strip(), actor_id, work_id),
                )
                connection.execute(
                    f"""
                        UPDATE {self._plans}
                        SET status = 'completed', completed_at = now()
                        WHERE work_id = %s
                    """,
                    (work_id,),
                )
            else:
                connection.execute(
                    f"""
                        UPDATE {self._works}
                        SET status = 'revision_requested', updated_at = now()
                        WHERE id = %s
                    """,
                    (work_id,),
                )
                connection.execute(
                    f"""
                        UPDATE {self._steps} AS step
                        SET status = CASE
                                WHEN step.step_key = 'development' THEN 'ready'
                                ELSE 'pending'
                            END,
                            completion_note = NULL,
                            completed_by = NULL,
                            completed_at = NULL,
                            updated_at = now()
                        FROM {self._plans} AS plan
                        WHERE plan.id = step.work_plan_id
                          AND plan.work_id = %s
                          AND step.position >= 3
                    """,
                    (work_id,),
                )
                connection.execute(
                    f"""
                        UPDATE {self._plans}
                        SET status = 'active', completed_at = NULL
                        WHERE work_id = %s
                    """,
                    (work_id,),
                )
            row = connection.execute(
                f"""
                    INSERT INTO {self._decisions} (
                        id, work_id, decision_type, reason,
                        evidence_id, commit_sha, actor_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, work_id, decision_type, reason, evidence_id,
                              commit_sha, actor_id, created_at
                """,
                (
                    decision_id,
                    work_id,
                    decision_type,
                    reason.strip(),
                    evidence_id,
                    commit_sha,
                    actor_id,
                ),
            ).fetchone()
        if row is None:
            raise RuntimeError("创建 Work 决定后未返回记录")
        return row
