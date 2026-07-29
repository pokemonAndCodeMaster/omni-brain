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
            "implemented_knowledge_ingestion_awaiting_real_use_validation",
            manifest["current_stage"]["status"],
        )
        ingestion = manifest["capabilities"]["knowledge_ingestion"]
        self.assertEqual(
            "implemented_knowledge_ingestion_awaiting_real_use_validation",
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

    def test_root_contract_keeps_ingestion_source_reads_on_workbench_path(self) -> None:
        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("授权来源的正文只通过工作台 `source-read` 展示", contract)
        self.assertIn("不得用原生 `read`", contract)

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
            "## 2. 先交付第一个可用知识单元",
            "## 3. 按问题逐个扩展知识",
            "## 4. 组装全貌与产品视图",
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
        software_architecture = (assets / "software-architecture.md").read_text(
            encoding="utf-8"
        )
        shared_capability = (assets / "shared-capability-review.md").read_text(
            encoding="utf-8"
        )
        review = (assets / "review.md").read_text(encoding="utf-8")

        self.assertIn("## 逐层内容地图", brief)
        self.assertIn("## 读者问题主线", brief)
        self.assertIn("代码地图、运行时序、核心类/数据关系", brief)
        self.assertIn("## 每个问题实际用了什么", inventory)
        self.assertIn("## 来源主题地图", inventory)
        self.assertIn("## 已读内容与知识落点", inventory)
        self.assertIn("## 当前问题缺口复核", inventory)
        self.assertIn("可能补足的未读来源", inventory)
        self.assertIn("不可丢失的机制、条件、边界、冲突或未知", inventory)
        self.assertIn("作为独立命令直接执行", inventory)
        self.assertIn("完成清单和正文两处落地再选择下一份来源", (
            ROOT / ".agents/skills/ingest-knowledge/SKILL.md"
        ).read_text(encoding="utf-8"))
        self.assertIn("source-select", brief)
        completion = (assets / "completion.yaml").read_text(encoding="utf-8")
        self.assertIn("knowledge_path:", completion)
        self.assertIn("covered/partial/unknown/not_applicable", completion)
        self.assertIn("source_id: <source-id>", completion)
        self.assertIn("相对于 draft/knowledge/ 根填写", completion)
        self.assertIn("level: parent", completion)
        self.assertIn("level: subject", completion)
        self.assertIn("level: focus", completion)
        self.assertIn("隐藏正文输出时，不得声明 `read_full`", inventory)
        self.assertIn("## 软件与代码事实源", inventory)
        self.assertIn("## 推荐路线：从全貌到细节", product_view)
        self.assertIn("## 按问题查找", product_view)
        self.assertIn("最小充分路线", product_view)
        self.assertIn("draft/knowledge/views/by-domain/<slug>.md", product_view)
        self.assertIn("不要另建 `draft/views/`", product_view)
        self.assertIn("## 逐题回答", reader_answers)
        self.assertIn("每个有效问题必须恰好对应一行", reader_answers)
        self.assertIn("最多三篇规范页", reader_answers)
        self.assertIn("不能用焦点局部的完整答案代替更大范围", reader_answers)
        self.assertIn("缺失事实、责任来源、对后续工作的影响和下一动作", reader_answers)
        self.assertIn("## 代码地图与职责", software_architecture)
        self.assertIn("## 核心对象和数据变化", software_architecture)
        self.assertIn("## 一次具体修改路径", software_architecture)
        self.assertIn("不要求先出现第二个外部领域", shared_capability)
        self.assertIn("draft/knowledge/capabilities/", shared_capability)
        questions = (assets / "questions.md").read_text(encoding="utf-8")
        self.assertIn("唯一状态源", questions)
        self.assertIn("open / answered / accepted_unknown", questions)
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("只在进入某一步时读取该步点名的模板", skill)
        self.assertIn("用户请求的完整范围", skill)
        self.assertIn("不要在开始时预读整个 `assets/` 目录", skill)
        self.assertIn("一次只处理一份实质来源", skill)
        self.assertIn("不并行执行多份 `source-read`", skill)
        self.assertIn("只有当前来源改变的具体内容已经离开会话上下文", skill)
        self.assertIn("将当前复合问题拆回它实际要求的各部分", skill)
        self.assertIn("当前代码纵切只能证明当前实现", skill)
        self.assertIn("正常摄入不得使用 `mark --all-unreviewed`", skill)
        self.assertIn("`.gitkeep`", skill)
        self.assertIn("相邻层围绕同一稳定主题", skill)
        self.assertNotIn("这里必须同步最后一次检查", review)
        for heading in (
            "## Agent 内容声明（待人工审查）",
            "## 结构门禁",
            "## 人工门禁",
        ):
            self.assertIn(heading, review)
        self.assertIn("[内容完成声明](completion.yaml)", review)
        self.assertIn("[机器来源摘要](source-summary.md)", review)
        self.assertLess(review.index("## 从这里开始看内容"), review.index("## 结构门禁"))

    def test_ingestion_delivers_content_before_context_sprawls(self) -> None:
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )
        brief = (
            ROOT / ".agents/skills/ingest-knowledge/assets/brief.md"
        ).read_text(encoding="utf-8")

        self.assertIn("一个读者问题就是一次最小交付", skill)
        self.assertIn("开始第六份来源前", skill)
        self.assertIn("非 `index.md` 的实质知识页", skill)
        self.assertIn("立即把新增机制写入 `inventory.md` 和对应候选知识章节", skill)
        self.assertIn("每个新增来源必须说明它准备补足哪个具体缺口", skill)
        self.assertIn("## 当前交付问题", brief)
        self.assertIn("不要等全部问题阅读完成后才第一次写正文", brief)

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
