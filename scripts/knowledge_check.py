#!/usr/bin/env python3
"""Read-only checks for the Omni-Brain OKF knowledge bundle."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml


RESERVED = {"index.md", "log.md"}
CANONICAL_AREAS = {"domains", "capabilities", "systems"}
DOMAIN_ID_RE = re.compile(r"^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
LINK_RE = re.compile(r"(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)")
WIKI_LINK_RE = re.compile(r"\[\[[^\]\n]+\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
HTML_ANCHOR_RE = re.compile(r"<a\s+(?:name|id)=[\"']([^\"']+)[\"']\s*></a>", re.IGNORECASE)
FORBIDDEN_EXTENSION_KEYS = {"stable_id", "home", "applies_to", "relations"}


@dataclass
class Report:
    knowledge_root: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    backlinks: dict[str, list[str]] = field(default_factory=dict)
    files_checked: int = 0
    concepts_checked: int = 0

    @property
    def passed(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "passed" if self.passed else "failed",
            "knowledge_root": str(self.knowledge_root),
            "files_checked": self.files_checked,
            "concepts_checked": self.concepts_checked,
            "errors": self.errors,
            "warnings": self.warnings,
            "backlinks": self.backlinks,
        }


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"~~~.*?~~~", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", "", text)


def parse_frontmatter(path: Path, text: str, report: Report) -> dict[str, Any] | None:
    match = FRONTMATTER_RE.match(text)
    rel = relative(path, report.knowledge_root)
    if not match:
        report.errors.append(f"{rel}: concept document lacks YAML frontmatter")
        return None
    try:
        value = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        report.errors.append(f"{rel}: invalid YAML frontmatter: {exc}")
        return None
    if not isinstance(value, dict):
        report.errors.append(f"{rel}: frontmatter must be a mapping")
        return None
    if not isinstance(value.get("type"), str) or not value["type"].strip():
        report.errors.append(f"{rel}: OKF field 'type' is required")
    for field_name in ("title", "description"):
        if not isinstance(value.get(field_name), str) or not value[field_name].strip():
            report.warnings.append(f"{rel}: recommended field '{field_name}' is missing")
    forbidden = FORBIDDEN_EXTENSION_KEYS.intersection(value)
    omni = value.get("omni")
    if isinstance(omni, dict):
        forbidden.update(FORBIDDEN_EXTENSION_KEYS.intersection(omni))
    if forbidden:
        report.errors.append(
            f"{rel}: unapproved M1 extension field(s): {', '.join(sorted(forbidden))}"
        )
    return value


def heading_slugs(text: str) -> set[str]:
    clean = strip_code(FRONTMATTER_RE.sub("", text, count=1))
    seen: Counter[str] = Counter()
    result = set(HTML_ANCHOR_RE.findall(clean))
    for match in HEADING_RE.finditer(clean):
        heading = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", match.group(2)).strip().lower()
        slug_chars: list[str] = []
        for char in heading:
            category = unicodedata.category(char)
            if char in {" ", "-", "_"} or category[0] in {"L", "N"}:
                slug_chars.append(char)
        base = re.sub(r"[\s-]+", "-", "".join(slug_chars)).strip("-")
        if not base:
            continue
        suffix = seen[base]
        seen[base] += 1
        result.add(base if suffix == 0 else f"{base}-{suffix}")
    return result


def split_link_target(raw: str) -> tuple[str, str]:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " \"" in target or " '" in target:
        target = re.split(r"\s+[\"']", target, maxsplit=1)[0]
    target = unquote(target)
    path_part, separator, fragment = target.partition("#")
    return path_part, fragment if separator else ""


def validate_domain_map(domain_map: Path, root: Path, report: Report) -> set[str]:
    if not domain_map.exists():
        report.errors.append(f"missing domain map: {domain_map}")
        return set()
    try:
        value = yaml.safe_load(domain_map.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        report.errors.append(f"invalid domain map {domain_map}: {exc}")
        return set()
    if not isinstance(value, dict) or value.get("schema_version") != "0.1":
        report.errors.append("domain map must declare schema_version: '0.1'")
        return set()
    domains = value.get("domains")
    if not isinstance(domains, list):
        report.errors.append("domain map field 'domains' must be a list")
        return set()

    by_id: dict[str, dict[str, Any]] = {}
    required = {"id", "title", "parent", "scope", "excludes"}
    for index, item in enumerate(domains):
        label = f"domain[{index}]"
        if not isinstance(item, dict):
            report.errors.append(f"{label}: must be a mapping")
            continue
        missing = required.difference(item)
        if missing:
            report.errors.append(f"{label}: missing field(s): {', '.join(sorted(missing))}")
            continue
        domain_id = item.get("id")
        if not isinstance(domain_id, str) or not DOMAIN_ID_RE.fullmatch(domain_id):
            report.errors.append(f"{label}: invalid id {domain_id!r}")
            continue
        if domain_id in by_id:
            report.errors.append(f"duplicate domain id: {domain_id}")
            continue
        for field_name in ("title", "scope", "excludes"):
            if not isinstance(item.get(field_name), str) or not item[field_name].strip():
                report.errors.append(f"{domain_id}: field '{field_name}' must be non-empty")
        parent = item.get("parent")
        if parent is not None and (not isinstance(parent, str) or not DOMAIN_ID_RE.fullmatch(parent)):
            report.errors.append(f"{domain_id}: invalid parent {parent!r}")
        by_id[domain_id] = item

    for domain_id, item in by_id.items():
        parent = item.get("parent")
        if parent is not None:
            if parent not in by_id:
                report.errors.append(f"{domain_id}: parent does not exist: {parent}")
            elif not domain_id.startswith(parent + "."):
                report.errors.append(f"{domain_id}: id must extend parent id {parent}")

    for start in by_id:
        visited: set[str] = set()
        current: str | None = start
        while current is not None and current in by_id:
            if current in visited:
                report.errors.append(f"domain cycle detected from {start}: {current}")
                break
            visited.add(current)
            parent = by_id[current].get("parent")
            current = parent if isinstance(parent, str) else None

    for domain_id in by_id:
        directory = root / "domains" / Path(*domain_id.split("."))
        if not directory.is_dir():
            report.errors.append(f"{domain_id}: missing mirrored directory {relative(directory, root)}")
        elif not (directory / "overview.md").is_file():
            report.errors.append(f"{domain_id}: mirrored directory lacks overview.md")
    return set(by_id)


def validate_bundle(knowledge_root: Path, domain_map: Path) -> Report:
    root = knowledge_root.resolve()
    report = Report(root)
    if not root.is_dir():
        report.errors.append(f"knowledge root does not exist: {root}")
        return report
    if not (root / "index.md").is_file():
        report.errors.append("knowledge/index.md is required")

    domain_ids = validate_domain_map(domain_map.resolve(), root, report)
    markdown_files = sorted(root.rglob("*.md"))
    report.files_checked = len(markdown_files)
    contents: dict[Path, str] = {}
    frontmatter: dict[Path, dict[str, Any]] = {}

    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        contents[path.resolve()] = text
        if path.name in RESERVED:
            if FRONTMATTER_RE.match(text):
                report.errors.append(f"{relative(path, root)}: OKF reserved file must not have frontmatter")
            continue
        report.concepts_checked += 1
        parsed = parse_frontmatter(path, text, report)
        if parsed is not None:
            frontmatter[path.resolve()] = parsed

    domains_root = root / "domains"
    if domains_root.exists():
        for path in domains_root.rglob("*.md"):
            if path.name in RESERVED:
                continue
            directory = path.parent.relative_to(domains_root)
            domain_id = ".".join(directory.parts)
            if domain_id not in domain_ids:
                report.errors.append(
                    f"{relative(path, root)}: directory is not declared in domain map ({domain_id})"
                )

    title_locations: dict[str, list[str]] = defaultdict(list)
    for path, fields in frontmatter.items():
        rel = relative(path, root)
        if rel.split("/", 1)[0] in CANONICAL_AREAS:
            title = fields.get("title")
            if isinstance(title, str) and title.strip():
                title_locations[title.strip()].append(rel)
    for title, locations in title_locations.items():
        if len(locations) > 1:
            report.errors.append(f"duplicate canonical title {title!r}: {', '.join(locations)}")

    inbound: dict[Path, set[Path]] = defaultdict(set)
    outbound: dict[Path, set[Path]] = defaultdict(set)
    for source, text in contents.items():
        rel_source = relative(source, root)
        visible = strip_code(text)
        if WIKI_LINK_RE.search(visible):
            report.errors.append(f"{rel_source}: Obsidian wiki link is not allowed")
        for _, raw_target in LINK_RE.findall(visible):
            path_part, fragment = split_link_target(raw_target)
            if not path_part:
                target = source
            else:
                scheme = urlsplit(path_part).scheme.lower()
                if scheme in {"http", "https", "mailto"}:
                    continue
                if scheme == "file":
                    report.errors.append(f"{rel_source}: file:// link is not portable: {raw_target}")
                    continue
                if scheme:
                    continue
                if path_part.startswith("/"):
                    report.errors.append(
                        f"{rel_source}: bundle/repository-root link is ambiguous; use a relative .md link: {raw_target}"
                    )
                    continue
                if "\\" in path_part:
                    report.errors.append(f"{rel_source}: use POSIX separators in links: {raw_target}")
                    continue
                if Path(path_part).suffix.lower() != ".md":
                    report.errors.append(f"{rel_source}: internal link must include .md: {raw_target}")
                    continue
                target = (source.parent / path_part).resolve()
                try:
                    target.relative_to(root)
                except ValueError:
                    report.errors.append(f"{rel_source}: internal link escapes knowledge bundle: {raw_target}")
                    continue
            if not target.is_file():
                report.errors.append(f"{rel_source}: broken internal link: {raw_target}")
                continue
            outbound[source].add(target)
            inbound[target].add(source)
            if fragment and fragment not in heading_slugs(contents.get(target, target.read_text(encoding="utf-8"))):
                report.errors.append(f"{rel_source}: missing heading anchor in {raw_target}")

    canonical_pages = {
        path
        for path in frontmatter
        if relative(path, root).split("/", 1)[0] in CANONICAL_AREAS
    }
    view_pages = {
        path for path in frontmatter if relative(path, root).startswith("views/")
    }
    if canonical_pages:
        domain_views = [path for path in view_pages if relative(path, root).startswith("views/by-domain/")]
        journey_views = [path for path in view_pages if relative(path, root).startswith("views/by-journey/")]
        if not domain_views:
            report.errors.append("published knowledge requires at least one by-domain product view")
        if not journey_views:
            report.errors.append("published knowledge requires at least one by-journey product view")
        for page in canonical_pages:
            if page.name == "overview.md" and relative(page, root).startswith("systems/"):
                continue
            if not any(source in view_pages for source in inbound.get(page, set())):
                report.errors.append(f"{relative(page, root)}: no product view links to this canonical page")

        start = (root / "index.md").resolve()
        reachable = {start}
        queue: deque[Path] = deque([start])
        while queue:
            current = queue.popleft()
            for target in outbound.get(current, set()):
                if target not in reachable:
                    reachable.add(target)
                    queue.append(target)
        for view in view_pages:
            if view not in reachable:
                report.errors.append(f"{relative(view, root)}: product view is not reachable from index.md")

    for page in canonical_pages:
        if page.name == "overview.md":
            continue
        text = contents[page]
        if not re.search(r"^#\s+Citations\s*$", text, flags=re.MULTILINE | re.IGNORECASE):
            report.errors.append(f"{relative(page, root)}: canonical page lacks '# Citations'")
        if not any(relative(target, root).startswith("sources/") for target in outbound.get(page, set())):
            report.errors.append(f"{relative(page, root)}: canonical page has no link to a source record")

    report.backlinks = {
        relative(target, root): sorted(relative(source, root) for source in sources)
        for target, sources in sorted(inbound.items(), key=lambda item: relative(item[0], root))
        if sources
    }
    return report


def render_text(report: Report) -> str:
    lines = [
        f"knowledge-check: {'PASS' if report.passed else 'FAIL'}",
        f"root: {report.knowledge_root}",
        f"files: {report.files_checked}; concepts: {report.concepts_checked}",
    ]
    if report.errors:
        lines.append("errors:")
        lines.extend(f"- {item}" for item in report.errors)
    if report.warnings:
        lines.append("warnings:")
        lines.extend(f"- {item}" for item in report.warnings)
    lines.append("backlinks:")
    if report.backlinks:
        for target, sources in report.backlinks.items():
            lines.append(f"- {target} <- {', '.join(sources)}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root", type=Path, default=project_root / "knowledge")
    parser.add_argument("--domain-map", type=Path, default=project_root / "config/knowledge-domains.yaml")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_bundle(args.knowledge_root, args.domain_map)
    if args.format == "json":
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())

