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

    def test_m1_ingestion_is_implemented_without_claiming_verified(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        self.assertEqual("M1", manifest["current_stage"]["id"])
        self.assertEqual(
            "implemented_goal_coverage_revision_failed_document_replay",
            manifest["current_stage"]["status"],
        )
        ingestion = manifest["capabilities"]["knowledge_ingestion"]
        self.assertEqual(
            "implemented_goal_coverage_revision_failed_document_replay",
            ingestion["adoption"],
        )
        self.assertIn(".agents/skills/ingest-knowledge/SKILL.md", ingestion["entrypoints"])
        self.assertIn("scripts/ingestion_workspace.py", ingestion["entrypoints"])
        self.assertNotIn("verified", ingestion["adoption"])

    def test_startup_context_does_not_expose_eval_history(self) -> None:
        startup = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in ("harness.yaml", "docs/now.md", "docs/roadmap.md")
        )
        for leaked_term in (
            "GLM",
            "Luna",
            "Kimi",
            "MiniMax",
            "Batch 1",
            "batch-1",
        ):
            self.assertNotIn(leaked_term, startup)
        self.assertIsNone(re.search(r"\bV\d+(?:\.\d+)?\b", startup))
        self.assertIsNone(re.search(r"\b\d+/\d+\b", startup))

    def test_root_contract_keeps_ingestion_source_reads_in_current_packet(self) -> None:
        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("先用工作台 `next` 取得当前小批来源", contract)
        self.assertIn("不得绕过它递归搜索", contract)
        self.assertIn("临时 Git worktree", contract)

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
        self.assertIn("以一个读者问题为最小交付单位", agents)
        self.assertIn("一小批直接来源", agents)

        expected_steps = (
            "## 1. 建立读者问题",
            "## 2. 规划当前知识单元",
            "## 3. 取得一小批直接来源",
            "## 4. 立即形成知识并登记结果",
            "## 5. 取得真实运行证据",
            "## 6. 收完一个问题",
            "## 7. 人工审查与发布",
        )
        positions = [skill.index(step) for step in expected_steps]
        self.assertEqual(sorted(positions), positions)
        self.assertLess(
            skill.index("立即更新规范知识"),
            skill.index("python scripts/ingestion_workspace.py check-unit"),
        )

    def test_ingestion_assets_drive_questions_sources_and_reading_routes(self) -> None:
        assets = ROOT / ".agents/skills/ingest-knowledge/assets"
        product_view = (assets / "product-view.md").read_text(encoding="utf-8")
        software_architecture = (assets / "software-architecture.md").read_text(
            encoding="utf-8"
        )
        shared_capability = (assets / "shared-capability-review.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## 推荐路线：从全貌到细节", product_view)
        self.assertIn("## 按问题查找", product_view)
        self.assertIn("最小充分路线", product_view)
        self.assertIn("draft/knowledge/views/by-domain/<slug>.md", product_view)
        self.assertIn("不要另建 `draft/views/`", product_view)
        self.assertIn("## 代码地图与职责", software_architecture)
        self.assertIn("## 核心对象和数据变化", software_architecture)
        self.assertIn("## 一次具体修改路径", software_architecture)
        self.assertIn("不要求先出现第二个外部领域", shared_capability)
        self.assertIn("draft/knowledge/capabilities/", shared_capability)
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不要在开始时读取全部模板", skill)
        self.assertIn("只打开返回的 `absolute_path`", skill)
        self.assertIn("一个问题需要超过三篇正文", skill)
        self.assertIn("不恢复逐文件 `mark`", skill)
        self.assertIn("目标覆盖", skill)
        self.assertIn("stop-search", skill)
        self.assertIn("id/title/parent/scope/excludes", (assets / "domain-overview.md").read_text(encoding="utf-8"))
        retired_assets = (
            "brief.md", "completion.yaml", "inventory.md", "questions.md",
            "reader-answers.md", "review.md",
        )
        self.assertTrue(all(not (assets / name).exists() for name in retired_assets))

    def test_ingestion_delivers_content_before_context_sprawls(self) -> None:
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("一个读者问题，一小批直接来源", skill)
        self.assertIn("读完当前小批后立即更新规范知识", skill)
        self.assertIn("工具只返回当前 **1—8 份**候选", skill)
        self.assertIn("不要再生成平行答案页或完成度表", skill)

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
