"""Reader checks focus on safe content, completeness, and actual user interactions."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("reader", ROOT / "scripts/render_personal_workbench.py")
reader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reader)


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "docs/linear-workbench/assets", self.root / "docs/linear-workbench/assets")
        self.snapshots = self.root / ".derived/linear"
        self.output = self.root / ".derived/personal-workbench/index.html"

    def save(self, folder, item):
        path = self.snapshots / folder / (item["id"] + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
        return path

    def fixture(self):
        self.save("issues", {"id":"YYH-11", "uuid":"issue-uuid", "title":"设计 Codex 接续方式", "status":"In Progress", "statusType":"started", "description":"目标：新会话能继续同一项工作。\n\n[方案](https://linear.app/example/document/abcdef123456)", "url":"https://linear.app/example/issue/YYH-11/title", "updatedAt":"2026-09-12T10:00:00Z", "documents":[{"id":"doc-issue"}]})
        self.save("issues", {"id":"YYH-2", "title":"已完成的工作", "status":"Done", "description":"已验证", "url":"https://linear.app/example/issue/YYH-2", "updatedAt":"2026-09-11T10:00:00Z"})
        self.save("documents", {"id":"doc-team", "title":"团队知识目录", "content":"这是完整的团队文档。独特中文正文。", "url":"https://linear.app/example/document/111111111111", "team":{"id":"team", "name":"个人团队"}, "updatedAt":"2026-09-12T10:00:00Z"})
        self.save("documents", {"id":"doc-issue", "title":"事项所属方案", "content":"# 安全正文\n\n<script>window.PWNED=true</script>\n\n[危险](javascript:alert(1))\n\n![远程图](https://example.com/tracker.png)\n\n</script><script>window.PWNED=true</script>", "url":"https://linear.app/example/document/design-abcdef123456", "issue":{"id":"issue-uuid", "title":"设计 Codex 接续方式"}, "updatedAt":"2026-09-12T10:00:00Z"})

    def test_includes_every_document_parent_and_closed_issues(self):
        self.fixture()
        self.save("issues", {"id":"YYH-3", "title":"准备做的事", "status":"Todo", "statusType":"unstarted", "description":"本周准备继续", "url":"https://linear.app/example/issue/YYH-3"})
        self.save("issues", {"id":"YYH-4", "title":"以后考虑的想法", "status":"Backlog", "statusType":"backlog", "description":"尚未安排", "url":"https://linear.app/example/issue/YYH-4"})
        items = reader.load_items(self.root, self.snapshots)
        self.assertEqual(len(items), 6)
        self.assertEqual(next(i for i in items if i["nativeId"] == "YYH-3")["group"], "now")
        self.assertEqual(next(i for i in items if i["nativeId"] == "YYH-4")["group"], "ideas")
        self.assertEqual({i["nativeId"] for i in items if i["kind"] == "document"}, {"doc-team", "doc-issue"})
        self.assertEqual(next(i for i in items if i["nativeId"] == "doc-issue")["parent"], "YYH-11")
        self.assertEqual(next(i for i in items if i["nativeId"] == "YYH-2")["group"], "closed")

    def test_rejects_summary_only_snapshot(self):
        self.save("documents", {"id":"doc-1", "title":"只有列表元数据", "url":"https://linear.app/example/document/a"})
        with self.assertRaisesRegex(ValueError, "缺少全文"):
            reader.load_items(self.root, self.snapshots)

    def test_markup_and_active_urls_are_not_executable(self):
        body = '<img src=x onerror="alert(1)"><script>alert(1)</script>\n\n[x](javascript:alert%281%29)\n\n![tracker](https://example.com/image.png)\n\n[local](file:///etc/passwd)'
        rendered = reader.render_markdown(body, "", {})
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img", rendered)
        self.assertNotIn('href="javascript:', rendered)
        self.assertNotIn('href="file:', rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn('rel="noopener noreferrer"', rendered)
        for url in ("javascript:alert(1)", "data:text/html,hi", "file:///etc/passwd", "//evil.example/path", "https://user:password@evil.example", "http://[invalid", "java\nscript:alert(1)"):
            self.assertEqual(reader.safe_url(url), "")

    def test_local_entries_respect_root_raw_and_explicit_full_text(self):
        (self.root / "docs/guide.md").write_text("完整本地知识\n\n[另一页](other.md)", encoding="utf-8")
        (self.root / "docs/other.md").write_text("另一份正文", encoding="utf-8")
        index = self.root / "local.json"
        index.write_text(json.dumps({"items":[{"id":"guide", "title":"本地知识", "path":"docs/guide.md", "kind":"knowledge", "updatedAt":"", "inspectedAt":"2026-09-12T12:00:00Z"}]}), encoding="utf-8")
        item = reader.load_items(self.root, self.snapshots, index)[0]
        self.assertIn("完整本地知识", item["body"])
        self.assertEqual(item["updatedAt"], "")
        self.assertEqual(item["inspectedAt"], "2026-09-12T12:00:00Z")
        self.assertIn("#view=knowledge&amp;item=local%3Aother", reader.render_markdown(item["body"], item["path"], {"docs/other.md":"local:other"}))
        for path in ("../outside.md", "/etc/passwd", "knowledge/raw/secret.md"):
            with self.assertRaises(ValueError):
                reader.contained_path(self.root, path)

    def test_online_catalogue_alias_does_not_duplicate_snapshot(self):
        self.fixture()
        index = self.root / "local.json"
        index.write_text(json.dumps({"items":[{"id":"catalogue", "title":"同一文档", "path":"", "url":"https://linear.app/example/document/abcdef123456", "domain":"个人工作台"}]}), encoding="utf-8")
        self.assertEqual(len(reader.load_items(self.root, self.snapshots, index)), 4)

    def test_frontmatter_stays_readable_without_becoming_a_heading(self):
        rendered = reader.render_markdown("---\ntype: Knowledge\ntitle: 资料标题\n---\n# 人能读的正文\n\n[本页目录](#实际口径)\n\n## 实际口径\n\n明确的业务定义。", "docs/guide.md", {})
        self.assertIn('<details class="document-metadata">', rendered)
        self.assertIn("type: Knowledge", rendered)
        self.assertNotIn("<h2>type:", rendered)
        self.assertIn('href="#reader-实际口径"', rendered)
        self.assertIn('id="reader-实际口径"', rendered)

    def test_embedded_json_cannot_close_script_and_output_rejects_symlinks(self):
        self.fixture()
        result = reader.build(self.root, self.snapshots, self.output)
        page = self.output.read_text(encoding="utf-8")
        self.assertEqual(result["documents"], 2)
        self.assertNotIn("</script><script>window.PWNED", page)
        self.assertIn("Content-Security-Policy", page)
        self.assertIn("connect-src &#x27;none&#x27;", page)
        (self.root / "link").symlink_to(self.output.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            reader.build(self.root, self.snapshots, self.root / "link/unsafe.html")

    def test_browser_search_related_reading_handoff_mobile_and_security(self):
        try:
            from playwright.sync_api import sync_playwright, expect
        except ImportError:
            self.skipTest("Playwright is optional; install it to run the real-browser reader check")
        self.fixture()
        (self.root / "docs/quality.md").write_text("---\ntype: Knowledge\n---\n# 正式质检知识\n\n[跳到案例](#具体案例)\n\n## 具体案例\n\n验收前先核对实际结果与判定口径。", encoding="utf-8")
        local_index = self.root / "local.json"
        local_index.write_text(json.dumps({"items":[{"id":"quality", "title":"正式质检知识", "path":"docs/quality.md", "kind":"knowledge", "domain":"Omni-Brain", "inspectedAt":"2026-09-12T12:00:00Z"}]}), encoding="utf-8")
        reader.build(self.root, self.snapshots, self.output, local_index)
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except Exception as error:
                self.skipTest("Chromium is not available: " + str(error).splitlines()[0])
            try:
                context = browser.new_context(viewport={"width":1440,"height":1000})
                context.add_init_script("Object.defineProperty(navigator, 'clipboard', {value: {writeText: async () => {throw new Error('Denied')}}});")
                page = context.new_page()
                errors, requests = [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("request", lambda request: requests.append(request.url))
                page.goto(self.output.as_uri())
                expect(page.locator(".item-button")).to_have_count(1)
                page.locator("#body a").click()
                expect(page.locator("#detail-title")).to_have_text("事项所属方案")
                self.assertIsNone(page.evaluate("window.PWNED"))
                self.assertEqual(page.locator("#body img, #body script").count(), 0)
                page.locator('[data-view="knowledge"]').click()
                expect(page.locator(".item-button")).to_have_count(3)
                page.locator("#search").fill("独特中文正文")
                expect(page.locator(".item-button")).to_have_count(1)
                expect(page.locator("#detail-title")).to_have_text("团队知识目录")
                page.locator("#handoff").click()
                page.locator("#copy-handoff").click()
                expect(page.locator("#copy-status")).to_contain_text("内容已选中")
                self.assertTrue(page.locator("#handoff-text").evaluate("el => el.selectionStart === 0 && el.selectionEnd === el.value.length"))
                page.keyboard.press("Escape")
                expect(page.locator("#handoff-dialog")).not_to_be_visible()
                page.locator("#search").fill("")
                page.locator("#domain").select_option("Omni-Brain")
                page.locator("#kind").select_option("local")
                expect(page.locator(".item-button")).to_have_count(1)
                expect(page.locator("#detail-title")).to_have_text("正式质检知识")
                expect(page.locator("#body")).to_contain_text("验收前先核对实际结果与判定口径")
                page.locator('#body a[href="#reader-具体案例"]').click()
                expect(page.locator("#detail-title")).to_have_text("正式质检知识")
                self.assertNotIn("type: Knowledge", page.locator("#body > h2").all_text_contents())
                page.set_viewport_size({"width":320,"height":740})
                page.locator(".item-button").click()
                expect(page.locator("#back-to-list")).to_be_visible()
                self.assertFalse(page.evaluate("document.documentElement.scrollWidth > innerWidth"))
                page.locator("#back-to-list").click()
                expect(page.locator(".directory")).to_be_visible()
                page.locator("#search").fill("")
                page.locator("body").click(position={"x":5,"y":5})
                page.keyboard.press("/")
                expect(page.locator("#search")).to_be_focused()
                self.assertEqual(errors, [])
                self.assertFalse(any(url.startswith("https://") for url in requests))
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
