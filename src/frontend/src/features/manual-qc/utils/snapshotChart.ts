import type {
  ChartBuilderValue,
  DashboardChartCard,
} from '@/shared/dashboard/types'
import type { SceneAggregate } from '../types/snapshot'

interface ChartMeasure {
  id: string
  name: string
  value: (row: SceneAggregate) => number
}

const dimensionLabels: Record<string, string> = {
  scene_name: '场景',
  stat_date: '快照日期',
}

const measures: ChartMeasure[] = [
  {
    id: 'annotation_submitted',
    name: '标注提交',
    value: (row) => row.annotation_submitted,
  },
  {
    id: 'accept_completed',
    name: '验收完成',
    value: (row) =>
      row.good_metrics.actual_complete + row.bad_metrics.actual_complete,
  },
  {
    id: 'accept_passed',
    name: '验收通过',
    value: (row) =>
      row.good_metrics.actual_pass + row.bad_metrics.actual_pass,
  },
  {
    id: 'accept_rejected',
    name: '验收打回',
    value: (row) =>
      row.good_metrics.actual_reject + row.bad_metrics.actual_reject,
  },
]

export const snapshotChartBuilderOptions = {
  dimensions: Object.entries(dimensionLabels).map(([id, label]) => ({
    id,
    label,
  })),
  measures: measures.map(({ id, name }) => ({ id, label: name })),
  defaultDimensionId: 'scene_name',
  defaultMeasureIds: ['accept_completed', 'accept_rejected'],
}

let sequence = 0

function nextCardId(): string {
  sequence += 1
  return `snapshot-chart-${Date.now()}-${sequence}`
}

export function buildSnapshotChartCard(
  rows: SceneAggregate[],
  builder: ChartBuilderValue,
  filterSummary: string,
  sourceLabel: string,
): DashboardChartCard {
  const selectedMeasures = measures.filter((measure) =>
    builder.measureIds.includes(measure.id),
  )
  const chartMeasures =
    builder.chartType === 'pie' ? selectedMeasures.slice(0, 1) : selectedMeasures
  const buckets = new Map<string, Map<string, number>>()

  for (const row of rows) {
    const category =
      builder.dimensionId === 'stat_date' ? row.stat_date : row.scene_name
    const current = buckets.get(category) ?? new Map<string, number>()
    for (const measure of chartMeasures) {
      current.set(
        measure.id,
        (current.get(measure.id) ?? 0) + measure.value(row),
      )
    }
    buckets.set(category, current)
  }

  const categories = [...buckets.keys()].sort()
  return {
    id: nextCardId(),
    kind: 'chart',
    title: builder.title,
    description: `${dimensionLabels[builder.dimensionId] ?? builder.dimensionId}聚合 · 当前数据快照`,
    chartType: builder.chartType,
    categories,
    series: chartMeasures.map((measure) => ({
      id: measure.id,
      name: measure.name,
      unit: '条',
      values: categories.map(
        (category) => buckets.get(category)?.get(measure.id) ?? 0,
      ),
    })),
    source: {
      sourceId: 'manual-qc-snapshot',
      sourceLabel,
      rowCount: rows.length,
      filterSummary,
      generatedAt: new Date().toISOString(),
    },
  }
}
