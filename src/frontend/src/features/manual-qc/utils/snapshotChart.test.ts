import { describe, expect, it } from 'vitest'
import type { SceneAggregate } from '../types/snapshot'
import { buildSnapshotChartCard } from './snapshotChart'

function metric(
  actualComplete: number,
  actualPass: number,
  actualReject: number,
) {
  return {
    annotation_total: 0,
    annotation_submitted: 0,
    expect_alloc: 0,
    actual_alloc: 0,
    actual_complete: actualComplete,
    correct: 0,
    incorrect: 0,
    expect_pass: 0,
    expect_reject: 0,
    actual_pass: actualPass,
    actual_reject: actualReject,
  }
}

const rows: SceneAggregate[] = [
  {
    stat_date: '2026-07-25',
    scene_name: '城区交互',
    annotation_total: 10,
    annotation_submitted: 9,
    good_metrics: metric(4, 3, 1),
    bad_metrics: metric(2, 1, 1),
    computed_at: '2026-07-25T10:00:00Z',
  },
  {
    stat_date: '2026-07-26',
    scene_name: '城区交互',
    annotation_total: 20,
    annotation_submitted: 18,
    good_metrics: metric(8, 7, 1),
    bad_metrics: metric(3, 2, 1),
    computed_at: '2026-07-26T10:00:00Z',
  },
]

describe('buildSnapshotChartCard', () => {
  it('按维度聚合所选指标并保留来源上下文', () => {
    const card = buildSnapshotChartCard(
      rows,
      {
        title: '当前表格结果',
        chartType: 'bar',
        dimensionId: 'scene_name',
        measureIds: ['accept_completed', 'accept_rejected'],
      },
      '场景=城区交互',
      '验收快照明细表',
    )

    expect(card.categories).toEqual(['城区交互'])
    expect(card.series.map((series) => series.values)).toEqual([[17], [4]])
    expect(card.source).toMatchObject({
      sourceLabel: '验收快照明细表',
      rowCount: 2,
      filterSummary: '场景=城区交互',
    })
  })

  it('饼图只使用首个指标，避免多指标语义混乱', () => {
    const card = buildSnapshotChartCard(
      rows,
      {
        title: '日期统计',
        chartType: 'pie',
        dimensionId: 'stat_date',
        measureIds: ['accept_completed', 'accept_rejected'],
      },
      '',
      '验收快照页面',
    )

    expect(card.categories).toEqual(['2026-07-25', '2026-07-26'])
    expect(card.series).toHaveLength(1)
    expect(card.series[0]?.values).toEqual([6, 11])
  })
})
