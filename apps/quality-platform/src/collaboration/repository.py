from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from psycopg import Connection
from psycopg.types.json import Jsonb

from src.database import PGConnector


IDEA_COLUMNS = """
    idea.id, idea.title, idea.raw_content, idea.domain_key, idea.status,
    idea.created_by, idea.owner_id, idea.created_at, idea.updated_at
"""

REQUIREMENT_COLUMNS = """
    requirement.id, requirement.source_type, requirement.source_idea_id,
    requirement.title, requirement.status, requirement.current_revision_id,
    requirement.accepted_revision_id, requirement.commitment,
    requirement.owner_id, requirement.target_window,
    requirement.entry_condition, requirement.review_at,
    requirement.merged_into_id, requirement.created_by,
    requirement.created_at, requirement.updated_at
"""


class CollaborationRepository:
    def __init__(self, postgres: PGConnector) -> None:
        self._postgres = postgres
        schema = postgres.schema
        self._ideas = f"{schema}.t_collab_idea"
        self._requirements = f"{schema}.t_collab_requirement"
        self._revisions = f"{schema}.t_collab_requirement_revision"
        self._threads = f"{schema}.t_collab_thread"
        self._entries = f"{schema}.t_collab_thread_entry"
        self._decisions = f"{schema}.t_collab_decision"
        self._runs = f"{schema}.t_agent_run"

    @staticmethod
    def validate_acceptance_content(content: dict[str, Any]) -> None:
        required_fields = {
            "current_problem": "当前问题",
            "expected_outcome": "期望结果",
            "in_scope": "范围",
            "acceptance_criteria": "验收标准",
        }
        missing = []
        for field, label in required_fields.items():
            value = content.get(field)
            if value is None or value == [] or (
                isinstance(value, str) and not value.strip()
            ):
                missing.append(label)
        if missing:
            raise ValueError(f"接纳前必须补齐：{'、'.join(missing)}")

    @staticmethod
    def _entry(
        connection: Connection[dict[str, Any]],
        table: str,
        *,
        thread_id: str,
        entry_type: str,
        actor_type: str,
        actor_id: str,
        body: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = connection.execute(
            f"""
                INSERT INTO {table} (
                    thread_id, entry_type, actor_type, actor_id, body, payload
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, thread_id, entry_type, actor_type, actor_id,
                          body, payload, created_at
            """,
            (
                thread_id,
                entry_type,
                actor_type,
                actor_id,
                body,
                Jsonb(payload or {}),
            ),
        ).fetchone()
        if row is None:
            raise RuntimeError("创建协作时间线条目后未返回记录")
        return row

    def create_idea(
        self,
        *,
        idea_id: str,
        thread_id: str,
        title: str,
        raw_content: str,
        domain_key: str | None,
        actor_id: str,
    ) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            idea = connection.execute(
                f"""
                    INSERT INTO {self._ideas} (
                        id, title, raw_content, domain_key, created_by, owner_id
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                """,
                (idea_id, title, raw_content, domain_key, actor_id, actor_id),
            ).fetchone()
            connection.execute(
                f"""
                    INSERT INTO {self._threads} (id, subject_type, subject_id)
                    VALUES (%s, 'idea', %s)
                """,
                (thread_id, idea_id),
            )
            self._entry(
                connection,
                self._entries,
                thread_id=thread_id,
                entry_type="system",
                actor_type="system",
                actor_id="system",
                body="Idea 已记录，原始内容将保持不变",
                payload={"action": "idea.created"},
            )
        if idea is None:
            raise RuntimeError("创建 Idea 后未返回记录")
        return idea

    def list_ideas(
        self,
        *,
        limit: int,
        offset: int,
        statuses: Iterable[str] = (),
    ) -> tuple[list[dict[str, Any]], int]:
        values = tuple(statuses)
        where = "WHERE idea.status = ANY(%(statuses)s)" if values else ""
        rows = self._postgres.fetch_all(
            f"""
                SELECT idea.id, idea.title, idea.domain_key, idea.status,
                       idea.owner_id, idea.created_at, idea.updated_at,
                       requirement.id AS requirement_id,
                       COUNT(run.id)::integer AS run_count,
                       COUNT(*) OVER()::integer AS total_count
                FROM {self._ideas} AS idea
                LEFT JOIN {self._requirements} AS requirement
                  ON requirement.source_idea_id = idea.id
                LEFT JOIN {self._runs} AS run
                  ON run.subject_type = 'idea' AND run.subject_id = idea.id
                {where}
                GROUP BY idea.id, requirement.id
                ORDER BY idea.updated_at DESC, idea.id DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """,
            {"statuses": list(values), "limit": limit, "offset": offset},
        )
        total = int(rows[0]["total_count"]) if rows else 0
        for row in rows:
            row.pop("total_count", None)
        return rows, total

    def get_idea(self, idea_id: str) -> dict[str, Any] | None:
        return self._postgres.fetch_one(
            f"""
                SELECT {IDEA_COLUMNS}, thread.id AS thread_id,
                       requirement.id AS requirement_id,
                       COUNT(run.id)::integer AS run_count
                FROM {self._ideas} AS idea
                JOIN {self._threads} AS thread
                  ON thread.subject_type = 'idea' AND thread.subject_id = idea.id
                LEFT JOIN {self._requirements} AS requirement
                  ON requirement.source_idea_id = idea.id
                LEFT JOIN {self._runs} AS run
                  ON run.subject_type = 'idea' AND run.subject_id = idea.id
                WHERE idea.id = %(id)s
                GROUP BY idea.id, thread.id, requirement.id
            """,
            {"id": idea_id},
        )

    def archive_idea(self, idea_id: str) -> dict[str, Any]:
        row = self._postgres.fetch_one(
            f"""
                UPDATE {self._ideas}
                SET status = 'archived', updated_at = now()
                WHERE id = %(id)s AND status IN ('captured', 'discussing')
                RETURNING *
            """,
            {"id": idea_id},
        )
        if row is None:
            current = self.get_idea(idea_id)
            if current is None:
                raise KeyError(idea_id)
            raise ValueError(f"Idea 当前状态不可归档：{current['status']}")
        return row

    def add_message(
        self,
        *,
        subject_type: str,
        subject_id: str,
        body: str,
        actor_id: str,
    ) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            table = self._ideas if subject_type == "idea" else self._requirements
            subject = connection.execute(
                f"SELECT id FROM {table} WHERE id = %s FOR UPDATE",
                (subject_id,),
            ).fetchone()
            if subject is None:
                raise KeyError(subject_id)
            thread = connection.execute(
                f"""
                    SELECT id FROM {self._threads}
                    WHERE subject_type = %s AND subject_id = %s
                """,
                (subject_type, subject_id),
            ).fetchone()
            if thread is None:
                raise RuntimeError("业务对象缺少协作 Thread")
            entry = self._entry(
                connection,
                self._entries,
                thread_id=str(thread["id"]),
                entry_type="human_message",
                actor_type="admin",
                actor_id=actor_id,
                body=body,
            )
            if subject_type == "idea":
                connection.execute(
                    f"""
                        UPDATE {self._ideas}
                        SET status = CASE WHEN status = 'captured' THEN 'discussing' ELSE status END,
                            updated_at = now()
                        WHERE id = %s
                    """,
                    (subject_id,),
                )
            else:
                connection.execute(
                    f"UPDATE {self._requirements} SET updated_at = now() WHERE id = %s",
                    (subject_id,),
                )
        return entry

    def touch_subject(self, subject_type: str, subject_id: str) -> None:
        table = self._ideas if subject_type == "idea" else self._requirements
        status = (
            "status = CASE WHEN status = 'captured' THEN 'discussing' ELSE status END,"
            if subject_type == "idea"
            else ""
        )
        updated = self._postgres.execute(
            f"UPDATE {table} SET {status} updated_at = now() WHERE id = %(id)s",
            {"id": subject_id},
        )
        if updated == 0:
            raise KeyError(subject_id)

    def context_messages(
        self,
        *,
        subject_type: str,
        subject_id: str,
        limit: int = 10,
    ) -> list[str]:
        rows = self._postgres.fetch_all(
            f"""
                SELECT entry.body
                FROM {self._entries} AS entry
                JOIN {self._threads} AS thread ON thread.id = entry.thread_id
                WHERE thread.subject_type = %(subject_type)s
                  AND thread.subject_id = %(subject_id)s
                  AND entry.entry_type = 'human_message'
                ORDER BY entry.created_at DESC, entry.id DESC
                LIMIT %(limit)s
            """,
            {
                "subject_type": subject_type,
                "subject_id": subject_id,
                "limit": limit,
            },
        )
        return [str(row["body"]) for row in reversed(rows)]

    def create_requirement(
        self,
        *,
        requirement_id: str,
        revision_id: str,
        thread_id: str,
        title: str,
        content: dict[str, Any],
        actor_id: str,
        source_idea_id: str | None = None,
        source_run_id: str | None = None,
    ) -> tuple[dict[str, Any], bool]:
        with self._postgres.transaction() as connection:
            idea_thread_id: str | None = None
            if source_idea_id:
                idea = connection.execute(
                    f"SELECT id FROM {self._ideas} WHERE id = %s FOR UPDATE",
                    (source_idea_id,),
                ).fetchone()
                if idea is None:
                    raise KeyError(source_idea_id)
                existing = connection.execute(
                    f"SELECT id FROM {self._requirements} WHERE source_idea_id = %s",
                    (source_idea_id,),
                ).fetchone()
                if existing is not None:
                    row = self._requirement_detail(connection, str(existing["id"]))
                    if row is None:
                        raise RuntimeError("关联 Requirement 无法读取")
                    return row, False
                idea_thread = connection.execute(
                    f"""
                        SELECT id FROM {self._threads}
                        WHERE subject_type = 'idea' AND subject_id = %s
                    """,
                    (source_idea_id,),
                ).fetchone()
                if idea_thread is None:
                    raise RuntimeError("Idea 缺少协作 Thread")
                idea_thread_id = str(idea_thread["id"])

            source_type = "idea" if source_idea_id else "direct"
            connection.execute(
                f"""
                    INSERT INTO {self._requirements} (
                        id, source_type, source_idea_id, title,
                        created_by, owner_id
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    requirement_id,
                    source_type,
                    source_idea_id,
                    title,
                    actor_id,
                    actor_id,
                ),
            )
            connection.execute(
                f"""
                    INSERT INTO {self._threads} (id, subject_type, subject_id)
                    VALUES (%s, 'requirement', %s)
                """,
                (thread_id, requirement_id),
            )
            connection.execute(
                f"""
                    INSERT INTO {self._revisions} (
                        id, requirement_id, revision_no, content,
                        source_run_id, created_by
                    ) VALUES (%s, %s, 1, %s, %s, %s)
                """,
                (
                    revision_id,
                    requirement_id,
                    Jsonb(content),
                    source_run_id,
                    actor_id,
                ),
            )
            connection.execute(
                f"""
                    UPDATE {self._requirements}
                    SET current_revision_id = %s, updated_at = now()
                    WHERE id = %s
                """,
                (revision_id, requirement_id),
            )
            self._entry(
                connection,
                self._entries,
                thread_id=thread_id,
                entry_type="system",
                actor_type="system",
                actor_id="system",
                body="候选需求与首个 Revision 已创建",
                payload={"action": "requirement.created", "revision_id": revision_id},
            )
            if source_idea_id and idea_thread_id:
                connection.execute(
                    f"""
                        UPDATE {self._ideas}
                        SET status = 'converted', updated_at = now()
                        WHERE id = %s
                    """,
                    (source_idea_id,),
                )
                self._entry(
                    connection,
                    self._entries,
                    thread_id=idea_thread_id,
                    entry_type="system",
                    actor_type="system",
                    actor_id="system",
                    body="Idea 已转为候选需求",
                    payload={
                        "action": "idea.converted",
                        "requirement_id": requirement_id,
                    },
                )
            row = self._requirement_detail(connection, requirement_id)
        if row is None:
            raise RuntimeError("创建 Requirement 后未返回记录")
        return row, True

    def _requirement_detail(
        self,
        connection: Connection[dict[str, Any]],
        requirement_id: str,
    ) -> dict[str, Any] | None:
        return connection.execute(
            f"""
                SELECT {REQUIREMENT_COLUMNS}, thread.id AS thread_id,
                       revision.revision_no AS current_revision_no,
                       revision.content AS current_revision_content,
                       revision.source_run_id AS current_revision_source_run_id,
                       revision.created_by AS current_revision_created_by,
                       revision.created_at AS current_revision_created_at,
                       COUNT(run.id)::integer AS run_count
                FROM {self._requirements} AS requirement
                JOIN {self._threads} AS thread
                  ON thread.subject_type = 'requirement'
                 AND thread.subject_id = requirement.id
                JOIN {self._revisions} AS revision
                  ON revision.id = requirement.current_revision_id
                LEFT JOIN {self._runs} AS run
                  ON run.subject_type = 'requirement'
                 AND run.subject_id = requirement.id
                WHERE requirement.id = %s
                GROUP BY requirement.id, thread.id, revision.id
            """,
            (requirement_id,),
        ).fetchone()

    def get_requirement(self, requirement_id: str) -> dict[str, Any] | None:
        with self._postgres.connection() as connection:
            return self._requirement_detail(connection, requirement_id)

    def list_requirements(
        self,
        *,
        limit: int,
        offset: int,
        statuses: Iterable[str] = (),
        commitments: Iterable[str] = (),
        query: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        status_values = tuple(statuses)
        if status_values:
            clauses.append("requirement.status = ANY(%(statuses)s)")
            params["statuses"] = list(status_values)
        commitment_values = tuple(commitments)
        if commitment_values:
            clauses.append("requirement.commitment = ANY(%(commitments)s)")
            params["commitments"] = list(commitment_values)
        if query:
            clauses.append("requirement.title ILIKE %(query)s")
            params["query"] = f"%{query}%"
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._postgres.fetch_all(
            f"""
                SELECT requirement.id, requirement.title,
                       requirement.source_type, requirement.source_idea_id,
                       requirement.status, requirement.commitment,
                       requirement.owner_id, revision.revision_no AS current_revision_no,
                       COUNT(run.id)::integer AS run_count,
                       requirement.created_at, requirement.updated_at,
                       COUNT(*) OVER()::integer AS total_count
                FROM {self._requirements} AS requirement
                JOIN {self._revisions} AS revision
                  ON revision.id = requirement.current_revision_id
                LEFT JOIN {self._runs} AS run
                  ON run.subject_type = 'requirement'
                 AND run.subject_id = requirement.id
                {where}
                GROUP BY requirement.id, revision.revision_no
                ORDER BY requirement.updated_at DESC, requirement.id DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        total = int(rows[0]["total_count"]) if rows else 0
        for row in rows:
            row.pop("total_count", None)
        return rows, total

    @staticmethod
    def _shape_requirement_detail(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        revision_id = str(result["current_revision_id"])
        result["current_revision"] = {
            "id": revision_id,
            "requirement_id": str(result["id"]),
            "revision_no": int(result["current_revision_no"]),
            "content": result.pop("current_revision_content"),
            "source_run_id": result.pop("current_revision_source_run_id"),
            "created_by": result.pop("current_revision_created_by"),
            "created_at": result.pop("current_revision_created_at"),
        }
        return result

    def requirement_detail(self, requirement_id: str) -> dict[str, Any] | None:
        row = self.get_requirement(requirement_id)
        return self._shape_requirement_detail(row) if row else None

    def list_revisions(
        self,
        requirement_id: str,
        *,
        include_content: bool,
    ) -> list[dict[str, Any]]:
        if self.get_requirement(requirement_id) is None:
            raise KeyError(requirement_id)
        content = "content" if include_content else "NULL::jsonb AS content"
        return self._postgres.fetch_all(
            f"""
                SELECT id, requirement_id, revision_no, {content}, source_run_id,
                       created_by, created_at
                FROM {self._revisions}
                WHERE requirement_id = %(id)s
                ORDER BY revision_no DESC
            """,
            {"id": requirement_id},
        )

    def add_revision(
        self,
        *,
        revision_id: str,
        requirement_id: str,
        content: dict[str, Any],
        source_run_id: str | None,
        actor_id: str,
    ) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            requirement = connection.execute(
                f"SELECT status FROM {self._requirements} WHERE id = %s FOR UPDATE",
                (requirement_id,),
            ).fetchone()
            if requirement is None:
                raise KeyError(requirement_id)
            if requirement["status"] != "candidate":
                raise ValueError(
                    f"Requirement 当前状态不可直接修订：{requirement['status']}"
                )
            row = connection.execute(
                f"""
                    INSERT INTO {self._revisions} (
                        id, requirement_id, revision_no, content,
                        source_run_id, created_by
                    )
                    SELECT %s, %s, COALESCE(MAX(revision_no), 0) + 1,
                           %s, %s, %s
                    FROM {self._revisions}
                    WHERE requirement_id = %s
                    RETURNING id, requirement_id, revision_no, content,
                              source_run_id, created_by, created_at
                """,
                (
                    revision_id,
                    requirement_id,
                    Jsonb(content),
                    source_run_id,
                    actor_id,
                    requirement_id,
                ),
            ).fetchone()
            if row is None:
                raise RuntimeError("创建 Requirement Revision 后未返回记录")
            connection.execute(
                f"""
                    UPDATE {self._requirements}
                    SET current_revision_id = %s, updated_at = now()
                    WHERE id = %s
                """,
                (revision_id, requirement_id),
            )
        return row

    def decide(
        self,
        *,
        decision_id: str,
        requirement_id: str,
        decision_type: str,
        actor_id: str,
        revision_id: str | None,
        reason: str | None,
        commitment: str | None,
        target_window: str | None,
        entry_condition: str | None,
        review_at: datetime | None,
        merged_into_id: str | None,
        reopen_revision_id: str | None = None,
        reopen_content: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        with self._postgres.transaction() as connection:
            requirement = connection.execute(
                f"SELECT * FROM {self._requirements} WHERE id = %s FOR UPDATE",
                (requirement_id,),
            ).fetchone()
            if requirement is None:
                raise KeyError(requirement_id)
            current_status = str(requirement["status"])
            selected_revision = revision_id or requirement["current_revision_id"]
            updates: dict[str, Any]

            if decision_type == "accept":
                if current_status != "candidate":
                    raise ValueError(f"当前状态不可接纳：{current_status}")
                if selected_revision != requirement["current_revision_id"]:
                    raise ValueError("只能接纳当前 Revision")
                revision = connection.execute(
                    f"SELECT content FROM {self._revisions} WHERE id = %s",
                    (selected_revision,),
                ).fetchone()
                if revision is None:
                    raise RuntimeError("待接纳 Revision 不存在")
                self.validate_acceptance_content(dict(revision["content"]))
                updates = {
                    "status": "accepted",
                    "accepted_revision_id": selected_revision,
                    "commitment": commitment,
                    "target_window": target_window,
                    "entry_condition": entry_condition,
                    "review_at": review_at,
                    "merged_into_id": None,
                }
            elif decision_type == "reject":
                if current_status != "candidate":
                    raise ValueError(f"当前状态不可驳回：{current_status}")
                updates = {
                    "status": "rejected",
                    "commitment": None,
                    "target_window": None,
                    "entry_condition": None,
                    "review_at": None,
                    "merged_into_id": None,
                }
            elif decision_type == "defer":
                if current_status != "candidate":
                    raise ValueError(f"当前状态不可延期：{current_status}")
                updates = {
                    "status": "deferred",
                    "commitment": None,
                    "target_window": None,
                    "entry_condition": entry_condition,
                    "review_at": review_at,
                    "merged_into_id": None,
                }
            elif decision_type == "merge":
                if current_status != "candidate":
                    raise ValueError(f"当前状态不可合并：{current_status}")
                if not merged_into_id or merged_into_id == requirement_id:
                    raise ValueError("必须选择其他承接 Requirement")
                target = connection.execute(
                    f"SELECT id FROM {self._requirements} WHERE id = %s",
                    (merged_into_id,),
                ).fetchone()
                if target is None:
                    raise ValueError(f"承接 Requirement 不存在：{merged_into_id}")
                updates = {
                    "status": "merged",
                    "commitment": None,
                    "target_window": None,
                    "entry_condition": None,
                    "review_at": None,
                    "merged_into_id": merged_into_id,
                }
            elif decision_type == "reopen":
                if current_status not in {"rejected", "deferred"}:
                    raise ValueError(f"当前状态不可重新打开：{current_status}")
                if not reopen_revision_id or reopen_content is None:
                    raise ValueError("重新打开必须创建新 Revision")
                revision = connection.execute(
                    f"""
                        INSERT INTO {self._revisions} (
                            id, requirement_id, revision_no, content, created_by
                        )
                        SELECT %s, %s, COALESCE(MAX(revision_no), 0) + 1, %s, %s
                        FROM {self._revisions}
                        WHERE requirement_id = %s
                        RETURNING id
                    """,
                    (
                        reopen_revision_id,
                        requirement_id,
                        Jsonb(reopen_content),
                        actor_id,
                        requirement_id,
                    ),
                ).fetchone()
                if revision is None:
                    raise RuntimeError("重新打开时未创建 Revision")
                selected_revision = reopen_revision_id
                updates = {
                    "status": "candidate",
                    "current_revision_id": reopen_revision_id,
                    "accepted_revision_id": None,
                    "commitment": None,
                    "target_window": None,
                    "entry_condition": None,
                    "review_at": None,
                    "merged_into_id": None,
                }
            else:
                raise ValueError(f"未知 Decision：{decision_type}")

            assignments = ", ".join(f"{key} = %({key})s" for key in updates)
            connection.execute(
                f"""
                    UPDATE {self._requirements}
                    SET {assignments}, updated_at = now()
                    WHERE id = %(requirement_id)s
                """,
                {"requirement_id": requirement_id, **updates},
            )
            decision = connection.execute(
                f"""
                    INSERT INTO {self._decisions} (
                        id, requirement_id, revision_id, decision_type, reason,
                        commitment, target_window, entry_condition, review_at,
                        merged_into_id, actor_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                """,
                (
                    decision_id,
                    requirement_id,
                    selected_revision,
                    decision_type,
                    reason,
                    commitment,
                    target_window,
                    entry_condition,
                    review_at,
                    merged_into_id,
                    actor_id,
                ),
            ).fetchone()
            detail = self._requirement_detail(connection, requirement_id)
        if decision is None or detail is None:
            raise RuntimeError("Decision 完成后未返回记录")
        return decision, self._shape_requirement_detail(detail)

    def timeline(
        self,
        *,
        subject_type: str,
        subject_id: str,
        cursor: int,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int | None]:
        thread = self._postgres.fetch_one(
            f"""
                SELECT id FROM {self._threads}
                WHERE subject_type = %(subject_type)s AND subject_id = %(subject_id)s
            """,
            {"subject_type": subject_type, "subject_id": subject_id},
        )
        if thread is None:
            raise KeyError(subject_id)
        requirement_union = ""
        if subject_type == "requirement":
            requirement_union = f"""
                UNION ALL
                SELECT 'revision'::text AS item_type, revision.id::text AS item_id,
                       revision.created_at AS occurred_at,
                       jsonb_build_object(
                           'revision_no', revision.revision_no,
                           'source_run_id', revision.source_run_id,
                           'created_by', revision.created_by
                       ) AS payload
                FROM {self._revisions} AS revision
                WHERE revision.requirement_id = %(subject_id)s
                UNION ALL
                SELECT 'decision'::text AS item_type, decision.id::text AS item_id,
                       decision.created_at AS occurred_at,
                       jsonb_build_object(
                           'decision_type', decision.decision_type,
                           'revision_id', decision.revision_id,
                           'reason', decision.reason,
                           'commitment', decision.commitment,
                           'target_window', decision.target_window,
                           'entry_condition', decision.entry_condition,
                           'review_at', decision.review_at,
                           'merged_into_id', decision.merged_into_id,
                           'actor_id', decision.actor_id
                       ) AS payload
                FROM {self._decisions} AS decision
                WHERE decision.requirement_id = %(subject_id)s
            """
        rows = self._postgres.fetch_all(
            f"""
                WITH timeline AS (
                    SELECT 'entry'::text AS item_type, entry.id::text AS item_id,
                           entry.created_at AS occurred_at,
                           jsonb_build_object(
                               'entry_type', entry.entry_type,
                               'actor_type', entry.actor_type,
                               'actor_id', entry.actor_id,
                               'body', entry.body,
                               'data', entry.payload
                           ) AS payload
                    FROM {self._entries} AS entry
                    WHERE entry.thread_id = %(thread_id)s
                    UNION ALL
                    SELECT 'run'::text AS item_type, run.id::text AS item_id,
                           run.created_at AS occurred_at,
                           jsonb_build_object(
                               'run_id', run.id,
                               'agent_id', run.agent_id,
                               'agent_name', run.agent_name,
                               'executor', run.executor,
                               'status', run.status,
                               'model', run.model,
                               'title', run.title,
                               'trigger_action', run.trigger_action,
                               'result_summary', run.result_summary,
                               'failure_code', run.failure_code
                           ) AS payload
                    FROM {self._runs} AS run
                    WHERE run.thread_id = %(thread_id)s
                    {requirement_union}
                )
                SELECT item_type, item_id, occurred_at, payload
                FROM timeline
                ORDER BY occurred_at DESC, item_id DESC
                LIMIT %(fetch_limit)s OFFSET %(cursor)s
            """,
            {
                "thread_id": str(thread["id"]),
                "subject_id": subject_id,
                "fetch_limit": limit + 1,
                "cursor": cursor,
            },
        )
        has_more = len(rows) > limit
        return rows[:limit], cursor + limit if has_more else None
