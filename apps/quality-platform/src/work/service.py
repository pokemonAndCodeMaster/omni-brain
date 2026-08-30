from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.agent_runtime import AgentRunService, WorktreeManager
from src.api.schemas.work import WorkCreate, WorkEvidenceCreate

from .repository import WorkRepository


STEP_DEFINITIONS = (
    (
        "knowledge_context",
        "知识上下文",
        "取得最低充分的正式知识、源码事实、未知与冲突。",
        "agent",
        "knowledge-assistant",
        "codex",
    ),
    (
        "solution",
        "方案",
        "形成可施工方案和验证路径，等待人的方案 Gate。",
        "agent",
        "solution-agent",
        "codex",
    ),
    (
        "development",
        "开发",
        "在共享 Work worktree 中实现并提交变化。",
        "agent",
        "development-agent",
        "codex",
    ),
    (
        "verification",
        "验证",
        "独立运行真实验证并核对用户结果。",
        "agent",
        "review-agent",
        "opencode",
    ),
    (
        "review",
        "审查",
        "对照需求、方案、代码与证据形成交付审查。",
        "agent",
        "review-agent",
        "opencode",
    ),
    (
        "acceptance",
        "人工接受",
        "由人基于最终 Commit、验证和审查证据决定是否接受。",
        "human",
        None,
        None,
    ),
)


def _git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        reason = (result.stderr or result.stdout).strip()
        raise RuntimeError(reason or f"git {' '.join(args)} 执行失败")
    return result.stdout.strip()


class WorkService:
    def __init__(
        self,
        *,
        repository: WorkRepository,
        run_service: AgentRunService,
        worktrees: WorktreeManager,
    ) -> None:
        self.repository = repository
        self.run_service = run_service
        self.worktrees = worktrees

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"

    def create_for_requirement(
        self,
        *,
        requirement_id: str,
        payload: WorkCreate,
        actor_id: str,
    ) -> dict[str, Any]:
        development_agent = self.run_service.registry.get("development-agent")
        repository = Path(
            payload.repository_path or str(development_agent["repository"])
        ).expanduser().resolve()
        if not repository.is_dir():
            raise ValueError(f"目标仓库不存在：{repository}")
        base_revision = payload.base_revision or str(development_agent["revision"])
        base_commit = _git(repository, "rev-parse", base_revision)
        work_id = self._id("work")
        workspace = self.worktrees.create_work(work_id, repository, base_commit)
        steps = []
        for position, definition in enumerate(STEP_DEFINITIONS, 1):
            step_key, title, description, actor_kind, agent_id, executor = definition
            steps.append(
                {
                    "id": self._id("step"),
                    "position": position,
                    "step_key": step_key,
                    "title": title,
                    "description": description,
                    "actor_kind": actor_kind,
                    "agent_id": agent_id,
                    "default_executor": executor,
                    "status": "ready" if position == 1 else "pending",
                }
            )
        try:
            return self.repository.create(
                work_id=work_id,
                plan_id=self._id("plan"),
                requirement_id=requirement_id,
                title=payload.title,
                owner_id=payload.owner_id,
                reviewer_id=payload.reviewer_id,
                timebox_start=payload.timebox_start,
                timebox_end=payload.timebox_end,
                repository_path=str(repository),
                base_commit=base_commit,
                worktree_path=workspace["path"],
                branch_name=workspace["branch"],
                actor_id=actor_id,
                steps=steps,
            )
        except Exception as exc:
            try:
                self.worktrees.discard(
                    repository=repository,
                    path=Path(workspace["path"]),
                    branch=workspace["branch"],
                )
            except Exception as cleanup_error:
                raise RuntimeError(
                    f"{exc}；新建 worktree 自动清理失败：{cleanup_error}"
                ) from exc
            raise

    def detail(self, work_id: str) -> dict[str, Any]:
        result = self.repository.detail(work_id)
        if result is None:
            raise KeyError(work_id)
        return result

    async def start_step(
        self,
        *,
        work_id: str,
        step_id: str,
        executor: str | None,
        model: str | None,
        instruction: str,
        actor_id: str,
    ) -> dict[str, Any]:
        work = self.detail(work_id)
        step = next((item for item in work["plan"]["steps"] if item["id"] == step_id), None)
        if step is None:
            raise KeyError(step_id)
        if step["actor_kind"] != "agent":
            raise ValueError("人工接受步骤不能启动 Agent Run")
        if step["display_status"] == "blocked":
            raise ValueError("前序步骤尚未完成")
        if step["display_status"] == "running":
            raise ValueError("该步骤已有活跃 Run，请等待结束或先取消")
        if step["display_status"] == "completed":
            raise ValueError("步骤已经完成")
        requirement = work["requirement_title"]
        context = self.repository.step_context(work_id, int(step["position"]))
        prompt = (
            "你正在执行平台中一条有界 Work 的固定开发步骤。\n"
            f"Work：{work['title']}（{work_id}）\n"
            f"来源 Requirement：{requirement}（{work['requirement_revision_id']}）\n"
            f"冻结的 Requirement 内容：{context['requirement_content']}\n"
            f"步骤：{step['title']} / {step['step_key']}\n"
            f"步骤契约：{step['description']}\n"
            f"固定 base commit：{work['base_commit']}\n"
            f"共享分支：{work['branch_name']}\n"
            f"上游确认与输出：{context['upstream']}\n"
            "遵守仓库 AGENTS.md；不要 Push、创建 PR/MR 或 Merge。"
        )
        if instruction.strip():
            prompt += f"\n人的补充：{instruction.strip()}"
        run = await self.run_service.start(
            agent_id=str(step["agent_id"]),
            prompt=prompt,
            title=f"{work['title']} · {step['title']}",
            model=model,
            actor_id=actor_id,
            executor=executor or str(step["default_executor"]),
            subject_type="work",
            subject_id=work_id,
            trigger_action=str(step["step_key"]),
            work_id=work_id,
            plan_step_id=step_id,
            repository_path=str(work["repository_path"]),
            base_revision=str(work["base_commit"]),
            workspace_path=str(work["worktree_path"]),
            branch_name=str(work["branch_name"]),
        )
        self.repository.mark_started(work_id)
        return run

    def record_evidence(
        self,
        *,
        work_id: str,
        payload: WorkEvidenceCreate,
        actor_id: str,
    ) -> dict[str, Any]:
        work = self.detail(work_id)
        git_evidence = self.worktrees.delivery_evidence(
            Path(str(work["worktree_path"])),
            str(work["base_commit"]),
        )
        previous = work.get("latest_evidence")
        merged = dict(previous["payload"]) if previous else {}
        for key, value in payload.model_dump().items():
            if value is not None:
                merged[key] = value.strip() if isinstance(value, str) else value
        merged.update(git_evidence)
        merged["base_commit"] = work["base_commit"]
        return self.repository.add_evidence(
            evidence_id=self._id("evidence"),
            work_id=work_id,
            payload=merged,
            actor_id=actor_id,
        )

    def complete_step(
        self,
        *,
        work_id: str,
        step_id: str,
        note: str,
        actor_id: str,
    ) -> dict[str, Any]:
        work = self.detail(work_id)
        step = next(
            (candidate for candidate in work["plan"]["steps"] if candidate["id"] == step_id),
            None,
        )
        if step is None:
            raise KeyError(step_id)
        if step["step_key"] == "development":
            if step["display_status"] != "awaiting_gate":
                raise ValueError("开发步骤需要最近一次 Run 成功后才能确认完成")
            self.worktrees.commit_delivery(
                Path(str(work["worktree_path"])),
                str(work["base_commit"]),
                f"agent: complete {work_id} development",
            )
        return self.repository.complete_step(
            work_id=work_id,
            step_id=step_id,
            note=note,
            actor_id=actor_id,
        )

    def decide(
        self,
        *,
        work_id: str,
        decision_type: str,
        reason: str,
        actor_id: str,
    ) -> dict[str, Any]:
        if decision_type == "accept":
            work = self.detail(work_id)
            evidence = work.get("latest_evidence")
            if evidence is not None:
                recorded = evidence["payload"]
                current = self.worktrees.delivery_evidence(
                    Path(str(work["worktree_path"])),
                    str(work["base_commit"]),
                )
                git_fields = (
                    "head_commit",
                    "branch_name",
                    "worktree_status",
                    "diff_summary",
                )
                if any(recorded.get(field) != current.get(field) for field in git_fields):
                    raise ValueError("当前 Git 状态已变化，请刷新并重新保存证据后再接受")
        return self.repository.decide(
            decision_id=self._id("work-decision"),
            work_id=work_id,
            decision_type=decision_type,
            reason=reason,
            actor_id=actor_id,
        )
