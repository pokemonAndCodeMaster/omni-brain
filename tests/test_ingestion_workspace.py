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

    def start_complete(self) -> Path:
        result = self.run_tool(
            "start",
            "complete-case",
            "--mode",
            "complete",
            "--goal",
            "让新成员从全貌到细节理解这批材料并继续工作",
            "--reader",
            "首次接触该领域的成员",
            "--source",
            f"materials={self.source}",
            "--boundary",
            "不能把目标设计写成当前实现",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return self.cases / "complete-case"

    def finish_complete_discovery(self) -> list[str]:
        finding_ids: list[str] = []
        number = 1
        while True:
            status = json.loads(self.run_tool("status", "complete-case").stdout)
            if status["stage"] != "discovering":
                break
            current = json.loads(self.run_tool("next", "complete-case").stdout)["current"]
            finding_id = f"finding-{number:03d}"
            source_ref = current["members"][0]["ref"]
            added = self.run_tool(
                "finding-add",
                "complete-case",
                finding_id,
                "--group-id",
                current["id"],
                "--content",
                f"材料组 {current['id']} 提供可用于读者理解的直接信息",
                "--detail",
                "保留该单元中决定读者理解的输入、转换、输出和边界",
                "--reality",
                "unknown",
                "--source",
                source_ref,
                "--anchor",
                "file",
                "--scope",
                "仅限当前固定材料包",
                "--topic",
                "指标链路",
            )
            self.assertEqual(0, added.returncode, added.stderr)
            recorded = self.run_tool(
                "record-material",
                "complete-case",
                current["id"],
                "--status",
                "reviewed",
                "--summary",
                "已阅读本组并记录精确来源、适用范围和现实边界",
            )
            self.assertEqual(0, recorded.returncode, recorded.stderr)
            finding_ids.append(finding_id)
            number += 1
        return finding_ids

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

    def test_complete_start_builds_observable_groups_without_reality_labels(self) -> None:
        duplicate = self.source / "README-copy.md"
        duplicate.write_bytes((self.source / "README.md").read_bytes())
        case = self.start_complete()
        survey = self.run_tool("survey", "complete-case", "--members")
        self.assertEqual(0, survey.returncode, survey.stderr)
        payload = json.loads(survey.stdout)
        self.assertEqual("complete", payload["mode"])
        self.assertTrue(any(item["kind"] == "exact_duplicate" for item in payload["groups"]))
        self.assertNotIn("reality_hints", survey.stdout)
        for group in payload["groups"]:
            self.assertNotIn("reality", group)
        state = json.loads((case / ".state" / "case.json").read_text(encoding="utf-8"))
        self.assertEqual("discovering", state["stage"])
        self.assertEqual(["case.json", "source-manifest.jsonl"], sorted(path.name for path in (case / ".state").iterdir()))

    def test_material_groups_limit_count_and_total_bytes_and_ignore_package_checksum(self) -> None:
        bulk = self.source / "bulk"
        bulk.mkdir()
        for index, marker in enumerate(("a", "b", "c"), 1):
            (bulk / f"{index}.md").write_text(marker * 45_000, encoding="utf-8")
        (self.source / "SHA256SUMS").write_text("package checksum metadata\n", encoding="utf-8")
        self.start_complete()
        payload = json.loads(self.run_tool("survey", "complete-case", "--members").stdout)
        refs = [member["ref"] for group in payload["groups"] for member in group["members"]]
        self.assertNotIn("materials:SHA256SUMS", refs)
        for group in payload["groups"]:
            self.assertLessEqual(group["member_count"], 12)
            self.assertTrue(
                group["total_bytes"] <= 100_000 or group["member_count"] == 1,
                group,
            )
        bulk_groups = [
            group
            for group in payload["groups"]
            if any(member["ref"].startswith("materials:bulk/") for member in group["members"])
        ]
        self.assertEqual(3, len(bulk_groups))
        self.assertTrue(all(group["kind"] == "narrative_document" for group in bulk_groups))

    def test_complete_next_and_material_record_are_idempotent(self) -> None:
        self.start_complete()
        first = self.run_tool("next", "complete-case")
        second = self.run_tool("next", "complete-case")
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(0, second.returncode, second.stderr)
        first_payload = json.loads(first.stdout)
        second_payload = json.loads(second.stdout)
        self.assertEqual(first_payload["current"]["id"], second_payload["current"]["id"])
        status = json.loads(self.run_tool("status", "complete-case").stdout)
        self.assertEqual(first_payload["current"]["id"], status["current"]["id"])
        self.assertTrue(status["current"]["open_paths"])
        group = first_payload["current"]
        source_ref = group["members"][0]["ref"]
        finding_args = (
            "finding-add", "complete-case", "finding-001",
            "--group-id", group["id"],
            "--content", "本组说明页面和接口之间存在直接调用关系",
            "--detail", "页面入口通过 api.ts 的 query 进入分析接口",
            "--reality", "current_implementation",
            "--source", source_ref,
            "--anchor", f"{source_ref}#file",
            "--scope", "当前固定源码",
            "--topic", "指标链路",
        )
        added = self.run_tool(*finding_args)
        repeated_add = self.run_tool(*finding_args)
        self.assertEqual(0, added.returncode, added.stderr)
        self.assertTrue(json.loads(repeated_add.stdout)["already_recorded"])
        record_args = (
            "record-material", "complete-case", group["id"],
            "--status", "reviewed",
            "--summary", "已读完会改变调用链结论的成员并形成发现",
        )
        recorded = self.run_tool(*record_args)
        repeated_record = self.run_tool(*record_args)
        self.assertEqual(0, recorded.returncode, recorded.stderr)
        self.assertTrue(json.loads(repeated_record.stdout)["already_recorded"])

    def test_complete_finding_requires_key_detail_and_precise_anchor(self) -> None:
        self.start_complete()
        group = json.loads(self.run_tool("next", "complete-case").stdout)["current"]
        source_ref = group["members"][0]["ref"]
        missing_detail = self.run_tool(
            "finding-add", "complete-case", "finding-001",
            "--group-id", group["id"],
            "--content", "材料给出一个可复用结论",
            "--reality", "current_implementation",
            "--source", source_ref,
            "--anchor", f"{source_ref}#file",
            "--scope", "当前固定材料包",
        )
        self.assertEqual(2, missing_detail.returncode)
        self.assertIn("--detail", missing_detail.stderr)
        missing_anchor = self.run_tool(
            "finding-add", "complete-case", "finding-001",
            "--group-id", group["id"],
            "--content", "材料给出一个可复用结论",
            "--detail", "这项细节决定后续理解或行动",
            "--reality", "current_implementation",
            "--source", source_ref,
            "--scope", "当前固定材料包",
        )
        self.assertEqual(2, missing_anchor.returncode)
        self.assertIn("--anchor", missing_anchor.stderr)
        added = self.run_tool(
            "finding-add", "complete-case", "finding-001",
            "--group-id", group["id"],
            "--content", "材料给出一个可复用结论",
            "--detail", "这项细节决定后续理解或行动",
            "--reality", "current_implementation",
            "--source", source_ref,
            "--anchor", "file",
            "--scope", "当前固定材料包",
        )
        self.assertEqual(0, added.returncode, added.stderr)
        case = json.loads(
            (self.cases / "complete-case" / ".state" / "case.json").read_text(encoding="utf-8")
        )
        self.assertEqual([f"{source_ref}#file"], case["findings"][0]["anchors"])

    def test_start_inherits_formal_knowledge_and_records_parent_identity(self) -> None:
        case = self.start_complete()
        state = json.loads((case / ".state" / "case.json").read_text(encoding="utf-8"))
        baseline = state["baseline"]
        self.assertGreater(baseline["file_count"], 0)
        self.assertEqual(64, len(baseline["fingerprint"]))
        self.assertEqual(
            (ROOT / "knowledge" / "index.md").read_bytes(),
            (case / "draft" / "knowledge" / "index.md").read_bytes(),
        )
        self.assertEqual(
            (ROOT / "config" / "knowledge-domains.yaml").read_bytes(),
            (case / "draft" / "config" / "knowledge-domains.yaml").read_bytes(),
        )
        self.assertEqual(
            ["case.json", "source-manifest.jsonl"],
            sorted(path.name for path in (case / ".state").iterdir()),
        )

    def test_incremental_topic_actions_must_match_parent_paths(self) -> None:
        self.start_complete()
        findings = self.finish_complete_discovery()
        common = [
            "--title", "系统知识入口",
            "--purpose", "把新增发现有机融入父知识",
            "--finding", findings[0],
            "--view", "draft/knowledge/views/by-domain/metric-flow.md",
        ]
        create_over_existing = self.run_tool(
            "topic-add", "complete-case", "existing-as-create",
            *common,
            "--action", "create",
            "--path", "draft/knowledge/log.md",
        )
        self.assertEqual(2, create_over_existing.returncode)
        self.assertIn("现有页面请使用 update 或 merge", create_over_existing.stderr)
        update_missing = self.run_tool(
            "topic-add", "complete-case", "missing-as-update",
            *common,
            "--action", "update",
            "--path", "draft/knowledge/systems/new-page.md",
        )
        self.assertEqual(2, update_missing.returncode)
        self.assertIn("新页面请使用 create", update_missing.stderr)

    def test_narrative_documents_remain_separate_but_keep_links(self) -> None:
        docs = self.source / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("# A\n\n[继续阅读](b.md)\n", encoding="utf-8")
        (docs / "b.md").write_text("# B\n\n独立结论。\n", encoding="utf-8")
        self.start_complete()
        groups = json.loads(
            self.run_tool("survey", "complete-case", "--members").stdout
        )["groups"]
        group_a = next(
            group for group in groups
            if any(member["ref"] == "materials:docs/a.md" for member in group["members"])
        )
        group_b = next(
            group for group in groups
            if any(member["ref"] == "materials:docs/b.md" for member in group["members"])
        )
        self.assertNotEqual(group_a["id"], group_b["id"])
        self.assertEqual("narrative_document", group_a["kind"])
        self.assertIn(group_b["id"], {item["group_id"] for item in group_a["related_groups"]})

    def test_plan_review_blocks_unreviewed_materials_and_missing_lenses(self) -> None:
        self.start_complete()
        too_early = self.run_tool(
            "plan-review", "complete-case",
            "--not-applicable", "position=范围明确不涉及上级位置",
        )
        self.assertEqual(2, too_early.returncode)
        self.assertIn("尚未进入", too_early.stderr)

        findings = self.finish_complete_discovery()
        reopened = self.run_tool(
            "material-reopen", "complete-case", "group-001",
            "--reason", "目录复核需要重新核对第一组的现实边界",
        )
        self.assertEqual(0, reopened.returncode, reopened.stderr)
        self.assertEqual("discovering", json.loads(reopened.stdout)["stage"])
        closed_again = self.run_tool(
            "record-material", "complete-case", "group-001",
            "--status", "reviewed",
            "--summary", "重新核对后原有发现和适用边界仍然成立",
        )
        self.assertEqual(0, closed_again.returncode, closed_again.stderr)
        topic = self.run_tool(
            "topic-add", "complete-case", "metric-flow",
            "--title", "指标数据链路",
            "--purpose", "让读者定位指标从入口到输出的变化",
            "--action", "create",
            "--path", "draft/knowledge/systems/metric-flow.md",
            *sum((["--finding", item] for item in findings), []),
            "--view", "draft/knowledge/views/by-domain/metric-flow.md",
            "--view", "draft/knowledge/views/by-journey/metric-flow.md",
        )
        self.assertEqual(0, topic.returncode, topic.stderr)
        updated = self.run_tool(
            "topic-add", "complete-case", "metric-flow",
            "--title", "指标数据链路",
            "--purpose", "让读者从输入、转换和输出理解指标链路并定位修改入口",
            "--action", "create",
            "--path", "draft/knowledge/systems/metric-flow.md",
            *sum((["--finding", item] for item in findings), []),
            "--view", "draft/knowledge/views/by-domain/metric-flow.md",
            "--view", "draft/knowledge/views/by-journey/metric-flow.md",
        )
        self.assertEqual(0, updated.returncode, updated.stderr)
        self.assertTrue(json.loads(updated.stdout)["updated"])
        incomplete = self.run_tool(
            "plan-review", "complete-case",
            "--lens", "software=metric-flow",
        )
        self.assertEqual(1, incomplete.returncode)
        report = json.loads(incomplete.stdout)["plan_review"]
        self.assertTrue(any("读者理解角度" in item for item in report["issues"]))

    def test_plan_review_rejects_duplicate_normative_ownership(self) -> None:
        self.start_complete()
        findings = self.finish_complete_discovery()
        common = [
            "--title", "指标链路",
            "--purpose", "说明指标变化",
            "--action", "create",
        ]
        first = self.run_tool(
            "topic-add", "complete-case", "topic-a", *common,
            "--path", "draft/knowledge/systems/topic-a.md",
            *sum((["--finding", item] for item in findings), []),
            "--view", "draft/knowledge/views/by-domain/metric-flow.md",
        )
        self.assertEqual(0, first.returncode, first.stderr)
        second = self.run_tool(
            "topic-add", "complete-case", "topic-b", *common,
            "--path", "draft/knowledge/systems/topic-b.md",
            "--finding", findings[0],
            "--view", "draft/knowledge/views/by-journey/metric-flow.md",
        )
        self.assertEqual(0, second.returncode, second.stderr)
        lenses = sum(
            (["--lens", f"{lens}=topic-a"] for lens in (
                "position", "lifecycle", "data", "rules", "software", "shared", "reality", "navigation"
            )),
            [],
        )
        reviewed = self.run_tool("plan-review", "complete-case", *lenses)
        self.assertEqual(1, reviewed.returncode)
        self.assertTrue(
            any(
                "多个规范主题重复维护" in item
                for item in json.loads(reviewed.stdout)["plan_review"]["issues"]
            )
        )

    def test_complete_flow_reaches_publish_review_with_one_cursor(self) -> None:
        case = self.start_complete()
        findings = self.finish_complete_discovery()
        planning = json.loads(self.run_tool("next", "complete-case").stdout)
        self.assertEqual("planning", planning["stage"])
        self.assertEqual(set(findings), {item["id"] for item in planning["current"]["findings"]})
        self.write_candidate(case)
        topic_args = [
            "topic-add", "complete-case", "metric-flow",
            "--title", "指标数据链路",
            "--purpose", "让读者从系统位置进入一次真实修改链路",
            "--action", "create",
            "--path", "draft/knowledge/systems/metric-flow.md",
        ]
        for finding_id in findings:
            topic_args.extend(["--finding", finding_id])
        topic_args.extend(
            [
                "--view", "draft/knowledge/views/by-domain/metric-flow.md",
                "--view", "draft/knowledge/views/by-journey/metric-flow.md",
            ]
        )
        self.assertEqual(0, self.run_tool(*topic_args).returncode)
        lenses: list[str] = []
        for lens in ("position", "lifecycle", "data", "rules", "software", "shared", "reality", "navigation"):
            lenses.extend(["--lens", f"{lens}=metric-flow"])
        reviewed = self.run_tool("plan-review", "complete-case", *lenses)
        self.assertEqual(0, reviewed.returncode, reviewed.stderr)
        first = json.loads(self.run_tool("next", "complete-case").stdout)
        second = json.loads(self.run_tool("next", "complete-case").stdout)
        self.assertEqual("metric-flow", first["current"]["id"])
        self.assertEqual(first["current"]["id"], second["current"]["id"])
        journey = case / "draft" / "knowledge" / "views" / "by-journey" / "metric-flow.md"
        journey.write_text(
            "---\ntype: Navigation View\ntitle: 空旅程\ndescription: 暂未链接正文\n---\n\n# 空旅程\n",
            encoding="utf-8",
        )
        missing_locations = self.run_tool("record-topic", "complete-case", "metric-flow")
        self.assertEqual(2, missing_locations.returncode)
        self.assertIn("尚未定位到正文真实章节", missing_locations.stderr)
        section_args = sum(
            (["--section", f"{finding_id}=页面入口与请求"] for finding_id in findings),
            [],
        )
        rejected = self.run_tool(
            "record-topic", "complete-case", "metric-flow", *section_args
        )
        self.assertEqual(2, rejected.returncode)
        self.assertIn("尚未链接规范知识", rejected.stderr)
        self.write_candidate(case)
        recorded = self.run_tool(
            "record-topic", "complete-case", "metric-flow", *section_args
        )
        self.assertEqual(0, recorded.returncode, recorded.stderr)
        final_review = self.run_tool("review", "complete-case")
        self.assertEqual(0, final_review.returncode, final_review.stdout + final_review.stderr)
        self.assertTrue(json.loads(final_review.stdout)["ready"])
        status = json.loads(self.run_tool("status", "complete-case").stdout)
        self.assertEqual("publish_ready", status["stage"])
        review_text = (case / "review.md").read_text(encoding="utf-8")
        self.assertIn("知识目录与完成状态", review_text)
        self.assertIn("材料范围与读后发现", review_text)
        source_index = (
            case / "draft" / "knowledge" / "sources" / "index.md"
        ).read_text(encoding="utf-8")
        self.assertIn("直接材料与结论定位", source_index)
        self.assertIn("materials:", source_index)
        self.assertIn("#file", source_index)
        self.assertIn("页面入口与请求", source_index)

    def test_next_returns_a_small_ranked_packet_and_import_neighbour(self) -> None:
        self.start()
        payload = self.get_packet()
        self.assertLessEqual(len(payload["packet"]), 2)
        refs = [item["ref"] for item in payload["packet"]]
        self.assertIn("app:page.vue", refs)
        self.assertIn("app:api.ts", refs)
        self.assertNotIn("app:unrelated.txt", refs)
        self.assertNotIn("source-manifest", payload)

    def test_next_resolves_common_vite_at_alias_without_project_specific_config(self) -> None:
        features = self.source / "frontend" / "src" / "features"
        shared = self.source / "frontend" / "src" / "shared"
        features.mkdir(parents=True)
        shared.mkdir(parents=True)
        (features / "page.ts").write_text(
            "import { helper } from '@/shared/tool'\nexport const unique_metric = helper()\n",
            encoding="utf-8",
        )
        (shared / "tool.ts").write_text("export const helper = () => 42\n", encoding="utf-8")
        self.start()
        result = self.run_tool(
            "next", "sample-case", "q-001",
            "--query", "unique_metric", "--limit", "2",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        refs = {item["ref"] for item in json.loads(result.stdout)["packet"]}
        self.assertIn("app:frontend/src/features/page.ts", refs)
        self.assertIn("app:frontend/src/shared/tool.ts", refs)

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

    def test_document_flow_does_not_require_a_run_or_run_integration(self) -> None:
        case = self.start()
        self.plan()
        self.write_candidate(case)
        packet = self.get_packet()
        self.assertEqual(0, self.record_answer(packet).returncode)

        status = json.loads(self.run_tool("status", "sample-case").stdout)
        self.assertEqual([], status["questions"][0]["run_ids"])
        self.assertEqual([], status["questions"][0]["pending_run_ids"])
        self.assertEqual(0, self.run_tool("check-unit", "sample-case", "q-001").returncode)

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

    def test_live_runtime_input_is_identified_and_exposed_by_absolute_path(self) -> None:
        case = self.start(require_git=True)
        self.plan(require_run=True)
        command = (
            f"{sys.executable} -c \"import os; from pathlib import Path; "
            "p=Path(os.environ['OMNI_MOUNT_1']); "
            "print(p.is_absolute(), (p/'db.bin').read_text())\""
        )
        result = self.run_tool(
            "run", "sample-case", "q-001",
            "--source-id", "app",
            "--kind", "health",
            "--purpose", "读取来源项目声明的外部运行数据",
            "--command", command,
            "--mount", ".runtime",
            "--runtime-note", "运行结果依赖当前外部服务状态",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("environment_bound", payload["runtime_scope"])
        self.assertEqual(["运行结果依赖当前外部服务状态"], payload["runtime_notes"])
        runtime_input = payload["runtime_inputs"][0]
        self.assertEqual("live_reference", runtime_input["mode"])
        self.assertEqual("OMNI_MOUNT_1", runtime_input["environment_variable"])
        evidence = case / "evidence" / "runs" / payload["id"]
        self.assertIn("True runtime-data", (evidence / "stdout.log").read_text(encoding="utf-8"))
        self.assertIn(
            "运行范围：环境绑定，不能当作固定基线",
            (case / "review.md").read_text(encoding="utf-8"),
        )

    def test_copy_mount_is_private_writable_and_does_not_change_source(self) -> None:
        self.start(require_git=True)
        self.plan(require_run=True)
        command = (
            f"{sys.executable} -c \"import os; from pathlib import Path; "
            "p=Path(os.environ['OMNI_MOUNT_1'])/'db.bin'; "
            "p.write_text('private-change'); print(p.read_text())\""
        )
        result = self.run_tool(
            "run", "sample-case", "q-001",
            "--source-id", "app",
            "--kind", "page",
            "--purpose", "在私有可写依赖副本中运行工具",
            "--command", command,
            "--copy-mount", ".runtime",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("private_snapshot", payload["runtime_scope"])
        runtime_input = payload["runtime_inputs"][0]
        self.assertEqual("private_copy", runtime_input["mode"])
        self.assertEqual(b"runtime-data", (self.source / ".runtime" / "db.bin").read_bytes())

    def test_same_runtime_path_cannot_be_live_and_copied(self) -> None:
        self.start(require_git=True)
        self.plan(require_run=True)
        result = self.run_tool(
            "run", "sample-case", "q-001",
            "--source-id", "app",
            "--kind", "other",
            "--purpose", "拒绝含糊的运行输入模式",
            "--command", "true",
            "--mount", ".runtime",
            "--copy-mount", ".runtime",
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("不能同时使用", result.stderr)

    def test_command_file_run_must_be_integrated_before_unit_can_close(self) -> None:
        case = self.start(require_git=True)
        self.plan(require_run=True)
        self.write_candidate(case)
        knowledge_path = "draft/knowledge/systems/metric-flow.md"
        packet = self.get_packet()
        refs = [item["ref"] for item in packet["packet"]]
        record_arguments = [
            "record", "sample-case", "q-001",
            "--status", "partial",
            "--summary", "静态调用链已经形成，仍需隔离运行",
            "--source", refs[0],
            "--knowledge", knowledge_path,
            "--missing", "真实运行结果尚未写回",
            "--close-candidates", "当前源码链已经充分，剩余缺口只能由运行证明",
        ]
        if len(refs) > 1:
            record_arguments.extend(["--dismiss-unused", "当前包其余文件只重复入口线索"])
        self.assertEqual(0, self.run_tool(*record_arguments).returncode)

        recipe = case / "evidence" / "recipes" / "verify.sh"
        recipe.parent.mkdir(parents=True)
        recipe.write_text("printf 'api=42\\nsql=42\\n'\n", encoding="utf-8")
        run = self.run_tool(
            "run", "sample-case", "q-001",
            "--source-id", "app",
            "--kind", "api",
            "--purpose", "核对固定范围 API 与 SQL",
            "--command-file", "evidence/recipes/verify.sh",
        )
        self.assertEqual(0, run.returncode, run.stderr)
        run_payload = json.loads(run.stdout)
        run_id = run_payload["id"]
        evidence = case / "evidence" / "runs" / run_id
        self.assertEqual("api=42\nsql=42\n", (evidence / "stdout.log").read_text(encoding="utf-8"))
        self.assertTrue((evidence / "command.sh").is_file())

        before_integration = self.run_tool("check-unit", "sample-case", "q-001")
        self.assertEqual(1, before_integration.returncode)
        self.assertIn("尚未写回规范知识", before_integration.stdout)

        page = case / knowledge_path
        page.write_text(
            page.read_text(encoding="utf-8")
            + "\n## 运行核对\n\n```vue\n<script setup>\n```\n\n"
            + "**结果：** 固定范围 API 与 SQL 都返回 42，当前实验范围内一致。\n",
            encoding="utf-8",
        )
        integrated = self.run_tool(
            "record", "sample-case", "q-001",
            "--status", "answered",
            "--summary", "静态调用链和固定范围运行结果均已写入规范知识",
            "--run-id", run_id,
            "--knowledge", knowledge_path,
        )
        self.assertEqual(0, integrated.returncode, integrated.stderr)
        self.assertEqual(0, self.run_tool("check-unit", "sample-case", "q-001").returncode)
        review = (case / "review.md").read_text(encoding="utf-8")
        self.assertNotIn("真实运行结果尚未写回", review)
        self.assertNotIn("尚待写回知识的运行结果", review)

    def test_missing_declared_artifact_preserves_failed_run_evidence(self) -> None:
        case = self.start(require_git=True)
        self.plan(require_run=True)
        result = self.run_tool(
            "run", "sample-case", "q-001",
            "--source-id", "app",
            "--kind", "other",
            "--purpose", "验证缺少声明产物时仍保留命令输出",
            "--command", "printf 'command-finished\\n'",
            "--artifact", "missing.txt",
        )
        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["evidence_complete"])
        self.assertTrue(payload["artifact_errors"])
        evidence = case / "evidence" / "runs" / payload["id"]
        self.assertEqual("command-finished\n", (evidence / "stdout.log").read_text(encoding="utf-8"))
        self.assertTrue((evidence / "run.json").is_file())

    def test_parallel_mutations_do_not_lose_questions(self) -> None:
        self.start()
        base = [
            sys.executable,
            str(SCRIPT),
            "--cases-root",
            str(self.cases),
            "question-add",
            "sample-case",
            "--text",
        ]
        first = subprocess.Popen(
            [*base, "补充业务边界？"], cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )
        second = subprocess.Popen(
            [*base, "补充运行路径？"], cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )
        first_stdout, first_stderr = first.communicate(timeout=10)
        second_stdout, second_stderr = second.communicate(timeout=10)
        self.assertEqual(0, first.returncode, first_stdout + first_stderr)
        self.assertEqual(0, second.returncode, second_stdout + second_stderr)

        case = json.loads(
            (self.cases / "sample-case" / ".state" / "case.json").read_text(encoding="utf-8")
        )
        self.assertEqual(3, len(case["questions"]))
        self.assertEqual({"q-001", "q-002", "q-003"}, {item["id"] for item in case["questions"]})

    def test_status_restores_questions_knowledge_candidates_and_next_action(self) -> None:
        self.start()
        result = self.run_tool("status", "sample-case")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("q-001", payload["questions"][0]["id"])
        self.assertIn("next", payload["questions"][0])
        self.assertTrue(payload["review"].endswith("review.md"))

    def test_status_exposes_git_identity_without_reading_internal_state(self) -> None:
        self.start(require_git=True)
        result = self.run_tool("status", "sample-case")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        source = payload["sources"][0]
        expected_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.source,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(str(self.source), source["root"])
        self.assertEqual("local_git", source["kind"])
        self.assertEqual(expected_commit, source["git"]["commit"])
        self.assertEqual(".", source["git"]["scope"])
        self.assertFalse(source["git"]["dirty"])

    def test_retired_commands_are_absent(self) -> None:
        result = self.run_tool("mark", "sample-case")
        self.assertEqual(2, result.returncode)
        help_result = self.run_tool("--help")
        self.assertNotIn("source-read", help_result.stdout)
        self.assertNotIn(" mark ", help_result.stdout)


if __name__ == "__main__":
    unittest.main()
