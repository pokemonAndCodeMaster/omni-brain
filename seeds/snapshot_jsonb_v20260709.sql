TRUNCATE TABLE manual_qc_lab.t_qc_daily_snapshot RESTART IDENTITY;

WITH seed (
    stat_date,
    scene_name,
    group_name,
    employee_id,
    project_name,
    annotation_total,
    annotation_submitted,
    good_submitted,
    bad_submitted,
    good_alloc,
    good_complete,
    good_correct,
    good_incorrect,
    bad_alloc,
    bad_complete,
    bad_correct,
    bad_incorrect,
    conclusion,
    confirmed_by,
    executed_by,
    question_label,
    option_name,
    option_count,
    age
) AS (
    VALUES
        (current_date,     '城区交互', '一组', 'E001', '城区专题', 120, 110, 82, 28, 16, 16, 15, 1,  8,  8, 7, 1, 'pass',    'lead-01', 'lead-01', '驾驶行为分类', 'CUT_IN', 12, interval '10 minutes'),
        (current_date,     '城区交互', '一组', 'E002', '城区专题', 100,  90, 62, 28, 12, 10,  8, 2,  8,  6, 4, 2, 'pending', NULL,      NULL,      '驾驶行为分类', 'YIELD',  11, interval '10 minutes'),
        (current_date,     '城区交互', '二组', 'E003', '城区专题', 140, 125, 95, 30, 20, 18, 17, 1, 10,  9, 7, 2, NULL,      NULL,      NULL,      '驾驶行为分类', 'CUT_IN', 15, interval '8 minutes'),
        (current_date,     '城区交互', '二组', 'E004', '城区专题',  80,  60, 45, 15,  8,  4,  3, 1,  4,  2, 1, 1, NULL,      NULL,      NULL,      '驾驶行为分类', 'CUT_IN',  5, interval '8 minutes'),
        (current_date,     '高速变道', '三组', 'E005', '高速专题', 160, 150,120, 30, 22, 22, 21, 1, 10, 10, 9, 1, 'pass',    'lead-02', 'lead-02', '驾驶行为分类', 'MERGE',   22, interval '6 minutes'),
        (current_date,     '高速变道', '三组', 'E006', '高速专题',  90,  88, 55, 33, 10, 10,  8, 2,  8,  8, 4, 4, 'reject',  'lead-02', 'lead-02', '驾驶行为分类', 'MERGE',    9, interval '6 minutes'),
        (current_date,     '高速变道', '四组', 'E007', '高速专题',  70,  50, 34, 16,  6,  2,  2, 0,  4,  2, 1, 1, NULL,      NULL,      NULL,      NULL,             NULL,        0, interval '5 minutes'),
        (current_date,     '高速变道', '四组', 'E008', '高速专题',  40,   0,  0,  0,  0,  0,  0, 0,  0,  0, 0, 0, NULL,      NULL,      NULL,      NULL,             NULL,        0, interval '5 minutes'),
        (current_date - 1, '城区交互', '一组', 'E001', '城区专题', 105, 100, 76, 24, 14, 14, 13, 1,  6,  6, 5, 1, 'pass',    'lead-01', 'lead-01', '驾驶行为分类', 'CUT_IN', 10, interval '22 hours'),
        (current_date - 1, '城区交互', '一组', 'E002', '城区专题',  95,  86, 60, 26, 11,  9,  8, 1,  7,  6, 4, 2, NULL,      NULL,      NULL,      '驾驶行为分类', 'YIELD',   9, interval '22 hours'),
        (current_date - 1, '城区交互', '二组', 'E003', '城区专题', 120, 112, 84, 28, 16, 15, 14, 1,  8,  7, 6, 1, NULL,      NULL,      NULL,      NULL,             NULL,        0, interval '22 hours'),
        (current_date - 1, '城区交互', '二组', 'E004', '城区专题',  75,  64, 44, 20,  9,  7,  6, 1,  5,  3, 2, 1, NULL,      NULL,      NULL,      NULL,             NULL,        0, interval '22 hours'),
        (current_date - 1, '高速变道', '三组', 'E005', '高速专题', 150, 142,110, 32, 20, 19, 18, 1, 10,  9, 8, 1, NULL,      NULL,      NULL,      '驾驶行为分类', 'MERGE',  19, interval '21 hours'),
        (current_date - 1, '高速变道', '三组', 'E006', '高速专题',  86,  80, 50, 30,  9,  8,  6, 2,  7,  6, 4, 2, NULL,      NULL,      NULL,      NULL,             NULL,        0, interval '21 hours'),
        (current_date - 1, '高速变道', '四组', 'E007', '高速专题',  66,  58, 39, 19,  7,  5,  4, 1,  5,  4, 3, 1, NULL,      NULL,      NULL,      NULL,             NULL,        0, interval '21 hours'),
        (current_date - 1, '高速变道', '四组', 'E008', '高速专题',  35,  30, 19, 11,  4,  2,  2, 0,  2,  1, 0, 1, NULL,      NULL,      NULL,      NULL,             NULL,        0, interval '21 hours')
)
INSERT INTO manual_qc_lab.t_qc_daily_snapshot (
    stat_date,
    scene_name,
    group_name,
    employee_id,
    project_name,
    annotation_total,
    annotation_submitted,
    good_metrics,
    bad_metrics,
    option_metrics,
    confirmed_by,
    confirmed_at,
    executed_by,
    executed_at,
    execution_note,
    computed_at,
    updated_at
)
SELECT
    stat_date,
    scene_name,
    group_name,
    employee_id,
    project_name,
    annotation_total,
    annotation_submitted,
    jsonb_build_object(
        'annotation_total', good_submitted,
        'annotation_submitted', good_submitted,
        'expect_alloc', good_alloc,
        'actual_alloc', good_alloc,
        'actual_complete', good_complete,
        'correct', good_correct,
        'incorrect', good_incorrect,
        'conclusion', conclusion,
        'expect_pass', good_correct,
        'expect_reject', good_incorrect,
        'actual_pass', good_correct,
        'actual_reject', good_incorrect,
        'exec_status', CASE
            WHEN executed_by IS NOT NULL AND conclusion = 'pass' THEN 'PASS_DONE'
            WHEN executed_by IS NOT NULL AND conclusion = 'reject' THEN 'REJECT_DONE'
            WHEN conclusion = 'pending' THEN 'PENDING'
            ELSE NULL
        END
    ),
    jsonb_build_object(
        'annotation_total', bad_submitted,
        'annotation_submitted', bad_submitted,
        'expect_alloc', bad_alloc,
        'actual_alloc', bad_alloc,
        'actual_complete', bad_complete,
        'correct', bad_correct,
        'incorrect', bad_incorrect,
        'conclusion', conclusion,
        'expect_pass', bad_correct,
        'expect_reject', bad_incorrect,
        'actual_pass', bad_correct,
        'actual_reject', bad_incorrect,
        'exec_status', CASE
            WHEN executed_by IS NOT NULL AND conclusion = 'pass' THEN 'PASS_DONE'
            WHEN executed_by IS NOT NULL AND conclusion = 'reject' THEN 'REJECT_DONE'
            WHEN conclusion = 'pending' THEN 'PENDING'
            ELSE NULL
        END
    ),
    CASE
        WHEN question_label IS NULL OR option_name IS NULL THEN '{}'::jsonb
        ELSE jsonb_build_object(
            question_label,
            jsonb_build_object(
                option_name,
                jsonb_build_object(
                    'annotation_total', option_count,
                    'annotation_submitted', option_count,
                    'expect_alloc', 0,
                    'actual_alloc', 0,
                    'actual_complete', 0,
                    'correct', 0,
                    'incorrect', 0,
                    'conclusion', NULL,
                    'expect_pass', 0,
                    'expect_reject', 0,
                    'actual_pass', 0,
                    'actual_reject', 0,
                    'exec_status', NULL
                )
            )
        )
    END,
    confirmed_by,
    CASE WHEN confirmed_by IS NOT NULL THEN now() - age - interval '20 minutes' END,
    executed_by,
    CASE WHEN executed_by IS NOT NULL THEN now() - age - interval '10 minutes' END,
    CASE
        WHEN executed_by IS NOT NULL THEN '本地固定种子：已完成模拟执行'
        WHEN conclusion = 'pending' THEN '本地固定种子：验收尚未完成'
    END,
    now() - age,
    now() - age
FROM seed;
