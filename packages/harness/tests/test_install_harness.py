from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_harness.py"


class InstallHarnessTest(unittest.TestCase):
    def run_installer(self, target: Path, *options: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INSTALLER), str(target), *options],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_overlay_install_keeps_project_rules_and_existing_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "sample-project"
            target.mkdir()
            (target / "AGENTS.md").write_text("# Sample project rules\n\nKeep this rule.\n", encoding="utf-8")
            (target / "knowledge").mkdir()
            (target / "knowledge" / "existing.md").write_text("keep me\n", encoding="utf-8")
            (target / "config").mkdir()
            (target / "config" / "knowledge-domains.yaml").write_text("domains: []\n", encoding="utf-8")
            skill = target / ".agents" / "skills" / "answer-from-knowledge" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("old harness\n", encoding="utf-8")

            result = self.run_installer(target)

            self.assertEqual(0, result.returncode, result.stderr)
            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Keep this rule.", agents)
            self.assertIn("<!-- omni-brain-harness:start -->", agents)
            self.assertIn("`develop-with-knowledge`", agents)
            self.assertNotEqual("old harness\n", skill.read_text(encoding="utf-8"))
            self.assertTrue((target / ".agents/skills/ingest-knowledge/SKILL.md").is_file())
            self.assertTrue((target / ".opencode/agents/delivery-reviewer.md").is_file())
            self.assertTrue((target / "scripts/ingestion_workspace.py").is_file())
            self.assertTrue((target / "scripts/knowledge_check.py").is_file())
            self.assertTrue((target / "harness.yaml").is_file())
            self.assertTrue((target / "requirements-omni-brain.txt").is_file())
            self.assertTrue((target / "knowledge/index.md").is_file())
            self.assertEqual("keep me\n", (target / "knowledge/existing.md").read_text(encoding="utf-8"))
            self.assertEqual("domains: []\n", (target / "config/knowledge-domains.yaml").read_text(encoding="utf-8"))
            self.assertTrue((target / "workspaces/knowledge-ingestion").is_dir())

            repeated = self.run_installer(target)
            self.assertEqual(0, repeated.returncode, repeated.stderr)
            self.assertEqual(1, (target / "AGENTS.md").read_text(encoding="utf-8").count("<!-- omni-brain-harness:start -->"))

    def test_install_creates_agents_when_target_has_none(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "sample-project"
            target.mkdir()

            result = self.run_installer(target)

            self.assertEqual(0, result.returncode, result.stderr)
            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("<!-- omni-brain-harness:start -->", agents)
            self.assertIn("`ingest-knowledge`", agents)

    def test_install_keeps_existing_opencode_agents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "sample-project"
            existing = target / ".opencode" / "agents" / "project-reviewer.md"
            existing.parent.mkdir(parents=True)
            existing.write_text("project owned\n", encoding="utf-8")

            result = self.run_installer(target)

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("project owned\n", existing.read_text(encoding="utf-8"))
            self.assertTrue((target / ".opencode/agents/delivery-reviewer.md").is_file())
