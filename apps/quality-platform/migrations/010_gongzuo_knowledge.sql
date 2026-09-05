CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_capability (
  id text PRIMARY KEY,
  workspace_key text NOT NULL CHECK (workspace_key IN ('personal','team')),
  title text NOT NULL,
  target text NOT NULL CHECK (target IN ('knowledge','skill','agent','harness')),
  source_item_id text,
  source_entity_id text,
  source_path text,
  base_version text,
  source_revision text,
  content text NOT NULL,
  desired_behavior text NOT NULL,
  validation_plan text NOT NULL,
  version text NOT NULL,
  status text NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate','verified','published','superseded')),
  created_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  published_by text,
  UNIQUE(workspace_key,id)
);
CREATE TABLE IF NOT EXISTS manual_qc_lab.t_gongzuo_capability_verification (
  id text PRIMARY KEY,
  workspace_key text NOT NULL,
  candidate_id text NOT NULL REFERENCES manual_qc_lab.t_gongzuo_capability(id),
  candidate_version text NOT NULL,
  run_id text NOT NULL,
  evidence_id text NOT NULL,
  assessment text NOT NULL,
  result text NOT NULL CHECK (result IN ('accepted','rejected')),
  checked_by text NOT NULL,
  checked_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_gongzuo_capability_workspace ON manual_qc_lab.t_gongzuo_capability(workspace_key,status);
ALTER TABLE manual_qc_lab.t_gongzuo_capability ADD COLUMN IF NOT EXISTS source_revision text;
CREATE UNIQUE INDEX IF NOT EXISTS ix_gongzuo_capability_active_source
ON manual_qc_lab.t_gongzuo_capability(workspace_key,target,COALESCE(source_path,title)) WHERE status='published';
