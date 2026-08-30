from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/knowledge_check.py"


class KnowledgeCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.knowledge = self.root / "knowledge"
        self.config = self.root / "config"
        self.knowledge.mkdir()
        self.config.mkdir()
        (self.knowledge / "index.md").write_text("# Knowledge\n", encoding="utf-8")
        (self.knowledge / "log.md").write_text("# Log\n", encoding="utf-8")
        self.write_domain_map([])

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_domain_map(self, domains: list[dict[str, object]]) -> None:
        (self.config / "knowledge-domains.yaml").write_text(
            yaml.safe_dump(
                {"schema_version": "0.1", "domains": domains},
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def write_concept(self, relative: str, title: str, body: str = "") -> Path:
        path = self.knowledge / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            "type: Test Concept\n"
            f"title: {title}\n"
            f"description: {title} description\n"
            "tags: []\n"
            "---\n\n"
            f"# {title}\n\n{body}\n",
            encoding="utf-8",
        )
        return path

    def run_check(self) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        before = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--knowledge-root",
                str(self.knowledge),
                "--domain-map",
                str(self.config / "knowledge-domains.yaml"),
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        after = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after, "knowledge_check.py must remain read-only")
        return result, json.loads(result.stdout)

    def make_valid_slice(self) -> None:
        domains = [
            {
                "id": "quality",
                "title": "质检",
                "parent": None,
                "scope": "质量评价",
                "excludes": "生产执行",
            }
        ]
        self.write_domain_map(domains)
        self.write_concept("domains/quality/overview.md", "质检")
        self.write_concept(
            "sources/source-a.md",
            "来源 A",
            "## 定位\n\n- source/file.md\n",
        )
        self.write_concept(
            "domains/quality/policy.md",
            "质检规则",
            "## 规则\n\n- **依据**：[来源 A](../../sources/source-a.md)\n\n"
            "# Citations\n\n1. [来源 A](../../sources/source-a.md)\n",
        )
        self.write_concept(
            "views/by-domain/quality.md",
            "质检领域视图",
            "- [质检](../../domains/quality/overview.md)\n"
            "- [质检规则](../../domains/quality/policy.md)\n",
        )
        self.write_concept(
            "views/by-journey/quality-check.md",
            "质检旅程",
            "- [质检规则](../../domains/quality/policy.md)\n",
        )
        (self.knowledge / "index.md").write_text(
            "# Knowledge\n\n"
            "- [质检领域视图](views/by-domain/quality.md)\n"
            "- [质检旅程](views/by-journey/quality-check.md)\n",
            encoding="utf-8",
        )

    def test_empty_scaffold_passes(self) -> None:
        result, report = self.run_check()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("passed", report["status"])

    def test_valid_slice_passes_and_reports_backlinks(self) -> None:
        self.make_valid_slice()
        result, report = self.run_check()
        self.assertEqual(0, result.returncode, report)
        backlinks = report["backlinks"]
        self.assertIn("domains/quality/policy.md", backlinks)
        self.assertEqual(
            ["views/by-domain/quality.md", "views/by-journey/quality-check.md"],
            backlinks["domains/quality/policy.md"],
        )

    def test_reader_facing_process_terms_warn_but_do_not_fail(self) -> None:
        self.make_valid_slice()
        page = self.knowledge / "domains/quality/policy.md"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                "## 规则", "## 规则\n\n当前候选补充了 Batch 2，但 K0 仍沿用父版本。"
            ),
            encoding="utf-8",
        )
        result, report = self.run_check()
        self.assertEqual(0, result.returncode, report)
        warnings = "\n".join(report["warnings"])
        self.assertIn("reader-facing page may expose ingestion process term", warnings)
        self.assertIn("Batch 2", warnings)
        self.assertIn("K0", warnings)
        self.assertIn("父版本", warnings)

    def test_obsidian_link_and_broken_link_fail(self) -> None:
        (self.knowledge / "index.md").write_text(
            "# Knowledge\n\n[[Hidden]]\n\n[Missing](missing.md)\n",
            encoding="utf-8",
        )
        result, report = self.run_check()
        self.assertEqual(1, result.returncode)
        joined = "\n".join(report["errors"])
        self.assertIn("Obsidian wiki link", joined)
        self.assertIn("broken internal link", joined)

    def test_domain_cycle_fails(self) -> None:
        self.write_domain_map(
            [
                {
                    "id": "a.b",
                    "title": "A",
                    "parent": "a.b.c",
                    "scope": "A",
                    "excludes": "none",
                },
                {
                    "id": "a.b.c",
                    "title": "B",
                    "parent": "a.b",
                    "scope": "B",
                    "excludes": "none",
                },
            ]
        )
        result, report = self.run_check()
        self.assertEqual(1, result.returncode)
        self.assertIn("domain cycle", "\n".join(report["errors"]))

    def test_published_knowledge_requires_both_product_views(self) -> None:
        self.write_domain_map(
            [
                {
                    "id": "quality",
                    "title": "质检",
                    "parent": None,
                    "scope": "质量评价",
                    "excludes": "生产执行",
                }
            ]
        )
        self.write_concept("domains/quality/overview.md", "质检")
        result, report = self.run_check()
        self.assertEqual(1, result.returncode)
        joined = "\n".join(report["errors"])
        self.assertIn("by-domain", joined)
        self.assertIn("by-journey", joined)

    def test_unapproved_relation_extensions_fail(self) -> None:
        path = self.knowledge / "concept.md"
        path.write_text(
            "---\ntype: Concept\ntitle: C\ndescription: C\n"
            "omni:\n  stable_id: c\n  relations: []\n---\n\n# C\n",
            encoding="utf-8",
        )
        result, report = self.run_check()
        self.assertEqual(1, result.returncode)
        self.assertIn("unapproved M1 extension", "\n".join(report["errors"]))

    def test_duplicate_or_wrong_level_citations_fail(self) -> None:
        self.make_valid_slice()
        page = self.knowledge / "domains/quality/policy.md"
        page.write_text(
            page.read_text(encoding="utf-8") + "\n## Citations\n\nDuplicate.\n",
            encoding="utf-8",
        )
        result, report = self.run_check()
        self.assertEqual(1, result.returncode)
        self.assertIn(
            "exactly one level-1 '# Citations' section",
            "\n".join(report["errors"]),
        )

    def test_duplicate_frontmatter_keys_fail(self) -> None:
        self.make_valid_slice()
        page = self.knowledge / "domains/quality/policy.md"
        text = page.read_text(encoding="utf-8")
        page.write_text(
            text.replace(
                "type: Test Concept\n",
                "type: Test Concept\ntype: Duplicate Concept\n",
                1,
            ),
            encoding="utf-8",
        )
        result, report = self.run_check()
        self.assertEqual(1, result.returncode)
        self.assertIn("duplicate key", "\n".join(report["errors"]))

    def test_duplicate_product_view_body_fails(self) -> None:
        self.make_valid_slice()
        original = self.knowledge / "views/by-domain/quality.md"
        duplicate = self.knowledge / "views/by-domain/index.md"
        text = original.read_text(encoding="utf-8")
        duplicate.write_text(
            re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL),
            encoding="utf-8",
        )
        result, report = self.run_check()
        self.assertEqual(1, result.returncode)
        self.assertIn("duplicate product view body", "\n".join(report["errors"]))

    def test_malformed_markdown_table_fails(self) -> None:
        self.make_valid_slice()
        page = self.knowledge / "domains/quality/policy.md"
        page.write_text(
            page.read_text(encoding="utf-8") + "\n| A | B |\n| one | two |\n",
            encoding="utf-8",
        )
        result, report = self.run_check()
        self.assertEqual(1, result.returncode)
        self.assertIn("Markdown table lacks a header separator", "\n".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
