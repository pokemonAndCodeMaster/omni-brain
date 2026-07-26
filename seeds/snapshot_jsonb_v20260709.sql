TRUNCATE TABLE manual_qc_lab.t_qc_daily_snapshot RESTART IDENTITY;

-- 固定实验规模：
-- 14 天 × 24 个任务 × 每任务 3 个组 × 每组每日 3 名轮转员工 = 3024 行。
-- 12 个组各有 10 名员工，轮转后覆盖 E001—E120。
WITH
tasks (task_index, project_name, scene_name) AS (
    VALUES
        ( 1, '城区/高速', '城区交互任务-01'),
        ( 2, '城区/高速', '高速变道任务-02'),
        ( 3, '城区/高速', '路口礼让任务-03'),
        ( 4, '城区/高速', '跟车距离任务-04'),
        ( 5, '城区/高速', '匝道汇入任务-05'),
        ( 6, '城区/高速', '无保护左转任务-06'),
        ( 7, '城区/高速', '行人避让任务-07'),
        ( 8, '城区/高速', '拥堵跟车任务-08'),
        ( 9, '城区/高速', '夜间行驶任务-09'),
        (10, '城区/高速', '雨天道路任务-10'),
        (11, '城区/高速', '施工区域任务-11'),
        (12, '城区/高速', '复杂掉头任务-12'),
        (13, '园区',      '园区通行任务-13'),
        (14, '园区',      '园区泊车任务-14'),
        (15, '园区',      '窄路会车任务-15'),
        (16, '园区',      '闸机通行任务-16'),
        (17, '园区',      '环岛绕行任务-17'),
        (18, '园区',      '静态障碍任务-18'),
        (19, '园区',      '动态障碍任务-19'),
        (20, '园区',      '低速跟随任务-20'),
        (21, '园区',      '路口停车任务-21'),
        (22, '园区',      '车位搜索任务-22'),
        (23, '园区',      '零提交边界任务-23'),
        (24, '园区',      '重复验收边界任务-24')
),
dates AS (
    SELECT
        day_index,
        current_date - (13 - day_index) AS stat_date
    FROM generate_series(0, 13) AS day(day_index)
),
task_groups AS (
    SELECT
        task.*,
        group_dimension.group_index,
        '质检组-' || lpad(group_dimension.group_index::text, 2, '0') AS group_name
    FROM tasks AS task
    CROSS JOIN LATERAL (
        VALUES
            (((task.task_index - 1) % 12) + 1),
            (((task.task_index + 3) % 12) + 1),
            (((task.task_index + 7) % 12) + 1)
    ) AS group_dimension(group_index)
),
active_rows AS (
    SELECT
        date_dimension.day_index,
        date_dimension.stat_date,
        task_group.*,
        active_slot,
        (
            (
                date_dimension.day_index
                + task_group.task_index
                + task_group.group_index
                + active_slot * 3
            ) % 10
        ) + 1 AS employee_slot
    FROM dates AS date_dimension
    CROSS JOIN task_groups AS task_group
    CROSS JOIN generate_series(0, 2) AS slot(active_slot)
),
submitted AS (
    SELECT
        active.*,
        'E' || lpad(
            (((group_index - 1) * 10) + employee_slot)::text,
            3,
            '0'
        ) AS employee_id,
        60 + (
            (
                task_index * 7
                + day_index * 3
                + employee_slot * 5
            ) % 61
        ) AS annotation_total,
        CASE
            -- 零分母边界：任务仍存在，但整个周期没有提交量。
            WHEN task_index = 23 THEN 0
            ELSE
                60
                + (
                    (
                        task_index * 7
                        + day_index * 3
                        + employee_slot * 5
                    ) % 61
                )
                - ((task_index + day_index + employee_slot) % 9)
        END AS annotation_submitted
    FROM active_rows AS active
),
categorized AS (
    SELECT
        submitted.*,
        floor(
            annotation_submitted
            * (
                58
                + (
                    (
                        task_index * 3
                        + day_index
                        + employee_slot
                    ) % 31
                )
            )
            / 100.0
        )::integer AS good_submitted
    FROM submitted
),
allocated AS (
    SELECT
        categorized.*,
        annotation_submitted - good_submitted AS bad_submitted,
        ceil(good_submitted * 0.18)::integer AS good_expect_alloc,
        ceil((annotation_submitted - good_submitted) * 0.35)::integer
            AS bad_expect_alloc,
        CASE
            -- 未分配边界：有标注提交，但该员工当日没有验收分配。
            WHEN task_index = 1
                AND day_index = 0
                AND group_index = 1
                AND active_slot = 0
                THEN 0
            -- 覆盖率 > 100% 边界：重复验收量大于唯一标注提交量。
            WHEN task_index = 24 THEN good_submitted
            ELSE least(
                good_submitted,
                ceil(
                    good_submitted
                    * (0.14 + ((task_index + day_index) % 4) * 0.02)
                )::integer
            )
        END AS good_actual_alloc,
        CASE
            WHEN task_index = 1
                AND day_index = 0
                AND group_index = 1
                AND active_slot = 0
                THEN 0
            WHEN task_index = 24
                THEN (annotation_submitted - good_submitted) + 6
            ELSE least(
                annotation_submitted - good_submitted,
                ceil(
                    (annotation_submitted - good_submitted)
                    * (0.30 + ((task_index + employee_slot) % 4) * 0.04)
                )::integer
            )
        END AS bad_actual_alloc
    FROM categorized
),
completed AS (
    SELECT
        allocated.*,
        CASE
            -- 低完成率边界。
            WHEN task_index = 8 THEN floor(good_actual_alloc * 0.45)::integer
            ELSE greatest(
                good_actual_alloc
                - ((day_index + employee_slot) % 2),
                0
            )
        END AS good_actual_complete,
        CASE
            WHEN task_index = 8 THEN floor(bad_actual_alloc * 0.35)::integer
            ELSE greatest(
                bad_actual_alloc
                - ((task_index + day_index + employee_slot) % 3),
                0
            )
        END AS bad_actual_complete
    FROM allocated
),
accepted AS (
    SELECT
        completed.*,
        CASE
            -- 低通过率边界。
            WHEN task_index = 12
                THEN floor(good_actual_complete * 0.60)::integer
            ELSE greatest(
                good_actual_complete
                - ((task_index + day_index) % 2),
                0
            )
        END AS good_actual_pass,
        CASE
            WHEN task_index = 12
                THEN floor(bad_actual_complete * 0.40)::integer
            ELSE greatest(
                bad_actual_complete
                - (1 + ((task_index + employee_slot) % 2)),
                0
            )
        END AS bad_actual_pass
    FROM completed
),
option_labeled AS (
    SELECT
        accepted.*,
        CASE
            WHEN (task_index + day_index + group_index) % 2 = 0
                THEN '驾驶行为分类'
            ELSE '障碍物类型'
        END AS question_label
    FROM accepted
),
option_named AS (
    SELECT
        option_labeled.*,
        CASE
            WHEN question_label = '驾驶行为分类' THEN
                (ARRAY['CUT_IN', 'MERGE', 'YIELD', 'FOLLOW_TOO_CLOSE'])[
                    ((task_index + day_index + employee_slot) % 4) + 1
                ]
            ELSE
                (ARRAY['STATIC', 'PEDESTRIAN', 'VEHICLE', 'CONE'])[
                    ((task_index + day_index + employee_slot) % 4) + 1
                ]
        END AS question_option
    FROM option_labeled
),
option_counted AS (
    SELECT
        option_named.*,
        least(
            bad_submitted,
            CASE
                WHEN bad_submitted = 0 THEN 0
                ELSE 1 + (
                    (
                        task_index
                        + day_index
                        + group_index
                        + employee_slot
                    ) % 9
                )
            END
        ) AS option_submitted
    FROM option_named
),
option_allocated AS (
    SELECT
        option_counted.*,
        ceil(option_submitted * 0.55)::integer AS option_expect_alloc,
        ceil(option_submitted * 0.50)::integer AS option_actual_alloc
    FROM option_counted
),
option_completed AS (
    SELECT
        option_allocated.*,
        CASE
            -- 问题选项低完成率边界。
            WHEN question_option = 'YIELD'
                THEN floor(option_actual_alloc * 0.30)::integer
            ELSE greatest(
                option_actual_alloc
                - ((day_index + employee_slot) % 2),
                0
            )
        END AS option_actual_complete
    FROM option_allocated
),
final_seed AS (
    SELECT
        option_completed.*,
        CASE
            -- 问题选项低通过率边界。
            WHEN question_option = 'STATIC'
                THEN floor(option_actual_complete * 0.40)::integer
            ELSE greatest(
                option_actual_complete
                - ((task_index + day_index) % 2),
                0
            )
        END AS option_actual_pass
    FROM option_completed
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
        'expect_alloc', good_expect_alloc,
        'actual_alloc', good_actual_alloc,
        'actual_complete', good_actual_complete,
        'correct', good_actual_pass,
        'incorrect', good_actual_complete - good_actual_pass,
        'conclusion', CASE
            WHEN good_actual_alloc = 0 THEN NULL
            WHEN good_actual_complete < good_actual_alloc THEN 'pending'
            WHEN good_actual_pass * 1.0 / NULLIF(good_actual_complete, 0) >= 0.8
                THEN 'pass'
            ELSE 'reject'
        END,
        'expect_pass', good_actual_pass,
        'expect_reject', good_actual_complete - good_actual_pass,
        'actual_pass', good_actual_pass,
        'actual_reject', good_actual_complete - good_actual_pass,
        'exec_status', CASE
            WHEN good_actual_complete < good_actual_alloc THEN 'PENDING'
            WHEN good_actual_complete = 0 THEN NULL
            WHEN good_actual_pass * 1.0 / NULLIF(good_actual_complete, 0) >= 0.8
                THEN 'PASS_DONE'
            ELSE 'REJECT_DONE'
        END
    ),
    jsonb_build_object(
        'annotation_total', bad_submitted,
        'annotation_submitted', bad_submitted,
        'expect_alloc', bad_expect_alloc,
        'actual_alloc', bad_actual_alloc,
        'actual_complete', bad_actual_complete,
        'correct', bad_actual_pass,
        'incorrect', bad_actual_complete - bad_actual_pass,
        'conclusion', CASE
            WHEN bad_actual_alloc = 0 THEN NULL
            WHEN bad_actual_complete < bad_actual_alloc THEN 'pending'
            WHEN bad_actual_pass * 1.0 / NULLIF(bad_actual_complete, 0) >= 0.8
                THEN 'pass'
            ELSE 'reject'
        END,
        'expect_pass', bad_actual_pass,
        'expect_reject', bad_actual_complete - bad_actual_pass,
        'actual_pass', bad_actual_pass,
        'actual_reject', bad_actual_complete - bad_actual_pass,
        'exec_status', CASE
            WHEN bad_actual_complete < bad_actual_alloc THEN 'PENDING'
            WHEN bad_actual_complete = 0 THEN NULL
            WHEN bad_actual_pass * 1.0 / NULLIF(bad_actual_complete, 0) >= 0.8
                THEN 'PASS_DONE'
            ELSE 'REJECT_DONE'
        END
    ),
    jsonb_build_object(
        question_label,
        jsonb_build_object(
            question_option,
            jsonb_build_object(
                'annotation_total', option_submitted,
                'annotation_submitted', option_submitted,
                'expect_alloc', option_expect_alloc,
                'actual_alloc', option_actual_alloc,
                'actual_complete', option_actual_complete,
                'correct', option_actual_pass,
                'incorrect', option_actual_complete - option_actual_pass,
                'conclusion', CASE
                    WHEN option_actual_alloc = 0 THEN NULL
                    WHEN option_actual_complete < option_actual_alloc THEN 'pending'
                    WHEN option_actual_pass * 1.0
                        / NULLIF(option_actual_complete, 0) >= 0.8
                        THEN 'pass'
                    ELSE 'reject'
                END,
                'expect_pass', option_actual_pass,
                'expect_reject', option_actual_complete - option_actual_pass,
                'actual_pass', option_actual_pass,
                'actual_reject', option_actual_complete - option_actual_pass,
                'exec_status', CASE
                    WHEN option_actual_complete < option_actual_alloc THEN 'PENDING'
                    WHEN option_actual_complete = 0 THEN NULL
                    WHEN option_actual_pass * 1.0
                        / NULLIF(option_actual_complete, 0) >= 0.8
                        THEN 'PASS_DONE'
                    ELSE 'REJECT_DONE'
                END
            )
        )
    ),
    CASE
        WHEN good_actual_complete + bad_actual_complete
            < good_actual_alloc + bad_actual_alloc
            THEN NULL
        ELSE 'lead-' || lpad(group_index::text, 2, '0')
    END,
    CASE
        WHEN good_actual_complete + bad_actual_complete
            < good_actual_alloc + bad_actual_alloc
            THEN NULL
        ELSE stat_date::timestamp + interval '20 hours'
    END,
    CASE
        WHEN good_actual_complete + bad_actual_complete
            < good_actual_alloc + bad_actual_alloc
            THEN NULL
        ELSE 'lead-' || lpad(group_index::text, 2, '0')
    END,
    CASE
        WHEN good_actual_complete + bad_actual_complete
            < good_actual_alloc + bad_actual_alloc
            THEN NULL
        ELSE stat_date::timestamp + interval '20 hours 10 minutes'
    END,
    CASE
        WHEN good_actual_alloc + bad_actual_alloc = 0
            THEN '本地固定种子：该员工当日未分配验收'
        WHEN good_actual_complete + bad_actual_complete
            < good_actual_alloc + bad_actual_alloc
            THEN '本地固定种子：仍有验收任务未完成'
        ELSE '本地固定种子：已完成模拟验收'
    END,
    stat_date::timestamp
        + interval '18 hours'
        + ((employee_slot + task_index) % 60) * interval '1 minute',
    stat_date::timestamp
        + interval '18 hours'
        + ((employee_slot + task_index) % 60) * interval '1 minute'
FROM final_seed;
