from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.agent_runtime import AgentRunRepository, AgentRunService
from src.api.schemas.collaboration import RequirementContent, RequirementDraft

from .repository import CollaborationRepository


ACTION_AGENTS = {
    "knowledge_context": "knowledge-assistant",
    "shape_requirement": "solution-agent",
}


def strict_output_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Normalize Pydantic JSON Schema to the strict structured-output subset."""

    result = deepcopy(schema)

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("default", None)
            properties = value.get("properties")
            if isinstance(properties, dict):
                value["required"] = list(properties)
                value["additionalProperties"] = False
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(result)
    return result


class CollaborationService:
    def __init__(
        self,
        *,
        repository: CollaborationRepository,
        run_service: AgentRunService,
        run_repository: AgentRunRepository,
    ) -> None:
        self.repository = repository
        self.run_service = run_service
        self.run_repository = run_repository

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"

    def create_idea(
        self,
        *,
        title: str,
        raw_content: str,
        domain_key: str | None,
        actor_id: str,
    ) -> dict[str, Any]:
        idea_id = self._id("idea")
        self.repository.create_idea(
            idea_id=idea_id,
            thread_id=self._id("thread"),
            title=title,
            raw_content=raw_content,
            domain_key=domain_key,
            actor_id=actor_id,
        )
        result = self.repository.get_idea(idea_id)
        if result is None:
            raise RuntimeError("创建 Idea 后无法回读")
        return result

    def idea(self, idea_id: str) -> dict[str, Any]:
        result = self.repository.get_idea(idea_id)
        if result is None:
            raise KeyError(idea_id)
        return result

    def requirement(self, requirement_id: str) -> dict[str, Any]:
        result = self.repository.requirement_detail(requirement_id)
        if result is None:
            raise KeyError(requirement_id)
        return result

    def archive_idea(self, idea_id: str) -> dict[str, Any]:
        self.repository.archive_idea(idea_id)
        return self.idea(idea_id)

    def _validate_source_run(
        self,
        source_run_id: str | None,
        *,
        subject_type: str | None = None,
        subject_id: str | None = None,
    ) -> None:
        if not source_run_id:
            return
        run = self.run_repository.get(source_run_id)
        if run is None:
            raise ValueError(f"来源 Run 不存在：{source_run_id}")
        if subject_type and (
            run.get("subject_type") != subject_type or run.get("subject_id") != subject_id
        ):
            raise ValueError("来源 Run 与当前业务对象不匹配")

    def create_requirement(
        self,
        *,
        title: str,
        content: RequirementContent | dict[str, Any],
        actor_id: str,
        source_run_id: str | None = None,
        source_idea_id: str | None = None,
    ) -> tuple[dict[str, Any], bool]:
        self._validate_source_run(
            source_run_id,
            subject_type="idea" if source_idea_id else None,
            subject_id=source_idea_id,
        )
        row, created = self.repository.create_requirement(
            requirement_id=self._id("req"),
            revision_id=self._id("rev"),
            thread_id=self._id("thread"),
            title=title,
            content=(content.model_dump() if isinstance(content, RequirementContent) else content),
            actor_id=actor_id,
            source_idea_id=source_idea_id,
            source_run_id=source_run_id,
        )
        return self.repository._shape_requirement_detail(row), created

    def add_revision(
        self,
        *,
        requirement_id: str,
        content: RequirementContent | dict[str, Any],
        source_run_id: str | None,
        actor_id: str,
    ) -> dict[str, Any]:
        self._validate_source_run(
            source_run_id,
            subject_type="requirement",
            subject_id=requirement_id,
        )
        return self.repository.add_revision(
            revision_id=self._id("rev"),
            requirement_id=requirement_id,
            content=(content.model_dump() if isinstance(content, RequirementContent) else content),
            source_run_id=source_run_id,
            actor_id=actor_id,
        )

    def decide(
        self,
        *,
        requirement_id: str,
        actor_id: str,
        decision_type: str,
        revision_id: str | None,
        reason: str | None,
        commitment: str | None,
        target_window: str | None,
        entry_condition: str | None,
        review_at: datetime | None,
        merged_into_id: str | None,
        revision_content: RequirementContent | dict[str, Any] | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        return self.repository.decide(
            decision_id=self._id("decision"),
            requirement_id=requirement_id,
            actor_id=actor_id,
            decision_type=decision_type,
            revision_id=revision_id,
            reason=reason,
            commitment=commitment,
            target_window=target_window,
            entry_condition=entry_condition,
            review_at=review_at,
            merged_into_id=merged_into_id,
            reopen_revision_id=self._id("rev") if decision_type == "reopen" else None,
            reopen_content=(
                revision_content.model_dump()
                if isinstance(revision_content, RequirementContent)
                else revision_content
            ),
        )

    async def start_action(
        self,
        *,
        subject_type: str,
        subject_id: str,
        action: str,
        executor: str | None,
        model: str | None,
        instruction: str,
        actor_id: str,
    ) -> dict[str, Any]:
        if action not in ACTION_AGENTS:
            raise ValueError(f"不支持的 Agent 动作：{action}")
        if subject_type == "idea":
            subject = self.idea(subject_id)
            context = f"Idea 标题：{subject['title']}\nIdea 原始内容：\n{subject['raw_content']}"
        elif subject_type == "requirement":
            subject = self.requirement(subject_id)
            revision = subject["current_revision"]
            context = (
                f"Requirement 标题：{subject['title']}\n"
                f"当前状态：{subject['status']}\n"
                f"当前 Revision：\n{revision['content']}"
            )
        else:
            raise ValueError(f"不支持的 subject_type：{subject_type}")
        action_contract = (
            "请补充最低充分的背景，明确已知、未知、冲突、适用范围和可回查入口。"
            if action == "knowledge_context"
            else "请把输入整理成候选 Requirement。结果必须符合给定 JSON Schema，不要替人接纳需求。"
        )
        context_messages = self.repository.context_messages(
            subject_type=subject_type,
            subject_id=subject_id,
        )
        human_context = "\n".join(
            f"{index}. {body}" for index, body in enumerate(context_messages, 1)
        )
        prompt = "\n\n".join(
            part
            for part in (
                "你正在为团队 AI 协作平台执行一次有界业务动作。",
                context,
                f"Thread 中人的显式补充：\n{human_context}" if human_context else "",
                f"动作契约：{action_contract}",
                f"用户补充：{instruction}" if instruction else "",
            )
            if part
        )
        output_schema = (
            strict_output_schema(RequirementDraft.model_json_schema())
            if action == "shape_requirement" and (executor or "codex") == "codex"
            else None
        )
        self.repository.touch_subject(subject_type, subject_id)
        return await self.run_service.start(
            agent_id=ACTION_AGENTS[action],
            prompt=prompt,
            title=("查背景" if action == "knowledge_context" else "梳理候选需求"),
            model=model,
            actor_id=actor_id,
            executor=executor,
            subject_type=subject_type,
            subject_id=subject_id,
            thread_id=str(subject["thread_id"]),
            trigger_action=action,
            output_schema=output_schema,
        )
