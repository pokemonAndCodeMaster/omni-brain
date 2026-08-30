import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  postAnalysisFacets,
  postAnalysisQuery,
} from '../analysis/api/analysis'
import { metricReferenceKey } from '../analysis/utils'
import type {
  AnalysisMetricReference,
  AnalysisQuery,
} from '../analysis/types/analysis'
import type { SnapshotQuery } from '../types/snapshot'
import type { LegacyDashboardChartCard } from '@/shared/dashboard/types'
import {
  defaultSnapshotChartCards,
  normalizeSnapshotChartCard,
  resolveSnapshotChartCard,
} from './snapshotChart'

vi.mock('../analysis/api/analysis', () => ({
  postAnalysisQuery: vi.fn(),
  postAnalysisFacets: vi.fn(),
}))

const pageQuery: SnapshotQuery = {
  stat_date_start: '2026-07-13',
  stat_date_end: '2026-07-26',
  project_name: '',
  scene_name: '',
  group_name: '',
  employee_id: '',
}

function measureValue(
  reference: AnalysisMetricReference,
  task: string,
): number {
  const taskOffset = task === '任务-A' ? 0 : 5
  return {
    'acceptance.allocated': 20 + taskOffset,
    'acceptance.completed': 18 + taskOffset,
    'acceptance.completion_rate': task === '任务-A' ? 90 : 92,
    'acceptance.passed': 16 + taskOffset,
    'acceptance.rejected': 2,
    'acceptance.pass_rate': task === '任务-A' ? 88.9 : 91.3,
    'annotation.good_submitted': 80 + taskOffset,
    'annotation.bad_submitted': 20,
    'annotation.good_rate': task === '任务-A' ? 80 : 81,
  }[reference.id] ?? 0
}

function queryResult(query: AnalysisQuery) {
  const rows = ['任务-A', '任务-B'].map((task, index) => ({
    key: task,
    dimensions: Object.fromEntries(
      query.groupBy.map((dimension) => [
        dimension,
        dimension === 'task'
          ? task
          : dimension === 'project'
            ? index === 0 ? '园区' : '城区/高速'
            : `值-${index + 1}`,
      ]),
    ),
    measures: Object.fromEntries(
      query.measures.map((reference) => [
        metricReferenceKey(reference),
        measureValue(reference, task),
      ]),
    ),
    computedAt: '2026-07-26T10:00:00Z',
  }))
  return {
    sourceId: query.sourceId,
    groupBy: query.groupBy,
    rows,
    total: rows.length,
    page: query.page ?? { number: 1, size: 200 },
    computedAt: '2026-07-26T10:00:00Z',
    warnings: [],
  }
}

describe('snapshot chart V2', () => {
  beforeEach(() => {
    vi.mocked(postAnalysisQuery).mockImplementation(async (query) =>
      queryResult(query),
    )
    vi.mocked(postAnalysisFacets).mockImplementation(async (request) => ({
      dimensionId: request.dimensionId,
      values:
        request.dimensionId === 'question_label'
          ? ['驾驶行为分类']
          : ['CUT_IN', 'MERGE'],
    }))
  })

  it('把数量与比例图层分别放入受控坐标轴', async () => {
    const card = defaultSnapshotChartCards().find(
      (item) => item.id === 'acceptance-progress',
    )!
    const result = await resolveSnapshotChartCard(card, pageQuery)

    expect(postAnalysisQuery).toHaveBeenCalledTimes(3)
    expect(result.categories).toEqual(['任务-A', '任务-B'])
    expect(result.series).toMatchObject([
      {
        id: 'allocated',
        axisId: 'count-axis',
        renderAs: 'bar',
        values: [20, 25],
      },
      {
        id: 'completed',
        axisId: 'count-axis',
        renderAs: 'bar',
        values: [18, 23],
      },
      {
        id: 'completion-rate',
        axisId: 'rate-axis',
        renderAs: 'line',
        values: [90, 92],
      },
    ])
    expect(result.source.sourceLabel).toBe('人工质检受控分析接口')
  })

  it('把旧组合图迁移为多个普通图层并保留布局', () => {
    const legacy: LegacyDashboardChartCard = {
      id: 'legacy',
      kind: 'chart',
      title: '旧组合图',
      description: '',
      query: {
        sourceId: 'manual-qc-snapshot-employee-day',
        dimensionId: 'stat_date',
        measureIds: ['accept_completed', 'completion_rate'],
        filters: {
          stat_date_start: '2026-07-13',
          stat_date_end: '2026-07-26',
        },
        filterSummary: '',
      },
      style: {
        chartType: 'combo',
        stacked: false,
        showLegend: true,
        showLabels: false,
        smooth: true,
        palette: 'business',
        orientation: 'vertical',
        legendPosition: 'top',
        fontScale: 'medium',
        showArea: false,
        sortDirection: 'natural',
        maxCategories: 20,
      },
      layout: { x: 2, y: 3, w: 7, h: 6, minW: 3, minH: 4 },
    }

    const migrated = normalizeSnapshotChartCard(legacy)

    expect(migrated.baseQuery).toMatchObject({
      categoryDimension: 'date',
      filters: [
        {
          target: { id: 'date' },
          operator: 'between',
          value: ['2026-07-13', '2026-07-26'],
        },
      ],
    })
    expect(migrated.layers).toMatchObject([
      {
        metric: { id: 'acceptance.completed' },
        renderAs: 'bar',
        axisId: 'count-axis',
      },
      {
        metric: { id: 'acceptance.completion_rate' },
        renderAs: 'line',
        axisId: 'rate-axis',
      },
    ])
    expect(migrated.layout).toMatchObject({ x: 2, y: 3, w: 7, h: 6 })
  })

  it('问题选项预设从受控 Facet 展开分类并按数量倒排', async () => {
    vi.mocked(postAnalysisQuery).mockImplementation(async (query) => {
      const reference = query.measures[0]!
      const option = reference.parameters?.questionOption ?? ''
      const value = option === 'CUT_IN' ? 36 : 18
      return {
        sourceId: query.sourceId,
        groupBy: query.groupBy,
        rows: [
          {
            key: '园区',
            dimensions: { project: '园区' },
            measures: { [metricReferenceKey(reference)]: value },
            computedAt: '2026-07-26T10:00:00Z',
          },
        ],
        total: 1,
        page: query.page ?? { number: 1, size: 200 },
        computedAt: '2026-07-26T10:00:00Z',
        warnings: [],
      }
    })
    const card = defaultSnapshotChartCards().find(
      (item) => item.id === 'bad-options',
    )!
    const result = await resolveSnapshotChartCard(card, pageQuery)

    expect(result.categories).toEqual([
      '驾驶行为分类 / CUT_IN',
      '驾驶行为分类 / MERGE',
    ])
    expect(result.series[0]?.values).toEqual([36, 18])
    expect(postAnalysisFacets).toHaveBeenCalledTimes(2)
  })

  it('一个图层可以按项目拆成多条序列', async () => {
    const card = defaultSnapshotChartCards().find(
      (item) => item.id === 'acceptance-progress',
    )!
    card.layers = [card.layers[0]!]
    card.layers[0]!.splitBy = { dimension: 'project' }
    const result = await resolveSnapshotChartCard(card, pageQuery)

    expect(result.series.map((item) => item.name)).toEqual([
      '验收分配量 · 城区/高速',
      '验收分配量 · 园区',
    ])
    expect(result.series.map((item) => item.values)).toEqual([
      [null, 25],
      [20, null],
    ])
  })
})
