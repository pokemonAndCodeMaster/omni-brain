from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.api.schemas.collaboration import (
    IdeaCreate,
    RequirementDecisionCreate,
    RequirementDraft,
)
from src.collaboration.service import strict_output_schema
from src.collaboration.repository import CollaborationRepository


def test_s0_rejects_client_supplied_actor_identity() -> None:
    with pytest.raises(ValidationError, match="actor_id"):
        IdeaCreate.model_validate(
            {
                "title": "平台灵感",
                "raw_content": "原始内容",
                "actor_id": "forged-user",
            }
        )


def test_acceptance_requires_explicit_next_or_later_evidence() -> None:
    with pytest.raises(ValidationError, match="NEXT 或 LATER"):
        RequirementDecisionCreate.model_validate({"decision_type": "accept"})

    with pytest.raises(ValidationError, match="预计窗口或进入条件"):
        RequirementDecisionCreate.model_validate(
            {"decision_type": "accept", "commitment": "NEXT"}
        )

    accepted = RequirementDecisionCreate.model_validate(
        {
            "decision_type": "accept",
            "commitment": "NEXT",
            "target_window": "S1",
        }
    )
    assert accepted.commitment == "NEXT"


def test_now_is_not_an_s0_commitment_value() -> None:
    with pytest.raises(ValidationError):
        RequirementDecisionCreate.model_validate(
            {
                "decision_type": "accept",
                "commitment": "NOW",
                "target_window": "本周",
            }
        )


def test_acceptance_requires_minimum_requirement_content() -> None:
    with pytest.raises(ValueError, match="当前问题、期望结果、范围、验收标准"):
        CollaborationRepository.validate_acceptance_content({})

    CollaborationRepository.validate_acceptance_content(
        {
            "current_problem": "团队无法追踪需求来源",
            "expected_outcome": "可从 Idea 追溯至正式需求",
            "in_scope": ["Idea 转候选需求"],
            "acceptance_criteria": ["重复转换不产生重复记录"],
        }
    )


def test_codex_output_schema_requires_every_declared_property() -> None:
    schema = strict_output_schema(RequirementDraft.model_json_schema())

    assert schema["required"] == ["title", "content"]
    content = schema["$defs"]["RequirementContent"]
    assert content["required"] == list(content["properties"])
    assert content["additionalProperties"] is False
