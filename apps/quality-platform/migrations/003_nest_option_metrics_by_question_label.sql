-- Keep the business hierarchy explicit:
-- question label -> option name -> metric state.
--
-- Existing flat option objects are preserved under a reviewable placeholder
-- instead of inventing a business label during migration.
UPDATE manual_qc_lab.t_qc_daily_snapshot
SET
    option_metrics = jsonb_build_object(
        '待确认问题标签',
        option_metrics
    ),
    updated_at = now()
WHERE option_metrics <> '{}'::jsonb
  AND EXISTS (
      SELECT 1
      FROM jsonb_each(option_metrics) AS item
      WHERE jsonb_typeof(item.value) = 'object'
        AND item.value ? 'annotation_total'
  );

ALTER TABLE manual_qc_lab.t_qc_daily_snapshot
    DROP CONSTRAINT IF EXISTS ck_qc_snapshot_option_question_layer;

ALTER TABLE manual_qc_lab.t_qc_daily_snapshot
    ADD CONSTRAINT ck_qc_snapshot_option_question_layer CHECK (
        NOT jsonb_path_exists(option_metrics, '$.*.annotation_total')
    );

INSERT INTO manual_qc_lab.schema_migrations (version)
VALUES ('003_nest_option_metrics_by_question_label')
ON CONFLICT (version) DO NOTHING;
