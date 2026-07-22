from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ingestion_workspace.py"


class IngestionWorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cases = self.root / "cases"
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "one.md").write_text("# One\n", encoding="utf-8")
        (self.source / "two.txt").write_text("two\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_tool(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--cases-root", str(self.cases), *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def init_case(self) -> Path:
        result = self.run_tool(
            "init",
            "sample-case",
            "--goal",
            "让零背景读者理解材料并可继续使用",
            "--source",
            f"sample={self.source}",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return self.cases / "sample-case"

    def complete_non_content_fields(self, case: Path) -> None:
        completion = yaml.safe_load((case / "completion.yaml").read_text(encoding="utf-8"))
        completion["target_reader"] = "零背景读者"
        completion["intended_outcome"] = "理解来源边界并知道当前没有可发布知识"
        for dimension in completion["dimensions"]:
            dimension["status"] = "not_applicable"
            dimension["rationale"] = "此测试只验证工作台机械契约"
        completion["visuals"] = {
            "status": "not_applicable",
            "rationale": "空知识 Bundle 无需图表",
            "evidence_pages": [],
        }
        (case / "completion.yaml").write_text(
            yaml.safe_dump(completion, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        (case / "review.md").write_text(
            "# 审查\n\n"
            "- [目标](brief.md)\n"
            "- [来源](source-summary.md)\n"
            "- [盘点](inventory.md)\n"
            "- [契约](completion.yaml)\n"
            "- [问题](questions.md)\n\n"
            "正式知识未改变，本测试没有可发布内容。\n",
            encoding="utf-8",
        )

    def test_init_generates_machine_inventory_and_fixed_root_entries(self) -> None:
        case = self.init_case()
        for name in (
            "case.yaml",
            "brief.md",
            "inventory.md",
            "questions.md",
            "completion.yaml",
            "coverage.yaml",
            "source-manifest.jsonl",
            "source-summary.md",
            "review.md",
        ):
            self.assertTrue((case / name).is_file(), name)
        records = [
            json.loads(line)
            for line in (case / "source-manifest.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(["one.md", "two.txt"], [record["path"] for record in records])
        self.assertIn("| 2 |", (case / "source-summary.md").read_text(encoding="utf-8"))
        self.assertTrue((case / "draft" / "knowledge" / "index.md").is_file())

    def test_check_rejects_unreviewed_sources_and_unfilled_contract(self) -> None:
        self.init_case()
        result = self.run_tool("check", "sample-case")
        self.assertEqual(1, result.returncode)
        self.assertIn("尚未分类 2 项", result.stdout)
        self.assertIn("target_reader 未填写", result.stdout)
        self.assertIn("review.md 仍包含模板占位符", result.stdout)

    def test_files_lists_a_bounded_manifest_slice(self) -> None:
        self.init_case()
        result = self.run_tool(
            "files", "sample-case", "sample", "--glob", "*.md", "--limit", "1"
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(1, payload["matched"])
        self.assertEqual(["one.md"], payload["files"])

    def test_mark_and_check_pass_for_complete_empty_candidate(self) -> None:
        case = self.init_case()
        mark = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "read_targeted",
            "--reason",
            "读取全部测试材料",
            "--evidence",
            "one.md#One",
            "--all-unreviewed",
        )
        self.assertEqual(0, mark.returncode, mark.stderr)
        self.complete_non_content_fields(case)
        result = self.run_tool("check", "sample-case")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("ingestion-check: PASS", result.stdout)
        self.assertIn("'read_targeted': 2", result.stdout)

    def test_check_detects_source_change(self) -> None:
        case = self.init_case()
        mark = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "excluded",
            "--reason",
            "测试排除",
            "--all-unreviewed",
        )
        self.assertEqual(0, mark.returncode, mark.stderr)
        self.complete_non_content_fields(case)
        (self.source / "three.md").write_text("new\n", encoding="utf-8")
        result = self.run_tool("check", "sample-case")
        self.assertEqual(1, result.returncode)
        self.assertIn("文件数已变化：2 -> 3", result.stdout)
        self.assertIn("内容指纹已变化", result.stdout)

    def test_check_detects_misplaced_fixed_entry(self) -> None:
        case = self.init_case()
        (case / "assets").mkdir()
        (case / "assets" / "brief.md").write_text("wrong\n", encoding="utf-8")
        result = self.run_tool("check", "sample-case")
        self.assertEqual(1, result.returncode)
        self.assertIn("固定入口被错误放入 assets/：brief.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
