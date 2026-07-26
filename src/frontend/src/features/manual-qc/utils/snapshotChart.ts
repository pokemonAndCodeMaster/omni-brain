import { getSnapshotRows } from '../api/snapshot'
import type {
  MetricTotals,
  SnapshotQuery,
  SnapshotRow,
} from '../types/snapshot'
import type {
  ChartBuilderOptions,
  ChartBuilderValue,
  DashboardChartCard,
  DashboardChartResult,
} from '@/shared/dashboard/types'

const SOURCE_ID = 'manual-qc-snapshot-employee-day'

const dimensionLabels: Record<string, string> = {
  stat_date: '日期',
  project_name: '项目',
  scene_name: '标注任务',
  group_name: '组',
  employee_id: '标注员',
  result_type: 'Good / Bad',
  question_label: '问题标签',
  question_option: '问题标签 / 选项',
}

interface MeasureContribution {
  numerator: number
  denominator?: number
}

interface ChartMeasure {
  id: string
  name: string
  unit: string
  value: (
    row: SnapshotRow,
    metric?: MetricTotals,
  ) => MeasureContribution
}

const measures: ChartMeasure[] = [
  {
    id: 'annotation_submitted',
    name: '标注提交',
    unit: '条',
    value: (row, metric) => ({
      numerator: metric?.annotation_submitted ?? row.annotation_submitted,
    }),
  },
  {
    id: 'good_annotation_submitted',
    name: 'Good 标注',
    unit: '条',
    value: (row) => ({
      numerator: row.good_metrics.annotation_submitted,
    }),
  },
  {
    id: 'bad_annotation_submitted',
    name: 'Bad 标注',
    unit: '条',
    value: (row) => ({
      numerator: row.bad_metrics.annotation_submitted,
    }),
  },
  {
    id: 'good_rate',
    name: 'Good 占比',
    unit: '%',
    value: (row) => ({
      numerator: row.good_metrics.annotation_submitted,
      denominator: row.annotation_submitted,
    }),
  },
  {
    id: 'bad_rate',
    name: 'Bad 占比',
    unit: '%',
    value: (row) => ({
      numerator: row.bad_metrics.annotation_submitted,
      denominator: row.annotation_submitted,
    }),
  },
  {
    id: 'accept_allocated',
    name: '验收分配',
    unit: '条',
    value: (row, metric) => ({
      numerator:
        metric?.actual_alloc ??
        row.good_metrics.actual_alloc + row.bad_metrics.actual_alloc,
    }),
  },
  {
    id: 'accept_completed',
    name: '验收完成',
    unit: '条',
    value: (row, metric) => ({
      numerator:
        metric?.actual_complete ??
        row.good_metrics.actual_complete + row.bad_metrics.actual_complete,
    }),
  },
  {
    id: 'accept_pending',
    name: '验收未完成',
    unit: '条',
    value: (row, metric) => ({
      numerator: metric
        ? Math.max(0, metric.actual_alloc - metric.actual_complete)
        : Math.max(
            0,
            row.good_metrics.actual_alloc +
              row.bad_metrics.actual_alloc -
              row.good_metrics.actual_complete -
              row.bad_metrics.actual_complete,
          ),
    }),
  },
  {
    id: 'accept_passed',
    name: '验收通过',
    unit: '条',
    value: (row, metric) => ({
      numerator:
        metric?.actual_pass ??
        row.good_metrics.actual_pass + row.bad_metrics.actual_pass,
    }),
  },
  {
    id: 'accept_rejected',
    name: '验收打回',
    unit: '条',
    value: (row, metric) => ({
      numerator:
        metric?.actual_reject ??
        row.good_metrics.actual_reject + row.bad_metrics.actual_reject,
    }),
  },
  {
    id: 'completion_rate',
    name: '验收完成率',
    unit: '%',
    value: (row, metric) => ({
      numerator:
        metric?.actual_complete ??
        row.good_metrics.actual_complete + row.bad_metrics.actual_complete,
      denominator:
        metric?.actual_alloc ??
        row.good_metrics.actual_alloc + row.bad_metrics.actual_alloc,
    }),
  },
  {
    id: 'pass_rate',
    name: '验收通过率',
    unit: '%',
    value: (row, metric) => ({
      numerator:
        metric?.actual_pass ??
        row.good_metrics.actual_pass + row.bad_metrics.actual_pass,
      denominator:
        metric?.actual_complete ??
        row.good_metrics.actual_complete + row.bad_metrics.actual_complete,
    }),
  },
  {
    id: 'reject_rate',
    name: '验收打回率',
    unit: '%',
    value: (row, metric) => ({
      numerator:
        metric?.actual_reject ??
        row.good_metrics.actual_reject + row.bad_metrics.actual_reject,
      denominator:
        metric?.actual_complete ??
        row.good_metrics.actual_complete + row.bad_metrics.actual_complete,
    }),
  },
]

const filterLabels: Record<string, string> = {
  stat_date_start: '起始日期',
  stat_date_end: '截止日期',
  project_name: '项目',
  scene_name: '标注任务',
  group_name: '组',
  employee_id: '标注员',
  question_label: '问题标签',
}

export function createSnapshotChartBuilderOptions(
  taskOptions: string[],
): ChartBuilderOptions {
  return {
    sources: [{ id: SOURCE_ID, label: '人工质检快照（员工日粒度）' }],
    dimensions: Object.entries(dimensionLabels).map(([id, label]) => ({
      id,
      label,
    })),
    measures: measures.map(({ id, name }) => ({ id, label: name })),
    filters: [
      { id: 'stat_date_start', label: '起始日期', type: 'date' },
      { id: 'stat_date_end', label: '截止日期', type: 'date' },
      {
        id: 'project_name',
        label: '项目',
        type: 'select',
        options: ['园区', '城区/高速'],
      },
      {
        id: 'scene_name',
        label: '标注任务',
        type: 'select',
        options: taskOptions,
      },
      {
        id: 'group_name',
        label: '组',
        type: 'text',
        placeholder: '精确组名',
      },
      {
        id: 'employee_id',
        label: '标注员',
        type: 'text',
        placeholder: '精确工号',
      },
      {
        id: 'question_label',
        label: '问题标签',
        type: 'text',
        placeholder: '仅用于问题选项维度',
      },
    ],
    defaultSourceId: SOURCE_ID,
    defaultDimensionId: 'scene_name',
    defaultMeasureIds: ['accept_completed', 'accept_rejected'],
  }
}

let sequence = 0

function nextCardId(): string {
  sequence += 1
  return `snapshot-chart-${Date.now()}-${sequence}`
}

export function summarizeSnapshotFilters(
  filters: Record<string, string>,
): string {
  const parts = Object.entries(filters)
    .filter(([, value]) => value)
    .map(([key, value]) => `${filterLabels[key] ?? key}：${value}`)
  return parts.join(' · ') || '全部实验数据'
}

export function buildSnapshotChartCard(
  builder: ChartBuilderValue,
  existing?: DashboardChartCard | null,
): DashboardChartCard {
  const measureNames = measures
    .filter((measure) => builder.measureIds.includes(measure.id))
    .map((measure) => measure.name)
  const filters = Object.fromEntries(
    Object.entries(builder.filters).filter(([, value]) => value),
  )
  return {
    id: existing?.id ?? nextCardId(),
    kind: 'chart',
    title: builder.title,
    description:
      builder.description ||
      `${dimensionLabels[builder.dimensionId] ?? builder.dimensionId} · ${measureNames.join('、')}`,
    query: {
      sourceId: builder.sourceId,
      dimensionId: builder.dimensionId,
      measureIds: [...builder.measureIds],
      filters,
      filterSummary: summarizeSnapshotFilters(filters),
    },
    style: {
      chartType: builder.chartType,
      stacked: builder.stacked,
      showLegend: builder.showLegend,
      showLabels: builder.showLabels,
      smooth: builder.smooth,
      palette: builder.palette,
      orientation: builder.orientation,
      legendPosition: builder.legendPosition,
      fontScale: builder.fontScale,
      showArea: builder.showArea,
      sortDirection: builder.sortDirection,
      maxCategories: builder.maxCategories,
    },
    layout: existing?.layout ?? {
      x: 0,
      y: 0,
      w: 6,
      h: 6,
      minW: 3,
      minH: 4,
    },
  }
}

export function chartBuilderValueFromCard(
  card: DashboardChartCard,
): ChartBuilderValue {
  return {
    title: card.title,
    description: card.description,
    sourceId: card.query.sourceId,
    chartType: card.style.chartType,
    dimensionId: card.query.dimensionId,
    measureIds: [...card.query.measureIds],
    filters: { ...card.query.filters },
    stacked: card.style.stacked,
    showLegend: card.style.showLegend,
    showLabels: card.style.showLabels,
    smooth: card.style.smooth,
    palette: card.style.palette,
    orientation: card.style.orientation,
    legendPosition: card.style.legendPosition,
    fontScale: card.style.fontScale,
    showArea: card.style.showArea,
    sortDirection: card.style.sortDirection,
    maxCategories: card.style.maxCategories,
  }
}

interface DimensionContribution {
  category: string
  metric?: MetricTotals
}

function dimensionContributions(
  row: SnapshotRow,
  dimensionId: string,
  questionLabel: string,
): DimensionContribution[] {
  if (dimensionId === 'result_type') {
    return [
      { category: 'Good', metric: row.good_metrics },
      { category: 'Bad', metric: row.bad_metrics },
    ]
  }

  if (dimensionId === 'question_option') {
    const values: DimensionContribution[] = []
    for (const [label, options] of Object.entries(row.option_metrics)) {
      if (questionLabel && label !== questionLabel) continue
      for (const [option, metric] of Object.entries(options)) {
        values.push({ category: `${label} / ${option}`, metric })
      }
    }
    return values
  }

  if (dimensionId === 'question_label') {
    const values: DimensionContribution[] = []
    for (const [label, options] of Object.entries(row.option_metrics)) {
      if (questionLabel && label !== questionLabel) continue
      for (const metric of Object.values(options)) {
        values.push({ category: label, metric })
      }
    }
    return values
  }

  const value = row[dimensionId as keyof SnapshotRow]
  return [{ category: String(value ?? '未填写') }]
}

export async function resolveSnapshotChartCard(
  card: DashboardChartCard,
): Promise<DashboardChartResult> {
  if (card.query.sourceId !== SOURCE_ID) {
    throw new Error(`未知统计数据源：${card.query.sourceId}`)
  }

  const { question_label: questionLabel = '', ...apiFilters } =
    card.query.filters
  const response = await getSnapshotRows(apiFilters as SnapshotQuery)
  if (response.total > response.items.length) {
    throw new Error(
      `当前筛选命中 ${response.total} 行，超过单卡 1000 行安全上限；请缩小日期或任务范围。`,
    )
  }

  const selected = measures.filter((measure) =>
    card.query.measureIds.includes(measure.id),
  )
  const chartMeasures =
    card.style.chartType === 'pie' ? selected.slice(0, 1) : selected
  const buckets = new Map<
    string,
    Map<string, { numerator: number; denominator: number }>
  >()

  for (const row of response.items) {
    const contributions = dimensionContributions(
      row,
      card.query.dimensionId,
      questionLabel,
    )
    for (const contribution of contributions) {
      const bucket =
        buckets.get(contribution.category) ??
        new Map<string, { numerator: number; denominator: number }>()
      for (const measure of chartMeasures) {
        const value = measure.value(row, contribution.metric)
        const current = bucket.get(measure.id) ?? {
          numerator: 0,
          denominator: 0,
        }
        current.numerator += value.numerator
        current.denominator += value.denominator ?? 0
        bucket.set(measure.id, current)
      }
      buckets.set(contribution.category, bucket)
    }
  }

  const fixedOrder =
    card.query.dimensionId === 'result_type' ? ['Good', 'Bad'] : null
  let categories = fixedOrder
    ? fixedOrder.filter((category) => buckets.has(category))
    : [...buckets.keys()].sort((left, right) =>
        left.localeCompare(right, 'zh-CN'),
      )
  if (card.style.sortDirection === 'value-desc' && chartMeasures[0]) {
    const firstMeasure = chartMeasures[0]
    categories = [...categories].sort((left, right) => {
      const leftValue = buckets.get(left)?.get(firstMeasure.id)?.numerator ?? 0
      const rightValue =
        buckets.get(right)?.get(firstMeasure.id)?.numerator ?? 0
      return rightValue - leftValue
    })
  }
  if (card.style.maxCategories > 0) {
    categories = categories.slice(0, card.style.maxCategories)
  }

  return {
    categories,
    series: chartMeasures.map((measure) => ({
      id: measure.id,
      name: measure.name,
      unit: measure.unit,
      axis: measure.unit === '%' ? 'rate' : 'count',
      renderAs:
        card.style.chartType === 'combo'
          ? measure.unit === '%'
            ? 'line'
            : 'bar'
          : card.style.chartType === 'line'
            ? 'line'
            : 'bar',
      values: categories.map((category) => {
        const value = buckets.get(category)?.get(measure.id)
        if (!value) return 0
        if (measure.unit !== '%') return value.numerator
        return value.denominator
          ? Math.round((value.numerator / value.denominator) * 1000) / 10
          : 0
      }),
    })),
    source: {
      sourceId: SOURCE_ID,
      sourceLabel: '人工质检员工日快照',
      rowCount: response.items.length,
      filterSummary: card.query.filterSummary,
      generatedAt: new Date().toISOString(),
    },
  }
}
