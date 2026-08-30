from __future__ import annotations

import copy
import logging
import os
import re
from pathlib import Path
from threading import RLock
from typing import Any, Mapping, Sequence

import yaml


class ConfigurationError(RuntimeError):
    """Raised when configuration cannot be loaded or validated."""


_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MISSING = object()


def _deep_merge(base: dict[str, Any], incoming: Mapping[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in incoming.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = _deep_merge(dict(merged[key]), value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _parse_env_file(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            raise ConfigurationError(f"{path}:{line_number} 不是有效的 KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ConfigurationError(f"{path}:{line_number} 的环境变量名为空")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _expand_string(value: str, environment: Mapping[str, str], path: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name, default = match.group(1), match.group(2)
        if name in environment:
            return environment[name]
        if default is not None:
            return default
        raise ConfigurationError(f"配置 {path} 缺少必填环境变量 {name}")

    return _ENV_PATTERN.sub(replace, value)


def _expand_values(value: Any, environment: Mapping[str, str], path: str = "<root>") -> Any:
    if isinstance(value, str):
        return _expand_string(value, environment, path)
    if isinstance(value, list):
        return [
            _expand_values(item, environment, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        return {
            str(key): _expand_values(item, environment, f"{path}.{key}")
            for key, item in value.items()
        }
    return value


class ConfigManager:
    """Load YAML configuration with environment substitution and atomic reload."""

    def __init__(
        self,
        config_dir: str | Path = "config",
        env_file: str | Path | None = ".env",
        *,
        auto_load: bool = True,
        verbose: bool = False,
        project_root: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.config_dir = self._resolve_path(config_dir)
        self.env_file = self._resolve_path(env_file) if env_file else None
        self.verbose = verbose
        self._config: dict[str, Any] = {}
        self._lock = RLock()
        if auto_load:
            self.load_config()

    def _resolve_path(self, path: str | Path) -> Path:
        value = Path(path)
        if not value.is_absolute():
            value = self.project_root / value
        return value.resolve()

    def _read_candidate(self) -> dict[str, Any]:
        if not self.config_dir.is_dir():
            raise ConfigurationError(f"配置目录不存在：{self.config_dir}")

        files = sorted(
            [
                *self.config_dir.glob("*.yaml"),
                *self.config_dir.glob("*.yml"),
            ]
        )
        if not files:
            raise ConfigurationError(f"配置目录中没有 YAML：{self.config_dir}")

        raw: dict[str, Any] = {}
        for file_path in files:
            try:
                parsed = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError as exc:
                raise ConfigurationError(f"YAML 解析失败：{file_path}: {exc}") from exc
            if not isinstance(parsed, Mapping):
                raise ConfigurationError(f"YAML 顶层必须是映射：{file_path}")
            raw = _deep_merge(raw, parsed)

        file_environment = _parse_env_file(self.env_file)
        environment = {**file_environment, **os.environ}
        expanded = _expand_values(raw, environment)
        self._validate(expanded)
        return expanded

    def _validate(self, config: Mapping[str, Any]) -> None:
        connections = self._nested(config, ("database", "connections"), _MISSING)
        if not isinstance(connections, Mapping) or not connections:
            raise ConfigurationError("配置 database.connections 必须是非空映射")

        aliases = self._nested(config, ("database", "aliases"), {})
        if not isinstance(aliases, Mapping):
            raise ConfigurationError("配置 database.aliases 必须是映射")
        for alias, target in aliases.items():
            if target not in connections:
                raise ConfigurationError(f"数据库别名 {alias} 指向不存在的连接 {target}")

        default_alias = self._nested(config, ("database", "default"), _MISSING)
        resolved_default = aliases.get(default_alias, default_alias)
        if not isinstance(default_alias, str) or resolved_default not in connections:
            raise ConfigurationError("配置 database.default 必须引用已存在的连接别名")

        for alias, raw_connection in connections.items():
            if not isinstance(raw_connection, Mapping):
                raise ConfigurationError(f"数据库别名 {alias} 的配置必须是映射")
            for key in ("driver", "host", "port", "database", "user", "schema"):
                if key not in raw_connection:
                    raise ConfigurationError(f"数据库别名 {alias} 缺少 {key}")
            try:
                int(raw_connection["port"])
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(f"数据库别名 {alias} 的 port 必须是整数") from exc
            schema = str(raw_connection["schema"])
            if not _IDENTIFIER_PATTERN.fullmatch(schema):
                raise ConfigurationError(f"数据库别名 {alias} 的 schema 不是安全标识符")

    @staticmethod
    def _nested(
        root: Mapping[str, Any],
        keys: Sequence[str],
        default: Any = None,
    ) -> Any:
        current: Any = root
        for key in keys:
            if not isinstance(current, Mapping) or key not in current:
                return default
            current = current[key]
        return current

    def load_config(self) -> dict[str, Any]:
        candidate = self._read_candidate()
        with self._lock:
            self._config = candidate
        if self.verbose:
            logging.getLogger(__name__).info(
                "已加载配置：dir=%s files=%d",
                self.config_dir,
                len(list(self.config_dir.glob("*.y*ml"))),
            )
        return copy.deepcopy(candidate)

    def reload(self, env_file: str | Path | None = None) -> dict[str, Any]:
        """Atomically replace the active snapshot only after full validation."""
        previous_env_file = self.env_file
        if env_file is not None:
            self.env_file = self._resolve_path(env_file)
        try:
            return self.load_config()
        except Exception:
            self.env_file = previous_env_file
            raise

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return copy.deepcopy(self._config.get(key, default))

    def get_nested(
        self,
        path: str | Sequence[str],
        default: Any = None,
        *,
        required: bool = False,
    ) -> Any:
        keys = tuple(path.split(".")) if isinstance(path, str) else tuple(path)
        with self._lock:
            result = self._nested(self._config, keys, _MISSING)
        if result is _MISSING:
            if required:
                raise ConfigurationError(f"缺少配置：{'.'.join(keys)}")
            return copy.deepcopy(default)
        return copy.deepcopy(result)

    def get_database_config(self, db_key: str | None = None) -> dict[str, Any]:
        database = self.get_nested("database", required=True)
        if not isinstance(database, dict):
            raise ConfigurationError("配置 database 必须是映射")
        if db_key is None:
            return database

        aliases = database.get("aliases", {})
        if aliases and not isinstance(aliases, Mapping):
            raise ConfigurationError("配置 database.aliases 必须是映射")
        selected = str(aliases.get(db_key, db_key))
        connections = database["connections"]
        if selected not in connections:
            available = ", ".join(sorted(connections))
            raise ConfigurationError(f"未知数据库配置 {db_key}；可用：{available}")
        return copy.deepcopy(connections[selected])

    def get_database_by_alias(self, alias: str | None = None) -> dict[str, Any]:
        database = self.get_database_config()
        selected = alias or database["default"]
        aliases = database.get("aliases", {})
        if aliases and not isinstance(aliases, Mapping):
            raise ConfigurationError("配置 database.aliases 必须是映射")
        mapped = str(aliases.get(selected, selected))
        result = self.get_database_config(mapped)
        host = Path(str(result["host"]))
        if not host.is_absolute() and str(result["host"]).startswith("."):
            result["host"] = str((self.project_root / host).resolve())
        result["port"] = int(result["port"])
        result["min_size"] = int(result.get("min_size", 1))
        result["max_size"] = int(result.get("max_size", 5))
        result["alias"] = mapped
        return result

    def get_obs_config(self) -> dict[str, Any]:
        value = self.get_nested("object_storage", {})
        if not isinstance(value, dict):
            raise ConfigurationError("配置 object_storage 必须是映射")
        return value

    def setup_logging(
        self,
        level: str | None = None,
        *,
        enable_enqueue: bool = False,
    ) -> None:
        """Configure stdlib logging; queue logging belongs to a later worker slice."""
        if enable_enqueue:
            raise ConfigurationError("本地纵切尚未启用多进程队列日志")
        level_name = str(level or self.get_nested("logging.level", "INFO")).upper()
        level = getattr(logging, level_name, None)
        if not isinstance(level, int):
            raise ConfigurationError(f"非法日志级别：{level_name}")
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )

    def __reduce__(self) -> tuple[type[ConfigManager], tuple[Any, ...], dict[str, Any]]:
        state = {
            "verbose": self.verbose,
        }
        return (
            type(self),
            (
                str(self.config_dir),
                str(self.env_file) if self.env_file else None,
            ),
            state,
        )


_global_lock = RLock()
_global_config: ConfigManager | None = None


def get_global_config(
    *,
    project_root: str | Path | None = None,
    for_multiprocess: bool = False,
) -> ConfigManager:
    """Return the process-local manager; child processes receive a new instance."""
    if for_multiprocess:
        return ConfigManager(project_root=project_root)

    global _global_config
    with _global_lock:
        if _global_config is None:
            _global_config = ConfigManager(project_root=project_root)
        return _global_config
