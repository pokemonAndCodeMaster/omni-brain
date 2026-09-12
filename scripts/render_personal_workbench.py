#!/usr/bin/env python3
"""Build a portable, read-only HTML view from full Linear snapshots and explicit local sources.

No API calls, credentials, background synchronization, or task database. Re-run after
the authenticated agent refreshes snapshots. Markdown HTML and active URLs are disabled.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, unquote

from markdown_it import MarkdownIt


def timestamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def safe_url(value: object) -> str:
    """URLs from material are navigation only; no data/file/javascript protocols."""
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        return ""
    try:
        url = urlsplit(value.strip())
    except ValueError:
        return ""
    if url.scheme in ("https", "http") and url.hostname and not url.username and not url.password:
        return value.strip()
    if url.scheme == "mailto" and url.path:
        return value.strip()
    return ""


def text_field(item: dict, name: str, default: str = "") -> str:
    value = item.get(name)
    return value if isinstance(value, str) else default


def canonical_url(value: str) -> str:
    url = urlsplit(value)
    parts = url.path.strip("/").split("/")
    if url.hostname == "linear.app" and len(parts) >= 3:
        if parts[1] == "issue":
            return "https://linear.app/" + "/".join(parts[:3])
        if parts[1] == "document":
            match = re.search(r"([a-f0-9]{12})$", parts[2])
            if match:
                return "https://linear.app/" + parts[0] + "/document/" + match.group(1)
    return value.rstrip("/")


def state_name(item: dict) -> str:
    value = item.get("status") or item.get("state") or "未提供状态"
    return value.get("name", "未提供状态") if isinstance(value, dict) else str(value)


def state_group(name: str, state_type: str = "") -> str:
    value = name.lower().replace(" ", "").replace("_", "")
    if value in ("inreview", "review", "待审阅", "待审核", "待看成果"):
        return "review"
    if value in ("done", "completed", "canceled", "cancelled", "duplicate", "已完成", "已取消"):
        return "closed"
    if state_type in ("completed", "canceled"):
        return "closed"
    if value in ("todo", "待办", "待处理") or state_type == "unstarted":
        return "now"
    if value in ("backlog", "triage", "未安排"):
        return "ideas"
    if state_type in ("backlog", "triage"):
        return "ideas"
    return "now"  # Unknown live states remain visible, with their actual label.


def contained_path(root: Path, relative: str) -> Path:
    candidate = root / relative
    if Path(relative).is_absolute() or not candidate.resolve().is_relative_to(root):
        raise ValueError("本地入口必须在仓库内：" + relative)
    if "raw" in Path(relative).parts:
        raise ValueError("原始资料不能直接收入阅读页：" + relative)
    if not candidate.exists():
        raise ValueError("本地入口不存在：" + relative)
    return candidate.resolve()


def read_object(path: Path) -> dict:
    item = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(item, dict) and isinstance(item.get("content"), list):
        blocks = [b.get("text") for b in item["content"] if b.get("type") == "text"]
        if item.get("isError") or len(blocks) != 1:
            raise ValueError("不是完整的 MCP 读取结果：" + str(path))
        item = json.loads(blocks[0])
    if not isinstance(item, dict):
        raise ValueError("快照应为 JSON 对象：" + str(path))
    return item


def infer_domain(item: dict) -> str:
    title = text_field(item, "title")
    project = item.get("project")
    name = project.get("name", "") if isinstance(project, dict) else str(project or "")
    if any(term in title + name for term in ("金铲铲", "迅捷", "地狱火", "黑暗仪式", "阵容")):
        return "金铲铲"
    if any(term in title + name for term in ("Omni-Brain", "共作", "质检", "Harness")):
        return "Omni-Brain"
    if any(term in title + name for term in ("工作台", "Codex", "想法", "AI 辅助")):
        return "个人工作台"
    return "其他"


def load_items(root: Path, snapshots: Path, local_index: Path | None = None) -> list[dict]:
    result = []
    for folder, kind, body_field in (("issues", "issue", "description"), ("documents", "document", "content")):
        for path in sorted((snapshots / folder).glob("*.json")):
            raw = read_object(path)
            if not isinstance(raw.get(body_field), str):
                raise ValueError("缺少全文，不能把列表摘要当作完整快照：" + str(path))
            if not raw.get("id") or not raw.get("title"):
                raise ValueError("快照缺少 id 或 title：" + str(path))
            if raw.get("archivedAt"):
                continue
            parent = next((raw.get(key) for key in ("issue", "project", "initiative", "team") if raw.get(key)), None)
            parent_label = (parent.get("identifier") or parent.get("name") or parent.get("title") or parent.get("id", "")) if isinstance(parent, dict) else str(parent or "")
            status = state_name(raw) if kind == "issue" else "Linear 文档"
            result.append({"id": kind + ":" + str(raw["id"]), "nativeId": str(raw["id"]),
                "identifier": text_field(raw, "identifier") or (str(raw["id"]) if kind == "issue" and re.fullmatch(r"[A-Z][A-Z0-9]*-\d+", str(raw["id"])) else ""), "kind": kind, "title": str(raw["title"]),
                "body": raw[body_field], "url": safe_url(raw.get("url")), "status": status,
                "group": state_group(status, text_field(raw, "statusType")) if kind == "issue" else "knowledge",
                "updatedAt": text_field(raw, "updatedAt"), "capturedAt": timestamp(path),
                "source": "Linear", "path": "", "domain": infer_domain(raw),
                "parent": parent_label, "parentId": parent.get("id", "") if isinstance(parent, dict) else "",
                "uuid": text_field(raw, "uuid", str(raw["id"])),
                "documentIds": [str(doc["id"]) for doc in raw.get("documents", []) if isinstance(doc, dict) and doc.get("id")],
                "relatedIssues": [], "authority": "线上当前工作记录的本地快照"})
    if local_index:
        index = read_object(local_index)
        if not isinstance(index.get("items"), list):
            raise ValueError("本地目录应包含 items 数组")
        known_urls = {canonical_url(item["url"]): item for item in result if item["url"]}
        for raw in index["items"]:
            if not isinstance(raw, dict) or not raw.get("id") or not raw.get("title"):
                raise ValueError("本地目录条目需要 id 和 title")
            relative = text_field(raw, "path")
            url = safe_url(raw.get("url"))
            if not relative and canonical_url(url) in known_urls:
                existing = known_urls[canonical_url(url)]
                existing["domain"] = text_field(raw, "domain") or existing["domain"]
                existing["authority"] = text_field(raw, "authority") or existing["authority"]
                continue
            source = contained_path(root, relative) if relative else None
            body = source.read_text(encoding="utf-8") if source and source.is_file() and source.suffix.lower() == ".md" else text_field(raw, "summary")
            if not body.strip():
                raise ValueError("本地目录条目没有正文或说明：" + str(raw["id"]))
            result.append({"id": "local:" + str(raw["id"]), "nativeId": str(raw["id"]),
                "identifier": "", "kind": text_field(raw, "kind", "knowledge"), "title": str(raw["title"]),
                "body": body, "url": url, "localUrl": source.as_uri() if source else "", "status": text_field(raw, "status", "本地材料"),
                "group": "knowledge", "updatedAt": text_field(raw, "updatedAt"),
                "capturedAt": "", "inspectedAt": text_field(raw, "inspectedAt"), "source": "本地仓库" if relative else "线上入口", "path": relative,
                "domain": text_field(raw, "domain", "Omni-Brain"), "parent": "",
                "relatedIssues": raw.get("relatedIssues", []), "authority": text_field(raw, "authority", "请以正文说明的适用范围为准")})
    by_native_id = {item.get("uuid"): item for item in result if item["kind"] == "issue"}
    for item in result:
        parent_issue = by_native_id.get(item.get("parentId"))
        if parent_issue:
            item["parent"] = parent_issue["identifier"] or parent_issue["title"]
    ids = [item["id"] for item in result]
    if len(ids) != len(set(ids)):
        raise ValueError("存在重复的条目标识")
    return sorted(result, key=lambda item: item["updatedAt"], reverse=True)


def heading_slug(value: str) -> str:
    return re.sub(r"[^\w\-\u3400-\u9fff]", "", re.sub(r"\s+", "-", unquote(value).strip().lower()))


class LinearIssueMention(HTMLParser):
    """Recognize one native issue reference; never render supplied HTML."""
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.events = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.events.append(("open", tag, attrs))

    def handle_data(self, data):
        self.events.append(("text", data))

    def handle_endtag(self, tag):
        self.events.append(("close", tag))

    def handle_comment(self, data):
        self.events.append(("other", data))

    def handle_pi(self, data):
        self.events.append(("other", data))

    def handle_decl(self, data):
        self.events.append(("other", data))

    def unknown_decl(self, data):
        self.events.append(("other", data))


def native_issue_rule(state, silent):
    # An inline rule preserves code spans/fences and escaped examples unchanged.
    if state.linkLevel or not state.src.startswith("<issue ", state.pos):
        return False
    end = state.src.find("</issue>", state.pos)
    if end < 0 or end - state.pos > 4096:
        return False
    events = LinearIssueMention(state.src[state.pos:end + 8]).events
    if (len(events) != 3 or events[0][:2] != ("open", "issue")
            or events[1][0] != "text" or events[2] != ("close", "issue")):
        return False
    attrs, label = dict(events[0][2]), events[1][1]
    target = urlsplit(safe_url(attrs.get("href")))
    parts = unquote(target.path).strip("/").split("/")
    if (len(attrs) != len(events[0][2]) or set(attrs) - {"id", "href"}
            or not re.fullmatch(r"[A-Z][A-Z0-9]*-\d+", label)
            or target.scheme != "https" or target.netloc != "linear.app"
            or len(parts) < 3 or parts[1:3] != ["issue", label]
            or any(part in (".", "..") for part in parts)
            or "\\" in unquote(attrs.get("href", ""))
            or target.query or target.fragment):
        return False
    if not silent:
        token = state.push("link_open", "a", 1)
        token.attrSet("href", attrs["href"])
        state.push("text", "", 0).content = label
        state.push("link_close", "a", -1)
    state.pos = end + 8
    return True


def render_markdown(body: str, local_path: str, by_path: dict) -> str:
    parser = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
    parser.inline.ruler.before("text", "linear_issue", native_issue_rule)
    metadata = ""
    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)", body, re.DOTALL)
    if frontmatter:
        metadata = frontmatter.group(1)
        body = body[frontmatter.end():]
    tokens = parser.parse(body)
    seen_headings = set()
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and index + 1 < len(tokens):
            base = "reader-" + (heading_slug(tokens[index + 1].content) or "section")
            ident, number = base, 1
            while ident in seen_headings:
                number += 1
                ident = base + "-" + str(number)
            token.attrSet("id", ident)
            seen_headings.add(ident)

    def walk(items):
        for token in items:
            if token.type == "link_open":
                href = token.attrGet("href") or ""
                safe = safe_url(href)
                if href.startswith("#") and ("reader-" + heading_slug(href[1:])) in seen_headings:
                    safe = "#reader-" + heading_slug(href[1:])
                if not safe and local_path and not urlsplit(href).scheme and not href.startswith(("//", "#")):
                    # Resolve only to explicitly indexed local documents, never arbitrary files.
                    target = (Path(local_path).parent / unquote(urlsplit(href).path)).as_posix()
                    target = str(Path(target))
                    parts = []
                    for part in target.split("/"):
                        if part == ".." and parts:
                            parts.pop()
                        elif part not in (".", ""):
                            parts.append(part)
                    linked = by_path.get("/".join(parts))
                    if linked:
                        from urllib.parse import urlencode
                        safe = "#" + urlencode({"view": "knowledge", "item": linked})
                if safe:
                    token.attrSet("href", safe)
                else:
                    token.attrs.pop("href", None)
                if safe.startswith(("http:", "https:", "mailto:")):
                    token.attrSet("target", "_blank")
                    token.attrSet("rel", "noopener noreferrer")
                if not safe:
                    token.attrSet("title", "此链接没有可安全打开的阅读入口；请查看原文")
            if token.children:
                walk(token.children)
    walk(tokens)

    def image_note(items, index, options, env):
        token = items[index]
        label = "图片：" + (token.content or "查看原文")
        url = safe_url(token.attrGet("src"))
        if url:
            return '<a class="image-note" target="_blank" rel="noopener noreferrer" href="' + html.escape(url, quote=True) + '">' + html.escape(label) + " ↗</a>"
        return '<span class="image-note">' + html.escape(label) + "</span>"
    parser.renderer.rules["image"] = image_note
    rendered = parser.renderer.render(tokens, parser.options, {})
    if metadata:
        rendered += '<details class="document-metadata"><summary>文档元信息</summary><pre>' + html.escape(metadata) + "</pre></details>"
    return rendered


def build(root: Path, snapshots: Path, output: Path, local_index: Path | None = None) -> dict:
    root = root.resolve()
    items = load_items(root, snapshots, local_index)
    by_path = {item["path"]: item["id"] for item in items if item["path"]}
    for item in items:
        item["html"] = render_markdown(item["body"], item["path"], by_path)
    assets = root / "docs/linear-workbench/assets"
    template = (assets / "reader.html").read_text(encoding="utf-8")
    css = (assets / "reader.css").read_text(encoding="utf-8")
    js = (assets / "reader.js").read_text(encoding="utf-8")
    data = json.dumps({"generatedAt": datetime.now(timezone.utc).isoformat(), "items": items}, ensure_ascii=False)
    # A document's literal </script> must never terminate the JSON data element.
    data = data.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    sha = lambda value: base64.b64encode(hashlib.sha256(value.encode()).digest()).decode()
    csp = "default-src 'none'; script-src 'sha256-" + sha(js) + "'; style-src 'sha256-" + sha(css) + "'; img-src 'none'; connect-src 'none'; base-uri 'none'; form-action 'none'"
    page = template.replace("{{CSP}}", html.escape(csp, quote=True)).replace("{{CSS}}", css).replace("{{DATA}}", data).replace("{{JS}}", js)
    output = output.absolute()
    if not output.resolve().is_relative_to(root):
        raise ValueError("输出文件必须在指定仓库内")
    current = root
    for part in output.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("输出路径不能经过符号链接")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    return {"output": str(output), "issues": sum(item["kind"] == "issue" for item in items),
            "documents": sum(item["kind"] == "document" for item in items), "localEntries": sum(item["id"].startswith("local:") for item in items)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--snapshots", type=Path, help="Default: ROOT/.derived/linear")
    parser.add_argument("--local-index", type=Path)
    parser.add_argument("--output", type=Path, help="Default: ROOT/.derived/personal-workbench/index.html")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        result = build(root, args.snapshots or root / ".derived/linear", args.output or root / ".derived/personal-workbench/index.html", args.local_index)
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
