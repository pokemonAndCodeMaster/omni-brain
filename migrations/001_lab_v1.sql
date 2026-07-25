CREATE SCHEMA IF NOT EXISTS manual_qc_lab;

CREATE TABLE IF NOT EXISTS manual_qc_lab.schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS manual_qc_lab.t_qc_daily_snapshot (
    stat_date date NOT NULL,
    scene_name text NOT NULL,
    group_name text NOT NULL,
    employee_id text NOT NULL,
    project_name text NOT NULL,

    annotation_total integer NOT NULL DEFAULT 0,
    annotation_submitted integer NOT NULL DEFAULT 0,
    good_annotation_submitted integer NOT NULL DEFAULT 0,
    bad_annotation_submitted integer NOT NULL DEFAULT 0,

    total_accept_assigned integer NOT NULL DEFAULT 0,
    total_accept_completed integer NOT NULL DEFAULT 0,
    total_accept_passed integer NOT NULL DEFAULT 0,
    total_accept_rejected integer NOT NULL DEFAULT 0,

    good_accept_assigned integer NOT NULL DEFAULT 0,
    good_accept_completed integer NOT NULL DEFAULT 0,
    good_accept_passed integer NOT NULL DEFAULT 0,
    good_accept_rejected integer NOT NULL DEFAULT 0,

    bad_accept_assigned integer NOT NULL DEFAULT 0,
    bad_accept_completed integer NOT NULL DEFAULT 0,
    bad_accept_passed integer NOT NULL DEFAULT 0,
    bad_accept_rejected integer NOT NULL DEFAULT 0,

    option_metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
    overall_conclusion text,
    conclusion_reason text,
    confirmed_by text,
    confirmed_at timestamptz,
    execution jsonb NOT NULL DEFAULT '{}'::jsonb,
    executed_by text,
    executed_at timestamptz,

    source_version text NOT NULL,
    computed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    PRIMARY KEY (stat_date, scene_name, group_name, employee_id),

    CONSTRAINT snapshot_conclusion_valid CHECK (
        overall_conclusion IS NULL OR overall_conclusion IN ('PASS', 'REJECT', 'PENDING')
    ),
    CONSTRAINT snapshot_counts_non_negative CHECK (
        annotation_total >= 0
        AND annotation_submitted >= 0
        AND good_annotation_submitted >= 0
        AND bad_annotation_submitted >= 0
        AND total_accept_assigned >= 0
        AND total_accept_completed >= 0
        AND total_accept_passed >= 0
        AND total_accept_rejected >= 0
        AND good_accept_assigned >= 0
        AND good_accept_completed >= 0
        AND good_accept_passed >= 0
        AND good_accept_rejected >= 0
        AND bad_accept_assigned >= 0
        AND bad_accept_completed >= 0
        AND bad_accept_passed >= 0
        AND bad_accept_rejected >= 0
    ),
    CONSTRAINT snapshot_annotation_flow_valid CHECK (
        annotation_submitted <= annotation_total
        AND good_annotation_submitted + bad_annotation_submitted <= annotation_submitted
    ),
    CONSTRAINT snapshot_total_acceptance_flow_valid CHECK (
        total_accept_completed <= total_accept_assigned
        AND total_accept_passed <= total_accept_completed
        AND total_accept_rejected <= total_accept_completed
        AND total_accept_passed + total_accept_rejected <= total_accept_completed
    ),
    CONSTRAINT snapshot_good_acceptance_flow_valid CHECK (
        good_accept_completed <= good_accept_assigned
        AND good_accept_passed <= good_accept_completed
        AND good_accept_rejected <= good_accept_completed
        AND good_accept_passed + good_accept_rejected <= good_accept_completed
    ),
    CONSTRAINT snapshot_bad_acceptance_flow_valid CHECK (
        bad_accept_completed <= bad_accept_assigned
        AND bad_accept_passed <= bad_accept_completed
        AND bad_accept_rejected <= bad_accept_completed
        AND bad_accept_passed + bad_accept_rejected <= bad_accept_completed
    ),
    CONSTRAINT snapshot_acceptance_categories_valid CHECK (
        good_accept_assigned + bad_accept_assigned <= total_accept_assigned
        AND good_accept_completed + bad_accept_completed <= total_accept_completed
        AND good_accept_passed + bad_accept_passed <= total_accept_passed
        AND good_accept_rejected + bad_accept_rejected <= total_accept_rejected
    )
);

CREATE INDEX IF NOT EXISTS idx_qc_snapshot_scene
    ON manual_qc_lab.t_qc_daily_snapshot (stat_date, scene_name);

CREATE INDEX IF NOT EXISTS idx_qc_snapshot_group
    ON manual_qc_lab.t_qc_daily_snapshot (stat_date, scene_name, group_name);

CREATE INDEX IF NOT EXISTS idx_qc_snapshot_employee
    ON manual_qc_lab.t_qc_daily_snapshot (employee_id, stat_date);

INSERT INTO manual_qc_lab.schema_migrations (version)
VALUES ('001_lab_v1')
ON CONFLICT (version) DO NOTHING;
