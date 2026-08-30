ALTER TABLE manual_qc_lab.t_collab_requirement
    DROP CONSTRAINT IF EXISTS ck_collab_requirement_commitment;

ALTER TABLE manual_qc_lab.t_collab_requirement
    ADD CONSTRAINT ck_collab_requirement_commitment CHECK (
        (
            status = 'accepted'
            AND accepted_revision_id IS NOT NULL
            AND commitment IN ('NOW', 'NEXT', 'LATER')
        )
        OR (
            status <> 'accepted'
            AND commitment IS NULL
        )
    );

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_work (
    id varchar(64) PRIMARY KEY,
    requirement_id varchar(64) NOT NULL UNIQUE
        REFERENCES manual_qc_lab.t_collab_requirement(id) ON DELETE RESTRICT,
    requirement_revision_id varchar(64) NOT NULL
        REFERENCES manual_qc_lab.t_collab_requirement_revision(id) ON DELETE RESTRICT,
    title varchar(256) NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'planned',
    owner_id varchar(128) NOT NULL DEFAULT 'admin',
    reviewer_id varchar(128) NOT NULL DEFAULT 'admin',
    timebox_start timestamptz,
    timebox_end timestamptz,
    repository_path text NOT NULL,
    base_commit varchar(64) NOT NULL,
    worktree_path text NOT NULL,
    branch_name varchar(256) NOT NULL,
    created_by varchar(128) NOT NULL DEFAULT 'admin',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    accepted_at timestamptz,

    CONSTRAINT ck_collab_work_title CHECK (length(btrim(title)) > 0),
    CONSTRAINT ck_collab_work_status CHECK (
        status IN (
            'planned', 'in_progress', 'in_review',
            'revision_requested', 'accepted', 'cancelled'
        )
    ),
    CONSTRAINT ck_collab_work_timebox CHECK (
        timebox_start IS NULL OR timebox_end IS NULL OR timebox_end > timebox_start
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_collab_work_active_repository
    ON manual_qc_lab.t_collab_work (repository_path)
    WHERE status IN ('planned', 'in_progress', 'in_review', 'revision_requested');

CREATE INDEX IF NOT EXISTS idx_collab_work_status_updated
    ON manual_qc_lab.t_collab_work (status, updated_at DESC);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_work_plan (
    id varchar(64) PRIMARY KEY,
    work_id varchar(64) NOT NULL UNIQUE
        REFERENCES manual_qc_lab.t_collab_work(id) ON DELETE CASCADE,
    recipe_key varchar(64) NOT NULL,
    revision_no integer NOT NULL DEFAULT 1,
    status varchar(32) NOT NULL DEFAULT 'active',
    created_by varchar(128) NOT NULL DEFAULT 'admin',
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,

    CONSTRAINT ck_collab_work_plan_recipe CHECK (
        recipe_key = 'standard_development_v1'
    ),
    CONSTRAINT ck_collab_work_plan_revision CHECK (revision_no = 1),
    CONSTRAINT ck_collab_work_plan_status CHECK (status IN ('active', 'completed'))
);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_plan_step (
    id varchar(64) PRIMARY KEY,
    work_plan_id varchar(64) NOT NULL
        REFERENCES manual_qc_lab.t_collab_work_plan(id) ON DELETE CASCADE,
    position integer NOT NULL,
    step_key varchar(64) NOT NULL,
    title varchar(128) NOT NULL,
    description text NOT NULL,
    actor_kind varchar(16) NOT NULL,
    agent_id varchar(128),
    default_executor varchar(32),
    status varchar(32) NOT NULL DEFAULT 'pending',
    completion_note text,
    completed_by varchar(128),
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT uq_collab_plan_step_position UNIQUE (work_plan_id, position),
    CONSTRAINT uq_collab_plan_step_key UNIQUE (work_plan_id, step_key),
    CONSTRAINT ck_collab_plan_step_position CHECK (position BETWEEN 1 AND 6),
    CONSTRAINT ck_collab_plan_step_actor CHECK (actor_kind IN ('agent', 'human')),
    CONSTRAINT ck_collab_plan_step_executor CHECK (
        default_executor IS NULL OR default_executor IN ('codex', 'opencode')
    ),
    CONSTRAINT ck_collab_plan_step_agent CHECK (
        (actor_kind = 'agent' AND agent_id IS NOT NULL AND default_executor IS NOT NULL)
        OR (actor_kind = 'human' AND agent_id IS NULL AND default_executor IS NULL)
    ),
    CONSTRAINT ck_collab_plan_step_status CHECK (
        status IN ('pending', 'ready', 'completed')
    )
);

CREATE INDEX IF NOT EXISTS idx_collab_plan_step_plan_position
    ON manual_qc_lab.t_collab_plan_step (work_plan_id, position);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_work_evidence (
    id varchar(64) PRIMARY KEY,
    work_id varchar(64) NOT NULL
        REFERENCES manual_qc_lab.t_collab_work(id) ON DELETE CASCADE,
    payload jsonb NOT NULL,
    created_by varchar(128) NOT NULL DEFAULT 'admin',
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ck_collab_work_evidence_payload CHECK (
        jsonb_typeof(payload) = 'object'
    )
);

CREATE INDEX IF NOT EXISTS idx_collab_work_evidence_created
    ON manual_qc_lab.t_collab_work_evidence (work_id, created_at DESC);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_collab_work_decision (
    id varchar(64) PRIMARY KEY,
    work_id varchar(64) NOT NULL
        REFERENCES manual_qc_lab.t_collab_work(id) ON DELETE CASCADE,
    decision_type varchar(32) NOT NULL,
    reason text NOT NULL,
    evidence_id varchar(64)
        REFERENCES manual_qc_lab.t_collab_work_evidence(id) ON DELETE RESTRICT,
    commit_sha varchar(64),
    actor_id varchar(128) NOT NULL DEFAULT 'admin',
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ck_collab_work_decision_type CHECK (
        decision_type IN ('accept', 'request_changes')
    ),
    CONSTRAINT ck_collab_work_decision_reason CHECK (length(btrim(reason)) > 0),
    CONSTRAINT ck_collab_work_accept_evidence CHECK (
        decision_type <> 'accept'
        OR (evidence_id IS NOT NULL AND commit_sha IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_collab_work_decision_created
    ON manual_qc_lab.t_collab_work_decision (work_id, created_at DESC);

ALTER TABLE manual_qc_lab.t_agent_run
    ADD COLUMN IF NOT EXISTS work_id varchar(64),
    ADD COLUMN IF NOT EXISTS plan_step_id varchar(64);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_agent_run_work'
          AND conrelid = 'manual_qc_lab.t_agent_run'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_agent_run
            ADD CONSTRAINT fk_agent_run_work
            FOREIGN KEY (work_id)
            REFERENCES manual_qc_lab.t_collab_work(id)
            ON DELETE RESTRICT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_agent_run_plan_step'
          AND conrelid = 'manual_qc_lab.t_agent_run'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_agent_run
            ADD CONSTRAINT fk_agent_run_plan_step
            FOREIGN KEY (plan_step_id)
            REFERENCES manual_qc_lab.t_collab_plan_step(id)
            ON DELETE RESTRICT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_agent_run_work_step_pair'
          AND conrelid = 'manual_qc_lab.t_agent_run'::regclass
    ) THEN
        ALTER TABLE manual_qc_lab.t_agent_run
            ADD CONSTRAINT ck_agent_run_work_step_pair
            CHECK ((work_id IS NULL) = (plan_step_id IS NULL));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_agent_run_work_step_created
    ON manual_qc_lab.t_agent_run (work_id, plan_step_id, created_at DESC)
    WHERE work_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_agent_run_active_plan_step
    ON manual_qc_lab.t_agent_run (plan_step_id)
    WHERE plan_step_id IS NOT NULL AND status IN ('queued', 'running');

INSERT INTO manual_qc_lab.schema_migrations (version)
VALUES ('007_create_collaboration_s1')
ON CONFLICT (version) DO NOTHING;
