from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ingestion_workspace.py"


class IngestionWorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cases = self.root / "cases"
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "README.md").write_text(
            "# Task analysis\n\nThe page renders annotation_submitted and completion_rate.\n",
            encoding="utf-8",
        )
        (self.source / "page.vue").write_text(
            "<script setup>\nimport { query } from './api'\n"
            "const metric = 'annotation_submitted'\n</script>\n",
            encoding="utf-8",
        )
        (self.source / "api.ts").write_text(
            "export async function query() { return fetch('/api/analysis') }\n",
            encoding="utf-8",
        )
        (self.source / "unrelated.txt").write_text("nothing useful\n", encoding="utf-8")
        (self.source / ".env").write_text("SECRET=not-for-manifest\n", encoding="utf-8")
        (self.source / ".runtime").mkdir()
        (self.source / ".runtime" / "db.bin").write_bytes(b"runtime-data")

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

    def start(self, *, require_git: bool = False) -> Path:
        if require_git:
            subprocess.run(["git", "init", "-q"], cwd=self.source, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.source, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=self.source, check=True)
            subprocess.run(["git", "add", "."], cwd=self.source, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.source, check=True)
        result = self.run_tool(
            "start",
            "sample-case",
            "--goal",
            "让开发者理解一个指标从数据到页面的完整链路",
            "--reader",
            "首次接触项目的开发者",
            "--source",
            f"app={self.source}",
            "--question",
            "annotation_submitted 怎样经过接口显示到页面？",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return self.cases / "sample-case"

    def plan(self, *, require_run: bool = False) -> None:
        arguments = [
            "plan-unit",
            "sample-case",
            "q-001",
            "metric-flow",
            "--title",
            "指标数据链路",
            "--kind",
            "software",
            "--path",
            "draft/knowledge/systems/metric-flow.md",
        ]
        if require_run:
            arguments.append("--require-run")
        result = self.run_tool(*arguments)
        self.assertEqual(0, result.returncode, result.stderr)

    def write_candidate(self, case: Path, *, stale: bool = False) -> None:
        knowledge = case / "draft" / "knowledge"
        source_record = knowledge / "sources" / "app.md"
        source_record.write_text(
            "---\ntype: Source\ntitle: 应用源码\ndescription: 本轮授权应用源码\n---\n\n"
            "# 应用源码\n\n固定来源范围和版本。\n",
            encoding="utf-8",
        )
        marker = "\n\n**状态：** 待核实。\n" if stale else ""
        body = (
            "---\ntype: Software System\ntitle: 指标数据链路\n"
            "description: 说明指标从页面入口到接口结果的转换链路\n---\n\n"
            "# 指标数据链路\n\n"
            "**核心结论：** 页面通过 `query` 请求分析接口，并把 `annotation_submitted` "
            "映射到表格单元格。这个链路用于定位字段来源和修改入口。\n\n"
            "## 页面入口与请求\n\n"
            "**入口：** `page.vue` 声明指标并调用 `api.ts` 的 `query`。请求进入分析接口后，"
            "返回值继续由页面状态转换为表格行；读取失败时页面不能把空值冒充零。\n\n"
            "## 修改与验证\n\n"
            "**修改路径：** 改字段时同时检查请求类型、返回类型、映射和表格列，随后使用同一筛选范围"
            "比较接口结果与页面显示。这个顺序防止只改标题而没有修改真实口径。\n"
            + marker
            + "\n# Citations\n\n1. [应用源码](../sources/app.md)\n"
        )
        (knowledge / "systems" / "metric-flow.md").write_text(body, encoding="utf-8")
        view_header = (
            "---\ntype: Navigation View\ntitle: 指标链路视图\n"
            "description: 从读者问题进入指标数据链路\n---\n\n# 指标链路视图\n\n"
        )
        domain_view = knowledge / "views" / "by-domain" / "metric-flow.md"
        journey_view = knowledge / "views" / "by-journey" / "metric-flow.md"
        domain_view.write_text(
            view_header + "从系统位置理解指标。\n\n- [指标数据链路](../../systems/metric-flow.md)\n",
            encoding="utf-8",
        )
        journey_view.write_text(
            view_header + "沿调试路径理解指标。\n\n- [指标数据链路](../../systems/metric-flow.md)\n",
            encoding="utf-8",
        )
        (knowledge / "views" / "index.md").write_text(
            "# 产品视图\n\n- [领域视图](by-domain/metric-flow.md)\n"
            "- [旅程视图](by-journey/metric-flow.md)\n",
            encoding="utf-8",
        )
        (knowledge / "index.md").write_text(
            "# 候选知识入口\n\n- [产品视图](views/index.md)\n",
            encoding="utf-8",
        )

    def get_packet(self) -> dict[str, object]:
        result = self.run_tool(
            "next",
            "sample-case",
            "q-001",
            "--query",
            "annotation_submitted",
            "--limit",
            "2",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def record_answer(self, packet: dict[str, object]) -> subprocess.CompletedProcess[str]:
        refs = [item["ref"] for item in packet["packet"]]
        arguments = [
            "record",
            "sample-case",
            "q-001",
            "--status",
            "answered",
            "--summary",
            "页面入口和 API 调用链已形成规范知识",
            "--source",
            refs[0],
            "--knowledge",
            "draft/knowledge/systems/metric-flow.md",
            "--close-candidates",
            "已有直接入口、导入关系和 API 实现，剩余候选不会改变本问题答案",
        ]
        if len(refs) > 1:
            arguments.extend(["--dismiss-unused", "当前包其余文件只重复入口线索"])
        return self.run_tool(*arguments)

    def test_start_keeps_only_user_outputs_and_two_internal_state_files(self) -> None:
        case = self.start()
        self.assertTrue((case / "review.md").is_file())
        self.assertTrue((case / "draft" / "knowledge" / "index.md").is_file())
        self.assertEqual(
            ["case.json", "source-manifest.jsonl"],
            sorted(path.name for path in (case / ".state").iterdir()),
        )
        for retired in (
            "brief.md", "coverage.yaml", "inventory.md", "reader-answers.md",
            "completion.yaml", "source-summary.md", "questions.md",
        ):
            self.assertFalse((case / retired).exists(), retired)
        records = [
            json.loads(line)
            for line in (case / ".state" / "source-manifest.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(4, len(records))

    def test_next_returns_a_small_ranked_packet_and_import_neighbour(self) -> None:
        self.start()
        payload = self.get_packet()
        self.assertLessEqual(len(payload["packet"]), 2)
        refs = [item["ref"] for item in payload["packet"]]
        self.assertIn("app:page.vue", refs)
        self.assertIn("app:api.ts", refs)
        self.assertNotIn("app:unrelated.txt", refs)
        self.assertNotIn("source-manifest", payload)

    def test_next_diversifies_a_code_packet_across_runtime_layers(self) -> None:
        (self.source / "src").mkdir()
        (self.source / "src" / "service.py").write_text(
            "def calculate(): return 'annotation_submitted'\n", encoding="utf-8"
        )
        (self.source / "migrations").mkdir()
        (self.source / "migrations" / "001.sql").write_text(
            "create table metric(annotation_submitted integer);\n", encoding="utf-8"
        )
        self.start()
        result = self.run_tool(
            "next", "sample-case", "q-001",
            "--query", "annotation_submitted", "--limit", "4",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        roles = {item["role"] for item in payload["packet"]}
        self.assertIn("frontend_view", roles)
        self.assertIn("backend_logic", roles)
        self.assertIn("data_schema", roles)

    def test_next_requires_record_before_another_packet(self) -> None:
        self.start()
        self.get_packet()
        second = self.run_tool("next", "sample-case", "q-001", "--query", "api")
        self.assertEqual(2, second.returncode)
        self.assertIn("尚未 record", second.stderr)

    def test_record_rejects_unresolved_packet_and_unknown_source(self) -> None:
        case = self.start()
        self.plan()
        self.write_candidate(case)
        packet = self.get_packet()
        refs = [item["ref"] for item in packet["packet"]]
        result = self.run_tool(
            "record", "sample-case", "q-001",
            "--status", "answered",
            "--summary", "形成答案",
            "--source", refs[0],
            "--knowledge", "draft/knowledge/systems/metric-flow.md",
        )
        self.assertEqual(2, result.returncode)
        self.assertTrue("未使用来源" in result.stderr or "相关候选" in result.stderr)

    def test_answered_unit_passes_with_knowledge_view_and_direct_source(self) -> None:
        case = self.start()
        self.plan()
        self.write_candidate(case)
        packet = self.get_packet()
        recorded = self.record_answer(packet)
        self.assertEqual(0, recorded.returncode, recorded.stderr)
        checked = self.run_tool("check-unit", "sample-case", "q-001")
        self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
        self.assertIn("knowledge-unit-check: PASS", checked.stdout)
        review = (case / "review.md").read_text(encoding="utf-8")
        self.assertIn("指标数据链路", review)
        self.assertNotIn("coverage", review)

    def test_answered_unit_rejects_stale_unknown_markers(self) -> None:
        case = self.start()
        self.plan()
        self.write_candidate(case, stale=True)
        packet = self.get_packet()
        self.assertEqual(0, self.record_answer(packet).returncode)
        checked = self.run_tool("check-unit", "sample-case", "q-001")
        self.assertEqual(1, checked.returncode)
        self.assertIn("待核实", checked.stdout)

    def test_external_missing_requires_explicit_missing_and_candidate_resolution(self) -> None:
        self.start()
        self.plan()
        packet = self.get_packet()
        refs = [item["ref"] for item in packet["packet"]]
        result = self.run_tool(
            "record", "sample-case", "q-001",
            "--status", "external_missing",
            "--summary", "当前源码只能说明调用入口",
            "--source", refs[0],
            "--missing", "生产环境返回值需要由运行系统补充",
            "--dismiss-unused", "其余文件不包含生产结果",
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("相关候选", result.stderr)

    def test_stop_search_closes_remaining_candidates_without_requerying_sources(self) -> None:
        case = self.start()
        self.plan()
        self.write_candidate(case)
        packet = self.get_packet()
        refs = [item["ref"] for item in packet["packet"]]
        arguments = [
            "record", "sample-case", "q-001",
            "--status", "partial",
            "--summary", "已形成页面入口和 API 调用链，真实返回仍需运行",
            "--source", refs[0],
            "--knowledge", "draft/knowledge/systems/metric-flow.md",
            "--missing", "真实接口返回需要隔离运行验证",
        ]
        if len(refs) > 1:
            arguments.extend(["--dismiss-unused", "当前包其余文件只重复入口线索"])
        recorded = self.run_tool(*arguments)
        self.assertEqual(0, recorded.returncode, recorded.stderr)

        stopped = self.run_tool(
            "stop-search", "sample-case", "q-001",
            "--reason", "剩余候选不改变已形成的调用链，运行缺口必须由来源项目验证",
        )
        self.assertEqual(0, stopped.returncode, stopped.stderr)
        payload = json.loads(stopped.stdout)
        self.assertTrue(payload["stopped"])

        status = json.loads(self.run_tool("status", "sample-case").stdout)
        self.assertEqual(0, status["questions"][0]["remaining_candidates"])
        checked = self.run_tool("check-unit", "sample-case", "q-001")
        self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
        review = (case / "review.md").read_text(encoding="utf-8")
        self.assertIn("已登记不重复直接来源：1 项", review)
        self.assertIn("仍需补充或人工决定", review)
        self.assertIn("真实接口返回需要隔离运行验证", review)

    def test_stop_search_rejects_an_unrecorded_active_packet(self) -> None:
        self.start()
        self.get_packet()
        stopped = self.run_tool(
            "stop-search", "sample-case", "q-001",
            "--reason", "错误地提前结束",
        )
        self.assertEqual(2, stopped.returncode)
        self.assertIn("先写入知识", stopped.stderr)

    def test_isolated_run_uses_a_temporary_worktree_and_preserves_source(self) -> None:
        case = self.start(require_git=True)
        self.plan(require_run=True)
        command = (
            f"{sys.executable} -c \"from pathlib import Path; "
            "Path('generated.txt').write_text('ok'); print('fresh-run')\""
        )
        result = self.run_tool(
            "run", "sample-case", "q-001",
            "--source-id", "app",
            "--kind", "health",
            "--purpose", "验证来源项目可以在隔离副本运行",
            "--command", command,
            "--artifact", "generated.txt",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("temporary_git_worktree", payload["isolation"])
        self.assertFalse((self.source / "generated.txt").exists())
        evidence = case / "evidence" / "runs" / payload["id"]
        self.assertEqual("fresh-run\n", (evidence / "stdout.log").read_text(encoding="utf-8"))
        self.assertEqual("ok", (evidence / "artifacts" / "generated.txt").read_text(encoding="utf-8"))
        self.assertEqual("", subprocess.run(["git", "status", "--short"], cwd=self.source, capture_output=True, text=True).stdout)

    def test_status_restores_questions_knowledge_candidates_and_next_action(self) -> None:
        self.start()
        result = self.run_tool("status", "sample-case")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("q-001", payload["questions"][0]["id"])
        self.assertIn("next", payload["questions"][0])
        self.assertTrue(payload["review"].endswith("review.md"))

    def test_retired_commands_are_absent(self) -> None:
        result = self.run_tool("mark", "sample-case")
        self.assertEqual(2, result.returncode)
        help_result = self.run_tool("--help")
        self.assertNotIn("source-read", help_result.stdout)
        self.assertNotIn(" mark ", help_result.stdout)


if __name__ == "__main__":
    unittest.main()
