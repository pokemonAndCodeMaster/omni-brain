from __future__ import annotations

import pickle
from pathlib import Path

import pytest

from quality_platform_lab.config import ConfigManager, ConfigurationError


def write_fixture(tmp_path: Path, yaml_text: str, env_text: str = "") -> ConfigManager:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "base.yaml").write_text(yaml_text, encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text(env_text, encoding="utf-8")
    return ConfigManager(
        config_dir=config_dir,
        env_file=env_file,
        project_root=tmp_path,
    )


BASE = """
database:
  default: primary
  connections:
    primary:
      driver: postgresql
      host: ${TEST_DB_HOST:.runtime/socket}
      port: ${TEST_DB_PORT:55432}
      database: quality_lab
      user: quality_lab
      password: ${TEST_DB_PASSWORD:}
      schema: manual_qc_lab
"""


def test_environment_overrides_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_DB_PORT", "6000")
    manager = write_fixture(tmp_path, BASE, "TEST_DB_PORT=5999\n")
    connection = manager.get_database_by_alias("primary")
    assert connection["port"] == 6000
    assert connection["host"] == str((tmp_path / ".runtime/socket").resolve())


def test_missing_required_variable_is_explicit(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="REQUIRED_SECRET"):
        write_fixture(tmp_path, BASE.replace("${TEST_DB_PASSWORD:}", "${REQUIRED_SECRET}"))


def test_failed_reload_keeps_old_snapshot(tmp_path: Path) -> None:
    manager = write_fixture(tmp_path, BASE)
    config_path = tmp_path / "config/base.yaml"
    config_path.write_text("database: [broken", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        manager.reload()
    assert manager.get_database_by_alias()["database"] == "quality_lab"


def test_unknown_alias_lists_available_values(tmp_path: Path) -> None:
    manager = write_fixture(tmp_path, BASE)
    with pytest.raises(ConfigurationError, match="primary"):
        manager.get_database_by_alias("missing")


def test_database_alias_mapping_and_named_lookup(tmp_path: Path) -> None:
    manager = write_fixture(
        tmp_path,
        BASE.replace(
            "  default: primary",
            "  default: portal\n  aliases:\n    portal: primary",
        ),
    )
    assert manager.get_database_config("primary")["database"] == "quality_lab"
    assert manager.get_database_by_alias("portal")["alias"] == "primary"


def test_pickle_reloads_from_same_sources(tmp_path: Path) -> None:
    manager = write_fixture(tmp_path, BASE)
    restored = pickle.loads(pickle.dumps(manager))
    assert restored.get_database_by_alias()["database"] == "quality_lab"


def test_reload_can_switch_env_file_atomically(tmp_path: Path) -> None:
    manager = write_fixture(tmp_path, BASE, "TEST_DB_PORT=55432\n")
    alternative = tmp_path / ".env.alternative"
    alternative.write_text("TEST_DB_PORT=6001\n", encoding="utf-8")
    manager.reload(alternative)
    assert manager.get_database_by_alias()["port"] == 6001
