"""Meaningful installation invariants: preserve user data, switch safely, recover failures."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "workbench_install", Path(__file__).parents[1] / "scripts/install_personal_workbench.py"
)
install_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(install_module)


class InstallTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        repo = self.root / "repo"
        skill = repo / ".agents/skills/personal-workbench"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: personal-workbench\n---\n")
        user = self.root / "user"
        codex = user / ".codex"
        codex.mkdir(parents=True)
        self.paths = repo, user, codex


    def test_install_preserves_existing_content_and_repeat_is_noop(self):
        paths = self.paths
        repo, user, codex = paths
        original = "# 私人规则\n\n保留我原来的设置。\n"
        (codex / "AGENTS.md").write_text(original)
        result = install_module.install(*paths)
        assert (codex / "AGENTS.md").read_text().startswith(original)
        assert (Path(result["backup"]) / "AGENTS.md").read_text() == original
        assert Path(result["skill_link"]).resolve() == repo / ".agents/skills/personal-workbench"
        assert install_module.install(*paths)["changed"] is False
        assert len(list((codex / "backups/personal-workbench").iterdir())) == 1


    def test_switch_preserves_both_sides_of_managed_block(self):
        paths, tmp_path = self.paths, self.root
        first = install_module.install(*paths)
        agents = Path(first["agents"])
        agents.write_text("头部原文\n" + agents.read_text() + "尾部用户新增\n")
        repo2 = tmp_path / "main"
        skill2 = repo2 / ".agents/skills/personal-workbench"
        skill2.mkdir(parents=True)
        (skill2 / "SKILL.md").write_text("new source")
        with self.assertRaisesRegex(ValueError, "--replace-link"):
            install_module.install(repo2, paths[1], paths[2])
        result = install_module.install(repo2, paths[1], paths[2], replace_existing_link=True)
        assert agents.read_text().startswith("头部原文\n")
        assert agents.read_text().endswith("尾部用户新增\n")
        assert Path(result["skill_link"]).resolve() == skill2
        assert str(paths[0]) not in agents.read_text()


    def test_refuses_existing_skill_directory_and_override(self):
        paths = self.paths
        repo, user, codex = paths
        link = user / ".agents/skills/personal-workbench"
        link.mkdir(parents=True)
        (link / "mine").write_text("user content")
        with self.assertRaisesRegex(ValueError, "独立内容"):
            install_module.install(*paths)
        assert (link / "mine").read_text() == "user content"
        assert not (codex / "AGENTS.md").exists()
        (codex / "AGENTS.override.md").write_text("stronger rule")
        with self.assertRaisesRegex(ValueError, "覆盖 AGENTS.md"):
            install_module.install(*paths)


    def test_failure_restores_old_link_and_agents(self):
        paths, tmp_path = self.paths, self.root
        first = install_module.install(*paths)
        before = Path(first["agents"]).read_bytes()
        repo2 = tmp_path / "replacement"
        skill2 = repo2 / ".agents/skills/personal-workbench"
        skill2.mkdir(parents=True)
        (skill2 / "SKILL.md").write_text("candidate")
        writer = install_module.atomic_write

        def fail_agents(path, data, mode=0o600):
            if path == Path(first["agents"]):
                raise OSError("simulated write failure")
            return writer(path, data, mode)

        with patch.object(install_module, "atomic_write", side_effect=fail_agents):
            with self.assertRaisesRegex(OSError, "simulated"):
                install_module.install(repo2, paths[1], paths[2], replace_existing_link=True)
        assert Path(first["agents"]).read_bytes() == before
        assert Path(first["skill_link"]).resolve() == paths[0] / ".agents/skills/personal-workbench"


    def test_check_is_read_only_and_backup_records_absence(self):
        paths = self.paths
        repo, user, codex = paths
        assert install_module.install(*paths, check=True)["installed"] is False
        assert not (user / ".agents").exists()
        result = install_module.install(*paths)
        old = json.loads((Path(result["backup"]) / "before.json").read_text())
        assert old["agents_existed"] is False
        assert old["skill_target"] is None
        assert install_module.install(*paths, check=True)["installed"] is True


    def test_bad_markers_and_symlinked_agents_are_not_overwritten(self):
        paths, tmp_path = self.paths, self.root
        repo, user, codex = paths
        agents = codex / "AGENTS.md"
        agents.write_text(install_module.START + "\nmissing end")
        with self.assertRaisesRegex(ValueError, "标记"):
            install_module.install(*paths)
        assert not (user / ".agents").exists()
        agents.unlink()
        original = tmp_path / "original.md"
        original.write_text("private content")
        agents.symlink_to(original)
        with self.assertRaisesRegex(ValueError, "普通文件"):
            install_module.install(*paths)
        assert original.read_text() == "private content"


if __name__ == "__main__":
    unittest.main()
