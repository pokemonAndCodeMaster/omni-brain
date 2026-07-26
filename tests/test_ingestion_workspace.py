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
        for layer in completion["knowledge_path"]:
            layer["topic"] = f"{layer['level']} 在本测试中不适用"
            layer["status"] = "not_applicable"
            layer["rationale"] = "此测试只验证工作台机械契约"
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
            "# 审查\n\n## 固定审查入口\n\n"
            "- [目标](brief.md)\n"
            "- [逐题实答](reader-answers.md)\n"
            "- [来源](source-summary.md)\n"
            "- [盘点](inventory.md)\n"
            "- [契约](completion.yaml)\n"
            "- [问题](questions.md)\n\n"
            "## Agent 内容声明（待人工审查）\n\n"
            "正式知识未改变，本测试没有可发布内容。\n\n"
            "## 结构门禁\n\ncontent-review: PENDING_HUMAN\n\n"
            "## 人工门禁\n\n- [ ] 等待人工审查\n",
            encoding="utf-8",
        )

    def test_init_generates_machine_inventory_and_fixed_root_entries(self) -> None:
        case = self.init_case()
        for name in (
            "case.yaml",
            "brief.md",
            "reader-answers.md",
            "inventory.md",
            "questions.md",
            "completion.yaml",
            "coverage.yaml",
            "source-manifest.jsonl",
            "source-summary.md",
            "review.md",
        ):
            self.assertTrue((case / name).is_file(), name)
        brief = (case / "brief.md").read_text(encoding="utf-8")
        self.assertIn("让零背景读者理解材料并可继续使用", brief)
        self.assertIn(str(self.source.resolve()), brief)
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

    def test_screen_and_check_pass_for_complete_empty_candidate(self) -> None:
        case = self.init_case()
        mark = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "screened",
            "--reason",
            "读取全部测试材料",
            "--all-unreviewed",
        )
        self.assertEqual(0, mark.returncode, mark.stderr)
        self.complete_non_content_fields(case)
        result = self.run_tool("check", "sample-case")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("ingestion-structure-check: PASS", result.stdout)
        self.assertIn("content-review: PENDING_HUMAN", result.stdout)
        self.assertIn("machine source files: 2", result.stdout)
        self.assertIn("agent coverage claims: {'screened': 2}", result.stdout)

    def test_strong_read_claim_requires_one_exact_path_and_bound_evidence(self) -> None:
        self.init_case()
        broad = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "read_full",
            "--reason",
            "声称全文阅读",
            "--evidence",
            "one.md#full-file",
            "--glob",
            "*.md",
        )
        self.assertEqual(2, broad.returncode)
        self.assertIn("只能使用一个精确 --path", broad.stderr)

        unbound = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "read_targeted",
            "--reason",
            "读取指定章节",
            "--evidence",
            "another.md#Section",
            "--path",
            "one.md",
        )
        self.assertEqual(2, unbound.returncode)
        self.assertIn("必须以精确文件路径开头", unbound.stderr)

        exact = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "read_targeted",
            "--reason",
            "读取指定章节",
            "--evidence",
            "one.md#One",
            "--path",
            "one.md",
        )
        self.assertEqual(0, exact.returncode, exact.stderr)
        payload = json.loads(exact.stdout)
        self.assertEqual(1, payload["updated"])
        self.assertEqual("agent_declared", payload["assertion"])

    def test_source_read_emits_bounded_contiguous_chunks_and_records_completion(self) -> None:
        (self.source / "long.md").write_text(
            "\n".join(f"line {number}" for number in range(1, 166)) + "\n",
            encoding="utf-8",
        )
        case = self.init_case()

        first = self.run_tool(
            "source-read",
            "sample-case",
            "sample",
            "--path",
            "long.md",
        )
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertIn("lines=1-80/165 displayed_complete=false", first.stdout)
        self.assertIn("000001 | line 1", first.stdout)
        self.assertIn("000080 | line 80", first.stdout)
        self.assertNotIn("000081 |", first.stdout)
        self.assertIn("next: python scripts/ingestion_workspace.py source-read", first.stdout)

        second = self.run_tool(
            "source-read",
            "sample-case",
            "sample",
            "--path",
            "long.md",
        )
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertIn("lines=81-160/165 displayed_complete=false", second.stdout)
        self.assertIn("000081 | line 81", second.stdout)

        third = self.run_tool(
            "source-read",
            "sample-case",
            "sample",
            "--path",
            "long.md",
        )
        self.assertEqual(0, third.returncode, third.stderr)
        self.assertIn("lines=161-165/165 displayed_complete=true", third.stdout)
        self.assertIn("000165 | line 165", third.stdout)

        coverage = yaml.safe_load((case / "coverage.yaml").read_text(encoding="utf-8"))
        entry = next(item for item in coverage["files"] if item["path"] == "long.md")
        self.assertEqual(
            {
                "assertion": "machine_emitted",
                "source_sha256": entry["display"]["source_sha256"],
                "total_lines": 165,
                "displayed_through_line": 165,
                "displayed_complete": True,
                "updated_at": entry["display"]["updated_at"],
            },
            entry["display"],
        )

    def test_read_full_requires_complete_machine_display(self) -> None:
        self.init_case()
        premature = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "read_full",
            "--reason",
            "理解全文",
            "--evidence",
            "one.md#full-file",
            "--path",
            "one.md",
        )
        self.assertEqual(2, premature.returncode)
        self.assertIn("需要先用 source-read 完整展示", premature.stderr)

        shown = self.run_tool(
            "source-read",
            "sample-case",
            "sample",
            "--path",
            "one.md",
        )
        self.assertEqual(0, shown.returncode, shown.stderr)
        self.assertIn("displayed_complete=true", shown.stdout)

        accepted = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "read_full",
            "--reason",
            "理解全文",
            "--evidence",
            "one.md#full-file",
            "--path",
            "one.md",
        )
        self.assertEqual(0, accepted.returncode, accepted.stderr)

    def test_source_read_stops_when_registered_file_changes(self) -> None:
        self.init_case()
        (self.source / "one.md").write_text("# Changed\n", encoding="utf-8")
        result = self.run_tool(
            "source-read",
            "sample-case",
            "sample",
            "--path",
            "one.md",
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("来源文件已变化", result.stderr)

    def test_source_select_binds_roles_and_rejects_screened_resolution(self) -> None:
        case = self.init_case()
        selected = self.run_tool(
            "source-select",
            "sample-case",
            "sample",
            "--path",
            "one.md",
            "--level",
            "parent",
            "--reason",
            "用于确定上级领域",
        )
        self.assertEqual(0, selected.returncode, selected.stderr)
        payload = json.loads(selected.stdout)
        self.assertEqual(
            ["parent"], payload["levels"]
        )
        coverage = yaml.safe_load((case / "coverage.yaml").read_text(encoding="utf-8"))
        entry = next(item for item in coverage["files"] if item["path"] == "one.md")
        self.assertEqual(
            ["parent"],
            entry["selection"]["levels"],
        )

        mark = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "screened",
            "--reason",
            "只看过标题",
            "--all-unreviewed",
        )
        self.assertEqual(0, mark.returncode, mark.stderr)
        self.complete_non_content_fields(case)
        result = self.run_tool("check", "sample-case")
        self.assertEqual(1, result.returncode)
        self.assertIn("已选择关键来源尚未阅读或阻塞", result.stdout)

    def test_covered_semantic_spine_requires_selected_read_source(self) -> None:
        case = self.init_case()
        selected = self.run_tool(
            "source-select",
            "sample-case",
            "sample",
            "--path",
            "one.md",
            "--level",
            "focus",
            "--reason",
            "用于解释用户焦点",
        )
        self.assertEqual(0, selected.returncode, selected.stderr)
        shown = self.run_tool(
            "source-read", "sample-case", "sample", "--path", "one.md"
        )
        self.assertEqual(0, shown.returncode, shown.stderr)
        marked = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "read_full",
            "--reason",
            "理解用户焦点",
            "--evidence",
            "one.md#full-file",
            "--path",
            "one.md",
        )
        self.assertEqual(0, marked.returncode, marked.stderr)
        remaining = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "screened",
            "--reason",
            "其余测试来源不改变焦点",
            "--all-unreviewed",
        )
        self.assertEqual(0, remaining.returncode, remaining.stderr)
        self.complete_non_content_fields(case)
        completion = yaml.safe_load((case / "completion.yaml").read_text(encoding="utf-8"))
        focus = next(
            item for item in completion["knowledge_path"] if item["level"] == "focus"
        )
        focus.update(
            {
                "topic": "测试用户焦点",
                "status": "covered",
                "source_files": [{"source_id": "sample", "path": "one.md"}],
                "primary_page": "index.md",
                "rationale": "",
            }
        )
        (case / "completion.yaml").write_text(
            yaml.safe_dump(completion, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        result = self.run_tool("check", "sample-case")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        status = self.run_tool("status", "sample-case")
        self.assertEqual(0, status.returncode, status.stderr)
        self.assertEqual(1, json.loads(status.stdout)["selected_sources"])

    def test_semantic_spine_rejects_shared_primary_page(self) -> None:
        case = self.init_case()
        for path, layer in (("one.md", "parent"), ("two.txt", "focus")):
            selected = self.run_tool(
                "source-select",
                "sample-case",
                "sample",
                "--path",
                path,
                "--level",
                layer,
                "--reason",
                f"用于 {layer}",
            )
            self.assertEqual(0, selected.returncode, selected.stderr)
            shown = self.run_tool(
                "source-read", "sample-case", "sample", "--path", path
            )
            self.assertEqual(0, shown.returncode, shown.stderr)
            marked = self.run_tool(
                "mark",
                "sample-case",
                "sample",
                "--status",
                "read_full",
                "--reason",
                f"理解 {layer}",
                "--evidence",
                f"{path}#full-file",
                "--path",
                path,
            )
            self.assertEqual(0, marked.returncode, marked.stderr)
        self.complete_non_content_fields(case)
        completion = yaml.safe_load((case / "completion.yaml").read_text(encoding="utf-8"))
        for layer in completion["knowledge_path"]:
            if layer["level"] not in {"parent", "focus"}:
                continue
            source_path = "one.md" if layer["level"] == "parent" else "two.txt"
            layer.update(
                {
                    "topic": layer["level"],
                    "status": "covered",
                    "source_files": [
                        {"source_id": "sample", "path": source_path}
                    ],
                    "primary_page": "index.md",
                    "relation_to_next": "上级包含用户焦点",
                    "rationale": "",
                }
            )
        (case / "completion.yaml").write_text(
            yaml.safe_dump(completion, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        result = self.run_tool("check", "sample-case")
        self.assertEqual(1, result.returncode)
        self.assertIn("不同层次共用同一主落点", result.stdout)

    def test_check_rejects_malformed_workbench_table(self) -> None:
        case = self.init_case()
        mark = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "screened",
            "--reason",
            "测试筛查",
            "--all-unreviewed",
        )
        self.assertEqual(0, mark.returncode, mark.stderr)
        self.complete_non_content_fields(case)
        (case / "inventory.md").write_text(
            "# 盘点\n\n| A | B |\n| one | two |\n",
            encoding="utf-8",
        )
        result = self.run_tool("check", "sample-case")
        self.assertEqual(1, result.returncode)
        self.assertIn("Markdown table lacks a header separator", result.stdout)

    def test_check_rejects_directly_inflated_read_claims(self) -> None:
        case = self.init_case()
        coverage = yaml.safe_load((case / "coverage.yaml").read_text(encoding="utf-8"))
        for item in coverage["files"]:
            item["status"] = "read_full"
            item["reason"] = "批量声称已全文读取"
            item["evidence"] = ["shared#full-file"]
        (case / "coverage.yaml").write_text(
            yaml.safe_dump(coverage, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        self.complete_non_content_fields(case)
        result = self.run_tool("check", "sample-case")
        self.assertEqual(1, result.returncode)
        self.assertIn("未标记为 Agent 声明", result.stdout)
        self.assertIn("强阅读声明没有逐文件绑定证据", result.stdout)

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

    def test_check_rejects_legacy_draft_views_tree(self) -> None:
        case = self.init_case()
        mark = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "screened",
            "--reason",
            "测试筛查",
            "--all-unreviewed",
        )
        self.assertEqual(0, mark.returncode, mark.stderr)
        self.complete_non_content_fields(case)
        legacy = case / "draft" / "views"
        legacy.mkdir()
        (legacy / "index.md").write_text("# 错误候选视图\n", encoding="utf-8")
        result = self.run_tool("check", "sample-case")
        self.assertEqual(1, result.returncode)
        self.assertIn(
            "draft/ 只允许 knowledge/ 和 config/",
            result.stdout,
        )

    def test_check_accepts_one_named_view_surface(self) -> None:
        case = self.init_case()
        mark = self.run_tool(
            "mark",
            "sample-case",
            "sample",
            "--status",
            "screened",
            "--reason",
            "测试筛查",
            "--all-unreviewed",
        )
        self.assertEqual(0, mark.returncode, mark.stderr)
        self.complete_non_content_fields(case)

        knowledge = case / "draft" / "knowledge"
        domain = knowledge / "domains" / "quality"
        domain.mkdir()
        concept = (
            "---\ntype: Domain Overview\ntitle: 质检\n"
            "description: 测试领域\n---\n\n# 质检\n"
        )
        (domain / "overview.md").write_text(concept, encoding="utf-8")
        (domain / "index.md").write_text(
            "# 质检\n\n- [领域概览](overview.md)\n", encoding="utf-8"
        )
        (case / "draft" / "config" / "knowledge-domains.yaml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "0.1",
                    "domains": [
                        {
                            "id": "quality",
                            "title": "质检",
                            "parent": None,
                            "scope": "质量评价",
                            "excludes": "生产执行",
                        }
                    ],
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        view_body = (
            "---\ntype: Navigation View\ntitle: {title}\n"
            "description: 测试视图\n---\n\n# {title}\n\n"
            "- [质检](../../domains/quality/overview.md)\n"
        )
        domain_view = knowledge / "views" / "by-domain" / "quality.md"
        journey_view = knowledge / "views" / "by-journey" / "quality.md"
        domain_view.write_text(
            view_body.format(title="质检领域视图"), encoding="utf-8"
        )
        journey_view.write_text(
            view_body.format(title="质检学习视图"), encoding="utf-8"
        )
        (knowledge / "views" / "by-domain" / "index.md").write_text(
            "# 按领域浏览\n\n- [质检领域视图](quality.md)\n", encoding="utf-8"
        )
        (knowledge / "views" / "by-journey" / "index.md").write_text(
            "# 按旅程浏览\n\n- [质检学习视图](quality.md)\n", encoding="utf-8"
        )
        (case / "review.md").write_text(
            (case / "review.md").read_text(encoding="utf-8")
            + "\n- [领域视图](draft/knowledge/views/by-domain/quality.md)\n"
            + "- [旅程视图](draft/knowledge/views/by-journey/quality.md)\n",
            encoding="utf-8",
        )
        (case / "reader-answers.md").write_text(
            "# 逐题实答\n\n"
            "- [旅程视图](draft/knowledge/views/by-journey/quality.md)\n",
            encoding="utf-8",
        )
        result = self.run_tool("check", "sample-case")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
