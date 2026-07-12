import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"


def load_skill(name: str) -> tuple[dict, str]:
    text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        raise AssertionError(f"{name} 缺少有效 YAML frontmatter")
    return yaml.safe_load(match.group(1)), match.group(2)


class SkillGovernanceContractTests(unittest.TestCase):
    def test_active_skill_directory_contains_only_supported_skills(self) -> None:
        active = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
        self.assertEqual(
            {"knowledge-query", "task-knowledge-prep", "writing-great-skills", "knowledge-ingest"},
            active,
        )
        self.assertFalse((ROOT / ".agents" / "skills.json").exists())
        self.assertFalse((SKILLS / "eval-runner" / "SKILL.md").exists())
        self.assertFalse((SKILLS / "skill-creator" / "SKILL.md").exists())
        self.assertFalse((SKILLS / "skill-change-proposal" / "SKILL.md").exists())
        self.assertFalse((SKILLS / "task-reflector" / "SKILL.md").exists())
        self.assertFalse((SKILLS / "knowledge-health" / "SKILL.md").exists())
        self.assertFalse((SKILLS / "code-ingest" / "SKILL.md").exists())

    def test_knowledge_ingest_has_narrow_trigger_and_real_fallback(self) -> None:
        frontmatter, body = load_skill("knowledge-ingest")
        description = frontmatter["description"]
        self.assertIn("明确要求", description)
        self.assertIn("长期知识", description)
        for broad_trigger in ("整理一下", "记录下来", "任务完成"):
            self.assertNotIn(broad_trigger, description)

        self.assertIn("manual_fallback", body)
        self.assertIn("任务投影", body)
        self.assertIn("长期知识候选", body)
        self.assertNotIn("scripts/chunk.py", body)
        self.assertNotIn("低风险（纯新增、无冲突）→ 直接进入入库", body)
        self.assertNotIn("信息无损", body)

    def test_routing_fixture_covers_positive_negative_and_failure_cases(self) -> None:
        fixture = ROOT / "eval" / "datasets" / "skill_execution" / "skill_governance_v1.yaml"
        data = yaml.safe_load(fixture.read_text(encoding="utf-8"))
        cases = data["cases"]
        kinds = {case["kind"] for case in cases}
        targets = {case["expected"]["skill"] for case in cases if case["expected"]["skill"]}
        self.assertTrue({"positive", "negative", "failure"} <= kinds)
        self.assertTrue({"knowledge-ingest", "task-knowledge-prep"} <= targets)
        self.assertTrue(any(case["id"] == "missing-eval-harness" for case in cases))
        self.assertTrue(any(case["id"] == "repeated-action-observation" for case in cases))
        self.assertGreaterEqual(len(cases), 8)


if __name__ == "__main__":
    unittest.main()
