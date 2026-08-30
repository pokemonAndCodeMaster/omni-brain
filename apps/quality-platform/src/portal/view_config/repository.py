from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from src.database import PGConnector


class ViewConfigRepository:
    """Persist public/individual view definitions without owning their semantics."""

    def __init__(self, postgres: PGConnector) -> None:
        self._postgres = postgres
        self._table = f"{postgres.schema}.t_portal_view_config"

    def get(
        self,
        *,
        owner_id: str,
        page_key: str,
        view_name: str,
    ) -> dict[str, Any] | None:
        return self._postgres.fetch_one(
            f"""
                SELECT owner_id, page_key, view_name, view_type, config,
                       version, created_at, updated_at
                FROM {self._table}
                WHERE owner_id = %(owner_id)s
                  AND page_key = %(page_key)s
                  AND view_name = %(view_name)s
            """,
            {
                "owner_id": owner_id,
                "page_key": page_key,
                "view_name": view_name,
            },
        )

    def save(
        self,
        *,
        owner_id: str,
        page_key: str,
        view_name: str,
        view_type: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        row = self._postgres.fetch_one(
            f"""
                INSERT INTO {self._table} (
                    owner_id, page_key, view_name, view_type, config
                )
                VALUES (
                    %(owner_id)s, %(page_key)s, %(view_name)s,
                    %(view_type)s, %(config)s
                )
                ON CONFLICT (owner_id, page_key, view_name)
                DO UPDATE SET
                    view_type = EXCLUDED.view_type,
                    config = EXCLUDED.config,
                    version = {self._table}.version + 1,
                    updated_at = now()
                RETURNING owner_id, page_key, view_name, view_type, config,
                          version, created_at, updated_at
            """,
            {
                "owner_id": owner_id,
                "page_key": page_key,
                "view_name": view_name,
                "view_type": view_type,
                "config": Jsonb(config),
            },
        )
        if row is None:
            raise RuntimeError("保存视图配置后未返回记录")
        return row
