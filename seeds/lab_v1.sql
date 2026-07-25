TRUNCATE TABLE manual_qc_lab.t_qc_daily_snapshot;

INSERT INTO manual_qc_lab.t_qc_daily_snapshot (
    stat_date, scene_name, group_name, employee_id, project_name,
    annotation_total, annotation_submitted,
    good_annotation_submitted, bad_annotation_submitted,
    total_accept_assigned, total_accept_completed,
    total_accept_passed, total_accept_rejected,
    good_accept_assigned, good_accept_completed,
    good_accept_passed, good_accept_rejected,
    bad_accept_assigned, bad_accept_completed,
    bad_accept_passed, bad_accept_rejected,
    option_metrics, overall_conclusion, conclusion_reason,
    confirmed_by, confirmed_at, execution, executed_by, executed_at,
    source_version, computed_at
) VALUES
(
    current_date, '城区交互', '一组', 'E001', '城区专题',
    120, 110, 82, 28,
    24, 24, 22, 2,
    16, 16, 15, 1,
    8, 8, 7, 1,
    '{"CUT_IN": 12, "YIELD": 18}', 'PASS', '样本完成且通过范围满足实验阈值',
    'lead-01', now() - interval '30 minutes',
    '{"requested": 24, "confirmed": 24, "status": "CONFIRMED"}',
    'lead-01', now() - interval '20 minutes',
    'seed-v1', now() - interval '10 minutes'
),
(
    current_date, '城区交互', '一组', 'E002', '城区专题',
    100, 90, 62, 28,
    20, 16, 12, 4,
    12, 10, 8, 2,
    8, 6, 4, 2,
    '{"CUT_IN": 8, "YIELD": 11}', 'PENDING', '仍有 4 条验收未完成',
    NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '10 minutes'
),
(
    current_date, '城区交互', '二组', 'E003', '城区专题',
    140, 125, 95, 30,
    30, 27, 24, 3,
    20, 18, 17, 1,
    10, 9, 7, 2,
    '{"CUT_IN": 15, "YIELD": 20}', NULL, NULL,
    NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '8 minutes'
),
(
    current_date, '城区交互', '二组', 'E004', '城区专题',
    80, 60, 45, 15,
    12, 6, 4, 2,
    8, 4, 3, 1,
    4, 2, 1, 1,
    '{"CUT_IN": 5}', NULL, NULL,
    NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '8 minutes'
),
(
    current_date, '高速变道', '三组', 'E005', '高速专题',
    160, 150, 120, 30,
    32, 32, 30, 2,
    22, 22, 21, 1,
    10, 10, 9, 1,
    '{"MERGE": 22}', 'PASS', '实验通过样本',
    'lead-02', now() - interval '25 minutes',
    '{"requested": 32, "confirmed": 32, "status": "CONFIRMED"}',
    'lead-02', now() - interval '15 minutes',
    'seed-v1', now() - interval '6 minutes'
),
(
    current_date, '高速变道', '三组', 'E006', '高速专题',
    90, 88, 55, 33,
    18, 18, 12, 6,
    10, 10, 8, 2,
    8, 8, 4, 4,
    '{"MERGE": 9}', 'REJECT', 'Bad 样本打回比例较高',
    'lead-02', now() - interval '25 minutes',
    '{"requested": 18, "confirmed": 15, "failed": 3, "status": "PARTIAL"}',
    'lead-02', now() - interval '15 minutes',
    'seed-v1', now() - interval '6 minutes'
),
(
    current_date, '高速变道', '四组', 'E007', '高速专题',
    70, 50, 34, 16,
    10, 4, 3, 1,
    6, 2, 2, 0,
    4, 2, 1, 1,
    '{}', NULL, NULL, NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '5 minutes'
),
(
    current_date, '高速变道', '四组', 'E008', '高速专题',
    40, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, 0,
    '{}', NULL, NULL, NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '5 minutes'
),
(
    current_date - 1, '城区交互', '一组', 'E001', '城区专题',
    105, 100, 76, 24,
    20, 20, 18, 2,
    14, 14, 13, 1,
    6, 6, 5, 1,
    '{"CUT_IN": 10}', 'PASS', '前一日实验结论',
    'lead-01', now() - interval '1 day',
    '{"requested": 20, "confirmed": 20, "status": "CONFIRMED"}',
    'lead-01', now() - interval '23 hours',
    'seed-v1', now() - interval '22 hours'
),
(
    current_date - 1, '城区交互', '一组', 'E002', '城区专题',
    95, 86, 60, 26,
    18, 15, 12, 3,
    11, 9, 8, 1,
    7, 6, 4, 2,
    '{"YIELD": 9}', NULL, NULL, NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '22 hours'
),
(
    current_date - 1, '城区交互', '二组', 'E003', '城区专题',
    120, 112, 84, 28,
    24, 22, 20, 2,
    16, 15, 14, 1,
    8, 7, 6, 1,
    '{}', NULL, NULL, NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '22 hours'
),
(
    current_date - 1, '城区交互', '二组', 'E004', '城区专题',
    75, 64, 44, 20,
    14, 10, 8, 2,
    9, 7, 6, 1,
    5, 3, 2, 1,
    '{}', NULL, NULL, NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '22 hours'
),
(
    current_date - 1, '高速变道', '三组', 'E005', '高速专题',
    150, 142, 110, 32,
    30, 28, 26, 2,
    20, 19, 18, 1,
    10, 9, 8, 1,
    '{"MERGE": 19}', NULL, NULL, NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '21 hours'
),
(
    current_date - 1, '高速变道', '三组', 'E006', '高速专题',
    86, 80, 50, 30,
    16, 14, 10, 4,
    9, 8, 6, 2,
    7, 6, 4, 2,
    '{}', NULL, NULL, NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '21 hours'
),
(
    current_date - 1, '高速变道', '四组', 'E007', '高速专题',
    66, 58, 39, 19,
    12, 9, 7, 2,
    7, 5, 4, 1,
    5, 4, 3, 1,
    '{}', NULL, NULL, NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '21 hours'
),
(
    current_date - 1, '高速变道', '四组', 'E008', '高速专题',
    35, 30, 19, 11,
    6, 3, 2, 1,
    4, 2, 2, 0,
    2, 1, 0, 1,
    '{}', NULL, NULL, NULL, NULL, '{}', NULL, NULL,
    'seed-v1', now() - interval '21 hours'
);
