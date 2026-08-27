from __future__ import annotations

import asyncio
import secrets
from collections import Counter
from pathlib import Path
from typing import Any

from .executors import CliExecutor
from .judge import JudgeService
from .registry import AgentRegistry
from .storage import RunStore
from .utils import safe_id, utc_now
from .worktrees import WorktreeManager


TERMINAL_STATES = {"completed", "failed", "cancelled", "interrupted"}


class WorkbenchService:
    def __init__(
        self,
        *,
        registry: AgentRegistry,
        store: RunStore,
        worktrees: WorktreeManager,
        executor: CliExecutor | None = None,
        judge: JudgeService | None = None,
    ) -> None:
        self.registry = registry
        self.store = store
        self.worktrees = worktrees
        self.executor = executor or CliExecutor()
        self.judge = judge or JudgeService(store)
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._evolution_tasks: dict[str, asyncio.Task[None]] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._guard = asyncio.Lock()
        self._repair_interrupted_runs()

    def _repair_interrupted_runs(self) -> None:
        for run in self.store.list_runs():
            if run.get("status") in {"queued", "preparing", "running", "evaluating"}:
                self.store.update_run(
                    run["id"],
                    status="interrupted",
                    updated_at=utc_now(),
                    error="控制服务重启，原进程状态不可恢复；可在原 session 上续接。",
                )
            elif run.get("evaluation_status") == "running":
                self.store.update_run(
                    run["id"],
                    evaluation_status="interrupted",
                    evaluation_error="控制服务重启，原 Judge 进程状态不可恢复；可以重新发起评测。",
                    updated_at=utc_now(),
                )
        for evolution in self.store.list_evolutions():
            if evolution.get("status") in {"queued", "running"}:
                self.store.update_evolution(
                    evolution["id"],
                    status="interrupted",
                    stage="interrupted",
                    error="控制服务重启，线性进化已停止；已经完成的 Run 和候选仍然保留。",
                    updated_at=utc_now(),
                )

    def _new_id(self, prefix: str) -> str:
        stamp = utc_now().replace("-", "").replace(":", "").replace("T", "-").replace("Z", "")
        return safe_id(f"{prefix}-{stamp}-{secrets.token_hex(3)}")

    def agents(self) -> list[dict[str, Any]]:
        counts = Counter(run.get("agent_id") for run in self.store.list_runs())
        return self.registry.list_agents(dict(counts))

    def _has_active_task(self) -> bool:
        return any(not task.done() for task in self._tasks.values()) or any(
            not task.done() for task in self._evolution_tasks.values()
        )

    async def start_run(
        self,
        *,
        agent_id: str,
        prompt: str,
        executor: str | None = None,
        model: str | None = None,
        eval_case_id: str | None = None,
        expected: Any = None,
    ) -> dict[str, Any]:
        async with self._guard:
            if self._has_active_task():
                raise RuntimeError("v0 同一时间只允许运行一个受管任务")
            return self._start_run(
                agent_id=agent_id,
                prompt=prompt,
                executor=executor,
                model=model,
                eval_case_id=eval_case_id,
                expected=expected,
            )

    def _start_run(
        self,
        *,
        agent_id: str,
        prompt: str,
        executor: str | None = None,
        model: str | None = None,
        eval_case_id: str | None = None,
        expected: Any = None,
        revision: str | None = None,
        evolution_id: str | None = None,
        run_role: str = "task",
    ) -> dict[str, Any]:
        agent = self.registry.get_agent(agent_id)
        if eval_case_id:
            case = self.registry.get_eval_case(eval_case_id)
            if not prompt:
                prompt = str(case.get("prompt") or "")
            if expected is None:
                expected = case.get("expected")
        if not prompt.strip():
            raise ValueError("任务内容不能为空")
        run_id = self._new_id("run")
        now = utc_now()
        record = {
            "id": run_id,
            "agent_id": agent_id,
            "agent_name": agent["name"],
            "agent_revision": revision or agent["revision"],
            "repository": agent["repository"],
            "executor": executor or agent.get("default_executor", "codex"),
            "model": model,
            "prompt": prompt.strip(),
            "expected": expected,
            "eval_case_id": eval_case_id,
            "evolution_id": evolution_id,
            "run_role": run_role,
            "status": "queued",
            "evaluation_status": "not_started",
            "created_at": now,
            "updated_at": now,
            "session_id": None,
            "worktree": None,
            "branch": None,
            "base_revision": None,
            "head_revision": None,
            "exit_code": None,
            "error": None,
            "event_count": 0,
        }
        self.store.create_run(record)
        self.store.write_artifact(run_id, "prompt.md", prompt.strip() + "\n")
        task = asyncio.create_task(self._execute(record, prompt.strip(), resume=False))
        self._tasks[run_id] = task
        return record

    async def _execute(self, record: dict[str, Any], prompt: str, resume: bool) -> None:
        run_id = record["id"]
        seq = len(self.store.events(run_id))

        async def on_event(event: dict[str, Any]) -> None:
            nonlocal seq
            seq += 1
            event["seq"] = seq
            self.store.append_event(run_id, event)
            self.store.update_run(run_id, event_count=seq, updated_at=utc_now())

        try:
            current = self.store.get_run(run_id) or record
            if resume:
                worktree_path = Path(str(current["worktree"]))
            else:
                self.store.update_run(run_id, status="preparing", updated_at=utc_now())
                info = await asyncio.to_thread(
                    self.worktrees.create,
                    run_id,
                    Path(str(current["repository"])),
                    str(current["agent_revision"]),
                )
                worktree_path = Path(info["path"])
                self.store.update_run(
                    run_id,
                    worktree=info["path"],
                    branch=info["branch"],
                    base_revision=info["base_revision"],
                    status="running",
                    updated_at=utc_now(),
                )
            await on_event(
                {
                    "timestamp": utc_now(),
                    "source": "workbench",
                    "channel": "lifecycle",
                    "type": "run.started" if not resume else "run.resumed",
                    "summary": f"在 {worktree_path} 启动 {current['executor']}",
                    "payload": {"worktree": str(worktree_path), "resume": resume},
                }
            )
            final_path = self.store.run_dir(run_id) / "final.md"
            result = await self.executor.run(
                executor=str(current["executor"]),
                worktree=worktree_path,
                prompt=prompt,
                final_path=final_path,
                model=current.get("model"),
                session_id=current.get("session_id") if resume else None,
                run_id=run_id,
                on_event=on_event,
                on_process=lambda process: self._processes.__setitem__(run_id, process),
            )
            snapshot = await asyncio.to_thread(self.worktrees.snapshot, worktree_path)
            self.store.write_artifact(run_id, "workspace.patch", snapshot["diff"])
            latest = self.store.get_run(run_id) or current
            status = "cancelled" if latest.get("cancel_requested") else (
                "completed" if result.exit_code == 0 else "failed"
            )
            self.store.update_run(
                run_id,
                status=status,
                exit_code=result.exit_code,
                session_id=result.session_id,
                head_revision=snapshot["head"],
                workspace_status=snapshot["status"],
                final_preview=result.last_message[:800],
                error=result.error_message if result.exit_code != 0 else None,
                updated_at=utc_now(),
            )
            await on_event(
                {
                    "timestamp": utc_now(),
                    "source": "workbench",
                    "channel": "lifecycle",
                    "type": f"run.{status}",
                    "summary": f"运行{status}，退出码 {result.exit_code}",
                    "payload": {"exit_code": result.exit_code},
                }
            )
        except Exception as exc:
            self.store.update_run(
                run_id,
                status="failed",
                error=str(exc),
                updated_at=utc_now(),
            )
            await on_event(
                {
                    "timestamp": utc_now(),
                    "source": "workbench",
                    "channel": "lifecycle",
                    "type": "run.failed",
                    "summary": str(exc),
                    "payload": {"error": str(exc)},
                }
            )
        finally:
            self._processes.pop(run_id, None)

    async def stop_run(self, run_id: str) -> dict[str, Any]:
        process = self._processes.get(run_id)
        run = self.store.get_run(run_id)
        if not run:
            raise KeyError(run_id)
        self.store.update_run(run_id, cancel_requested=True, updated_at=utc_now())
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
        return self.store.get_run(run_id) or run

    async def resume_run(self, run_id: str, prompt: str) -> dict[str, Any]:
        async with self._guard:
            if self._has_active_task():
                raise RuntimeError("v0 同一时间只允许运行一个受管任务")
            run = self.store.get_run(run_id)
            if not run:
                raise KeyError(run_id)
            if run.get("status") not in TERMINAL_STATES:
                raise RuntimeError("只有已结束的 Run 可以续接")
            if not run.get("session_id"):
                raise RuntimeError("该 Run 没有可恢复的 session id")
            self.store.write_artifact(
                run_id,
                f"resume-{len(self.store.events(run_id)) + 1}.md",
                prompt.strip() + "\n",
            )
            run = self.store.update_run(
                run_id,
                status="queued",
                cancel_requested=False,
                error=None,
                updated_at=utc_now(),
            )
            task = asyncio.create_task(self._execute(run, prompt.strip(), resume=True))
            self._tasks[run_id] = task
            return run

    async def evaluate_run(self, run_id: str, model: str | None = None) -> dict[str, Any]:
        async with self._guard:
            if self._has_active_task():
                raise RuntimeError("请等待当前受管任务结束后再评测")
            run = self.store.get_run(run_id)
            if not run:
                raise KeyError(run_id)
            if run.get("status") not in TERMINAL_STATES:
                raise RuntimeError("只能评测已经结束的 Run")
            self.store.update_run(run_id, evaluation_status="running", updated_at=utc_now())

            async def work() -> None:
                try:
                    result = await self.judge.evaluate(run, model)
                    self.store.update_run(
                        run_id,
                        evaluation_status="completed",
                        evaluation=result,
                        updated_at=utc_now(),
                    )
                except Exception as exc:
                    self.store.update_run(
                        run_id,
                        evaluation_status="failed",
                        evaluation_error=str(exc),
                        updated_at=utc_now(),
                    )

            task = asyncio.create_task(work())
            self._tasks[f"judge:{run_id}"] = task
            return self.store.get_run(run_id) or run

    async def _wait_for_run(self, run_id: str) -> dict[str, Any]:
        task = self._tasks.get(run_id)
        if task:
            await task
        run = self.store.get_run(run_id)
        if not run:
            raise KeyError(run_id)
        return run

    async def _evaluate_now(self, run_id: str, model: str | None = None) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        if not run:
            raise KeyError(run_id)
        self.store.update_run(run_id, evaluation_status="running", updated_at=utc_now())
        try:
            result = await self.judge.evaluate(run, model)
            self.store.update_run(
                run_id,
                evaluation_status="completed",
                evaluation=result,
                updated_at=utc_now(),
            )
            return result
        except Exception as exc:
            self.store.update_run(
                run_id,
                evaluation_status="failed",
                evaluation_error=str(exc),
                updated_at=utc_now(),
            )
            raise

    @staticmethod
    def _score(evaluation: dict[str, Any]) -> float:
        completion = float(evaluation.get("completion_score", 0))
        process = float(evaluation.get("process_score", 0))
        return round((completion + process) / 2, 1)

    @staticmethod
    def _optimization_prompt(
        *,
        target_prompt: str,
        previous_evaluation: dict[str, Any],
        iteration: int,
    ) -> str:
        problems = "\n".join(f"- {item}" for item in previous_evaluation.get("problems", []))
        suggestion = previous_evaluation.get("improvement_suggestion") or "没有单独建议"
        return f"""你正在改进当前仓库中的 Agent Harness，而不是重新回答原任务。

这是线性进化的第 {iteration} 个候选。只根据下面一次真实运行的失败证据，做一个最小、可解释、可复用的 Harness 改进。优先修改直接影响行为的 AGENTS.md、Skill、配置或其测试；不要修改产品业务代码，不要为单个答案写硬编码特例，也不要扩建通用平台。完成后运行与修改相称的验证，并在最终回答中说明改了什么、对应哪个问题、验证结果和仍有何边界。

原任务：
{target_prompt}

上轮评测摘要：
{previous_evaluation.get('summary', '')}

上轮问题：
{problems or '- 未列出具体问题'}

改进建议：
{suggestion}
"""

    async def start_evolution(
        self,
        *,
        agent_id: str,
        prompt: str,
        eval_case_id: str | None = None,
        executor: str | None = None,
        model: str | None = None,
        judge_model: str | None = None,
        max_iterations: int = 1,
    ) -> dict[str, Any]:
        async with self._guard:
            if self._has_active_task():
                raise RuntimeError("v0 同一时间只允许运行一个受管任务或进化")
            agent = self.registry.get_agent(agent_id)
            expected: Any = None
            if eval_case_id:
                case = self.registry.get_eval_case(eval_case_id)
                if not prompt:
                    prompt = str(case.get("prompt") or "")
                expected = case.get("expected")
            if not prompt.strip():
                raise ValueError("进化目标不能为空")
            iterations = max(1, min(int(max_iterations), 3))
            evolution_id = self._new_id("evo")
            now = utc_now()
            record = {
                "id": evolution_id,
                "agent_id": agent_id,
                "agent_name": agent["name"],
                "prompt": prompt.strip(),
                "expected": expected,
                "eval_case_id": eval_case_id,
                "executor": executor or agent.get("default_executor", "codex"),
                "model": model,
                "judge_model": judge_model,
                "max_iterations": iterations,
                "status": "queued",
                "stage": "queued",
                "created_at": now,
                "updated_at": now,
                "seed_revision": agent["revision"],
                "best_revision": agent["revision"],
                "baseline": None,
                "candidates": [],
                "error": None,
            }
            self.store.create_evolution(record)
            task = asyncio.create_task(self._run_evolution(record))
            self._evolution_tasks[evolution_id] = task
            return record

    async def _run_evolution(self, evolution: dict[str, Any]) -> None:
        evolution_id = evolution["id"]
        try:
            self.store.update_evolution(
                evolution_id,
                status="running",
                stage="baseline_running",
                updated_at=utc_now(),
            )
            baseline = self._start_run(
                agent_id=evolution["agent_id"],
                prompt=evolution["prompt"],
                executor=evolution["executor"],
                model=evolution.get("model"),
                eval_case_id=evolution.get("eval_case_id"),
                expected=evolution.get("expected"),
                revision=evolution["seed_revision"],
                evolution_id=evolution_id,
                run_role="baseline",
            )
            baseline = await self._wait_for_run(baseline["id"])
            if baseline["status"] != "completed":
                raise RuntimeError(f"基线运行未完成：{baseline['status']}")
            self.store.update_evolution(
                evolution_id,
                stage="baseline_evaluating",
                baseline={"run_id": baseline["id"], "evaluation": None, "score": None},
                updated_at=utc_now(),
            )
            baseline_evaluation = await self._evaluate_now(
                baseline["id"], evolution.get("judge_model")
            )
            best_score = self._score(baseline_evaluation)
            best_revision = evolution["seed_revision"]
            best_evaluation = baseline_evaluation
            self.store.update_evolution(
                evolution_id,
                baseline={
                    "run_id": baseline["id"],
                    "evaluation": baseline_evaluation,
                    "score": best_score,
                },
                best_revision=best_revision,
                updated_at=utc_now(),
            )

            candidates: list[dict[str, Any]] = []
            previous_evaluation = baseline_evaluation
            for iteration in range(1, int(evolution["max_iterations"]) + 1):
                self.store.update_evolution(
                    evolution_id,
                    stage=f"candidate_{iteration}_improving",
                    updated_at=utc_now(),
                )
                optimizer = self._start_run(
                    agent_id=evolution["agent_id"],
                    prompt=self._optimization_prompt(
                        target_prompt=evolution["prompt"],
                        previous_evaluation=previous_evaluation,
                        iteration=iteration,
                    ),
                    executor="codex",
                    model=evolution.get("model"),
                    revision=best_revision,
                    evolution_id=evolution_id,
                    run_role="optimizer",
                )
                optimizer = await self._wait_for_run(optimizer["id"])
                if optimizer["status"] != "completed":
                    raise RuntimeError(f"候选 {iteration} 改进运行未完成：{optimizer['status']}")
                candidate_revision = best_revision
                has_changes = bool(str(optimizer.get("workspace_status") or "").strip())
                if has_changes:
                    committed = await self.commit_run(
                        optimizer["id"], f"agent-console: evolution {evolution_id} candidate {iteration}"
                    )
                    candidate_revision = str(committed["head_revision"])

                self.store.update_evolution(
                    evolution_id,
                    stage=f"candidate_{iteration}_evaluating",
                    updated_at=utc_now(),
                )
                target = self._start_run(
                    agent_id=evolution["agent_id"],
                    prompt=evolution["prompt"],
                    executor=evolution["executor"],
                    model=evolution.get("model"),
                    eval_case_id=evolution.get("eval_case_id"),
                    expected=evolution.get("expected"),
                    revision=candidate_revision,
                    evolution_id=evolution_id,
                    run_role="candidate",
                )
                target = await self._wait_for_run(target["id"])
                if target["status"] != "completed":
                    raise RuntimeError(f"候选 {iteration} 重跑未完成：{target['status']}")
                evaluation = await self._evaluate_now(target["id"], evolution.get("judge_model"))
                score = self._score(evaluation)
                accepted = has_changes and score > best_score
                candidate = {
                    "iteration": iteration,
                    "optimizer_run_id": optimizer["id"],
                    "evaluation_run_id": target["id"],
                    "parent_revision": best_revision,
                    "revision": candidate_revision,
                    "has_changes": has_changes,
                    "change_summary": optimizer.get("final_preview", ""),
                    "workspace_patch": self.store.artifact_text(
                        optimizer["id"], "workspace.patch", 80_000
                    ),
                    "evaluation": evaluation,
                    "score": score,
                    "delta": round(score - best_score, 1),
                    "accepted": accepted,
                }
                candidates.append(candidate)
                if accepted:
                    best_score = score
                    best_revision = candidate_revision
                    best_evaluation = evaluation
                previous_evaluation = best_evaluation
                self.store.update_evolution(
                    evolution_id,
                    candidates=candidates,
                    best_revision=best_revision,
                    updated_at=utc_now(),
                )

            self.store.update_evolution(
                evolution_id,
                status="completed",
                stage="completed",
                best_revision=best_revision,
                updated_at=utc_now(),
            )
        except Exception as exc:
            self.store.update_evolution(
                evolution_id,
                status="failed",
                stage="failed",
                error=str(exc),
                updated_at=utc_now(),
            )

    async def commit_run(self, run_id: str, message: str) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        if not run or not run.get("worktree"):
            raise KeyError(run_id)
        commit = await asyncio.to_thread(self.worktrees.commit, Path(run["worktree"]), message)
        snapshot = await asyncio.to_thread(self.worktrees.snapshot, Path(run["worktree"]))
        return self.store.update_run(
            run_id,
            head_revision=commit,
            commit=commit,
            workspace_status=snapshot["status"],
            updated_at=utc_now(),
        )

    async def release_worktree(self, run_id: str) -> dict[str, Any]:
        async with self._guard:
            if self._has_active_task():
                raise RuntimeError("请等待当前受管任务结束后再释放工作区")
            run = self.store.get_run(run_id)
            if not run or not run.get("worktree"):
                raise KeyError(run_id)
            if run.get("status") not in TERMINAL_STATES:
                raise RuntimeError("只能释放已经结束的 Run 工作区")
            if run.get("workspace_released_at"):
                return run
            await asyncio.to_thread(self.worktrees.release, Path(run["worktree"]))
            return self.store.update_run(
                run_id,
                workspace_available=False,
                workspace_released_at=utc_now(),
                updated_at=utc_now(),
            )

    def run_detail(self, run_id: str) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        if not run:
            raise KeyError(run_id)
        run = dict(run)
        run["final_output"] = self.store.artifact_text(run_id, "final.md")
        run["workspace_patch"] = self.store.artifact_text(run_id, "workspace.patch")
        return run
