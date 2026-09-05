from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

WorkspaceKey = Literal['personal', 'team']
ItemType = Literal['requirement', 'research', 'fix', 'learning', 'review', 'personal', 'hobby', 'game', 'other']
ItemStatus = Literal['open', 'planned', 'in_progress', 'blocked', 'awaiting_acceptance', 'completed', 'cancelled']
EntityType = Literal['idea', 'topic', 'domain', 'resource', 'artifact', 'improvement']


class WireModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class ItemCreate(WireModel):
    item_type: ItemType = Field(alias='itemType')
    title: str = Field(min_length=1, max_length=256)
    status: ItemStatus = 'open'
    payload: dict[str, Any] = Field(default_factory=dict)
    initial_context: dict[str, Any] | None = Field(default=None, alias='initialContext')
    provenance: list[dict[str, Any]] = Field(default_factory=list)


class ItemUpdate(WireModel):
    version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=256)
    status: ItemStatus | None = None
    payload: dict[str, Any] | None = None

    @model_validator(mode='after')
    def changed(self) -> 'ItemUpdate':
        if self.title is None and self.status is None and self.payload is None:
            raise ValueError('至少提交一个要更新的字段')
        return self


class EntityCreate(WireModel):
    entity_type: EntityType = Field(alias='entityType')
    title: str = Field(min_length=1, max_length=256)
    payload: dict[str, Any] = Field(default_factory=dict)


class EntityUpdate(WireModel):
    version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=256)
    payload: dict[str, Any] | None = None


class RelationCreate(WireModel):
    from_kind: Literal['item', 'entity'] = Field(alias='fromKind')
    from_id: str = Field(alias='fromId', min_length=1, max_length=64)
    to_kind: Literal['item', 'entity'] = Field(alias='toKind')
    to_id: str = Field(alias='toId', min_length=1, max_length=64)
    relation_type: Literal['formed_from', 'serves', 'part_of', 'depends_on', 'impacts', 'produces', 'verifies', 'references', 'contributes_to'] = Field(alias='relationType')


class DiscussionCreate(WireModel):
    body: str = Field(min_length=1)
    anchor: str | None = Field(default=None, max_length=256)
    payload: dict[str, Any] = Field(default_factory=dict)


class ContextProposalCreate(WireModel):
    base_version: int = Field(alias='baseVersion', ge=1)
    title: str = Field(min_length=1, max_length=256)
    proposed_content: dict[str, Any] = Field(alias='proposedContent')
    provenance: list[dict[str, Any]] = Field(default_factory=list)


class ContextResolve(WireModel):
    version: int = Field(ge=1)
    reason: str | None = None


class EvidenceCreate(WireModel):
    artifact_ref: str = Field(alias='artifactRef', min_length=1)
    artifact_version: str = Field(alias='artifactVersion', min_length=1, max_length=256)
    environment_ref: str = Field(alias='environmentRef', min_length=1)
    summary: str | None = None
    run_id: str | None = Field(default=None, alias='runId', max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class EvidenceReview(WireModel):
    status: Literal['accepted', 'rejected']
    reason: str | None = None


class PreferenceUpdate(WireModel):
    version: int | None = Field(default=None, ge=1)
    payload: dict[str, Any]


class MeetingConfigUpdate(WireModel):
    version: int | None = Field(default=None, ge=1)
    config: dict[str, Any]


class MeetingNoteCreate(WireModel):
    item_id: str = Field(alias='itemId', min_length=1, max_length=64)
    body: str = Field(min_length=1)
    snapshot_id: str | None = Field(default=None, alias='snapshotId', max_length=64)


class ActivityCreate(WireModel):
    kind: str = Field(min_length=1, max_length=64)
    body: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
