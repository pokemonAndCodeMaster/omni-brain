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
        self.assertEqual("release", manifest["release_channel"])
        self.assertEqual("m1-ingestion-harness-v1", manifest["release_id"])
        self.assertEqual("opencode", runtime["primary"])
        self.assertEqual("native_file_conventions", runtime["adapter"])
        self.assertFalse(runtime["opencode_specific_config_required"])
        self.assertTrue((ROOT / runtime["instructions"]).exists())
        self.assertTrue((ROOT / manifest["roadmap"]).exists())

    def test_m1_ingestion_declares_only_scoped_verification(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        self.assertEqual("M1", manifest["current_stage"]["id"])
        self.assertEqual(
            "released_verified_at_quality_check_incremental_slice",
            manifest["current_stage"]["status"],
        )
        ingestion = manifest["capabilities"]["knowledge_ingestion"]
        self.assertEqual(
            "verified_at_cross_model_incremental_slice",
            ingestion["adoption"],
        )
        self.assertIn(".agents/skills/ingest-knowledge/SKILL.md", ingestion["entrypoints"])
        self.assertIn("scripts/ingestion_workspace.py", ingestion["entrypoints"])
        self.assertIn("cross_model", ingestion["adoption"])

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
        self.assertIn("先用工作台 `next` 取得当前材料单元、主题或聚焦小批", contract)
        self.assertIn("不得绕过它递归搜索", contract)
        self.assertIn("临时 Git worktree", contract)

    def test_existing_knowledge_queries_do_not_trigger_ingestion(self) -> None:
        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("加载 `answer-from-knowledge`", contract)
        self.assertIn("不加载 `ingest-knowledge`", contract)

    def test_trusted_query_skill_is_stateless_and_bounded(self) -> None:
        skill = (ROOT / ".agents/skills/answer-from-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不创建工作区、账本、YAML", skill)
        self.assertIn("最多三篇", skill)
        self.assertIn("没有搜到", skill)
        self.assertIn("任务上下文额外给出一个紧凑交接", skill)
        self.assertIn("没有用户授权时不创建文件", skill)
        self.assertIn("不运行 `rg --files`", skill)
        self.assertIn("不能用“等、等等、诸如此类”", skill)
        self.assertIn("绝对文件路径", skill)
        self.assertIn("相对于包含该链接的文档解析", skill)
        self.assertIn("先只读取最直接的一篇", skill)
        self.assertIn("硬上限而不是建议目标", skill)
        self.assertIn("knowledge_route.py", skill)
        self.assertIn("先只读取 `PRIMARY`", skill)

    def test_skill_frontmatter_is_discoverable(self) -> None:
        for name in (
            "task-knowledge-prep", "ingest-knowledge", "answer-from-knowledge",
            "develop-with-knowledge",
        ):
            path = ROOT / f".agents/skills/{name}/SKILL.md"
            match = re.match(r"\A---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
            self.assertIsNotNone(match, name)
            self.assertEqual(name, yaml.safe_load(match.group(1))["name"])

    def test_declared_entrypoints_exist(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        for capability in manifest["capabilities"].values():
            for entrypoint in capability["entrypoints"]:
                self.assertTrue((ROOT / entrypoint).exists(), entrypoint)

    def test_development_workflow_is_verified_in_three_scoped_slices(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        capability = manifest["capabilities"]["knowledge_guided_development"]
        self.assertEqual(
            "verified_at_three_manual_qc_development_slices",
            capability["adoption"],
        )
        self.assertEqual(
            [".agents/skills/develop-with-knowledge/SKILL.md"],
            capability["entrypoints"],
        )

        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        skill = (ROOT / capability["entrypoints"][0]).read_text(encoding="utf-8")
        self.assertIn("加载 `develop-with-knowledge`", contract)
        self.assertIn("最低充分上下文", skill)
        self.assertIn("## 实现前快照", skill)
        self.assertIn("固定项 + 用户可追加项 + 隐式项 - 去重 = 最大合法总量", skill)
        self.assertIn("组合审计", skill)
        self.assertIn("最大合法状态的完整构成", skill)
        self.assertIn("最大合法状态通过、再多一项失败", skill)
        self.assertIn("副作用基线", skill)
        self.assertIn("冲突样本", skill)
        self.assertIn("行数相同", skill)
        self.assertIn("不能继续写入", skill)
        self.assertIn("实际输出证据", skill)
        self.assertIn("真实路径验证", skill)
        self.assertIn("知识变化候选", skill)
        self.assertIn("来源身份", skill)

    def test_knowledge_bundle_matches_declared_adoption(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        domains = yaml.safe_load(
            (ROOT / "config/knowledge-domains.yaml").read_text(encoding="utf-8")
        )
        substantive = [
            path
            for area in ("domains", "capabilities", "systems", "sources")
            for path in (ROOT / "knowledge" / area).rglob("*.md")
            if path.name not in {"index.md", "log.md"}
        ]
        adoption = manifest["capabilities"]["knowledge_base"]["adoption"]
        if adoption == "implemented_empty_okf_scaffold":
            self.assertEqual([], domains["domains"])
            self.assertEqual([], substantive)
        else:
            self.assertTrue(domains["domains"])
            self.assertTrue(substantive)
        self.assertFalse((ROOT / "knowledge/index.md").read_text(encoding="utf-8").startswith("---"))

    def test_release_surface_contains_only_runtime_assets(self) -> None:
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("review.md", skill)
        self.assertIn("领域/旅程视图都存在", skill)
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
        self.assertIn("每项发现只表达一个可复用结论", agents)
        self.assertIn("一个明确读者问题为最小交付单位", agents)

        expected_steps = (
            "## 1. 选择最低充分路径",
            "## 2. 宽范围完整整理",
            "### 2.1 固定用户承诺与材料范围",
            "### 2.2 审视材料地图并形成读后发现",
            "### 2.3 规划并复核知识目录",
            "### 2.4 按目录形成规范知识和产品视图",
            "## 3. 代码变化回写",
            "### 3.1 先固定读者问题与系统身份",
            "### 3.2 从影响面规划，不从仓库目录规划",
            "### 3.3 把发现重构成知识，而不是更新摘要",
            "### 3.4 完成父知识融合与审查",
            "## 4. 聚焦代码或问题整理",
            "## 5. 人工审查与发布",
        )
        positions = [skill.index(step) for step in expected_steps]
        self.assertEqual(sorted(positions), positions)
        self.assertLess(
            skill.index("审视材料地图并形成读后发现"),
            skill.index("规划并复核知识目录"),
        )
        self.assertIn("保留父知识不等于逐字冻结", skill)
        self.assertIn("没有当前态表述与新发现互相矛盾", skill)

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
        self.assertIn("不在开始时加载全部资产", skill)
        self.assertIn("只读取 `next` 返回的 `absolute_path`", skill)
        self.assertIn("每题规划一至四个", skill)
        self.assertIn("需要更多时先收束问题或调整知识地图", skill)
        self.assertIn("不恢复逐文件 `mark`", skill)
        self.assertIn("目标覆盖", skill)
        self.assertIn("stop-search", skill)
        self.assertIn("从项目根可复制执行的命令", skill)
        self.assertIn("绑定旧 commit、分支、版本或能力状态", skill)
        self.assertIn("新增消费者与责任边界", skill)
        self.assertIn("id/title/parent/scope/excludes", (assets / "domain-overview.md").read_text(encoding="utf-8"))
        retired_assets = (
            "brief.md", "completion.yaml", "inventory.md", "questions.md",
            "reader-answers.md", "review.md",
        )
        self.assertTrue(all(not (assets / name).exists() for name in retired_assets))

    def test_ingestion_keeps_complete_and_focused_reading_bounded(self) -> None:
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不维护逐文件阅读打卡", skill)
        self.assertIn("同一个当前审视单元", skill)
        self.assertIn("每项发现保存决定理解或行动的关键细节", skill)
        self.assertIn("正文中的真实章节标题", skill)
        self.assertIn("只读取 `next` 返回的 `absolute_path`", skill)
        self.assertIn("正文必须充分内化", skill)
        self.assertIn("只把候选知识、产品视图和根 `review.md` 交给用户", skill)

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
