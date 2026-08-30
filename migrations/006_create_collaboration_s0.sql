CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_idea (
    id varchar(64) PRIMARY KEY,
    title varchar(256) NOT NULL,
    raw_content text NOT NULL,
    domain_key varchar(128),
    status varchar(32) NOT NULL DEFAULT 'captured',
    created_by varchar(128) NOT NULL DEFAULT 'admin',
    owner_id varchar(128) NOT NULL DEFAULT 'admin',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ck_collab_idea_title CHECK (length(btrim(title)) > 0),
    CONSTRAINT ck_collab_idea_content CHECK (length(btrim(raw_content)) > 0),
    CONSTRAINT ck_collab_idea_status CHECK (
        status IN ('captured', 'discussing', 'converted', 'archived')
    )
);

CREATE INDEX IF NOT EXISTS idx_collab_idea_status_updated
    ON manual_qc_lab.t_collab_idea (status, updated_at DESC);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_requirement (
    id varchar(64) PRIMARY KEY,
    source_type varchar(32) NOT NULL DEFAULT 'direct',
    source_idea_id varchar(64)
        REFERENCES manual_qc_lab.t_collab_idea(id) ON DELETE RESTRICT,
    title varchar(256) NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'candidate',
    current_revision_id varchar(64),
    accepted_revision_id varchar(64),
    commitment varchar(16),
    owner_id varchar(128) NOT NULL DEFAULT 'admin',
    target_window varchar(256),
    entry_condition text,
    review_at timestamptz,
    merged_into_id varchar(64)
        REFERENCES manual_qc_lab.t_collab_requirement(id) ON DELETE RESTRICT,
    created_by varchar(128) NOT NULL DEFAULT 'admin',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ck_collab_requirement_title CHECK (length(btrim(title)) > 0),
    CONSTRAINT ck_collab_requirement_source CHECK (
        (source_type = 'direct' AND source_idea_id IS NULL)
        OR (source_type = 'idea' AND source_idea_id IS NOT NULL)
    ),
    CONSTRAINT ck_collab_requirement_status CHECK (
        status IN (
            'candidate', 'accepted', 'rejected', 'deferred',
            'merged', 'superseded', 'closed'
        )
    ),
    CONSTRAINT ck_collab_requirement_commitment CHECK (
        (
            status = 'accepted'
            AND accepted_revision_id IS NOT NULL
            AND commitment IN ('NEXT', 'LATER')
        )
        OR (
            status <> 'accepted'
            AND commitment IS NULL
        )
    ),
    CONSTRAINT ck_collab_requirement_next CHECK (
        commitment <> 'NEXT'
        OR target_window IS NOT NULL
        OR entry_condition IS NOT NULL
    ),
    CONSTRAINT ck_collab_requirement_later CHECK (
        commitment <> 'LATER'
        OR review_at IS NOT NULL
        OR entry_condition IS NOT NULL
    ),
    CONSTRAINT ck_collab_requirement_merged CHECK (
        status <> 'merged'
        OR (merged_into_id IS NOT NULL AND merged_into_id <> id)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_collab_requirement_source_idea
    ON manual_qc_lab.t_collab_requirement (source_idea_id)
    WHERE source_type = 'idea' AND source_idea_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_collab_requirement_status_updated
    ON manual_qc_lab.t_collab_requirement (status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_collab_requirement_commitment_updated
    ON manual_qc_lab.t_collab_requirement (commitment, updated_at DESC);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_requirement_revision (
    id varchar(64) PRIMARY KEY,
    requirement_id varchar(64) NOT NULL
        REFERENCES manual_qc_lab.t_collab_requirement(id) ON DELETE CASCADE,
    revision_no integer NOT NULL,
    content jsonb NOT NULL,
    source_run_id varchar(64)
        REFERENCES manual_qc_lab.t_agent_run(id) ON DELETE SET NULL,
    created_by varchar(128) NOT NULL DEFAULT 'admin',
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT uq_collab_requirement_revision UNIQUE (requirement_id, revision_no),
    CONSTRAINT ck_collab_requirement_revision_no CHECK (revision_no > 0),
    CONSTRAINT ck_collab_requirement_revision_content CHECK (
        jsonb_typeof(content) = 'object'
    )
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_collab_requirement_current_revision'
          AND conrelid = 'manual_qc_lab.t_collab_requirement'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_collab_requirement
            ADD CONSTRAINT fk_collab_requirement_current_revision
            FOREIGN KEY (current_revision_id)
            REFERENCES manual_qc_lab.t_collab_requirement_revision(id)
            ON DELETE RESTRICT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_collab_requirement_accepted_revision'
          AND conrelid = 'manual_qc_lab.t_collab_requirement'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_collab_requirement
            ADD CONSTRAINT fk_collab_requirement_accepted_revision
            FOREIGN KEY (accepted_revision_id)
            REFERENCES manual_qc_lab.t_collab_requirement_revision(id)
            ON DELETE RESTRICT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_collab_requirement_revision_created
    ON manual_qc_lab.t_collab_requirement_revision (
        requirement_id, revision_no DESC
    );

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_thread (
    id varchar(64) PRIMARY KEY,
    subject_type varchar(32) NOT NULL,
    subject_id varchar(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT uq_collab_thread_subject UNIQUE (subject_type, subject_id),
    CONSTRAINT ck_collab_thread_subject_type CHECK (
        subject_type IN ('idea', 'requirement')
    )
);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_thread_entry (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    thread_id varchar(64) NOT NULL
        REFERENCES manual_qc_lab.t_collab_thread(id) ON DELETE CASCADE,
    entry_type varchar(32) NOT NULL,
    actor_type varchar(32) NOT NULL,
    actor_id varchar(128) NOT NULL,
    body text NOT NULL DEFAULT '',
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ck_collab_thread_entry_type CHECK (
        entry_type IN ('human_message', 'system')
    ),
    CONSTRAINT ck_collab_thread_entry_actor_type CHECK (
        actor_type IN ('admin', 'system')
    ),
    CONSTRAINT ck_collab_thread_entry_payload CHECK (
        jsonb_typeof(payload) = 'object'
    )
);

CREATE INDEX IF NOT EXISTS idx_collab_thread_entry_cursor
    ON manual_qc_lab.t_collab_thread_entry (thread_id, created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_decision (
    id varchar(64) PRIMARY KEY,
    requirement_id varchar(64) NOT NULL
        REFERENCES manual_qc_lab.t_collab_requirement(id) ON DELETE CASCADE,
    revision_id varchar(64)
        REFERENCES manual_qc_lab.t_collab_requirement_revision(id) ON DELETE RESTRICT,
    decision_type varchar(32) NOT NULL,
    reason text,
    commitment varchar(16),
    target_window varchar(256),
    entry_condition text,
    review_at timestamptz,
    merged_into_id varchar(64)
        REFERENCES manual_qc_lab.t_collab_requirement(id) ON DELETE RESTRICT,
    actor_id varchar(128) NOT NULL DEFAULT 'admin',
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ck_collab_decision_type CHECK (
        decision_type IN ('accept', 'reject', 'defer', 'merge', 'reopen')
    ),
    CONSTRAINT ck_collab_decision_commitment CHECK (
        commitment IS NULL OR commitment IN ('NEXT', 'LATER')
    ),
    CONSTRAINT ck_collab_decision_reason CHECK (
        decision_type NOT IN ('reject', 'defer', 'merge')
        OR length(btrim(reason)) > 0
    )
);

CREATE INDEX IF NOT EXISTS idx_collab_decision_requirement_created
    ON manual_qc_lab.t_collab_decision (requirement_id, created_at DESC);

ALTER TABLE manual_qc_lab.t_agent_run
    ADD COLUMN IF NOT EXISTS executor varchar(32) NOT NULL DEFAULT 'opencode',
    ADD COLUMN IF NOT EXISTS executor_session_id varchar(128),
    ADD COLUMN IF NOT EXISTS subject_type varchar(32),
    ADD COLUMN IF NOT EXISTS subject_id varchar(64),
    ADD COLUMN IF NOT EXISTS thread_id varchar(64),
    ADD COLUMN IF NOT EXISTS trigger_action varchar(64),
    ADD COLUMN IF NOT EXISTS result_payload jsonb;

ALTER TABLE manual_qc_lab.t_agent_run
    ALTER COLUMN actor_id SET DEFAULT 'admin';

UPDATE manual_qc_lab.t_agent_run
SET executor_session_id = opencode_session_id
WHERE executor_session_id IS NULL
  AND opencode_session_id IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_agent_run_executor'
          AND conrelid = 'manual_qc_lab.t_agent_run'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_agent_run
            ADD CONSTRAINT ck_agent_run_executor
            CHECK (executor IN ('codex', 'opencode'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_agent_run_subject_type'
          AND conrelid = 'manual_qc_lab.t_agent_run'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_agent_run
            ADD CONSTRAINT ck_agent_run_subject_type
            CHECK (subject_type IS NULL OR subject_type IN ('idea', 'requirement', 'work'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_agent_run_subject_pair'
          AND conrelid = 'manual_qc_lab.t_agent_run'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_agent_run
            ADD CONSTRAINT ck_agent_run_subject_pair
            CHECK ((subject_type IS NULL) = (subject_id IS NULL));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_agent_run_result_payload'
          AND conrelid = 'manual_qc_lab.t_agent_run'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_agent_run
            ADD CONSTRAINT ck_agent_run_result_payload
            CHECK (result_payload IS NULL OR jsonb_typeof(result_payload) = 'object');
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_agent_run_thread'
          AND conrelid = 'manual_qc_lab.t_agent_run'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_agent_run
            ADD CONSTRAINT fk_agent_run_thread
            FOREIGN KEY (thread_id)
            REFERENCES manual_qc_lab.t_collab_thread(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_agent_run_subject_created
    ON manual_qc_lab.t_agent_run (subject_type, subject_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_run_executor_status_updated
    ON manual_qc_lab.t_agent_run (executor, status, updated_at DESC);

INSERT INTO manual_qc_lab.schema_migrations (version)
VALUES ('006_create_collaboration_s0')
ON CONFLICT (version) DO NOTHING;
