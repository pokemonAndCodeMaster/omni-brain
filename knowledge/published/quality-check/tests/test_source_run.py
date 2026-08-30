from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPOSITORY = Path(__file__).resolve().parents[1]
SOURCE_RUN_SCRIPT = REPOSITORY / "scripts" / "source_run.py"
TASK_CASE_SCRIPT = REPOSITORY / "scripts" / "task_case.py"


class SourceRunCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.workspace = self.base / "workspace"
        self.cases_root = self.base / "task-cases"
        self.workspace.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test User")
        self.write("docs/in-scope.md", "version one\n")
        self.write("docs/other.md", "outside\n")
        self.git("add", ".")
        self.git("commit", "-qm", "initial")
        self.create_case()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", *arguments],
            cwd=self.workspace,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        return result

    def write(self, relative_path: str, content: str) -> Path:
        path = self.workspace / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_source(
        self,
        *arguments: str,
        expected: int = 0,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command_env = os.environ.copy()
        if env:
            command_env.update(env)
        result = subprocess.run(
            [
                sys.executable,
                str(SOURCE_RUN_SCRIPT),
                "--cases-root",
                str(self.cases_root),
                "--workspace",
                str(self.workspace),
                *arguments,
            ],
            cwd=REPOSITORY,
            check=False,
            capture_output=True,
            text=True,
            env=command_env,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return result

    def run_task(
        self, *arguments: str, expected: int = 0
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [
                sys.executable,
                str(TASK_CASE_SCRIPT),
                "--root",
                str(self.cases_root),
                *arguments,
            ],
            cwd=REPOSITORY,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return result

    def create_case(self) -> Path:
        self.run_task(
            "create",
            "来源运行测试",
            "--id",
            "source-envelope",
            "--goal",
            "验证来源状态",
            "--decision",
            "是否进入语义判断",
        )
        return self.case_dir

    @property
    def case_dir(self) -> Path:
        return self.cases_root / "source-envelope"

    @property
    def source_dir(self) -> Path:
        return self.case_dir / "source-runs" / "local-docs"

    def register(self, *includes: str, replace: bool = False) -> dict:
        arguments = [
            "register",
            "source-envelope",
            "local-docs",
            "--kind",
            "local_git",
            "--root",
            ".",
            "--authority",
            "contextual",
            "--purpose",
            "test source",
        ]
        for include in includes or ("docs/in-scope.md",):
            arguments.extend(["--include", include])
        if replace:
            arguments.append("--replace")
        return json.loads(self.run_source(*arguments).stdout)

    def execute_run(self, expected: int = 0, env: dict[str, str] | None = None) -> dict:
        result = self.run_source(
            "run", "source-envelope", "local-docs", expected=expected, env=env
        )
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def load_yaml(self, path: Path) -> dict:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertIsInstance(value, dict)
        return value

    def load_manifest(self, run_id: str) -> list[dict]:
        path = self.source_dir / "runs" / run_id / "manifest.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def prepare_open_question(self, question_id: str = "q-001") -> None:
        case = self.load_yaml(self.case_dir / "case.yaml")
        case["questions"] = [
            {
                "id": question_id,
                "text": "现有资料是否充分？",
                "criticality": "critical",
                "status": "open",
                "evidence_ids": [],
            }
        ]
        case["next_actions"] = ["检查来源"]
        (self.case_dir / "case.yaml").write_text(
            yaml.safe_dump(case, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

    def test_initial_run_is_complete_and_verifiable(self) -> None:
        registered = self.register()
        self.assertTrue(registered["created"])

        run = self.execute_run()

        self.assertEqual("completed", run["execution"])
        self.assertEqual("initial", run["comparison"])
        self.assertEqual("complete", run["coverage"])
        self.assertEqual("not_performed", run["semantic_assessment"])
        manifest = self.load_manifest(run["id"])
        self.assertEqual("tracked_clean", manifest[0]["state"])
        self.assertIsNone(manifest[0]["snapshot"])
        verified = json.loads(
            self.run_source(
                "verify", "source-envelope", "local-docs", run["id"]
            ).stdout
        )
        self.assertTrue(verified["valid"])

    def test_same_configuration_and_same_content_are_noops(self) -> None:
        self.register()
        first = self.execute_run()
        registration = self.register()
        second = self.execute_run()

        self.assertFalse(registration["created"])
        self.assertEqual("unchanged", second["comparison"])
        self.assertEqual(first["revision"]["scoped_fingerprint"], second["cursor_before"])
        self.assertEqual(first["revision"]["scoped_fingerprint"], second["cursor_after"])

    def test_scoped_change_reports_only_the_changed_file(self) -> None:
        self.register()
        self.execute_run()
        self.write("docs/in-scope.md", "version two\n")

        changed = self.execute_run()

        self.assertEqual("changed", changed["comparison"])
        self.assertEqual(["docs/in-scope.md"], changed["changed_paths"])
        self.assertIn("content_changed", changed["change_reasons"])

    def test_commit_outside_scope_remains_unchanged(self) -> None:
        self.register()
        first = self.execute_run()
        self.write("docs/other.md", "outside changed\n")
        self.git("add", "docs/other.md")
        self.git("commit", "-qm", "outside scope")

        second = self.execute_run()

        self.assertNotEqual(first["revision"]["git_head"], second["revision"]["git_head"])
        self.assertEqual("unchanged", second["comparison"])
        self.assertEqual([], second["changed_paths"])

    def test_dirty_and_untracked_content_is_frozen(self) -> None:
        self.register("docs/in-scope.md", "docs/untracked.md")
        self.write("docs/in-scope.md", "dirty content\n")
        self.write("docs/untracked.md", "new evidence\n")

        run = self.execute_run()

        manifest = {item["path"]: item for item in self.load_manifest(run["id"])}
        self.assertEqual("tracked_dirty", manifest["docs/in-scope.md"]["state"])
        self.assertEqual("untracked", manifest["docs/untracked.md"]["state"])
        for item in manifest.values():
            snapshot = self.source_dir / "runs" / run["id"] / item["snapshot"]
            self.assertTrue(snapshot.is_file())
            self.assertEqual(item["sha256"], hashlib.sha256(snapshot.read_bytes()).hexdigest())

    def test_partial_run_does_not_advance_last_complete_cursor(self) -> None:
        self.register()
        complete = self.execute_run()
        (self.workspace / "docs/in-scope.md").unlink()

        partial = self.execute_run()
        state = self.load_yaml(self.source_dir / "state.yaml")

        self.assertEqual("completed", partial["execution"])
        self.assertEqual("partial", partial["coverage"])
        self.assertEqual("unknown", partial["comparison"])
        self.assertEqual(complete["id"], state["last_complete_run_id"])
        self.assertEqual(complete["revision"]["scoped_fingerprint"], state["last_scoped_fingerprint"])

    def test_path_escape_and_symlink_escape_are_rejected_without_writes(self) -> None:
        outside = self.base / "outside.md"
        outside.write_text("secret\n", encoding="utf-8")
        (self.workspace / "docs/link.md").symlink_to(outside)

        traversal = self.run_source(
            "register",
            "source-envelope",
            "bad-traversal",
            "--kind",
            "local_git",
            "--root",
            ".",
            "--include",
            "../outside.md",
            expected=1,
        )
        symlink = self.run_source(
            "register",
            "source-envelope",
            "bad-symlink",
            "--kind",
            "local_git",
            "--root",
            ".",
            "--include",
            "docs/link.md",
            expected=1,
        )

        self.assertIn("越界", traversal.stderr)
        self.assertIn("符号链接", symlink.stderr)
        self.assertFalse((self.case_dir / "source-runs" / "bad-traversal").exists())
        self.assertFalse((self.case_dir / "source-runs" / "bad-symlink").exists())

    def test_interruption_before_publish_preserves_state_and_is_recoverable(self) -> None:
        self.register()
        complete = self.execute_run()
        state_before = (self.source_dir / "state.yaml").read_bytes()
        interrupted = self.run_source(
            "run",
            "source-envelope",
            "local-docs",
            expected=1,
            env={"SOURCE_RUN_TEST_FAILPOINT": "before_publish"},
        )

        self.assertIn("before_publish", interrupted.stderr)
        self.assertEqual(state_before, (self.source_dir / "state.yaml").read_bytes())
        status = json.loads(
            self.run_source("status", "source-envelope", "local-docs").stdout
        )
        self.assertEqual(complete["id"], status["state"]["last_complete_run_id"])
        self.assertEqual(1, len(status["orphaned_staging"]))

    def test_runtime_failure_is_published_without_advancing_complete_state(self) -> None:
        self.register()
        complete = self.execute_run()
        state_before = (self.source_dir / "state.yaml").read_bytes()
        (self.workspace / ".git").rename(self.workspace / ".git-disabled")

        failed = self.execute_run(expected=2)

        self.assertEqual("failed", failed["execution"])
        self.assertEqual("unknown", failed["comparison"])
        self.assertEqual("unknown", failed["coverage"])
        self.assertIsNone(failed["cursor_after"])
        self.assertIn("不是 Git 仓库", failed["error"])
        self.assertEqual(state_before, (self.source_dir / "state.yaml").read_bytes())
        verified = json.loads(
            self.run_source(
                "verify", "source-envelope", "local-docs", failed["id"]
            ).stdout
        )
        self.assertTrue(verified["valid"])
        status = json.loads(
            self.run_source("status", "source-envelope", "local-docs").stdout
        )
        self.assertEqual(failed["id"], status["latest_run"]["id"])
        self.assertEqual(complete["id"], status["state"]["last_complete_run_id"])

    def test_manifest_or_snapshot_tampering_fails_verification(self) -> None:
        self.register()
        run = self.execute_run()
        manifest_path = self.source_dir / "runs" / run["id"] / "manifest.jsonl"
        manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")

        invalid = json.loads(
            self.run_source(
                "verify", "source-envelope", "local-docs", run["id"], expected=2
            ).stdout
        )

        self.assertFalse(invalid["valid"])
        self.assertTrue(any("manifest" in error for error in invalid["errors"]))

    def test_run_envelope_tampering_fails_verification(self) -> None:
        self.register()
        run = self.execute_run()
        run_path = self.source_dir / "runs" / run["id"] / "run.yaml"
        envelope = self.load_yaml(run_path)
        envelope["coverage"] = "partial"
        run_path.write_text(
            yaml.safe_dump(envelope, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

        invalid = json.loads(
            self.run_source(
                "verify", "source-envelope", "local-docs", run["id"], expected=2
            ).stdout
        )

        self.assertFalse(invalid["valid"])
        self.assertTrue(any("envelope" in error for error in invalid["errors"]))

    def test_source_configuration_tampering_blocks_new_run(self) -> None:
        self.register()
        complete = self.execute_run()
        state_before = (self.source_dir / "state.yaml").read_bytes()
        source_path = self.source_dir / "source.yaml"
        source = self.load_yaml(source_path)
        source["scope"]["include_paths"].append("docs/other.md")
        source_path.write_text(
            yaml.safe_dump(source, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

        blocked = self.run_source(
            "run", "source-envelope", "local-docs", expected=1
        )

        self.assertIn("config_fingerprint", blocked.stderr)
        self.assertEqual(state_before, (self.source_dir / "state.yaml").read_bytes())
        published = [
            path.name
            for path in (self.source_dir / "runs").iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ]
        self.assertEqual([complete["id"]], published)

    def test_state_tampering_is_reported_and_blocks_new_run(self) -> None:
        self.register()
        complete = self.execute_run()
        state_path = self.source_dir / "state.yaml"
        state = self.load_yaml(state_path)
        state["last_scoped_fingerprint"] = "0" * 64
        state_path.write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

        status = json.loads(
            self.run_source("status", "source-envelope", "local-docs").stdout
        )
        blocked = self.run_source(
            "run", "source-envelope", "local-docs", expected=1
        )

        self.assertFalse(status["state_valid"])
        self.assertTrue(any("scoped fingerprint" in item for item in status["state_errors"]))
        self.assertIn("Source state 校验失败", blocked.stderr)
        published = [
            path.name
            for path in (self.source_dir / "runs").iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ]
        self.assertEqual([complete["id"]], published)

    def test_replacing_scope_marks_configuration_change(self) -> None:
        self.register()
        self.execute_run()
        self.register("docs/in-scope.md", "docs/other.md", replace=True)

        changed = self.execute_run()

        self.assertEqual("changed", changed["comparison"])
        self.assertIn("config_changed", changed["change_reasons"])
        self.assertEqual(["docs/other.md"], changed["changed_paths"])

    def test_run_does_not_advance_task_questions_or_gates(self) -> None:
        self.prepare_open_question()
        before = (self.case_dir / "case.yaml").read_bytes()
        self.register()

        run = self.execute_run()

        self.assertEqual(before, (self.case_dir / "case.yaml").read_bytes())
        self.assertFalse(run["task_state_changed"])
        self.assertEqual("not_performed", run["semantic_assessment"])

    def test_status_recovers_source_state_without_reading_the_source(self) -> None:
        self.register()
        run = self.execute_run()
        (self.workspace / "docs/in-scope.md").unlink()

        status = json.loads(
            self.run_source("status", "source-envelope", "local-docs").stdout
        )

        self.assertEqual("local-docs", status["source"]["id"])
        self.assertEqual(run["id"], status["latest_run"]["id"])
        self.assertEqual("complete", status["latest_run"]["coverage"])
        self.assertEqual("not_performed", status["semantic_assessment"])

    def test_task_answer_accepts_only_existing_valid_source_run_uri(self) -> None:
        self.prepare_open_question()
        self.register()
        run = self.execute_run()
        uri = run["uri"]

        answered = self.run_task(
            "answer",
            "source-envelope",
            "q-001",
            "--answer",
            "声明范围已完整读取，但知识充分性仍需语义判断",
            "--source",
            uri,
        )

        self.assertEqual(uri, json.loads(answered.stdout)["source_run_uri"])

    def test_invalid_source_run_uri_fails_before_ledger_write(self) -> None:
        self.prepare_open_question()
        before = {
            path.name: path.read_bytes()
            for path in (
                self.case_dir / "case.yaml",
                self.case_dir / "events.jsonl",
                self.case_dir / "evidence.jsonl",
            )
        }

        invalid = self.run_task(
            "answer",
            "source-envelope",
            "q-001",
            "--answer",
            "不应写入",
            "--source",
            "source-run://source-envelope/local-docs/missing-run",
            expected=1,
        )

        self.assertIn("SourceRun", invalid.stderr)
        after = {
            path.name: path.read_bytes()
            for path in (
                self.case_dir / "case.yaml",
                self.case_dir / "events.jsonl",
                self.case_dir / "evidence.jsonl",
            )
        }
        self.assertEqual(before, after)

    def test_tampered_source_run_invalidates_answer_traceability(self) -> None:
        self.prepare_open_question()
        self.register()
        run = self.execute_run()
        self.run_task(
            "answer",
            "source-envelope",
            "q-001",
            "--answer",
            "来源已读取",
            "--source",
            run["uri"],
        )
        manifest_path = self.source_dir / "runs" / run["id"] / "manifest.jsonl"
        manifest_path.write_text("{}\n", encoding="utf-8")

        checked = json.loads(
            self.run_task("check", "source-envelope", expected=2).stdout
        )
        report = (self.case_dir / "outputs/readiness-report.md").read_text(encoding="utf-8")

        self.assertFalse(checked["decision_ready"])
        self.assertIn("answers_traceable", report)
        self.assertIn("q-001", report)


if __name__ == "__main__":
    unittest.main()
