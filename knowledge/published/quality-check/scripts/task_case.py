#!/usr/bin/env python3
"""Manage recoverable task-knowledge preparation cases.

The AI/session performs semantic work. This script only owns deterministic ledger
operations: create, inspect, append, validate, render, and close a task case.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from source_run import SourceRunError, validate_source_run_uri

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised in real environments
    raise SystemExit(
        "缺少依赖 PyYAML。请按 environment.yml 安装环境，或运行："
        "python -m pip install 'pyyaml>=6.0.1'"
    ) from exc


SCHEMA_VERSION = "0.1"
CASE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
CASE_STATUSES = {
    "active",
    "waiting_human",
    "ready_for_decision",
    "blocked",
    "closed",
    "superseded",
    "abandoned",
}
FOCUS_STAGES = {"framing", "inventory", "gap_resolution", "weaving", "validation", "handoff"}
QUESTION_STATUSES = {"open", "answered", "accepted_risk", "deferred"}
KNOWLEDGE_DISPOSITIONS = {"create", "merge", "update", "task_only", "discard"}
TERMINAL_STATUSES = {"closed", "superseded", "abandoned"}


class TaskCaseError(Exception):
    """A user-actionable task case error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_root() -> Path:
    return Path(__file__).resolve().parents[1] / "workspaces" / "task-cases"


def validate_case_id(case_id: str) -> None:
    if not CASE_ID_PATTERN.fullmatch(case_id):
        raise TaskCaseError(
            "case id 只能包含小写字母、数字和连字符，长度 1-63，且必须以字母或数字开头"
        )


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not value:
        value = "task"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{value[:43].rstrip('-')}-{timestamp}"


def case_dir(root: Path, case_id: str) -> Path:
    validate_case_id(case_id)
    return root / case_id


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, prefix=f".{path.name}."
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TaskCaseError(f"{path}:{line_number} 不是有效 JSONL：{exc}") from exc
        if not isinstance(value, dict):
            raise TaskCaseError(f"{path}:{line_number} 必须是 JSON 对象")
        records.append(value)
    return records


def load_case(directory: Path) -> dict[str, Any]:
    path = directory / "case.yaml"
    if not path.exists():
        raise TaskCaseError(f"任务案不存在：{path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TaskCaseError(f"无法解析 {path}：{exc}") from exc
    if not isinstance(value, dict):
        raise TaskCaseError(f"{path} 顶层必须是 YAML mapping")
    return value


def save_case(directory: Path, case: dict[str, Any]) -> None:
    case["updated_at"] = utc_now()
    content = yaml.safe_dump(case, allow_unicode=True, sort_keys=False, width=100)
    atomic_write_text(directory / "case.yaml", content)


def initial_case(
    case_id: str,
    title: str,
    trigger: str,
    goal: str,
    decision: str,
) -> dict[str, Any]:
    now = utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "id": case_id,
        "title": title,
        "status": "active",
        "current_focus": "framing",
        "frame_version": 1,
        "created_at": now,
        "updated_at": now,
        "task_frame": {
            "trigger": trigger,
            "goal": goal,
            "decision_to_support": decision,
            "in_scope": [],
            "out_of_scope": [],
            "constraints": [],
            "assumptions": [],
        },
        "questions": [],
        "blockers": [],
        "knowledge_candidates": [],
        "gates": {
            "decision_ready": {"status": "pending", "checked_at": None, "checks": []},
            "knowledge_handoff_ready": {
                "status": "pending",
                "checked_at": None,
                "checks": [],
            },
        },
        "next_actions": [],
        "closure": None,
    }


def create_case(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    case_id = args.id or slugify(args.title)
    validate_case_id(case_id)
    directory = case_dir(root, case_id)
    if directory.exists():
        raise TaskCaseError(f"任务案已存在：{directory}")

    case = initial_case(case_id, args.title, args.trigger, args.goal, args.decision)
    (directory / "outputs").mkdir(parents=True)
    (directory / "knowledge-proposals").mkdir()
    save_case(directory, case)
    atomic_write_text(directory / "events.jsonl", "")
    atomic_write_text(directory / "evidence.jsonl", "")
    atomic_write_text(directory / "knowledge-proposals" / "change-set.md", "# 知识变更候选\n\n")
    append_jsonl(
        directory / "events.jsonl",
        {
            "id": "event-0001",
            "at": utc_now(),
            "type": "case_created",
            "actor": args.actor,
            "summary": "创建任务知识准备案",
            "frame_version": 1,
            "data": {},
        },
    )
    render_case(directory, case)
    print(directory)
    return 0


def next_record_id(records: list[dict[str, Any]], prefix: str) -> str:
    largest = 0
    for record in records:
        match = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", str(record.get("id", "")))
        if match:
            largest = max(largest, int(match.group(1)))
    return f"{prefix}-{largest + 1:04d}"


def parse_data(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise TaskCaseError(f"--data 必须是 JSON 对象：{exc}") from exc
    if not isinstance(parsed, dict):
        raise TaskCaseError("--data 必须是 JSON 对象")
    return parsed


def validate_source_reference(
    source: str, cases_root: Path, case_id: str
) -> dict[str, Any] | None:
    """Resolve task-local SourceRun URIs without changing ordinary source strings."""
    if not source.startswith("source-run://"):
        return None
    try:
        run = validate_source_run_uri(source, cases_root, expected_case_id=case_id)
    except SourceRunError as exc:
        raise TaskCaseError(f"SourceRun 引用无效：{exc}") from exc
    return {
        "uri": source,
        "id": run.get("id"),
        "source_id": run.get("source_id"),
        "execution": run.get("execution"),
        "comparison": run.get("comparison"),
        "coverage": run.get("coverage"),
        "config_fingerprint": run.get("config_fingerprint"),
        "scoped_fingerprint": run.get("revision", {}).get("scoped_fingerprint"),
    }


def add_event(args: argparse.Namespace) -> int:
    directory = case_dir(args.root.resolve(), args.case_id)
    case = load_case(directory)
    records = load_jsonl(directory / "events.jsonl")
    record = {
        "id": next_record_id(records, "event"),
        "at": utc_now(),
        "type": args.type,
        "actor": args.actor,
        "summary": args.summary,
        "frame_version": case.get("frame_version"),
        "data": parse_data(args.data),
    }
    append_jsonl(directory / "events.jsonl", record)
    print(record["id"])
    return 0


def add_evidence(args: argparse.Namespace) -> int:
    directory = case_dir(args.root.resolve(), args.case_id)
    case = load_case(directory)
    records = load_jsonl(directory / "evidence.jsonl")
    record = {
        "id": next_record_id(records, "evidence"),
        "at": utc_now(),
        "kind": args.kind,
        "summary": args.summary,
        "source": args.source,
        "status": args.status,
        "criticality": args.criticality,
        "frame_version": case.get("frame_version"),
        "data": parse_data(args.data),
    }
    append_jsonl(directory / "evidence.jsonl", record)
    add_internal_event(directory, case, "evidence_added", f"追加证据 {record['id']}", args.actor)
    print(record["id"])
    return 0


def answer_question(args: argparse.Namespace) -> int:
    """Answer one recorded question and advance all deterministic case state.

    All validation happens before the first write. Evidence is appended before the
    question references it, so an unexpected process/filesystem failure can at
    worst leave an unreferenced evidence record; it cannot leave a question
    pointing at evidence that was never written. This is a command-level
    consistency boundary, not a multi-file crash-safe database transaction.
    """
    directory = case_dir(args.root.resolve(), args.case_id)
    case = load_case(directory)
    if case.get("status") in TERMINAL_STATUSES:
        raise TaskCaseError(f"任务案已经结束：{case.get('status')}")

    answer = args.answer.strip()
    source = args.source.strip()
    evidence_summary = (args.evidence_summary or answer).strip()
    if not answer:
        raise TaskCaseError("--answer 不能为空")
    if not source:
        raise TaskCaseError("--source 不能为空")
    if not evidence_summary:
        raise TaskCaseError("--evidence-summary 不能为空")
    data = parse_data(args.data)
    source_run = validate_source_reference(source, args.root.resolve(), args.case_id)
    if source_run is not None:
        if "source_run" in data:
            raise TaskCaseError("--data.source_run 由工具生成，不能由调用方覆盖")
        data["source_run"] = source_run

    questions = case.get("questions")
    if not isinstance(questions, list):
        raise TaskCaseError("questions 必须是列表")
    matches = [
        question
        for question in questions
        if isinstance(question, dict) and str(question.get("id")) == args.question_id
    ]
    if not matches:
        raise TaskCaseError(f"关键问题不存在：{args.question_id}")
    if len(matches) > 1:
        raise TaskCaseError(f"关键问题 ID 不唯一：{args.question_id}")
    question = matches[0]
    if question.get("status") in {"answered", "accepted_risk"}:
        raise TaskCaseError(
            f"关键问题已经处理：{args.question_id}（{question.get('status')}），拒绝覆盖原答案"
        )
    references = question.get("evidence_ids", [])
    if not isinstance(references, list):
        raise TaskCaseError(f"{args.question_id}.evidence_ids 必须是列表")

    evidence_records = load_jsonl(directory / "evidence.jsonl")
    evidence_id = next_record_id(evidence_records, "evidence")
    answered_at = utc_now()
    criticality = args.criticality or question.get("criticality", "normal")
    evidence_record = {
        "id": evidence_id,
        "at": answered_at,
        "kind": args.kind,
        "summary": evidence_summary,
        "source": source,
        "status": args.status,
        "criticality": criticality,
        "frame_version": case.get("frame_version"),
        "data": data,
    }

    append_jsonl(directory / "evidence.jsonl", evidence_record)
    add_internal_event(
        directory,
        case,
        "evidence_added",
        f"追加证据 {evidence_id}",
        args.actor,
        {"evidence_id": evidence_id, "question_id": args.question_id},
    )

    question["status"] = "answered"
    question["answer"] = answer
    question["answered_at"] = answered_at
    question["answered_by"] = args.actor
    question["evidence_ids"] = [*references, evidence_id]
    if args.next_actions is not None:
        case["next_actions"] = args.next_actions
    save_case(directory, case)
    add_internal_event(
        directory,
        case,
        "question_answered",
        f"回答关键问题 {args.question_id}",
        args.actor,
        {"question_id": args.question_id, "evidence_id": evidence_id},
    )
    gates = run_check(directory, case, args.actor)
    print(
        json.dumps(
            {
                "case_id": case.get("id"),
                "question_id": args.question_id,
                "evidence_id": evidence_id,
                "case_status": case.get("status"),
                "gates": gates,
                "next_actions": case.get("next_actions", []),
                "source_run_uri": source if source_run is not None else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def add_internal_event(
    directory: Path,
    case: dict[str, Any],
    event_type: str,
    summary: str,
    actor: str = "task_case.py",
    data: dict[str, Any] | None = None,
) -> str:
    records = load_jsonl(directory / "events.jsonl")
    event_id = next_record_id(records, "event")
    append_jsonl(
        directory / "events.jsonl",
        {
            "id": event_id,
            "at": utc_now(),
            "type": event_type,
            "actor": actor,
            "summary": summary,
            "frame_version": case.get("frame_version"),
            "data": data or {},
        },
    )
    return event_id


def check_item(code: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"code": code, "passed": passed, "detail": detail}


def validate_shape(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "id",
        "title",
        "status",
        "current_focus",
        "frame_version",
        "task_frame",
        "questions",
        "blockers",
        "knowledge_candidates",
        "gates",
        "next_actions",
    }
    missing = sorted(required - case.keys())
    if missing:
        errors.append(f"缺少顶层字段：{', '.join(missing)}")
    if case.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"不支持 schema_version：{case.get('schema_version')!r}")
    if case.get("status") not in CASE_STATUSES:
        errors.append(f"无效 status：{case.get('status')!r}")
    if case.get("current_focus") not in FOCUS_STAGES:
        errors.append(f"无效 current_focus：{case.get('current_focus')!r}")
    if not isinstance(case.get("frame_version"), int) or case.get("frame_version", 0) < 1:
        errors.append("frame_version 必须是大于等于 1 的整数")
    for field in ("questions", "blockers", "knowledge_candidates", "next_actions"):
        if field in case and not isinstance(case[field], list):
            errors.append(f"{field} 必须是列表")
    if "task_frame" in case and not isinstance(case["task_frame"], dict):
        errors.append("task_frame 必须是 mapping")
    return errors


def evaluate_gates(directory: Path, case: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    shape_errors = validate_shape(case)
    evidence = load_jsonl(directory / "evidence.jsonl")
    evidence_ids = {str(item.get("id")) for item in evidence}
    evidence_by_id = {str(item.get("id")): item for item in evidence}
    frame = case.get("task_frame") if isinstance(case.get("task_frame"), dict) else {}
    questions = case.get("questions") if isinstance(case.get("questions"), list) else []
    candidates = (
        case.get("knowledge_candidates")
        if isinstance(case.get("knowledge_candidates"), list)
        else []
    )

    critical_open: list[str] = []
    invalid_question_evidence: list[str] = []
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            critical_open.append(f"question[{index}] 格式无效")
            continue
        question_id = str(question.get("id") or f"question[{index}]")
        status = question.get("status", "open")
        if status not in QUESTION_STATUSES:
            critical_open.append(f"{question_id} 状态无效")
        if question.get("criticality", "critical") == "critical" and status not in {
            "answered",
            "accepted_risk",
        }:
            critical_open.append(question_id)
        if status == "answered":
            references = question.get("evidence_ids", [])
            if not references or any(
                str(reference) not in evidence_ids for reference in references
            ):
                invalid_question_evidence.append(question_id)
                continue
            for reference in references:
                evidence_record = evidence_by_id[str(reference)]
                source = str(evidence_record.get("source", ""))
                try:
                    validate_source_reference(source, directory.parent, str(case.get("id")))
                except TaskCaseError:
                    invalid_question_evidence.append(question_id)
                    break

    unresolved_conflicts = [
        str(item.get("id", "unknown"))
        for item in evidence
        if item.get("kind") == "conflict"
        and item.get("criticality", "critical") == "critical"
        and item.get("status") not in {"resolved", "accepted_risk"}
    ]
    decision_checks = [
        check_item("schema_valid", not shape_errors, "; ".join(shape_errors) or "结构有效"),
        check_item(
            "goal_defined",
            bool(str(frame.get("goal", "")).strip()),
            "当前目标已定义" if str(frame.get("goal", "")).strip() else "当前目标必须明确",
        ),
        check_item(
            "decision_defined",
            bool(str(frame.get("decision_to_support", "")).strip()),
            (
                "待支持决策已定义"
                if str(frame.get("decision_to_support", "")).strip()
                else "待支持决策必须明确"
            ),
        ),
        check_item(
            "critical_questions_resolved",
            not critical_open,
            f"未解决：{', '.join(critical_open)}" if critical_open else "关键问题已处理",
        ),
        check_item(
            "blockers_cleared",
            not case.get("blockers"),
            (
                f"仍有阻塞项：{len(case.get('blockers', []))}"
                if case.get("blockers")
                else "无显式阻塞项"
            ),
        ),
        check_item(
            "answers_traceable",
            not invalid_question_evidence,
            (
                f"缺少有效证据引用：{', '.join(invalid_question_evidence)}"
                if invalid_question_evidence
                else "已回答问题可追溯"
            ),
        ),
        check_item(
            "critical_conflicts_resolved",
            not unresolved_conflicts,
            (
                f"未解决冲突：{', '.join(unresolved_conflicts)}"
                if unresolved_conflicts
                else "无未解决关键冲突"
            ),
        ),
        check_item(
            "next_action_defined",
            bool(case.get("next_actions")),
            "已登记下一允许动作" if case.get("next_actions") else "至少登记一个下一允许动作",
        ),
    ]

    unrouted: list[str] = []
    untraceable: list[str] = []
    change_set_needed = False
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            unrouted.append(f"candidate[{index}] 格式无效")
            continue
        candidate_id = str(candidate.get("id") or f"candidate[{index}]")
        disposition = candidate.get("disposition")
        if disposition not in KNOWLEDGE_DISPOSITIONS:
            unrouted.append(candidate_id)
        if disposition in {"create", "merge", "update"}:
            change_set_needed = True
        references = candidate.get("evidence_ids", [])
        if not references or any(str(reference) not in evidence_ids for reference in references):
            untraceable.append(candidate_id)

    change_set = directory / "knowledge-proposals" / "change-set.md"
    change_set_body = change_set.read_text(encoding="utf-8").strip() if change_set.exists() else ""
    has_change_set = not change_set_needed or change_set_body not in {"", "# 知识变更候选"}
    handoff_checks = [
        check_item("schema_valid", not shape_errors, "; ".join(shape_errors) or "结构有效"),
        check_item(
            "stable_candidates_routed",
            not unrouted,
            f"未分流：{', '.join(unrouted)}" if unrouted else "长期知识候选已分流",
        ),
        check_item(
            "candidate_sources_traceable",
            not untraceable,
            f"缺少有效证据引用：{', '.join(untraceable)}" if untraceable else "候选可追溯",
        ),
        check_item(
            "change_set_prepared",
            has_change_set,
            "需要补充可审查的 change-set.md" if not has_change_set else "变更提案已就绪或无需提案",
        ),
        check_item(
            "critical_conflicts_resolved",
            not unresolved_conflicts,
            (
                f"未解决冲突：{', '.join(unresolved_conflicts)}"
                if unresolved_conflicts
                else "无未解决关键冲突"
            ),
        ),
    ]
    return {"decision_ready": decision_checks, "knowledge_handoff_ready": handoff_checks}


def all_passed(checks: list[dict[str, Any]]) -> bool:
    return all(item["passed"] for item in checks)


def run_check(
    directory: Path, case: dict[str, Any], actor: str = "task_case.py"
) -> dict[str, bool]:
    evaluated = evaluate_gates(directory, case)
    checked_at = utc_now()
    results: dict[str, bool] = {}
    gates = case.setdefault("gates", {})
    for gate_name, checks in evaluated.items():
        passed = all_passed(checks)
        results[gate_name] = passed
        gates[gate_name] = {
            "status": "passed" if passed else "failed",
            "checked_at": checked_at,
            "checks": checks,
        }
    if case.get("status") not in TERMINAL_STATUSES:
        case["status"] = "ready_for_decision" if results["decision_ready"] else "active"
    save_case(directory, case)
    add_internal_event(directory, case, "gates_checked", "重新检查任务案门禁", actor, results)
    render_case(directory, case)
    return results


def check_case(args: argparse.Namespace) -> int:
    directory = case_dir(args.root.resolve(), args.case_id)
    case = load_case(directory)
    results = run_check(directory, case, args.actor)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(results.values()) else 2


def markdown_list(values: list[Any], empty: str = "暂无") -> str:
    if not values:
        return f"- {empty}"
    lines = []
    for value in values:
        if isinstance(value, dict):
            if value.get("text"):
                identity = f"{value.get('id')} " if value.get("id") else ""
                status = f"[{value.get('status')}] " if value.get("status") else ""
                label = f"{identity}{status}{value.get('text')}"
                if value.get("answer"):
                    label += f" — 答案：{value.get('answer')}"
            else:
                label = (
                    value.get("summary")
                    or value.get("id")
                    or json.dumps(value, ensure_ascii=False)
                )
        else:
            label = str(value)
        lines.append(f"- {label}")
    return "\n".join(lines)


def render_case(directory: Path, case: dict[str, Any]) -> None:
    events = load_jsonl(directory / "events.jsonl")
    evidence = load_jsonl(directory / "evidence.jsonl")
    frame = case.get("task_frame", {})
    gates = case.get("gates", {})
    latest_events = list(reversed(events[-5:]))
    overview = f"""# {case.get("title", case.get("id"))}

> 任务案：`{case.get("id")}`
> 状态：`{case.get("status")}`｜当前焦点：`{case.get("current_focus")}`｜框架版本：`{case.get("frame_version")}`
> 最近更新：{case.get("updated_at")}

## 当前目标

{frame.get("goal") or "尚未明确"}

## 待支持决策

{frame.get("decision_to_support") or "尚未明确"}

## 阻塞项

{markdown_list(case.get("blockers", []))}

## 关键问题

{markdown_list(case.get("questions", []))}

## 门禁

- decision_ready：`{gates.get("decision_ready", {}).get("status", "pending")}`
- knowledge_handoff_ready：`{gates.get("knowledge_handoff_ready", {}).get("status", "pending")}`

## 下一动作

{markdown_list(case.get("next_actions", []))}

## 最近事件

{markdown_list(latest_events)}

## 账本入口

- 当前状态：[case.yaml](case.yaml)
- 证据流：[evidence.jsonl](evidence.jsonl)（{len(evidence)} 条）
- 事件流：[events.jsonl](events.jsonl)（{len(events)} 条）
- 准备度报告：[outputs/readiness-report.md](outputs/readiness-report.md)
- 决策上下文：[outputs/decision-context.md](outputs/decision-context.md)
- 长期知识候选：[knowledge-proposals/change-set.md](knowledge-proposals/change-set.md)
"""
    atomic_write_text(directory / "overview.md", overview)
    render_readiness(directory, case)
    render_decision_context(directory, case, evidence)


def render_readiness(directory: Path, case: dict[str, Any]) -> None:
    lines = [f"# {case.get('title')}｜准备度报告", "", f"> 生成时间：{utc_now()}", ""]
    for gate_name in ("decision_ready", "knowledge_handoff_ready"):
        gate = case.get("gates", {}).get(gate_name, {})
        lines.extend([f"## {gate_name}：`{gate.get('status', 'pending')}`", ""])
        checks = gate.get("checks", [])
        if not checks:
            lines.extend(["- 尚未运行机械门禁检查。", ""])
            continue
        for item in checks:
            mark = "PASS" if item.get("passed") else "FAIL"
            lines.append(f"- **{mark}** `{item.get('code')}`：{item.get('detail')}")
        lines.append("")
    lines.extend(
        [
            "## 边界",
            "",
            "本报告只验证结构、引用和显式状态，不判断证据真实性、知识充分性或业务方案质量。",
            "",
        ]
    )
    atomic_write_text(directory / "outputs" / "readiness-report.md", "\n".join(lines))


def render_decision_context(
    directory: Path, case: dict[str, Any], evidence: list[dict[str, Any]]
) -> None:
    gate = case.get("gates", {}).get("decision_ready", {})
    if gate.get("status") != "passed":
        content = "# 决策上下文\n\n> `decision_ready` 尚未通过，本视图暂不生成。\n"
    else:
        frame = case.get("task_frame", {})
        content = f"""# {case.get("title")}｜决策上下文

> 框架版本：`{case.get("frame_version")}`｜生成时间：{utc_now()}

## 目标

{frame.get("goal")}

## 待支持决策

{frame.get("decision_to_support")}

## 约束

{markdown_list(frame.get("constraints", []))}

## 关键问题

{markdown_list(case.get("questions", []))}

## 证据入口

{markdown_list(evidence)}

## 已接受未知与假设

{markdown_list(frame.get("assumptions", []))}

## 下一动作

{markdown_list(case.get("next_actions", []))}
"""
    atomic_write_text(directory / "outputs" / "decision-context.md", content)


def render_command(args: argparse.Namespace) -> int:
    directory = case_dir(args.root.resolve(), args.case_id)
    case = load_case(directory)
    render_case(directory, case)
    print(directory / "overview.md")
    return 0


def status_summary(directory: Path, case: dict[str, Any]) -> dict[str, Any]:
    events = load_jsonl(directory / "events.jsonl")
    return {
        "id": case.get("id"),
        "title": case.get("title"),
        "status": case.get("status"),
        "current_focus": case.get("current_focus"),
        "frame_version": case.get("frame_version"),
        "goal": case.get("task_frame", {}).get("goal"),
        "decision_to_support": case.get("task_frame", {}).get("decision_to_support"),
        "blockers": case.get("blockers", []),
        "gates": {
            name: case.get("gates", {}).get(name, {}).get("status", "pending")
            for name in ("decision_ready", "knowledge_handoff_ready")
        },
        "next_actions": case.get("next_actions", []),
        "latest_event": events[-1] if events else None,
        "path": str(directory),
    }


def show_status(args: argparse.Namespace) -> int:
    directory = case_dir(args.root.resolve(), args.case_id)
    case = load_case(directory)
    summary = status_summary(directory, case)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"{summary['id']}｜{summary['status']}｜{summary['current_focus']}")
        print(f"目标：{summary['goal'] or '尚未明确'}")
        print(f"决策：{summary['decision_to_support'] or '尚未明确'}")
        print(
            "门禁："
            f"decision={summary['gates']['decision_ready']}, "
            f"knowledge={summary['gates']['knowledge_handoff_ready']}"
        )
        print("阻塞：" + ("；".join(map(str, summary["blockers"])) or "暂无"))
        print("下一步：" + ("；".join(map(str, summary["next_actions"])) or "尚未登记"))
        print(f"路径：{summary['path']}")
    return 0


def list_cases(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    summaries = []
    if root.exists():
        for directory in sorted(path for path in root.iterdir() if path.is_dir()):
            if (directory / "case.yaml").exists():
                summaries.append(status_summary(directory, load_case(directory)))
    if args.json:
        print(json.dumps(summaries, ensure_ascii=False, indent=2))
    else:
        for summary in summaries:
            print(
                f"{summary['id']}\t{summary['status']}\t{summary['current_focus']}\t{summary['title']}"
            )
    return 0


def close_case(args: argparse.Namespace) -> int:
    directory = case_dir(args.root.resolve(), args.case_id)
    case = load_case(directory)
    if case.get("status") in TERMINAL_STATUSES:
        raise TaskCaseError(f"任务案已经结束：{case.get('status')}")
    if args.termination:
        target_status = args.termination
    else:
        results = run_check(directory, case, args.actor)
        if not all(results.values()):
            raise TaskCaseError("两个门禁尚未全部通过；若用户明确终止，请使用 --termination")
        target_status = "closed"
    case["status"] = target_status
    case["current_focus"] = "handoff"
    case["closure"] = {"at": utc_now(), "reason": args.reason, "actor": args.actor}
    save_case(directory, case)
    add_internal_event(directory, case, "case_closed", f"任务案结束：{target_status}", args.actor)
    render_case(directory, case)
    print(target_status)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="管理可恢复的任务知识准备案")
    parser.add_argument("--root", type=Path, default=default_root(), help="任务案根目录")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="创建任务案")
    create.add_argument("title")
    create.add_argument("--id")
    create.add_argument("--trigger", default="")
    create.add_argument("--goal", default="")
    create.add_argument("--decision", default="")
    create.add_argument("--actor", default="agent")
    create.set_defaults(func=create_case)

    status = subparsers.add_parser("status", help="显示可恢复状态")
    status.add_argument("case_id")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=show_status)

    listing = subparsers.add_parser("list", help="列出任务案")
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(func=list_cases)

    event = subparsers.add_parser("event", help="追加过程事件")
    event.add_argument("case_id")
    event.add_argument("--type", required=True)
    event.add_argument("--summary", required=True)
    event.add_argument("--actor", default="agent")
    event.add_argument("--data", default="{}")
    event.set_defaults(func=add_event)

    evidence = subparsers.add_parser("evidence", help="追加证据、Claim、冲突或人工确认")
    evidence.add_argument("case_id")
    evidence.add_argument(
        "--kind", required=True, choices=("source", "claim", "conflict", "human_confirmation")
    )
    evidence.add_argument("--summary", required=True)
    evidence.add_argument("--source", required=True)
    evidence.add_argument(
        "--status",
        default="current",
        choices=("current", "historical", "inferred", "open", "resolved", "accepted_risk"),
    )
    evidence.add_argument("--criticality", default="normal", choices=("normal", "critical"))
    evidence.add_argument("--actor", default="agent")
    evidence.add_argument("--data", default="{}")
    evidence.set_defaults(func=add_evidence)

    answer = subparsers.add_parser("answer", help="回答一个关键问题并同步证据、门禁和视图")
    answer.add_argument("case_id")
    answer.add_argument("question_id")
    answer.add_argument("--answer", required=True, help="写回问题的简洁答案")
    answer.add_argument("--source", required=True, help="答案依据的可追溯来源")
    answer.add_argument(
        "--kind",
        default="claim",
        choices=("source", "claim", "human_confirmation"),
        help="答案证据类型；冲突应先用 evidence 命令登记和解决",
    )
    answer.add_argument("--evidence-summary", help="证据摘要；默认复用 --answer")
    answer.add_argument(
        "--status",
        default="current",
        choices=("current", "historical", "inferred", "resolved", "accepted_risk"),
    )
    answer.add_argument("--criticality", choices=("normal", "critical"))
    answer.add_argument(
        "--next-action",
        dest="next_actions",
        action="append",
        help="替换任务案下一动作；可重复传入，省略时保留原值",
    )
    answer.add_argument("--actor", default="agent")
    answer.add_argument("--data", default="{}")
    answer.set_defaults(func=answer_question)

    check = subparsers.add_parser("check", help="执行机械门禁并重建视图")
    check.add_argument("case_id")
    check.add_argument("--actor", default="task_case.py")
    check.set_defaults(func=check_case)

    render = subparsers.add_parser("render", help="重建 Markdown 视图")
    render.add_argument("case_id")
    render.set_defaults(func=render_command)

    close = subparsers.add_parser("close", help="关闭或明确终止任务案")
    close.add_argument("case_id")
    close.add_argument("--reason", required=True)
    close.add_argument("--termination", choices=("abandoned", "superseded"))
    close.add_argument("--actor", default="agent")
    close.set_defaults(func=close_case)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except TaskCaseError as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
