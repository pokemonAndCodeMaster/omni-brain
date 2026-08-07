#!/usr/bin/env python3
"""Route a natural-language question to governed Markdown knowledge entrypoints.

The router is deliberately read-only and stateless.  It ranks pages already
reachable from the knowledge root and navigation views; it does not answer the
question, index raw material, or create another source of truth.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path


LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,3}\s+(.+?)\s*$", re.MULTILINE)
ASCII_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_.:/-]*|\d+(?:\.\d+)*")
CHINESE_RE = re.compile(r"[\u3400-\u9fff]+")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FRONTMATTER_FIELD_RE = re.compile(r"^(title|description|tags):\s*(.*?)\s*$", re.MULTILINE)


@dataclass
class Candidate:
    path: Path
    anchors: list[str] = field(default_factory=list)
    title: str = ""
    descriptor: str = ""
    headings: list[str] = field(default_factory=list)
    body: str = ""

    @property
    def anchor_text(self) -> str:
        return " ".join(self.anchors + [self.title, self.descriptor])

    @property
    def document_text(self) -> str:
        return " ".join([self.title, self.descriptor, *self.headings, self.body])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank governed knowledge pages for one question without writing state."
    )
    parser.add_argument("--root", default="knowledge/index.md", help="Knowledge root Markdown file")
    parser.add_argument("--query", required=True, help="Original user question")
    parser.add_argument("--limit", type=int, default=3, choices=range(1, 6))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def tokens(text: str) -> set[str]:
    result = {word.lower() for word in ASCII_WORD_RE.findall(text)}
    for segment in CHINESE_RE.findall(text):
        if 2 <= len(segment) <= 8:
            result.add(segment)
        for size in (2, 3, 4):
            result.update(
                segment[index : index + size]
                for index in range(max(0, len(segment) - size + 1))
            )
    return {token for token in result if len(token) >= 2}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def page_metadata(path: Path) -> tuple[str, str, list[str], str]:
    text = read_text(path)
    title = ""
    descriptor_parts: list[str] = []
    frontmatter = FRONTMATTER_RE.match(text)
    if frontmatter:
        for key, value in FRONTMATTER_FIELD_RE.findall(frontmatter.group(1)):
            if key == "title" and not title:
                title = value.strip("'\"")
            else:
                descriptor_parts.append(value.strip("'\""))
    headings = [heading.strip() for heading in HEADING_RE.findall(text)]
    if not title and headings:
        title = headings[0]
    if not title:
        title = path.stem
    body = re.sub(r"[`*_>|#\[\]()]", " ", text)
    body = re.sub(r"\s+", " ", body).strip()
    return title, " ".join(descriptor_parts), headings[:24], body


def clean_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    target = target.split("#", 1)[0].strip()
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    return target


def within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def is_navigation(path: Path, knowledge_root: Path) -> bool:
    relative = path.relative_to(knowledge_root)
    return path.name == "index.md" or "views" in relative.parts


def collect_candidates(root: Path, max_navigation_depth: int = 2) -> dict[Path, Candidate]:
    knowledge_root = root.parent.resolve()
    queue: deque[tuple[Path, int]] = deque([(root.resolve(), 0)])
    visited: set[Path] = set()
    candidates: dict[Path, Candidate] = {}

    while queue:
        current, depth = queue.popleft()
        if current in visited or not current.is_file():
            continue
        visited.add(current)
        text = read_text(current)
        heading = ""
        for line in text.splitlines():
            heading_match = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
            if heading_match:
                heading = heading_match.group(1)
            for label, raw_target in LINK_RE.findall(line):
                target_text = clean_link_target(raw_target)
                if target_text is None:
                    continue
                target = (current.parent / target_text).resolve()
                if target.suffix.lower() != ".md" or not target.is_file():
                    continue
                if not within(target, knowledge_root) or target == root.resolve():
                    continue
                candidate = candidates.setdefault(target, Candidate(path=target))
                candidate.anchors.append(" ".join(part for part in (heading, label, line) if part))
                if depth < max_navigation_depth and is_navigation(target, knowledge_root):
                    queue.append((target, depth + 1))

    for candidate in candidates.values():
        (
            candidate.title,
            candidate.descriptor,
            candidate.headings,
            candidate.body,
        ) = page_metadata(candidate.path)
    return candidates


def rank_candidates(query: str, candidates: dict[Path, Candidate]) -> list[dict[str, object]]:
    query_tokens = tokens(query)
    if not query_tokens:
        return []
    navigation_intent = any(
        marker in query.lower()
        for marker in ("学习", "入门", "全貌", "浏览", "导航", "阅读路线", "从哪里开始")
    )
    provenance_intent = any(
        marker in query.lower()
        for marker in ("来源", "出处", "依据", "追溯", "哪份材料", "证据在哪里")
    )
    uncertainty_intent = any(
        marker in query.lower()
        for marker in ("能否确认", "是否已经", "生产上线", "当前是否", "未知", "冲突", "可靠吗")
    )

    document_tokens = {
        path: tokens(candidate.anchor_text + " " + candidate.document_text)
        for path, candidate in candidates.items()
    }
    frequencies: Counter[str] = Counter()
    for page_tokens in document_tokens.values():
        frequencies.update(page_tokens)
    count = max(1, len(document_tokens))

    ranked: list[dict[str, object]] = []
    for path, candidate in candidates.items():
        anchor_tokens = tokens(candidate.anchor_text)
        page_tokens = document_tokens[path]
        matched = query_tokens & page_tokens
        if not matched:
            continue
        score = 0.0
        for token in matched:
            idf = math.log((count + 1) / (frequencies[token] + 1)) + 1.0
            score += idf * (2.5 if token in anchor_tokens else 1.0)
            if len(token) >= 4:
                score += idf * 0.35
        if "views" in path.parts or path.name == "index.md":
            score *= 1.0 if navigation_intent else 0.2
        if "sources" in path.parts:
            score *= 1.0 if provenance_intent else 0.15
        uncertainty_text = " ".join(
            [path.stem, candidate.title, candidate.descriptor, *candidate.headings]
        ).lower()
        if uncertainty_intent and any(
            marker in uncertainty_text
            for marker in ("open-question", "unknown", "未知", "冲突", "证据边界")
        ):
            score *= 1.65
        ranked.append(
            {
                "path": str(path),
                "title": candidate.title,
                "score": round(score, 3),
                "matched_terms": sorted(matched, key=lambda item: (-len(item), item))[:10],
            }
        )
    return sorted(ranked, key=lambda item: (-float(item["score"]), str(item["path"])))


def build_result(root: Path, query: str, limit: int) -> dict[str, object]:
    candidates = collect_candidates(root)
    ranked = rank_candidates(query, candidates)[:limit]
    return {
        "root": str(root.resolve()),
        "query": query,
        "primary": ranked[0] if ranked else None,
        "fallbacks": ranked[1:] if len(ranked) > 1 else [],
        "candidate_count": len(candidates),
        "instruction": (
            "Read primary only. Open a fallback only when a named part of the question "
            "remains unanswered after reading primary."
        ),
    }


def render_text(result: dict[str, object]) -> str:
    primary = result["primary"]
    lines = [f"ROOT\t{result['root']}", f"QUERY\t{result['query']}"]
    if primary is None:
        lines.append("PRIMARY\tNONE")
    else:
        lines.append(
            "PRIMARY\t{path}\t{title}\tmatched={matched}".format(
                path=primary["path"],
                title=primary["title"],
                matched=",".join(primary["matched_terms"]),
            )
        )
    for fallback in result["fallbacks"]:
        lines.append(
            "FALLBACK\t{path}\t{title}\tmatched={matched}".format(
                path=fallback["path"],
                title=fallback["title"],
                matched=",".join(fallback["matched_terms"]),
            )
        )
    lines.append(f"NEXT\t{result['instruction']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_file():
        print(f"knowledge root not found: {root}", file=sys.stderr)
        return 2
    result = build_result(root, args.query, args.limit)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    return 0 if result["primary"] is not None else 3


if __name__ == "__main__":
    raise SystemExit(main())
