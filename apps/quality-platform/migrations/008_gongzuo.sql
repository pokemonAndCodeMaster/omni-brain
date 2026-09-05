CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_workspace (
    key varchar(32) PRIMARY KEY,
    mode varchar(16) NOT NULL CHECK (mode IN ('personal', 'team')),
    created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO manual_qc_lab.t_gongzuo_workspace (key, mode) VALUES
    ('personal', 'personal'), ('team', 'team') ON CONFLICT (key) DO NOTHING;

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_item (
    id varchar(64) PRIMARY KEY,
    workspace_key varchar(32) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_workspace(key),
    item_type varchar(32) NOT NULL CHECK (item_type IN ('requirement','research','fix','learning','review','personal','hobby','game','other')),
    title varchar(256) NOT NULL CHECK (length(btrim(title)) > 0),
    status varchar(32) NOT NULL DEFAULT 'open' CHECK (status IN ('open','planned','in_progress','blocked','awaiting_acceptance','completed','cancelled')),
    payload jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(payload) = 'object'),
    version integer NOT NULL DEFAULT 1 CHECK (version > 0),
    created_by varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
    updated_by varchar(128) NOT NULL, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_gongzuo_item_workspace_updated ON manual_qc_lab.t_gongzuo_item (workspace_key, updated_at DESC);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_entity (
    id varchar(64) PRIMARY KEY, workspace_key varchar(32) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_workspace(key),
    entity_type varchar(32) NOT NULL CHECK (entity_type IN ('idea','topic','domain','resource','artifact','improvement')),
    title varchar(256) NOT NULL CHECK (length(btrim(title)) > 0), payload jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(payload) = 'object'),
    version integer NOT NULL DEFAULT 1 CHECK (version > 0), created_by varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), updated_by varchar(128) NOT NULL, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_gongzuo_entity_workspace_type_updated ON manual_qc_lab.t_gongzuo_entity(workspace_key, entity_type, updated_at DESC);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_relation (
    id varchar(64) PRIMARY KEY, workspace_key varchar(32) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_workspace(key),
    from_kind varchar(16) NOT NULL CHECK (from_kind IN ('item','entity')), from_id varchar(64) NOT NULL,
    to_kind varchar(16) NOT NULL CHECK (to_kind IN ('item','entity')), to_id varchar(64) NOT NULL,
    relation_type varchar(32) NOT NULL CHECK (relation_type IN ('formed_from','serves','part_of','depends_on','impacts','produces','verifies','references','contributes_to')),
    created_by varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(workspace_key, from_kind, from_id, to_kind, to_id, relation_type)
);
CREATE INDEX IF NOT EXISTS idx_gongzuo_relation_from ON manual_qc_lab.t_gongzuo_relation(workspace_key, from_kind, from_id);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_context (
    id varchar(64) PRIMARY KEY, workspace_key varchar(32) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_workspace(key), item_id varchar(64) NOT NULL UNIQUE REFERENCES manual_qc_lab.t_gongzuo_item(id) ON DELETE CASCADE,
    current_version_id varchar(64), version integer NOT NULL DEFAULT 1 CHECK (version > 0), created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_context_version (
    id varchar(64) PRIMARY KEY, context_id varchar(64) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_context(id) ON DELETE CASCADE,
    revision_no integer NOT NULL CHECK (revision_no > 0), status varchar(16) NOT NULL CHECK (status IN ('accepted','rejected','superseded')),
    content jsonb NOT NULL CHECK (jsonb_typeof(content) = 'object'), provenance jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(provenance) = 'array'),
    proposal_id varchar(64), accepted_by varchar(128), accepted_at timestamptz, created_by varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(context_id, revision_no)
);
ALTER TABLE manual_qc_lab.t_gongzuo_context DROP CONSTRAINT IF EXISTS fk_gongzuo_context_current_version;
ALTER TABLE manual_qc_lab.t_gongzuo_context ADD CONSTRAINT fk_gongzuo_context_current_version FOREIGN KEY(current_version_id) REFERENCES manual_qc_lab.t_gongzuo_context_version(id) ON DELETE RESTRICT;
CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_context_proposal (
    id varchar(64) PRIMARY KEY, context_id varchar(64) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_context(id) ON DELETE CASCADE,
    base_version integer NOT NULL, title varchar(256) NOT NULL, proposed_content jsonb NOT NULL CHECK (jsonb_typeof(proposed_content) = 'object'), provenance jsonb NOT NULL DEFAULT '[]'::jsonb,
    status varchar(16) NOT NULL DEFAULT 'open' CHECK(status IN ('open','accepted','rejected')), reason text, created_by varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), resolved_by varchar(128), resolved_at timestamptz
);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_discussion (
    id varchar(64) PRIMARY KEY, workspace_key varchar(32) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_workspace(key),
    item_id varchar(64) REFERENCES manual_qc_lab.t_gongzuo_item(id) ON DELETE CASCADE, entity_id varchar(64) REFERENCES manual_qc_lab.t_gongzuo_entity(id) ON DELETE CASCADE,
    anchor varchar(256), body text NOT NULL CHECK(length(btrim(body)) > 0), payload jsonb NOT NULL DEFAULT '{}'::jsonb, created_by varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((item_id IS NOT NULL) <> (entity_id IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_gongzuo_discussion_subject ON manual_qc_lab.t_gongzuo_discussion(workspace_key, item_id, entity_id, created_at);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_evidence (
    id varchar(64) PRIMARY KEY, workspace_key varchar(32) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_workspace(key), item_id varchar(64) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_item(id) ON DELETE CASCADE,
    artifact_ref text NOT NULL CHECK(length(btrim(artifact_ref)) > 0), artifact_version varchar(256) NOT NULL CHECK(length(btrim(artifact_version)) > 0), environment_ref text NOT NULL CHECK(length(btrim(environment_ref)) > 0),
    summary text, status varchar(16) NOT NULL DEFAULT 'submitted' CHECK(status IN ('submitted','accepted','rejected')), run_id varchar(64), payload jsonb NOT NULL DEFAULT '{}'::jsonb, created_by varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), reviewed_by varchar(128), reviewed_at timestamptz, review_reason text
);
CREATE INDEX IF NOT EXISTS idx_gongzuo_evidence_item ON manual_qc_lab.t_gongzuo_evidence(workspace_key,item_id,created_at DESC);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_activity (
    id varchar(64) PRIMARY KEY, workspace_key varchar(32) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_workspace(key), item_id varchar(64) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_item(id) ON DELETE CASCADE,
    kind varchar(64) NOT NULL, body text NOT NULL, payload jsonb NOT NULL DEFAULT '{}'::jsonb, actor_id varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_preference (
    workspace_key varchar(32) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_workspace(key), preference_key varchar(128) NOT NULL, payload jsonb NOT NULL CHECK(jsonb_typeof(payload)='object'), version integer NOT NULL DEFAULT 1, updated_by varchar(128) NOT NULL, updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(workspace_key,preference_key)
);
CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_meeting (
    id varchar(64) PRIMARY KEY, workspace_key varchar(32) NOT NULL UNIQUE REFERENCES manual_qc_lab.t_gongzuo_workspace(key), config jsonb NOT NULL CHECK(jsonb_typeof(config)='object'), version integer NOT NULL DEFAULT 1, updated_by varchar(128) NOT NULL, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_meeting_snapshot (
    id varchar(64) PRIMARY KEY, meeting_id varchar(64) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_meeting(id) ON DELETE CASCADE, meeting_version integer NOT NULL, snapshot jsonb NOT NULL CHECK(jsonb_typeof(snapshot)='object'), created_by varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_meeting_note (
    id varchar(64) PRIMARY KEY, meeting_id varchar(64) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_meeting(id) ON DELETE CASCADE, item_id varchar(64) NOT NULL REFERENCES manual_qc_lab.t_gongzuo_item(id) ON DELETE RESTRICT, body text NOT NULL CHECK(length(btrim(body)) > 0), created_by varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE manual_qc_lab.t_gongzuo_meeting_note
    ADD COLUMN IF NOT EXISTS snapshot_id varchar(64)
        REFERENCES manual_qc_lab.t_gongzuo_meeting_snapshot(id) ON DELETE CASCADE;

-- A new workspace can open its default review immediately. Re-running the
-- migration must never replace a presentation the user has already configured.
INSERT INTO manual_qc_lab.t_gongzuo_meeting(id,workspace_key,config,updated_by)
VALUES
('meeting-default-personal','personal',
 '{"title":"我的周回顾","sections":[{"key":"decisions","title":"需要决定的事","enabled":true},{"key":"topics","title":"专题目标与缺口","enabled":true},{"key":"deliveries","title":"近期交付与变化","enabled":true,"filters":{"recentDays":14}}]}'::jsonb,'migration-008'),
('meeting-default-team','team',
 '{"title":"周度组会","sections":[{"key":"decisions","title":"需要决定的事","enabled":true},{"key":"topics","title":"专题目标与缺口","enabled":true},{"key":"deliveries","title":"近期交付与变化","enabled":true,"filters":{"recentDays":14}}]}'::jsonb,'migration-008')
ON CONFLICT(workspace_key) DO NOTHING;

-- One-way historical bridge. IDs are bounded and stable even when old IDs use all 64 chars.
-- The NOT EXISTS key is the legacy identity in JSON, so rerunning migrations never overwrites
-- a user's subsequent item edits.
WITH legacy AS (
    SELECT r.*, current_rev.content AS current_content, accepted_rev.content AS accepted_content,
           idea.title AS idea_title, idea.raw_content AS idea_raw_content, idea.owner_id AS idea_owner_id
    FROM manual_qc_lab.t_collab_requirement r
    LEFT JOIN manual_qc_lab.t_collab_requirement_revision current_rev ON current_rev.id = r.current_revision_id
    LEFT JOIN manual_qc_lab.t_collab_requirement_revision accepted_rev ON accepted_rev.id = r.accepted_revision_id
    LEFT JOIN manual_qc_lab.t_collab_idea idea ON idea.id = r.source_idea_id
)
INSERT INTO manual_qc_lab.t_gongzuo_item (id, workspace_key, item_type, title, status, payload, created_by, updated_by)
SELECT 'legacy-rq-' || md5(r.id), 'team', 'requirement', r.title,
       CASE r.status
           WHEN 'accepted' THEN 'planned'
           WHEN 'deferred' THEN 'blocked'
           WHEN 'rejected' THEN 'cancelled'
           WHEN 'merged' THEN 'cancelled'
           WHEN 'superseded' THEN 'cancelled'
           WHEN 'closed' THEN 'cancelled'
           ELSE 'open'
       END,
       jsonb_strip_nulls(jsonb_build_object(
           'legacyRequirementId', r.id,
           'legacyRoute', '/api/requirements/' || r.id,
           'legacyStatus', r.status,
           'legacyCurrentRevisionId', r.current_revision_id,
           'legacyAcceptedRevisionId', r.accepted_revision_id,
           'legacyMergedIntoId', r.merged_into_id,
           'legacyMergedIntoRoute', CASE WHEN r.merged_into_id IS NULL THEN NULL ELSE '/api/requirements/' || r.merged_into_id END,
           'owner', r.owner_id,
           'legacyCommitment', r.commitment,
           'legacyTargetWindow', r.target_window,
           'legacyEntryCondition', r.entry_condition,
           'legacyCurrentContent', r.current_content,
           'legacyAcceptedContent', r.accepted_content,
           'legacySourceIdea', CASE WHEN r.source_idea_id IS NULL THEN NULL ELSE jsonb_build_object(
               'id', r.source_idea_id, 'route', '/api/ideas/' || r.source_idea_id,
               'title', r.idea_title, 'rawContent', r.idea_raw_content, 'owner', r.idea_owner_id) END,
           'source', 'collaboration_s0'
       )), 'migration-008', 'migration-008'
FROM legacy r
WHERE NOT EXISTS (
    SELECT 1 FROM manual_qc_lab.t_gongzuo_item i
    WHERE i.payload ->> 'legacyRequirementId' = r.id
);

-- Only an old accepted Requirement receives a context. Candidate/rejected history remains
-- explicitly in the payload instead of being represented as a new approved consensus.
WITH legacy AS (
    SELECT r.id, r.owner_id, r.accepted_revision_id, accepted_rev.content
    FROM manual_qc_lab.t_collab_requirement r
    JOIN manual_qc_lab.t_collab_requirement_revision accepted_rev ON accepted_rev.id = r.accepted_revision_id
    WHERE r.status = 'accepted'
)
INSERT INTO manual_qc_lab.t_gongzuo_context (id, workspace_key, item_id)
SELECT 'legacy-ctx-' || md5(r.id), 'team', i.id
FROM legacy r
JOIN manual_qc_lab.t_gongzuo_item i ON i.payload ->> 'legacyRequirementId' = r.id
WHERE NOT EXISTS (SELECT 1 FROM manual_qc_lab.t_gongzuo_context c WHERE c.item_id = i.id);

WITH legacy AS (
    SELECT r.id, r.owner_id, r.accepted_revision_id, accepted_rev.content
    FROM manual_qc_lab.t_collab_requirement r
    JOIN manual_qc_lab.t_collab_requirement_revision accepted_rev ON accepted_rev.id = r.accepted_revision_id
    WHERE r.status = 'accepted'
)
INSERT INTO manual_qc_lab.t_gongzuo_context_version (id, context_id, revision_no, status, content, provenance, accepted_by, accepted_at, created_by)
SELECT 'legacy-cv-' || md5(r.id), 'legacy-ctx-' || md5(r.id), 1, 'accepted', r.content,
       jsonb_build_array(jsonb_build_object('kind','legacy_requirement_revision','requirementId',r.id,'revisionId',r.accepted_revision_id,'route','/api/requirements/' || r.id)),
       r.owner_id, now(), 'migration-008'
FROM legacy r
WHERE EXISTS (SELECT 1 FROM manual_qc_lab.t_gongzuo_context c WHERE c.id = 'legacy-ctx-' || md5(r.id))
ON CONFLICT (id) DO NOTHING;

UPDATE manual_qc_lab.t_gongzuo_context c
SET current_version_id = 'legacy-cv-' || substr(c.id, length('legacy-ctx-') + 1)
WHERE c.id LIKE 'legacy-ctx-%'
  AND c.current_version_id IS NULL
  AND EXISTS (SELECT 1 FROM manual_qc_lab.t_gongzuo_context_version v WHERE v.id = 'legacy-cv-' || substr(c.id, length('legacy-ctx-') + 1));

INSERT INTO manual_qc_lab.schema_migrations(version) VALUES ('008_gongzuo') ON CONFLICT(version) DO NOTHING;
