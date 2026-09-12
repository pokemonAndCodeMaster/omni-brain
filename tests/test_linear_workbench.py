"""Protection of publication identity, concurrent edits and current readback."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("linear_workbench", Path(__file__).parents[1] / "scripts/linear_workbench.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class PublicationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        self.source = self.root / "docs/guide.md"
        self.source.write_text("# 使用说明\n\n- 先读材料\n", encoding="utf-8")
        self.config = {"workspace": "workspace", "team_id": "team-1", "publications": [{"key": "guide", "source": "docs/guide.md", "title": "说明"}]}
        M.write_json(self.root / "config/linear-workbench.json", self.config)
        self.wb = M.Workbench(self.root)
        self.inventory = {"documents": [], "hasNextPage": False}

    def published(self):
        plan = self.wb.plan("guide", inventory=self.inventory)
        remote = {"id": "doc-1", "title": "说明", "content": plan["expected_content"].replace("- 先读", "* 先读"),
                  "url": "https://linear.app/workspace/document/doc-1", "updatedAt": "2026-09-11T00:00:00Z",
                  "team": {"id": "team-1"}}
        self.wb.receipt(plan, remote)
        return remote

    def test_create_readback_and_repeat_is_noop(self):
        remote = self.published()
        self.assertEqual(self.wb.plan("guide", remote=remote)["action"], "noop")
        self.assertFalse(self.wb.status()[0]["local_changed"])
        self.assertTrue((self.root / ".derived/linear/documents/doc-1.md").exists())
        self.assertIn("documents/doc-1.md", (self.root / ".derived/linear/index.md").read_text())

    def test_directory_includes_team_and_issue_docs_and_preserves_navigation(self):
        self.source.write_text('# 阅读路线\n\n保留这段说明\n\n## 全部 Linear 文档\n\n旧目录\n\n## 目录怎样更新\n\n按需刷新\n')
        docs=[{'id':'a','title':'团队文档','url':'https://linear.app/workspace/document/a','team':{'name':'团队'}},
              {'id':'b','title':'事项 | 文档','url':'https://linear.app/workspace/document/b','issue':{'id':'YYH-12'}}]
        result=self.wb.directory('guide',{'documents':docs,'hasNextPage':False})
        body=self.source.read_text()
        self.assertEqual(result['documents'],2)
        self.assertIn('团队文档',body)
        self.assertIn('事项 \\| 文档',body)
        self.assertIn('YYH-12',body)
        self.assertIn('保留这段说明',body)
        self.assertIn('按需刷新',body)
        self.assertNotIn('旧目录',body)
        before=self.source.read_bytes()
        self.wb.directory('guide',{'documents':docs,'hasNextPage':False})
        self.assertEqual(before,self.source.read_bytes())

    def test_directory_rejects_partial_inventory_and_bad_identity_without_writing(self):
        self.source.write_text('## 全部 Linear 文档\n\n## 目录怎样更新\n')
        doc={'id':'a','title':'文档','url':'https://linear.app/workspace/document/a'}
        bad=[{'documents':[doc],'hasNextPage':True}, {'documents':[doc,doc],'hasNextPage':False},
             {'documents':[{**doc,'url':'https://evil.example/document/a'}],'hasNextPage':False}]
        before=self.source.read_bytes()
        for inv in bad:
            with self.subTest(inv=inv),self.assertRaises(M.WorkbenchError):self.wb.directory('guide',inv)
            self.assertEqual(before,self.source.read_bytes())

    def test_update_uses_exact_current_body(self):
        remote = self.published()
        self.source.write_text("# 使用说明\n\n新步骤\n", encoding="utf-8")
        plan = self.wb.plan("guide", remote=remote)
        self.assertEqual(plan["arguments"]["patch"][0]["old_string"], remote["content"])
        self.assertEqual(plan["arguments"]["id"], "doc-1")
        self.assertNotIn("title", plan["arguments"])

    def test_remote_changes_leave_candidate_and_keep_source(self):
        remote = self.published()
        remote["content"] += "\n线上补充的重要限制\n"
        before = self.source.read_bytes()
        with self.assertRaisesRegex(M.WorkbenchError, "Remote changed"):
            self.wb.plan("guide", remote=remote)
        self.assertEqual(before, self.source.read_bytes())
        candidates = list((self.root / ".derived/linear/candidates").rglob("remote.md"))
        self.assertEqual(len(candidates), 1)
        self.assertIn("线上补充的重要限制", candidates[0].read_text())
        self.source.write_text("# 使用说明\n\n先读材料；线上补充的重要限制\n")
        with self.assertRaisesRegex(M.WorkbenchError, "stale"):
            self.wb.plan("guide", remote=remote, reviewed_remote="old")
        plan = self.wb.plan("guide", remote=remote, reviewed_remote=M.fingerprint(remote))
        self.assertEqual(plan["action"], "update")

    def test_partial_readback_does_not_register(self):
        plan = self.wb.plan("guide", inventory=self.inventory)
        remote = {"id": "doc-1", "title": "说明", "content": "被截断的正文", "url": "https://linear.app/document/doc-1",
                  "updatedAt": "now", "team": {"id": "team-1"}}
        with self.assertRaisesRegex(M.WorkbenchError, "Readback does not match"):
            self.wb.receipt(plan, remote)
        self.assertNotIn("id", M.read_json(self.wb.config_path)["publications"][0])

    def test_source_changed_after_plan_is_not_accepted(self):
        remote = self.published()
        plan = self.wb.plan("guide", remote=remote)
        self.source.write_text("Changed while publishing")
        with self.assertRaisesRegex(M.WorkbenchError, "Local source changed"):
            self.wb.receipt(plan, remote)

    def test_missing_inventory_existing_title_or_partial_inventory_rejected(self):
        for inventory in (None, {"documents": [], "hasNextPage": True},
                          {"documents": [{"id": "existing", "title": "说明"}], "hasNextPage": False}):
            with self.subTest(inventory=inventory), self.assertRaises(M.WorkbenchError):
                self.wb.plan("guide", inventory=inventory)

    def test_metadata_only_and_archived_documents_rejected(self):
        remote = self.published()
        for bad in ({"id": "doc-1", "title": "说明"}, {**remote, "archivedAt": "now"}):
            with self.subTest(bad=bad), self.assertRaises(M.WorkbenchError):
                self.wb.plan("guide", remote=bad)

    def test_wrong_document_or_team_receipt_rejected(self):
        remote = self.published()
        plan = self.wb.plan("guide", remote=remote)
        with self.assertRaisesRegex(M.WorkbenchError, "different document"):
            self.wb.receipt(plan, {**remote, "id": "doc-2"})
        with self.assertRaisesRegex(M.WorkbenchError, "parent changed"):
            self.wb.receipt(plan, {**remote, "team": None, "issue": {"id": "YYH-9"}})
        plan["action"] = "create"
        with self.assertRaisesRegex(M.WorkbenchError, "wrong team"):
            self.wb.receipt(plan, {**remote, "team": {"id": "team-2"}})

    def test_paths_and_raw_sources_rejected(self):
        for source in ("../escape.md", "/tmp/out.md", "knowledge/raw/data.md"):
            bad = copy.deepcopy(self.config)
            bad["publications"][0]["source"] = source
            M.write_json(self.wb.config_path, bad)
            with self.subTest(source=source), self.assertRaises(M.WorkbenchError):
                M.Workbench(self.root)
        (self.root / "knowledge/raw").mkdir(parents=True)
        (self.root / "docs/raw-link.md").symlink_to(self.root / "knowledge/raw/data.md")
        bad["publications"][0]["source"] = "docs/raw-link.md"
        M.write_json(self.wb.config_path, bad)
        with self.assertRaises(M.WorkbenchError):
            M.Workbench(self.root)

    def test_unresolved_links_and_empty_source_rejected(self):
        for content in ("", "[本地](another.md)", "[x][ref]\n\n[ref]: ../config/private.json",
                        '[x][ref]\n\n[ref]: <../config/private.json> "title"',
                        '<a href="../private.json">local</a>', '<file:///tmp/private.json>',
                        '> [x][ref]\n>\n> [ref]: ../private.md', '<a href=../private.md>x</a>'):
            self.source.write_text(content)
            with self.subTest(content=content), self.assertRaises(M.WorkbenchError):
                self.wb.plan("guide", inventory=self.inventory)

    def test_mcp_error_and_metadata_capture_rejected(self):
        path = self.root / "tool.json"
        path.write_text(json.dumps({"isError": True, "content": [{"type": "text", "text": "{}"}]}))
        with self.assertRaises(M.WorkbenchError):
            M.read_json(path)
        with self.assertRaises(M.WorkbenchError):
            self.wb.capture({"id": "doc-1", "title": "metadata"})

    def test_normalization_preserves_code_semantics(self):
        plain = '[正文](https://linear.app/中文)\n- 条件\nYYH-7'
        rich = '[正文](<https://linear.app/%E4%B8%AD%E6%96%87>)\n* 条件\n<issue id="uuid" href="https://linear.app/work/issue/YYH-7/title">YYH-7</issue>'
        self.assertEqual(M.normalized(plain, "work"), M.normalized(rich, "work"))
        self.assertNotEqual(M.normalized(plain, "work"), M.normalized(rich.replace('/work/', '/unrelated/'), "work"))
        self.assertNotEqual(M.normalized("```\n- value\n```"), M.normalized("```\n* value\n```"))
        self.assertNotEqual(M.normalized("```\nx  \n```"), M.normalized("```\nx\n```"))
        self.assertNotEqual(M.normalized("````\n```\n- code value\n````"),
                            M.normalized("````\n```\n* code value\n````"))

    def test_url_identity_change_is_a_conflict(self):
        self.source.write_text("[source](https://example.com/a%2Fb)")
        remote = self.published()
        remote["content"] = remote["content"].replace("a%2Fb", "a/b")
        self.source.write_text("[source](https://example.com/a%2Fb)\n\n本地新段落")
        with self.assertRaisesRegex(M.WorkbenchError, "Remote changed"):
            self.wb.plan("guide", remote=remote)
        for encoded, literal in (("%2F", "/"), ("%3F", "?"), ("%23", "#")):
            self.assertNotEqual(M.normalized("[x](https://a/b" + encoded + "c)"),
                                M.normalized("[x](https://a/b" + literal + "c)"))

    def test_capture_refuses_symlink_file_and_directory(self):
        remote = self.published()
        raw = self.root / "knowledge/raw/evidence.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("immutable evidence")
        snapshot = self.root / ".derived/linear/documents/doc-1.md"
        snapshot.unlink()
        snapshot.symlink_to(raw)
        with self.assertRaisesRegex(M.WorkbenchError, "symlink"):
            self.wb.capture(remote)
        self.assertEqual(raw.read_text(), "immutable evidence")
        snapshot.unlink()
        folder = self.root / ".derived/linear/issues"
        folder.symlink_to(raw.parent, target_is_directory=True)
        with self.assertRaisesRegex(M.WorkbenchError, "symlink"):
            self.wb.capture({"id": "evidence", "title": "issue", "description": "overwrite", "url": "https://linear.app/issue/evidence"})
        self.assertEqual(raw.read_text(), "immutable evidence")


if __name__ == "__main__":
    unittest.main()
