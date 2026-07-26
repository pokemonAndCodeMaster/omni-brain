import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getSnapshotRows } from '../api/snapshot'
import type { MetricState, SnapshotRow } from '../types/snapshot'
import {
  buildSnapshotChartCard,
  resolveSnapshotChartCard,
} from './snapshotChart'

vi.mock('../api/snapshot', () => ({
  getSnapshotRows: vi.fn(),
}))

function metric(
  actualComplete: number,
  actualPass: number,
  actualReject: number,
): MetricState {
  return {
    annotation_total: 0,
    annotation_submitted: 0,
    expect_alloc: 0,
    actual_alloc: actualComplete,
    actual_complete: actualComplete,
    correct: 0,
    incorrect: 0,
    expect_pass: 0,
    expect_reject: 0,
    actual_pass: actualPass,
    actual_reject: actualReject,
    conclusion: null,
    exec_status: null,
  }
}

function row(
  id: number,
  statDate: string,
  good: MetricState,
  bad: MetricState,
): SnapshotRow {
  return {
    id,
    stat_date: statDate,
    project_name: '城区/高速',
    scene_name: '城区交互任务-A',
    group_name: '一组',
    employee_id: `E00${id}`,
    annotation_total: 20,
    annotation_submitted: 18,
    good_metrics: good,
    bad_metrics: bad,
    option_metrics: {},
    confirmed_by: null,
    confirmed_at: null,
    executed_by: null,
    executed_at: null,
    execution_note: null,
    computed_at: `${statDate}T10:00:00Z`,
    updated_at: `${statDate}T10:00:00Z`,
  }
}

const rows = [
  row(1, '2026-07-25', metric(4, 3, 1), metric(2, 1, 1)),
  row(2, '2026-07-26', metric(8, 7, 1), metric(3, 2, 1)),
]

function builder(chartType: 'bar' | 'pie' = 'bar') {
  return {
    title: '当前表格结果',
    description: '同一标注任务内比较',
    sourceId: 'manual-qc-snapshot-employee-day',
    chartType,
    dimensionId: chartType === 'pie' ? 'stat_date' : 'scene_name',
    measureIds: ['accept_completed', 'accept_rejected'],
    filters: { project_name: '城区/高速' },
    stacked: false,
    showLegend: true,
    showLabels: false,
    smooth: true,
    palette: 'quality' as const,
    orientation: 'vertical' as const,
  }
}

describe('snapshot dashboard card', () => {
  beforeEach(() => {
    vi.mocked(getSnapshotRows).mockResolvedValue({
      schema_version: 'snapshot-jsonb-v20260709',
      items: rows,
      total: rows.length,
      computed_at: '2026-07-26T10:00:00Z',
    })
  })

  it('保存可重新执行的数据定义，并用最新快照聚合', async () => {
    const card = buildSnapshotChartCard(builder())
    const result = await resolveSnapshotChartCard(card)

    expect(card.query).toMatchObject({
      dimensionId: 'scene_name',
      filters: { project_name: '城区/高速' },
    })
    expect(card.layout).toMatchObject({ w: 6, h: 6 })
    expect(result.categories).toEqual(['城区交互任务-A'])
    expect(result.series.map((series) => series.values)).toEqual([[17], [4]])
    expect(result.source).toMatchObject({
      rowCount: 2,
      filterSummary: '项目：城区/高速',
    })
  })

  it('饼图只解析首个指标，避免多指标语义混乱', async () => {
    const card = buildSnapshotChartCard(builder('pie'))
    const result = await resolveSnapshotChartCard(card)

    expect(result.categories).toEqual(['2026-07-25', '2026-07-26'])
    expect(result.series).toHaveLength(1)
    expect(result.series[0]?.values).toEqual([6, 11])
  })
})
