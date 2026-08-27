from __future__ import annotations

import asyncio
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml


REPOSITORY = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_brain_console.executors import ExecutionResult  # noqa: E402
from omni_brain_console.registry import AgentRegistry  # noqa: E402
from omni_brain_console.service import WorkbenchService  # noqa: E402
from omni_brain_console.storage import RunStore  # noqa: E402
from omni_brain_console.worktrees import WorktreeManager  # noqa: E402


class FakeExecutor:
    async def run(
        self,
        *,
        executor: str,
        worktree: Path,
        prompt: str,
        final_path: Path,
        model: str | None,
        session_id: str | None,
        run_id: str,
        on_event: Any,
        on_process: Any,
    ) -> ExecutionResult:
        await on_event(
            {
                "timestamp": "2026-08-26T00:00:00Z",
                "source": executor,
                "channel": "stdout",
                "type": "agent.message",
                "summary": "正在处理固定任务",
                "payload": {"text": "正在处理固定任务"},
            }
        )
        if "改进当前仓库中的 Agent Harness" in prompt:
            (worktree / "candidate-improvement.md").write_text(
                "evidence-backed harness candidate\n", encoding="utf-8"
            )
        final_path.write_text("任务已经完成，并保留了可见证据。\n", encoding="utf-8")
        return ExecutionResult(0, session_id or f"session-{run_id}", "任务已经完成")


class FakeJudge:
    def __init__(self, store: RunStore) -> None:
        self.store = store

    async def evaluate(self, run: dict[str, Any], model: str | None = None) -> dict[str, Any]:
        score = 82 if run.get("run_role") == "candidate" else 62
        return {
            "success": score >= 80,
            "completion_score": score,
            "process_score": score,
            "summary": "候选有可见提升" if score >= 80 else "基线仍有明确缺口",
            "strengths": ["保留了运行证据"],
            "problems": [] if score >= 80 else ["缺少稳定的 Harness 指引"],
            "evidence_refs": ["event:2", "final.md"],
            "improvement_suggestion": "把失败证据转化为最小 Harness 修改",
            "judge": "fake",
        }


class AgentConsoleServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.project = self.base / "design"
        self.release = self.base / "release"
        self.project.mkdir()
        self.release.mkdir()
        self._git("init", "-q", "-b", "release/harness")
        self._git("config", "user.email", "console-test@example.com")
        self._git("config", "user.name", "Console Test")
        (self.release / "AGENTS.md").write_text("# Release Harness\n", encoding="utf-8")
        (self.release / "harness.yaml").write_text(
            yaml.safe_dump(
                {
                    "release_channel": "release",
                    "capabilities": {
                        "knowledge_query_and_context": {
                            "adoption": "verified_at_test_slice",
                            "entrypoints": ["AGENTS.md"],
                            "limits": ["test only"],
                        }
                    },
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        self._git("add", ".")
        self._git("commit", "-qm", "release seed")

        registry_path = self.project / "agent-registry.yaml"
        registry_path.write_text(
            yaml.safe_dump(
                {
                    "source": {
                        "repository": str(self.release),
                        "revision": "release/harness",
                        "manifest": "harness.yaml",
                    },
                    "agents": [
                        {
                            "id": "knowledge-assistant",
                            "name": "知识问答 Agent",
                            "category": "知识管理",
                            "description": "测试能力",
                            "capability_keys": ["knowledge_query_and_context"],
                            "default_executor": "codex",
                        }
                    ],
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        dataset = self.project / "eval" / "datasets" / "skill_execution" / "case.yaml"
        dataset.parent.mkdir(parents=True)
        dataset.write_text(
            yaml.safe_dump(
                {
                    "id": "CONSOLE_CASE",
                    "title": "工作台固定用例",
                    "cases": [
                        {
                            "id": "visible-result",
                            "prompt": "完成一项可判断成功与否的任务",
                            "expected": {"must_include": ["证据"]},
                        }
                    ],
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        store = RunStore(self.base / "state")
        self.service = WorkbenchService(
            registry=AgentRegistry(self.project, registry_path),
            store=store,
            worktrees=WorktreeManager(self.base / "runs"),
            executor=FakeExecutor(),  # type: ignore[arg-type]
            judge=FakeJudge(store),  # type: ignore[arg-type]
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> None:
        result = subprocess.run(
            ["git", *arguments],
            cwd=self.release,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_registry_run_trace_diff_and_evaluation(self) -> None:
        async def scenario() -> None:
            agents = self.service.agents()
            self.assertEqual("verified", agents[0]["state"])
            cases = self.service.registry.list_eval_cases()
            self.assertEqual("CONSOLE_CASE:visible-result", cases[0]["id"])

            run = await self.service.start_run(
                agent_id="knowledge-assistant",
                prompt="完成可见任务",
            )
            completed = await self.service._wait_for_run(run["id"])
            self.assertEqual("completed", completed["status"])
            self.assertTrue(Path(completed["worktree"]).is_dir())
            self.assertNotEqual(self.release, Path(completed["worktree"]))
            self.assertGreaterEqual(completed["event_count"], 3)
            self.assertIn("任务已经完成", self.service.run_detail(run["id"])["final_output"])

            await self.service.evaluate_run(run["id"])
            await self.service._tasks[f"judge:{run['id']}"]
            evaluated = self.service.run_detail(run["id"])
            self.assertEqual("completed", evaluated["evaluation_status"])
            self.assertEqual(62, evaluated["evaluation"]["completion_score"])

            worktree = Path(evaluated["worktree"])
            released = await self.service.release_worktree(run["id"])
            self.assertFalse(released["workspace_available"])
            self.assertFalse(worktree.exists())
            self.assertTrue(released["workspace_released_at"])

        asyncio.run(scenario())

    def test_linear_evolution_keeps_candidate_runs_and_revision(self) -> None:
        async def scenario() -> None:
            evolution = await self.service.start_evolution(
                agent_id="knowledge-assistant",
                prompt="",
                eval_case_id="CONSOLE_CASE:visible-result",
                max_iterations=1,
            )
            await self.service._evolution_tasks[evolution["id"]]
            completed = self.service.store.get_evolution(evolution["id"])
            self.assertIsNotNone(completed)
            assert completed is not None
            self.assertEqual("completed", completed["status"])
            self.assertEqual(62, completed["baseline"]["score"])
            self.assertEqual(1, len(completed["candidates"]))
            candidate = completed["candidates"][0]
            self.assertTrue(candidate["accepted"])
            self.assertEqual(20, candidate["delta"])
            self.assertNotEqual(completed["seed_revision"], completed["best_revision"])
            related = [
                run for run in self.service.store.list_runs()
                if run.get("evolution_id") == evolution["id"]
            ]
            self.assertEqual({"baseline", "optimizer", "candidate"}, {run["run_role"] for run in related})

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
