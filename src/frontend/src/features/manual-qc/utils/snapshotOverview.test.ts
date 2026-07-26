import { describe, expect, it } from 'vitest'
import type { MetricState, SnapshotRow } from '../types/snapshot'
import type { LegacyDashboardMetricCard } from '@/shared/dashboard/types'
import {
  defaultOverviewCards,
  duplicateOverviewCard,
  normalizeOverviewCard,
  resolveOverviewMetric,
  restoreOverviewPreset,
} from './snapshotOverview'

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

    expect(result.values.submitted).toMatchObject({
      value: 150,
      formattedValue: '150',
    })
    expect(result.values.good).toMatchObject({
      value: 125,
      formattedValue: '125',
    })
    expect(result.values['good-rate']).toMatchObject({
      formattedValue: '83.3%',
    })
    expect(result.breakdowns['by-project']).toHaveLength(2)
    expect(result.breakdowns['by-project']?.map((item) => item.label)).toEqual([
      '城区/高速',
      '园区',
    ])
  })

  it('把旧总览配置迁移成指标块并保留用户样式和布局', () => {
    const legacy: LegacyDashboardMetricCard = {
      id: 'legacy-card',
      kind: 'metric',
      title: '我的验收进度',
      description: '旧配置',
      metricId: 'acceptance_completion',
      jumpTarget: 'acceptance-progress',
      style: {
        accentColor: '#123456',
        backgroundColor: '#ffffff',
        textColor: '#111111',
        titleSize: 17,
        valueSize: 42,
        density: 'compact',
        showProjectBreakdown: false,
      },
      layout: { x: 2, y: 1, w: 5, h: 4, minW: 3, minH: 3 },
    }

    const migrated = normalizeOverviewCard(legacy)
    expect(migrated.title).toBe('我的验收进度')
    expect(migrated.origin).toMatchObject({
      type: 'user',
      presetId: 'manual-qc.acceptance-progress-overview',
    })
    expect(migrated.blocks.some((block) => block.kind === 'breakdown')).toBe(false)
    expect(
      migrated.blocks.find(
        (block) =>
          block.kind === 'metric-value' && block.emphasis === 'primary',
      ),
    ).toMatchObject({ style: { valueSize: 42 } })
  })

  it('复制品脱离系统预设，恢复默认只重置原卡内容并保留布局', () => {
    const card = defaultOverviewCards()[0]!
    const copy = duplicateOverviewCard(card)
    expect(copy.origin).toEqual({ type: 'user' })
    expect(copy.title).toContain('副本')

    const edited = structuredClone(card)
    edited.origin.type = 'user'
    edited.title = '已修改标题'
    edited.layout.x = 6
    const restored = restoreOverviewPreset(edited)
    expect(restored?.title).toBe('标注产出与质量构成')
    expect(restored?.layout.x).toBe(6)
    expect(copy.title).toContain('副本')
  })
})
