import { describe, expect, it } from 'vitest'
import type { MetricState, SnapshotRow } from '../types/snapshot'
import { defaultOverviewCards, resolveOverviewMetric } from './snapshotOverview'

function metric(
  submitted: number,
  allocated: number,
  completed: number,
  passed: number,
  rejected: number,
): MetricState {
  return {
    annotation_total: submitted,
    annotation_submitted: submitted,
    expect_alloc: allocated,
    actual_alloc: allocated,
    actual_complete: completed,
    correct: 0,
    incorrect: 0,
    expect_pass: passed,
    expect_reject: rejected,
    actual_pass: passed,
    actual_reject: rejected,
    conclusion: null,
    exec_status: null,
  }
}

function row(
  id: number,
  projectName: string,
  good: MetricState,
  bad: MetricState,
): SnapshotRow {
  return {
    id,
    stat_date: '2026-07-26',
    project_name: projectName,
    scene_name: `任务-${id}`,
    group_name: '一组',
    employee_id: `E-${id}`,
    annotation_total:
      good.annotation_submitted + bad.annotation_submitted,
    annotation_submitted:
      good.annotation_submitted + bad.annotation_submitted,
    good_metrics: good,
    bad_metrics: bad,
    option_metrics: {},
    confirmed_by: null,
    confirmed_at: null,
    executed_by: null,
    executed_at: null,
    execution_note: null,
    computed_at: '2026-07-26T10:00:00Z',
    updated_at: '2026-07-26T10:00:00Z',
  }
}

describe('业务总览指标', () => {
  const rows = [
    row(1, '园区', metric(80, 20, 18, 16, 2), metric(20, 10, 8, 5, 3)),
    row(
      2,
      '城区/高速',
      metric(45, 12, 10, 9, 1),
      metric(5, 3, 2, 1, 1),
    ),
  ]

  it('同一张卡同时给出全量和项目拆分', () => {
    const card = defaultOverviewCards()[0]!
    const result = resolveOverviewMetric(card, rows)

    expect(result.primaryValue).toBe(150)
    expect(result.details).toEqual([
      { label: 'Good', value: '125' },
      { label: 'Bad', value: '25' },
      { label: 'Good 占比', value: '83.3%' },
    ])
    expect(result.projects).toHaveLength(2)
    expect(result.projects.map((item) => item.projectName)).toEqual([
      '城区/高速',
      '园区',
    ])
  })
})
