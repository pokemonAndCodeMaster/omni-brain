from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/answer-from-knowledge/scripts/knowledge_route.py"


class KnowledgeRouteTest(unittest.TestCase):
    def make_knowledge(self, base: Path) -> Path:
        knowledge = base / "knowledge"
        (knowledge / "systems").mkdir(parents=True)
        (knowledge / "domains").mkdir(parents=True)
        (knowledge / "views").mkdir(parents=True)
        (knowledge / "sources").mkdir(parents=True)
        (knowledge / "index.md").write_text(
            "# Knowledge\n\n"
            "| Question | Entry |\n|---|---|\n"
            "| 空库 migration 与 Ratio 预览 | [当前原型](systems/prototype.md) |\n"
            "| 五类业务对象 | [学习视图](views/learning.md) |\n",
            encoding="utf-8",
        )
        (knowledge / "systems/prototype.md").write_text(
            "---\ntitle: 当前仓库原型\ndescription: PostgreSQL migration、空库与 Ratio 预览边界\n---\n"
            "# 当前仓库原型\n## 数据库迁移缺口\n",
            encoding="utf-8",
        )
        (knowledge / "views/learning.md").write_text(
            "# 学习视图\n[生命周期](../domains/lifecycle.md)\n",
            encoding="utf-8",
        )
        (knowledge / "domains/lifecycle.md").write_text(
            "---\ntitle: 验收生命周期\ndescription: 候选总体、样本、记录、结论和执行结果\n---\n"
            "# 验收生命周期\n## 五类业务对象\n",
            encoding="utf-8",
        )
        (knowledge / "sources/current.md").write_text(
            "# 当前原型来源\nPostgreSQL migration、空库与 Ratio 预览证据。\n",
            encoding="utf-8",
        )
        return knowledge / "index.md"

    def test_routes_to_primary_and_resolves_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_knowledge(Path(tmp))
            completed = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--query",
                    "空 PostgreSQL 执行 migration 能否跑 Ratio 预览",
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(
                str((root.parent / "systems/prototype.md").resolve()),
                result["primary"]["path"],
            )
            self.assertTrue(Path(result["primary"]["path"]).is_absolute())
            self.assertIn("Read primary only", result["instruction"])

    def test_follows_navigation_links_without_listing_unreachable_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_knowledge(Path(tmp))
            unreachable = root.parent / "domains/unreachable.md"
            unreachable.write_text("# 五类业务对象的错误副本\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--query",
                    "完整列出五类业务对象",
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(
                str((root.parent / "domains/lifecycle.md").resolve()),
                result["primary"]["path"],
            )
            paths = {
                item["path"]
                for item in [result["primary"], *result["fallbacks"]]
                if item is not None
            }
            self.assertNotIn(str(unreachable.resolve()), paths)

    def test_missing_root_fails_without_writing(self) -> None:
        completed = subprocess.run(
            ["python", str(SCRIPT), "--root", "/missing/index.md", "--query", "anything"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("knowledge root not found", completed.stderr)

    def test_source_page_is_not_primary_without_provenance_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_knowledge(Path(tmp))
            root.write_text(
                root.read_text(encoding="utf-8")
                + "| 空库来源 | [当前来源](sources/current.md) |\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--query",
                    "空 PostgreSQL migration 能否运行 Ratio 预览",
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
            self.assertNotIn("/sources/", result["primary"]["path"])


if __name__ == "__main__":
    unittest.main()
