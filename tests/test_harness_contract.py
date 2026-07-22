from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class HarnessContractTest(unittest.TestCase):
    def test_opencode_uses_native_project_conventions(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        runtime = manifest["runtime"]
        self.assertEqual("opencode", runtime["primary"])
        self.assertEqual("native_file_conventions", runtime["adapter"])
        self.assertFalse(runtime["opencode_specific_config_required"])
        self.assertTrue((ROOT / runtime["instructions"]).exists())
        self.assertTrue((ROOT / manifest["roadmap"]).exists())

    def test_m1_content_first_v5_is_implemented_but_not_claimed_verified(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        self.assertEqual("M1", manifest["current_stage"]["id"])
        self.assertEqual(
            "implemented_content_first_v5_awaiting_forward_test",
            manifest["current_stage"]["status"],
        )
        ingestion = manifest["capabilities"]["knowledge_ingestion"]
        self.assertEqual(
            "implemented_content_first_v5_awaiting_forward_test",
            ingestion["adoption"],
        )
        self.assertIn(".agents/skills/ingest-knowledge/SKILL.md", ingestion["entrypoints"])
        self.assertIn("scripts/ingestion_workspace.py", ingestion["entrypoints"])
        self.assertNotIn("verified", ingestion["adoption"])

    def test_skill_frontmatter_is_discoverable(self) -> None:
        for name in ("task-knowledge-prep", "ingest-knowledge"):
            path = ROOT / f".agents/skills/{name}/SKILL.md"
            match = re.match(r"\A---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
            self.assertIsNotNone(match, name)
            self.assertEqual(name, yaml.safe_load(match.group(1))["name"])

    def test_declared_entrypoints_exist(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        for capability in manifest["capabilities"].values():
            for entrypoint in capability["entrypoints"]:
                self.assertTrue((ROOT / entrypoint).exists(), entrypoint)

    def test_knowledge_scaffold_is_empty_and_okf_native(self) -> None:
        domains = yaml.safe_load(
            (ROOT / "config/knowledge-domains.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual([], domains["domains"])
        for area in ("domains", "capabilities", "systems", "sources"):
            files = [
                path
                for path in (ROOT / "knowledge" / area).rglob("*.md")
                if path.name not in {"index.md", "log.md"}
            ]
            self.assertEqual([], files, area)
        self.assertFalse((ROOT / "knowledge/index.md").read_text(encoding="utf-8").startswith("---"))

    def test_release_surface_contains_only_runtime_assets(self) -> None:
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("review.md", skill)
        self.assertIn("同步建立领域位置视图和旅程/学习视图", skill)
        self.assertIn("python scripts/knowledge_check.py", skill)
        self.assertIn("python scripts/ingestion_workspace.py", skill)
        self.assertFalse((ROOT / "eval").exists())
        self.assertFalse((ROOT / "docs/experiments").exists())
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        for capability in manifest["capabilities"].values():
            self.assertTrue(all(not path.startswith("eval/") for path in capability["entrypoints"]))

    def test_ingestion_workflow_is_content_first(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## 知识内容优先", agents)
        self.assertIn("上级定位 → 主题全貌 → 用户焦点", agents)
        self.assertIn("至少沿一个真实业务动作", agents)

        expected_steps = (
            "## 1. 定义读者结果并建立工作台",
            "## 2. 沿问题主线阅读直接事实源",
            "## 3. 先设计知识地图，再写正文",
            "## 4. 从全貌到细节编织候选",
            "## 5. 先做内容消费，再做结构检查",
            "## 6. 人工审查、发布与立即使用",
        )
        positions = [skill.index(step) for step in expected_steps]
        self.assertEqual(sorted(positions), positions)
        self.assertLess(
            skill.index("逐个回答 `brief.md` 的问题主线"),
            skill.index("python scripts/ingestion_workspace.py check <case-id>"),
        )

    def test_ingestion_assets_drive_questions_sources_and_reading_routes(self) -> None:
        assets = ROOT / ".agents/skills/ingest-knowledge/assets"
        brief = (assets / "brief.md").read_text(encoding="utf-8")
        inventory = (assets / "inventory.md").read_text(encoding="utf-8")
        product_view = (assets / "product-view.md").read_text(encoding="utf-8")
        reader_answers = (assets / "reader-answers.md").read_text(encoding="utf-8")
        review = (assets / "review.md").read_text(encoding="utf-8")

        self.assertIn("## 逐层内容地图", brief)
        self.assertIn("## 读者问题主线", brief)
        self.assertIn("真实入口、包/模块、类/函数、数据转换和输出", brief)
        self.assertIn("## 每个问题实际用了什么", inventory)
        self.assertIn("## 软件与代码事实源", inventory)
        self.assertIn("## 推荐路线：从全貌到细节", product_view)
        self.assertIn("## 按问题查找", product_view)
        self.assertIn("## 逐题回答", reader_answers)
        self.assertIn("每个有效问题必须恰好对应一行", reader_answers)
        self.assertIn("最多三篇规范页", reader_answers)
        self.assertLess(review.index("## 从这里开始看内容"), review.index("## 结构状态"))

    def test_retired_knowledge_layout_is_absent(self) -> None:
        retired_paths = (
            "knowledge/hubs",
            "knowledge/concepts",
            "knowledge/playbooks",
            "knowledge/code",
            "knowledge/taxonomy.yaml",
        )
        self.assertTrue(all(not (ROOT / path).exists() for path in retired_paths))

    def test_skill_asset_markdown_table_headers_match_separators(self) -> None:
        assets = ROOT / ".agents/skills/ingest-knowledge/assets"
        for path in assets.glob("*.md"):
            lines = path.read_text(encoding="utf-8").splitlines()
            for previous, current in zip(lines, lines[1:]):
                if re.fullmatch(r"\|(?:\s*:?-+:?\s*\|)+", current):
                    self.assertEqual(
                        previous.count("|"),
                        current.count("|"),
                        f"malformed Markdown table in {path.name}: {previous!r}",
                    )


if __name__ == "__main__":
    unittest.main()
