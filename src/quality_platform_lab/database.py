from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Mapping, Sequence

from psycopg import Connection
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import ConfigManager


@dataclass(frozen=True)
class DatabaseHealth:
    alias: str
    database: str
    server_version: str
    ok: bool = True


class PostgresConnector:
    """Named PostgreSQL connection with parameterized helpers and transactions."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        self.alias = str(config["alias"])
        self.database = str(config["database"])
        self.schema = str(config["schema"])
        self._pool = ConnectionPool(
            conninfo=self._conninfo(config),
            min_size=int(config.get("min_size", 1)),
            max_size=int(config.get("max_size", 5)),
            kwargs={"row_factory": dict_row},
            open=False,
            name=f"quality-platform-{self.alias}",
        )

    @staticmethod
    def _conninfo(config: Mapping[str, Any]) -> str:
        values: dict[str, str | int] = {
            "host": str(config["host"]),
            "port": int(config["port"]),
            "dbname": str(config["database"]),
            "user": str(config["user"]),
            "application_name": "quality-platform-lab",
        }
        password = str(config.get("password", ""))
        if password:
            values["password"] = password
        return make_conninfo(**values)

    def open(self) -> None:
        if self._pool.closed:
            self._pool.open(wait=True, timeout=10)

    def close(self) -> None:
        if not self._pool.closed:
            self._pool.close()

    @contextmanager
    def connection(self) -> Iterator[Connection[dict[str, Any]]]:
        self.open()
        with self._pool.connection() as connection:
            yield connection

    @contextmanager
    def transaction(self) -> Iterator[Connection[dict[str, Any]]]:
        with self.connection() as connection:
            with connection.transaction():
                yield connection

    def fetch_all(
        self,
        statement: str,
        params: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self.execute_query(statement, params)

    def execute_query(
        self,
        statement: str,
        params: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a query inside a PostgreSQL read-only transaction."""
        with self.connection() as connection:
            with connection.transaction():
                connection.execute("SET TRANSACTION READ ONLY")
                with connection.cursor() as cursor:
                    cursor.execute(statement, params)
                    return list(cursor.fetchall())

    def fetch_one(
        self,
        statement: str,
        params: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, params)
                return cursor.fetchone()

    def execute(
        self,
        statement: str,
        params: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> int:
        with self.transaction() as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, params)
                return cursor.rowcount

    def execute_update(
        self,
        statement: str,
        params: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> int:
        return self.execute(statement, params)

    def execute_values(
        self,
        statement: str,
        values: Sequence[Sequence[Any] | Mapping[str, Any]],
    ) -> int:
        with self.transaction() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(statement, values)
                return cursor.rowcount

    def execute_script(self, script: str) -> None:
        with self.transaction() as connection:
            connection.execute(script)

    def health_check(self) -> DatabaseHealth:
        row = self.fetch_one(
            "SELECT current_database() AS database, "
            "current_setting('server_version') AS server_version"
        )
        if row is None:
            raise RuntimeError("PostgreSQL health query returned no row")
        return DatabaseHealth(
            alias=self.alias,
            database=str(row["database"]),
            server_version=str(row["server_version"]),
        )


class DatabaseManager:
    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._connectors: dict[str, PostgresConnector] = {}

    def postgres(self, alias: str | None = None) -> PostgresConnector:
        selected = alias or str(self._config.get_nested("database.default", required=True))
        if selected not in self._connectors:
            self._connectors[selected] = PostgresConnector(
                self._config.get_database_by_alias(selected)
            )
        return self._connectors[selected]

    def close(self) -> None:
        for connector in self._connectors.values():
            connector.close()
        self._connectors.clear()
