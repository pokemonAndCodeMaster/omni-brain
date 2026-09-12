#!/usr/bin/env python3
"""Prepare and verify Agent-mediated Linear publication; never stores credentials.

MCP calls remain with the authenticated agent. Inputs are fresh get_document/get_issue
results, either plain JSON or an MCP content envelope. Runtime copies are not knowledge.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from html.parser import HTMLParser
from datetime import datetime, timezone

from markdown_it import MarkdownIt


class WorkbenchError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class HtmlLinks(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.starts, self.ends, self.targets = [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.starts.append((tag, values))
        self.targets.extend(value for key, value in attrs if key in ("href", "src") and value)

    def handle_endtag(self, tag):
        self.ends.append(tag)


def markdown_parser():
    parser = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
    # Parse even disallowed protocols so validation can reject rather than hide them.
    parser.validateLink = lambda value: True
    return parser


def normalized(text, workspace=None):
    """Canonical rendering for readback only; remote conflict hashes stay byte-exact."""
    parser = markdown_parser()
    env = {}
    tokens = parser.parse(text, env)
    for token in tokens:
        if token.children is None:
            continue
        children, index = [], 0
        while index < len(token.children):
            group = token.children[index:index + 3]
            if (workspace and len(group) == 3 and group[0].type == "html_inline"
                    and group[1].type == "text" and group[2].type == "html_inline"
                    and group[2].content == "</issue>"):
                html = HtmlLinks(group[0].content)
                if len(html.starts) == 1 and html.starts[0][0] == "issue" and not html.ends:
                    attrs = html.starts[0][1]
                    target = urlsplit(attrs.get("href") or "")
                    label = group[1].content
                    prefix = "/" + workspace + "/issue/" + label
                    if (set(attrs) <= {"id", "href"} and target.scheme == "https"
                            and target.netloc == "linear.app"
                            and re.fullmatch(r"[A-Z][A-Z0-9]*-\d+", label)
                            and (target.path == prefix or target.path.startswith(prefix + "/"))
                            and not target.query and not target.fragment):
                        children.append(group[1])
                        index += 3
                        continue
            children.append(token.children[index])
            index += 1
        token.children = children
    return parser.renderer.render(tokens, parser.options, env)


def markdown_links(text):
    parser, env = markdown_parser(), {}
    tokens = parser.parse(text, env)
    targets = [entry["href"] for entry in env.get("references", {}).values()]
    def visit(items):
        for token in items:
            if token.type == "link_open":
                targets.append(token.attrGet("href"))
            elif token.type == "image":
                targets.append(token.attrGet("src"))
            elif token.type in ("html_inline", "html_block"):
                targets.extend(HtmlLinks(token.content).targets)
            if token.children:
                visit(token.children)
    visit(tokens)
    return targets

def read_json(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("content"), list):
        if data.get("isError"):
            raise WorkbenchError("MCP returned an error; no snapshot accepted")
        blocks = [x["text"] for x in data["content"] if x.get("type") == "text"]
        if len(blocks) != 1:
            raise WorkbenchError("Expected one JSON text result from MCP")
        data = json.loads(blocks[0])
    return data


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_text(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
        file.write(value)
        tmp = Path(file.name)
    try:
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def safe_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise WorkbenchError("Invalid object identifier")
    return value


def validate_document(doc):
    if not isinstance(doc, dict) or not isinstance(doc.get("content"), str):
        raise WorkbenchError("Full get_document content is required; list metadata is insufficient")
    for field in ("id", "title", "url", "updatedAt"):
        if not isinstance(doc.get(field), str) or not doc[field]:
            raise WorkbenchError("Document is missing " + field)
    safe_name(doc["id"])
    if urlsplit(doc["url"]).hostname != "linear.app":
        raise WorkbenchError("Expected a Linear document URL")
    if doc.get("archivedAt"):
        raise WorkbenchError("Document is archived; review it before publishing")
    return doc


def fingerprint(doc):
    validate_document(doc)
    # Content, title and parent identity are owned together, not the update timestamp.
    obj = {"title": doc["title"], "content": doc["content"]}
    for field in ("team", "project", "issue", "initiative", "cycle"):
        obj[field] = (doc.get(field) or {}).get("id")
    return digest(json.dumps(obj, ensure_ascii=False, sort_keys=True))


class Workbench:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.config_path = self.root / "config/linear-workbench.json"
        self.safe_output(self.config_path)
        self.config = read_json(self.config_path)
        self.runtime = self.root / ".derived/linear"
        keys, ids, paths = set(), set(), set()
        for doc in self.config["publications"]:
            key = safe_name(doc["key"])
            source = self.source(doc)
            if key in keys or source in paths or (doc.get("id") and doc["id"] in ids):
                raise WorkbenchError("Duplicate publication key, source or remote ID")
            keys.add(key)
            paths.add(source)
            if doc.get("id"):
                ids.add(doc["id"])

    def safe_output(self, path):
        if not path.is_relative_to(self.root):
            raise WorkbenchError("Output escapes repository")
        current = self.root
        for part in path.relative_to(self.root).parts:
            current = current / part
            if current.is_symlink():
                raise WorkbenchError("Refusing symlink in output path: " + str(current))
        return path

    def source(self, entry):
        rel = Path(entry["source"])
        path = (self.root / rel).resolve()
        if (rel.is_absolute() or not path.is_relative_to(self.root)
                or rel.parts[0] not in ("docs", "knowledge")
                or path.relative_to(self.root).parts[0] not in ("docs", "knowledge")
                or "raw" in rel.parts or "raw" in path.relative_to(self.root).parts
                or path.suffix != ".md"):
            raise WorkbenchError("Publication source must be an explicit docs/ or knowledge/ Markdown file outside raw/")
        return path

    def entry(self, key):
        for entry in self.config["publications"]:
            if entry["key"] == key:
                return entry
        raise WorkbenchError("Publication is not registered: " + key)

    def body(self, entry):
        text = self.source(entry).read_text(encoding="utf-8")
        if not text.strip():
            raise WorkbenchError("Refusing to publish empty content")
        if re.search(r"(?m)^---\s*\n", text[:5]):
            raise WorkbenchError("Prepare an explicit reader-facing document without YAML front matter")
        # Do not silently publish local links inaccessible to ChatGPT or other readers.
        for target in markdown_links(text):
            target = target.strip().strip("<>")
            if not target.startswith(("https://", "http://", "#", "mailto:")):
                raise WorkbenchError("Resolve local Markdown link before publishing: " + target)
        return text.strip() + "\n\n---\n\n来源：`" + entry["source"] + "`。本页是 Git 文档的阅读副本；线上修订需先带回合并，再发布。\n"

    def capture(self, data):
        if "description" in data and "content" not in data:
            ident = safe_name(data["id"])
            if not isinstance(data.get("description"), str):
                raise WorkbenchError("Full issue description is required")
            if not isinstance(data.get("url"), str) or urlsplit(data["url"]).hostname != "linear.app":
                raise WorkbenchError("Issue URL is missing or invalid")
            folder = self.runtime / "issues"
            body = data["description"]
        else:
            validate_document(data)
            ident = safe_name(data["id"])
            folder = self.runtime / "documents"
            body = data["content"]
        # Check both destinations before writing either file.
        json_path = self.safe_output(folder / (ident + ".json"))
        path = self.safe_output(folder / (ident + ".md"))
        self.safe_output(self.runtime / "index.md")
        write_json(json_path, data)
        write_text(path, "# " + data["title"] + "\n\n来源：[Linear](" + data["url"]
                        + ")\n\n读取到的版本：" + str(data.get("updatedAt", "未提供"))
                        + "\n\n本文件是本地阅读快照，不是已认证知识；继续工作前重新读取线上版本。\n\n"
                        + body + "\n")
        self.refresh_index()
        return {"snapshot": str(path), "id": ident}

    def directory(self, key, inventory):
        """Refresh only the declared directory section from a complete inventory."""
        if (not isinstance(inventory, dict) or inventory.get("hasNextPage") is not False
                or not isinstance(inventory.get("documents"), list)):
            raise WorkbenchError("A complete document inventory with hasNextPage=false is required")
        docs = inventory["documents"]
        seen = set()
        for doc in docs:
            if not all(isinstance(doc.get(k), str) and doc[k] for k in ("id", "title", "url")):
                raise WorkbenchError("Every directory entry needs an ID, title and URL")
            if doc["id"] in seen or doc.get("archivedAt"):
                raise WorkbenchError("Duplicate or archived document in active directory")
            parsed = urlsplit(doc["url"])
            if parsed.hostname != "linear.app" or not parsed.path.startswith("/" + self.config["workspace"] + "/document/"):
                raise WorkbenchError("Directory document is outside this workspace")
            seen.add(doc["id"])
        source = self.source(self.entry(key))
        self.safe_output(self.root / self.entry(key)["source"])
        before = source.read_text(encoding="utf-8")
        start, end = "## 全部 Linear 文档\n", "## 目录怎样更新\n"
        if before.count(start) != 1 or before.count(end) != 1 or before.index(start) > before.index(end):
            raise WorkbenchError("Directory source must have unique ordered directory headings")
        def cell(value):
            return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]").replace("\n", " ")
        lines = [start.rstrip(), "", f"最近完整核对：{datetime.now(timezone.utc).date().isoformat()}，共 {len(docs)} 篇当前可访问文档。团队、项目和事项下的文档统一列在这里；关联位置不同不会漏掉。", "",
                 "| 文档 | 所属位置 | 正文更新时间 |", "| --- | --- | --- |"]
        for doc in sorted(docs, key=lambda d: (d["title"], d["id"])):
            owner = next(((kind, doc[kind]) for kind in ("issue", "project", "initiative", "team") if doc.get(kind)), None)
            place = "独立资料"
            if owner:
                kind, value = owner
                place = value.get("id", "事项") if kind == "issue" else value.get("name", kind)
            url = doc["url"].replace("(", "%28").replace(")", "%29").replace("|", "%7C")
            lines.append(f"| [{cell(doc['title'])}]({url}) | {cell(place)} | {cell(str(doc.get('updatedAt', '未提供'))[:10])} |")
        after = before[:before.index(start)] + "\n".join(lines) + "\n\n" + before[before.index(end):]
        if source.read_text(encoding="utf-8") != before:
            raise WorkbenchError("Directory source changed during generation")
        write_text(source, after)
        return {"source": str(source), "documents": len(docs), "published": False}

    def refresh_index(self):
        lines = ["# Linear 本地阅读入口", "", "这些是具体时刻的全文快照；继续工作前重新读取线上版本。未自动收入正式知识。", ""]
        for kind, title in (("issues", "事项"), ("documents", "文档")):
            lines.extend(["## " + title, ""])
            self.safe_output(self.runtime / kind)
            for path in sorted((self.runtime / kind).glob("*.json")):
                self.safe_output(path)
                item = read_json(path)
                label = item["title"].replace("[", "\\[").replace("]", "\\]")
                lines.append("- [" + label + "](" + kind + "/" + path.stem + ".md) · [线上原文](" + item["url"] + ")")
            lines.append("")
        write_text(self.safe_output(self.runtime / "index.md"), "\n".join(lines))

    def conflict(self, entry, remote):
        fp = fingerprint(remote)
        folder = self.runtime / "candidates" / entry["key"] / fp
        for name in ("remote.json", "remote.md", "changes.diff"):
            self.safe_output(folder / name)
        write_json(folder / "remote.json", remote)
        write_text(folder / "remote.md", remote["content"])
        diff = "".join(difflib.unified_diff(
            remote["content"].splitlines(True), self.body(entry).splitlines(True),
            fromfile="Linear (current)", tofile=entry["source"]))
        write_text(folder / "changes.diff", diff)
        raise WorkbenchError("Remote changed; review and merge before publishing. Candidate: "
                             + str(folder) + "; reviewed-remote fingerprint: " + fp)

    def plan(self, key, remote=None, inventory=None, reviewed_remote=None):
        entry = self.entry(key)
        body = self.body(entry)
        result = {"key": key, "source_sha256": digest(self.source(entry).read_text(encoding="utf-8")),
                  "expected_content": body, "expected_title": entry["title"]}
        if entry.get("id"):
            if remote is None:
                raise WorkbenchError("Fetch get_document immediately before planning and pass --remote")
            validate_document(remote)
            if remote["id"] != entry["id"]:
                raise WorkbenchError("Remote ID does not match registry")
            current = fingerprint(remote)
            if reviewed_remote is not None and reviewed_remote != current:
                raise WorkbenchError("Reviewed remote fingerprint is stale")
            if current != entry.get("remote_sha256") and reviewed_remote != current:
                self.conflict(entry, remote)
            if remote["title"] != entry["title"]:
                raise WorkbenchError("Remote title changed; reconcile registry title before publication")
            result["remote_sha256"] = current
            result["parents"] = {field: (remote.get(field) or {}).get("id")
                                 for field in ("team", "project", "issue", "initiative", "cycle")}
            if normalized(remote["content"], self.config.get("workspace")) == normalized(body, self.config.get("workspace")):
                result["action"] = "noop"
            else:
                if not remote["content"]:
                    raise WorkbenchError("Remote body is empty; recover or explicitly adopt it first")
                result.update(action="update", tool="save_document", arguments={
                    "id": entry["id"], "patch": [{"op": "replace", "old_string": remote["content"],
                                                "new_string": body}]})
        else:
            if inventory is None or not isinstance(inventory.get("documents"), list) or inventory.get("hasNextPage") is not False:
                raise WorkbenchError("First publish requires a complete current document inventory (--inventory)")
            matches = [d for d in inventory["documents"] if d["title"] == entry["title"]]
            if matches:
                raise WorkbenchError("A document with this title already exists; recover its ID and reconcile instead of creating a duplicate")
            result.update(action="create", tool="save_document", arguments={
                "title": entry["title"], "team": self.config["team_id"], "content": body})
        path = self.runtime / "plans" / (key + ".json")
        write_json(self.safe_output(path), result)
        return {"plan": str(path), **result}

    def receipt(self, plan, remote):
        entry = self.entry(plan["key"])
        validate_document(remote)
        if entry.get("id") and entry["id"] != remote["id"]:
            raise WorkbenchError("Receipt belongs to a different document")
        if any(e.get("id") == remote["id"] and e["key"] != entry["key"] for e in self.config["publications"]):
            raise WorkbenchError("Receipt ID is already registered to another source")
        if digest(self.source(entry).read_text(encoding="utf-8")) != plan["source_sha256"]:
            raise WorkbenchError("Local source changed after planning; re-plan before recording success")
        if self.body(entry) != plan["expected_content"]:
            raise WorkbenchError("Plan content no longer matches source")
        if (normalized(remote["content"], self.config.get("workspace")) != normalized(plan["expected_content"], self.config.get("workspace"))
                or remote["title"] != entry["title"]):
            raise WorkbenchError("Readback does not match publication; registry not updated")
        if plan["action"] == "create" and (remote.get("team") or {}).get("id") != self.config["team_id"]:
            raise WorkbenchError("Created document belongs to the wrong team")
        if plan.get("parents") is not None and plan["parents"] != {
                field: (remote.get(field) or {}).get("id")
                for field in ("team", "project", "issue", "initiative", "cycle")}:
            raise WorkbenchError("Document parent changed after planning; re-read and review")
        self.capture(remote)
        entry.update(id=remote["id"], url=remote["url"], source_sha256=plan["source_sha256"],
                     remote_sha256=fingerprint(remote))
        write_json(self.safe_output(self.config_path), self.config)
        return {"verified": True, "key": entry["key"], "url": entry["url"]}

    def status(self):
        rows = []
        for entry in self.config["publications"]:
            local = digest(self.source(entry).read_text(encoding="utf-8"))
            rows.append({"key": entry["key"], "source": entry["source"], "url": entry.get("url"),
                         "local_changed": local != entry.get("source_sha256"),
                         "remote": "Fetch live document before publication"})
        return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    capture = sub.add_parser("capture")
    capture.add_argument("--input", required=True)
    directory = sub.add_parser("directory")
    directory.add_argument("--key", default="knowledge-home")
    directory.add_argument("--inventory", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--key", required=True)
    plan.add_argument("--remote")
    plan.add_argument("--inventory")
    plan.add_argument("--reviewed-remote")
    receipt = sub.add_parser("receipt")
    receipt.add_argument("--plan", required=True)
    receipt.add_argument("--remote", required=True)
    args = parser.parse_args()
    try:
        wb = Workbench(args.root)
        if args.command == "status":
            result = wb.status()
        elif args.command == "capture":
            result = wb.capture(read_json(args.input))
        elif args.command == "directory":
            result = wb.directory(args.key, read_json(args.inventory))
        elif args.command == "plan":
            result = wb.plan(args.key, read_json(args.remote) if args.remote else None,
                             read_json(args.inventory) if args.inventory else None, args.reviewed_remote)
        else:
            result = wb.receipt(read_json(args.plan), read_json(args.remote))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (WorkbenchError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
