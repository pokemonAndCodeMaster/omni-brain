from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "scripts" / "task_case.py"


class TaskCaseCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "task-cases"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *arguments],
            cwd=REPOSITORY,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return result

    def create_case(self) -> Path:
        self.run_cli(
            "create",
            "复杂业务能力探索",
            "--id",
            "acceptance-exploration",
            "--trigger",
            "验收过程难以理解和演进",
        )
        return self.root / "acceptance-exploration"

    def load_case(self, directory: Path) -> dict:
        return yaml.safe_load((directory / "case.yaml").read_text(encoding="utf-8"))

    def save_case(self, directory: Path, case: dict) -> None:
        (directory / "case.yaml").write_text(
            yaml.safe_dump(case, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

    def test_create_produces_recoverable_ledger(self) -> None:
        directory = self.create_case()

        expected = {
            "case.yaml",
            "events.jsonl",
            "evidence.jsonl",
            "overview.md",
            "outputs/readiness-report.md",
            "outputs/decision-context.md",
            "knowledge-proposals/change-set.md",
        }
        actual = {
            str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file()
        }
        self.assertEqual(expected, actual)

        status = self.run_cli("status", "acceptance-exploration", "--json")
        summary = json.loads(status.stdout)
        self.assertEqual("framing", summary["current_focus"])
        self.assertEqual("pending", summary["gates"]["decision_ready"])
        self.assertIn("创建任务知识准备案", summary["latest_event"]["summary"])

    def test_gate_fails_until_decision_questions_and_actions_are_traceable(self) -> None:
        directory = self.create_case()

        failed = self.run_cli("check", "acceptance-exploration", expected=2)
        self.assertFalse(json.loads(failed.stdout)["decision_ready"])
        report = (directory / "outputs" / "readiness-report.md").read_text(encoding="utf-8")
        self.assertIn("**FAIL** `goal_defined`", report)

        evidence_id = self.run_cli(
            "evidence",
            "acceptance-exploration",
            "--kind",
            "human_confirmation",
            "--summary",
            "用户确认当前任务以建设 Omni-Brain 组件为目标",
            "--source",
            "user-confirmation:2026-07-12",
        ).stdout.strip()
        case = self.load_case(directory)
        case["task_frame"]["goal"] = "验证任务知识准备组件能否支持验收能力探索"
        case["task_frame"]["decision_to_support"] = "是否进入验收能力方案设计"
        case["questions"] = [
            {
                "id": "q-001",
                "text": "本轮核心产物是什么？",
                "criticality": "critical",
                "status": "answered",
                "evidence_ids": [evidence_id],
            }
        ]
        case["knowledge_candidates"] = [
            {
                "id": "kc-001",
                "summary": "任务目标确认",
                "disposition": "task_only",
                "evidence_ids": [evidence_id],
            }
        ]
        case["next_actions"] = ["基于当前决策上下文讨论验收知识对象"]
        self.save_case(directory, case)

        passed = self.run_cli("check", "acceptance-exploration")
        self.assertEqual(
            {"decision_ready": True, "knowledge_handoff_ready": True},
            json.loads(passed.stdout),
        )
        recovered = json.loads(self.run_cli("status", "acceptance-exploration", "--json").stdout)
        self.assertEqual("ready_for_decision", recovered["status"])
        self.assertEqual("基于当前决策上下文讨论验收知识对象", recovered["next_actions"][0])
        decision_context = (directory / "outputs" / "decision-context.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("是否进入验收能力方案设计", decision_context)

    def test_unresolved_critical_conflict_blocks_both_gates(self) -> None:
        directory = self.create_case()
        case = self.load_case(directory)
        case["task_frame"]["goal"] = "准备验收探索知识"
        case["task_frame"]["decision_to_support"] = "选择下一探索方向"
        case["next_actions"] = ["解决冲突"]
        self.save_case(directory, case)
        self.run_cli(
            "evidence",
            "acceptance-exploration",
            "--kind",
            "conflict",
            "--summary",
            "两份资料对验收通过口径描述不一致",
            "--source",
            "docs:a-vs-b",
            "--status",
            "open",
            "--criticality",
            "critical",
        )

        result = self.run_cli("check", "acceptance-exploration", expected=2)
        self.assertEqual(
            {"decision_ready": False, "knowledge_handoff_ready": False},
            json.loads(result.stdout),
        )
        close = self.run_cli("close", "acceptance-exploration", "--reason", "准备完成", expected=1)
        self.assertIn("两个门禁尚未全部通过", close.stderr)

    def test_answer_records_evidence_updates_question_and_rebuilds_state(self) -> None:
        directory = self.create_case()
        case = self.load_case(directory)
        case["task_frame"]["goal"] = "验证恢复后的任务状态能否被可靠推进"
        case["task_frame"]["decision_to_support"] = "是否进入下一项组件建设"
        case["questions"] = [
            {
                "id": "q-001",
                "text": "下一项最小组件是什么？",
                "criticality": "critical",
                "status": "open",
                "evidence_ids": [],
            }
        ]
        case["next_actions"] = ["回答 q-001"]
        self.save_case(directory, case)

        recovered_before = json.loads(
            self.run_cli("status", "acceptance-exploration", "--json").stdout
        )
        self.assertEqual("回答 q-001", recovered_before["next_actions"][0])

        result = self.run_cli(
            "answer",
            "acceptance-exploration",
            "q-001",
            "--answer",
            "实现可由弱模型调用的原子问题回答命令",
            "--source",
            "user-confirmation:2026-07-15",
            "--kind",
            "human_confirmation",
            "--next-action",
            "在新进程中恢复更新后的任务案",
            "--actor",
            "test-agent",
        )

        output = json.loads(result.stdout)
        self.assertEqual("q-001", output["question_id"])
        self.assertEqual("evidence-0001", output["evidence_id"])
        self.assertEqual(
            {"decision_ready": True, "knowledge_handoff_ready": True}, output["gates"]
        )
        self.assertEqual("ready_for_decision", output["case_status"])

        updated = self.load_case(directory)
        question = updated["questions"][0]
        self.assertEqual("answered", question["status"])
        self.assertEqual("实现可由弱模型调用的原子问题回答命令", question["answer"])
        self.assertEqual(["evidence-0001"], question["evidence_ids"])
        self.assertEqual("test-agent", question["answered_by"])
        self.assertEqual(["在新进程中恢复更新后的任务案"], updated["next_actions"])

        recovered_after = json.loads(
            self.run_cli("status", "acceptance-exploration", "--json").stdout
        )
        self.assertEqual("ready_for_decision", recovered_after["status"])
        self.assertEqual(
            "在新进程中恢复更新后的任务案", recovered_after["next_actions"][0]
        )

        evidence = [
            json.loads(line)
            for line in (directory / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual("human_confirmation", evidence[0]["kind"])
        self.assertEqual(question["answer"], evidence[0]["summary"])

        events = [
            json.loads(line)
            for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(
            ["case_created", "evidence_added", "question_answered", "gates_checked"],
            [event["type"] for event in events],
        )
        overview = (directory / "overview.md").read_text(encoding="utf-8")
        self.assertIn("q-001 [answered] 下一项最小组件是什么？", overview)
        self.assertIn("答案：实现可由弱模型调用的原子问题回答命令", overview)

    def test_answer_unknown_question_does_not_modify_ledger(self) -> None:
        directory = self.create_case()
        before = {
            path.name: path.read_bytes()
            for path in (
                directory / "case.yaml",
                directory / "events.jsonl",
                directory / "evidence.jsonl",
            )
        }

        result = self.run_cli(
            "answer",
            "acceptance-exploration",
            "q-missing",
            "--answer",
            "不应写入",
            "--source",
            "test:missing",
            expected=1,
        )

        self.assertIn("关键问题不存在", result.stderr)
        after = {
            path.name: path.read_bytes()
            for path in (
                directory / "case.yaml",
                directory / "events.jsonl",
                directory / "evidence.jsonl",
            )
        }
        self.assertEqual(before, after)

    def test_answer_refuses_to_overwrite_resolved_question(self) -> None:
        directory = self.create_case()
        case = self.load_case(directory)
        case["questions"] = [
            {
                "id": "q-001",
                "text": "已经回答的问题",
                "criticality": "critical",
                "status": "answered",
                "answer": "原答案",
                "evidence_ids": ["evidence-0001"],
            }
        ]
        self.save_case(directory, case)
        (directory / "evidence.jsonl").write_text(
            json.dumps(
                {
                    "id": "evidence-0001",
                    "kind": "claim",
                    "summary": "原答案",
                    "source": "test:existing",
                    "status": "current",
                    "criticality": "critical",
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        evidence_before = (directory / "evidence.jsonl").read_bytes()

        result = self.run_cli(
            "answer",
            "acceptance-exploration",
            "q-001",
            "--answer",
            "覆盖答案",
            "--source",
            "test:overwrite",
            expected=1,
        )

        self.assertIn("已经处理", result.stderr)
        self.assertEqual(evidence_before, (directory / "evidence.jsonl").read_bytes())
        self.assertEqual("原答案", self.load_case(directory)["questions"][0]["answer"])

    def test_explicit_termination_is_recorded_without_passing_gates(self) -> None:
        directory = self.create_case()
        self.run_cli(
            "close",
            "acceptance-exploration",
            "--reason",
            "用户决定更换测试任务",
            "--termination",
            "superseded",
        )

        case = self.load_case(directory)
        self.assertEqual("superseded", case["status"])
        self.assertEqual("用户决定更换测试任务", case["closure"]["reason"])

    def test_close_rechecks_stale_gate_result(self) -> None:
        directory = self.create_case()
        case = self.load_case(directory)
        case["task_frame"]["goal"] = "准备验收探索知识"
        case["task_frame"]["decision_to_support"] = "选择下一探索方向"
        case["next_actions"] = ["进入方案讨论"]
        self.save_case(directory, case)
        self.run_cli("check", "acceptance-exploration")

        case = self.load_case(directory)
        case["blockers"] = ["门禁通过后新增的阻塞项"]
        self.save_case(directory, case)

        result = self.run_cli("close", "acceptance-exploration", "--reason", "准备完成", expected=1)
        self.assertIn("两个门禁尚未全部通过", result.stderr)
        self.assertEqual("failed", self.load_case(directory)["gates"]["decision_ready"]["status"])


if __name__ == "__main__":
    unittest.main()
