import {
  postAnalysisFacets,
  postAnalysisQuery,
} from '../analysis/api/analysis'
import { metricReferenceKey } from '../analysis/utils'
import type {
  AnalysisCatalog,
  AnalysisFilter,
  AnalysisMetricReference,
  AnalysisQueryResult,
  AnalysisScope,
} from '../analysis/types/analysis'
import type { SnapshotQuery, SnapshotRow } from '../types/snapshot'
import type {
  ChartBuilderOptions,
  ChartSeries,
  DashboardChartAxis,
  DashboardChartCard,
  DashboardChartDimension,
  DashboardChartFilter,
  DashboardChartLayer,
  DashboardChartResult,
  DashboardMetricReference,
  LegacyDashboardChartCard,
} from '@/shared/dashboard/types'

const SOURCE_ID = 'manual_qc.snapshot.v20260709'
const PRESET_VERSION = 2

const dimensionLabels: Record<DashboardChartDimension, string> = {
  date: '日期',
  project: '项目',
  task: '标注任务',
  group: '组',
  employee: '标注员',
  'question-option': '问题选项',
}

const legacyDimensionMap: Record<string, DashboardChartDimension> = {
  stat_date: 'date',
  project_name: 'project',
  scene_name: 'task',
  group_name: 'group',
  employee_id: 'employee',
  question_option: 'question-option',
}

const legacyMetricMap: Record<string, string> = {
  annotation_submitted: 'annotation.submitted',
  good_annotation_submitted: 'annotation.good_submitted',
  bad_annotation_submitted: 'annotation.bad_submitted',
  good_rate: 'annotation.good_rate',
  bad_rate: 'annotation.bad_rate',
  accept_allocated: 'acceptance.allocated',
  accept_completed: 'acceptance.completed',
  accept_pending: 'acceptance.pending',
  accept_passed: 'acceptance.passed',
  accept_rejected: 'acceptance.rejected',
  completion_rate: 'acceptance.completion_rate',
  pass_rate: 'acceptance.pass_rate',
  reject_rate: 'acceptance.reject_rate',
}

const metricLabels: Record<string, string> = {
  'annotation.submitted': '标注提交量',
  'annotation.good_submitted': 'Good 提交量',
  'annotation.bad_submitted': 'Bad 提交量',
  'annotation.good_rate': 'Good 占比',
  'annotation.bad_rate': 'Bad 占比',
  'acceptance.allocated': '验收分配量',
  'acceptance.completed': '验收完成量',
  'acceptance.pending': '验收未完成量',
  'acceptance.passed': '验收通过量',
  'acceptance.rejected': '验收打回量',
  'acceptance.completion_rate': '验收完成率',
  'acceptance.pass_rate': '验收通过率',
  'acceptance.reject_rate': '验收打回率',
  'option.annotation_submitted': '问题选项标注量',
  'option.annotation_rate_of_bad': '问题选项占 Bad 比例',
}

const metricUnits: Record<string, 'count' | 'percent'> = {
  'annotation.good_rate': 'percent',
  'annotation.bad_rate': 'percent',
  'acceptance.allocation_coverage_rate': 'percent',
  'acceptance.allocation_fulfillment_rate': 'percent',
  'acceptance.completion_rate': 'percent',
  'acceptance.pass_rate': 'percent',
  'acceptance.reject_rate': 'percent',
  'good.acceptance.completion_rate': 'percent',
  'good.acceptance.pass_rate': 'percent',
  'bad.acceptance.completion_rate': 'percent',
  'bad.acceptance.pass_rate': 'percent',
  'option.annotation_rate_of_bad': 'percent',
  'option.acceptance.completion_rate': 'percent',
  'option.acceptance.pass_rate': 'percent',
}

const layerColors = [
  '#315fc4',
  '#268462',
  '#d5535d',
  '#d48a2f',
  '#7451b8',
  '#4f7f8d',
  '#9b6b43',
  '#56616f',
]

function copyCard(card: DashboardChartCard): DashboardChartCard {
  return JSON.parse(JSON.stringify(card)) as DashboardChartCard
}

function countAxis(): DashboardChartAxis {
  return {
    id: 'count-axis',
    side: 'left',
    unit: 'count',
    label: '数量',
    minimum: 0,
    maximum: null,
  }
}

function rateAxis(): DashboardChartAxis {
  return {
    id: 'rate-axis',
    side: 'right',
    unit: 'percent',
    label: '占比',
    minimum: 0,
    maximum: 100,
  }
}

function layer(
  id: string,
  metricId: string,
  renderAs: DashboardChartLayer['renderAs'],
  options: {
    label?: string
    color?: string
    axisId?: string
    stackGroup?: string | null
  } = {},
): DashboardChartLayer {
  return {
    id,
    label: options.label ?? metricLabels[metricId] ?? metricId,
    metric: { id: metricId },
    renderAs,
    axisId:
      options.axisId ??
      (metricUnits[metricId] === 'percent' ? 'rate-axis' : 'count-axis'),
    splitBy: null,
    filters: [],
    stackGroup: options.stackGroup ?? null,
    style: {
      color: options.color ?? layerColors[0]!,
      smooth: true,
      showLabels: false,
    },
  }
}

function preset(
  value: Omit<
    DashboardChartCard,
    'kind' | 'origin' | 'baseQuery' | 'axes' | 'presentation'
  > & {
    presetId: string
    categoryDimension: DashboardChartDimension
    axes?: DashboardChartAxis[]
    orientation?: 'vertical' | 'horizontal'
  },
): DashboardChartCard {
  return {
    id: value.id,
    kind: 'chart',
    origin: {
      type: 'system-preset',
      presetId: value.presetId,
      presetVersion: PRESET_VERSION,
    },
    title: value.title,
    description: value.description,
    baseQuery: {
      sourceId: SOURCE_ID,
      scopeMode: 'inherit-page',
      categoryDimension: value.categoryDimension,
      timeGrain: value.categoryDimension === 'date' ? 'day' : null,
      questionLabels: [],
      filters: [],
    },
    axes: value.axes ?? [countAxis(), rateAxis()],
    layers: value.layers,
    presentation: {
      showLegend: true,
      legendPosition: 'top',
      categorySort:
        value.categoryDimension === 'question-option'
          ? 'value-desc'
          : 'natural',
      categoryLimit:
        value.categoryDimension === 'question-option' ? 12 : 24,
      orientation: value.orientation ?? 'vertical',
      fontScale: 'medium',
    },
    layout: value.layout,
  }
}

const chartPresets: DashboardChartCard[] = [
  preset({
    id: 'annotation-quality',
    presetId: 'manual-qc.annotation-quality',
    title: '标注数量与质量构成',
    description: '按任务查看 Good、Bad 数量与 Good 占比',
    categoryDimension: 'task',
    layers: [
      layer('good', 'annotation.good_submitted', 'bar', {
        color: '#268462',
        stackGroup: 'annotation',
      }),
      layer('bad', 'annotation.bad_submitted', 'bar', {
        color: '#d5535d',
        stackGroup: 'annotation',
      }),
      layer('good-rate', 'annotation.good_rate', 'line', {
        color: '#315fc4',
      }),
    ],
    layout: { x: 0, y: 0, w: 8, h: 7, minW: 4, minH: 5 },
  }),
  preset({
    id: 'bad-options',
    presetId: 'manual-qc.bad-options',
    title: 'Bad 问题排行',
    description: '按问题标签与选项查看 Bad 问题提交量',
    categoryDimension: 'question-option',
    axes: [countAxis()],
    orientation: 'horizontal',
    layers: [
      layer('bad-option-count', 'option.annotation_submitted', 'bar', {
        color: '#d5535d',
      }),
    ],
    layout: { x: 8, y: 0, w: 4, h: 7, minW: 4, minH: 5 },
  }),
  preset({
    id: 'acceptance-progress',
    presetId: 'manual-qc.acceptance-progress',
    title: '验收分配与完成',
    description: '分配量、完成量与完成率使用独立坐标轴',
    categoryDimension: 'task',
    layers: [
      layer('allocated', 'acceptance.allocated', 'bar', {
        color: '#315fc4',
      }),
      layer('completed', 'acceptance.completed', 'bar', {
        color: '#268462',
      }),
      layer('completion-rate', 'acceptance.completion_rate', 'line', {
        color: '#d48a2f',
      }),
    ],
    layout: { x: 0, y: 7, w: 6, h: 7, minW: 4, minH: 5 },
  }),
  preset({
    id: 'acceptance-result',
    presetId: 'manual-qc.acceptance-result',
    title: '验收通过与打回',
    description: '通过、打回数量与通过率使用独立坐标轴',
    categoryDimension: 'task',
    layers: [
      layer('passed', 'acceptance.passed', 'bar', {
        color: '#268462',
        stackGroup: 'result',
      }),
      layer('rejected', 'acceptance.rejected', 'bar', {
        color: '#d5535d',
        stackGroup: 'result',
      }),
      layer('pass-rate', 'acceptance.pass_rate', 'line', {
        color: '#315fc4',
      }),
    ],
    layout: { x: 6, y: 7, w: 6, h: 7, minW: 4, minH: 5 },
  }),
]

export function defaultSnapshotChartCards(): DashboardChartCard[] {
  return chartPresets.map(copyCard)
}

let sequence = 0

function nextCardId(prefix = 'snapshot-chart'): string {
  sequence += 1
  return `${prefix}-${Date.now()}-${sequence}`
}

export function nextSnapshotChartCard(): DashboardChartCard {
  const card = preset({
    id: nextCardId(),
    presetId: 'manual-qc.user-template',
    title: '人工质检自定义统计',
    description: '按任务查看验收完成量与完成率',
    categoryDimension: 'task',
    layers: [
      layer('completed', 'acceptance.completed', 'bar', {
        color: '#315fc4',
      }),
      layer('completion-rate', 'acceptance.completion_rate', 'line', {
        color: '#d48a2f',
      }),
    ],
    layout: { x: 0, y: 0, w: 6, h: 7, minW: 4, minH: 5 },
  })
  card.origin = { type: 'user' }
  return card
}

export function duplicateSnapshotChartCard(
  card: DashboardChartCard,
): DashboardChartCard {
  const duplicate = copyCard(card)
  duplicate.id = nextCardId('snapshot-chart-copy')
  duplicate.title = `${card.title}（副本）`
  duplicate.origin = { type: 'user' }
  duplicate.layout = {
    ...duplicate.layout,
    y: duplicate.layout.y + 1,
  }
  return duplicate
}

export function restoreSnapshotChartPreset(
  card: DashboardChartCard,
): DashboardChartCard | null {
  const presetId = card.origin.presetId
  if (!presetId) return null
  const current = chartPresets.find(
    (candidate) => candidate.origin.presetId === presetId,
  )
  if (!current) return null
  return {
    ...copyCard(current),
    id: card.id,
    layout: { ...card.layout },
  }
}

function legacyFilters(
  filters: Record<string, string>,
): DashboardChartFilter[] {
  const result: DashboardChartFilter[] = []
  const start = filters.stat_date_start
  const end = filters.stat_date_end
  if (start && end) {
    result.push({
      target: { id: 'date' },
      operator: 'between',
      value: [start, end],
    })
  } else if (start || end) {
    result.push({
      target: { id: 'date' },
      operator: 'equals',
      value: start || end,
    })
  }
  for (const [legacy, current] of Object.entries({
    project_name: 'project',
    scene_name: 'task',
    group_name: 'group',
    employee_id: 'employee',
  })) {
    const value = filters[legacy]
    if (value) {
      result.push({
        target: { id: current },
        operator: 'equals',
        value,
      })
    }
  }
  return result
}

export function normalizeSnapshotChartCard(
  card: DashboardChartCard | LegacyDashboardChartCard,
): DashboardChartCard {
  if ('baseQuery' in card) return copyCard(card)
  const dimension = legacyDimensionMap[card.query.dimensionId] ?? 'task'
  const selected = card.query.measureIds
    .map((id) => legacyMetricMap[id])
    .filter((id): id is string => Boolean(id))
  const layers = selected.map((metricId, index) => {
    const unit = metricUnits[metricId] ?? 'count'
    const renderAs =
      card.style.chartType === 'combo'
        ? unit === 'percent' ? 'line' : 'bar'
        : card.style.chartType === 'line'
          ? card.style.showArea ? 'area' : 'line'
          : 'bar'
    const next = layer(`migrated-${index + 1}`, metricId, renderAs, {
      color: layerColors[index % layerColors.length],
    })
    next.style.showLabels = card.style.showLabels
    next.style.smooth = card.style.smooth
    next.stackGroup =
      card.style.stacked && unit === 'count' ? 'legacy-stack' : null
    return next
  })
  return {
    id: card.id,
    kind: 'chart',
    origin: { type: 'user' },
    title: card.title,
    description: card.description,
    baseQuery: {
      sourceId: SOURCE_ID,
      scopeMode: 'inherit-page',
      categoryDimension: dimension,
      timeGrain: dimension === 'date' ? 'day' : null,
      questionLabels: [],
      filters: legacyFilters(card.query.filters),
    },
    axes: [countAxis(), rateAxis()],
    layers: layers.length
      ? layers
      : [layer('fallback', 'annotation.submitted', 'bar')],
    presentation: {
      showLegend: card.style.showLegend,
      legendPosition: card.style.legendPosition,
      categorySort: card.style.sortDirection,
      categoryLimit: card.style.maxCategories,
      orientation: card.style.orientation,
      fontScale: card.style.fontScale,
    },
    layout: { ...card.layout, minH: Math.max(5, card.layout.minH) },
  }
}

export function createSnapshotChartBuilderOptions(
  catalog: AnalysisCatalog | null,
  rows: SnapshotRow[],
): ChartBuilderOptions {
  const questionOptions: Record<string, Set<string>> = {}
  for (const row of rows) {
    for (const [label, options] of Object.entries(row.option_metrics)) {
      const values = questionOptions[label] ?? new Set<string>()
      Object.keys(options).forEach((option) => values.add(option))
      questionOptions[label] = values
    }
  }
  return {
    sourceId: catalog?.sourceId ?? SOURCE_ID,
    dimensions: [
      ...(catalog?.dimensions.map((item) => ({
        id: item.id,
        label: item.label,
        valueType: item.valueType,
      })) ?? Object.entries(dimensionLabels)
        .filter(([id]) => id !== 'question-option')
        .map(([id, label]) => ({
          id,
          label,
          valueType: id === 'date' ? 'date' as const : 'text' as const,
        }))),
      {
        id: 'question-option',
        label: '问题选项',
        valueType: 'text',
      },
    ],
    metrics: (
      catalog?.metrics ??
      Object.entries(metricLabels).map(([id, label]) => ({
        id,
        label,
        unit: metricUnits[id] ?? 'count',
        requiresQuestionOption: id.startsWith('option.'),
        description: '',
        filterOperators: [],
        sortable: true,
      }))
    ).map((item) => ({
      id: item.id,
      label: item.label,
      unit: item.unit,
      requiresQuestionOption: item.requiresQuestionOption,
    })),
    questionOptions: Object.fromEntries(
      Object.entries(questionOptions).map(([label, values]) => [
        label,
        [...values].sort((left, right) =>
          left.localeCompare(right, 'zh-CN'),
        ),
      ]),
    ),
  }
}

function analysisScope(pageQuery: SnapshotQuery): AnalysisScope {
  return {
    dateStart: pageQuery.stat_date_start || undefined,
    dateEnd: pageQuery.stat_date_end || undefined,
    projectNames: pageQuery.project_name ? [pageQuery.project_name] : [],
    taskNames: pageQuery.scene_name ? [pageQuery.scene_name] : [],
    groupNames: pageQuery.group_name ? [pageQuery.group_name] : [],
    employeeIds: pageQuery.employee_id ? [pageQuery.employee_id] : [],
  }
}

function analysisFilter(filter: DashboardChartFilter): AnalysisFilter {
  return {
    target: {
      id: filter.target.id,
      parameters: filter.target.parameters,
    },
    operator: filter.operator,
    value: filter.value,
  }
}

async function queryAll(
  card: DashboardChartCard,
  pageQuery: SnapshotQuery,
  groupBy: string[],
  measures: AnalysisMetricReference[],
  filters: DashboardChartFilter[],
): Promise<AnalysisQueryResult> {
  let page = 1
  let rows: AnalysisQueryResult['rows'] = []
  let latest: string | null = null
  let total = 0
  do {
    const result = await postAnalysisQuery({
      sourceId: card.baseQuery.sourceId,
      scope: analysisScope(pageQuery),
      groupBy,
      measures,
      filters: filters.map(analysisFilter),
      page: { number: page, size: 200 },
    })
    rows = [...rows, ...result.rows]
    total = result.total
    if (result.computedAt && (!latest || result.computedAt > latest)) {
      latest = result.computedAt
    }
    page += 1
  } while (rows.length < total)
  return {
    sourceId: card.baseQuery.sourceId,
    groupBy,
    rows,
    total,
    page: { number: 1, size: Math.min(200, Math.max(1, rows.length)) },
    computedAt: latest,
    warnings: [],
  }
}

function referenceWithOption(
  metricId: string,
  questionLabel: string,
  questionOption: string,
): AnalysisMetricReference {
  return {
    id: metricId,
    parameters: { questionLabel, questionOption },
  }
}

const optionRateComponents: Record<
  string,
  { numerator: string; denominator: string; denominatorUsesOption: boolean }
> = {
  'option.annotation_rate_of_bad': {
    numerator: 'option.annotation_submitted',
    denominator: 'annotation.bad_submitted',
    denominatorUsesOption: false,
  },
  'option.acceptance.completion_rate': {
    numerator: 'option.acceptance.completed',
    denominator: 'option.acceptance.allocated',
    denominatorUsesOption: true,
  },
  'option.acceptance.pass_rate': {
    numerator: 'option.acceptance.passed',
    denominator: 'option.acceptance.completed',
    denominatorUsesOption: true,
  },
}

function sumMeasure(
  rows: AnalysisQueryResult['rows'],
  reference: AnalysisMetricReference,
): number {
  const key = metricReferenceKey(reference)
  return rows.reduce(
    (sum, row) => sum + (row.measures[key] ?? 0),
    0,
  )
}

function groupMeasure(
  rows: AnalysisQueryResult['rows'],
  dimension: string,
  reference: AnalysisMetricReference,
): Map<string, number | null> {
  const key = metricReferenceKey(reference)
  return new Map(
    rows.map((row) => [
      row.dimensions[dimension] ?? '未填写',
      row.measures[key] ?? null,
    ]),
  )
}

async function questionOptions(
  card: DashboardChartCard,
  pageQuery: SnapshotQuery,
  split?: DashboardChartLayer['splitBy'],
): Promise<Array<{ label: string; option: string }>> {
  const scope = analysisScope(pageQuery)
  const labels = split?.questionLabel
    ? [split.questionLabel]
    : card.baseQuery.questionLabels.length
      ? card.baseQuery.questionLabels
      : (
          await postAnalysisFacets({
            sourceId: card.baseQuery.sourceId,
            scope,
            dimensionId: 'question_label',
          })
        ).values
  const result: Array<{ label: string; option: string }> = []
  for (const label of labels) {
    const values = split?.values?.length
      ? split.values
      : (
          await postAnalysisFacets({
            sourceId: card.baseQuery.sourceId,
            scope,
            dimensionId: 'question_option',
            questionLabel: label,
          })
        ).values
    values.forEach((option) => result.push({ label, option }))
  }
  return result
}

interface SeriesMap {
  series: Omit<ChartSeries, 'values'>
  values: Map<string, number | null>
}

function seriesDefinition(
  layerDefinition: DashboardChartLayer,
  axis: DashboardChartAxis,
  suffix = '',
): Omit<ChartSeries, 'values'> {
  return {
    id: suffix ? `${layerDefinition.id}:${suffix}` : layerDefinition.id,
    name: suffix ? `${layerDefinition.label} · ${suffix}` : layerDefinition.label,
    unit: axis.unit === 'percent' ? '%' : '条',
    axis: axis.unit === 'percent' ? 'rate' : 'count',
    axisId: axis.id,
    renderAs: layerDefinition.renderAs,
    color: layerDefinition.style.color,
    stackGroup: layerDefinition.stackGroup,
    smooth: layerDefinition.style.smooth,
    showLabels: layerDefinition.style.showLabels,
  }
}

async function regularLayer(
  card: DashboardChartCard,
  layerDefinition: DashboardChartLayer,
  pageQuery: SnapshotQuery,
): Promise<{ maps: SeriesMap[]; rowCount: number; computedAt: string | null }> {
  const category = card.baseQuery.categoryDimension
  if (category === 'question-option') {
    throw new Error('问题选项横轴必须使用问题选项解析路径。')
  }
  const axis = card.axes.find((item) => item.id === layerDefinition.axisId)
  if (!axis) throw new Error(`图层“${layerDefinition.label}”引用了不存在的坐标轴。`)
  const split = layerDefinition.splitBy?.dimension
  const groupBy = [
    category,
    ...(split && split !== 'question-option' && split !== category
      ? [split]
      : []),
  ]
  const result = await queryAll(
    card,
    pageQuery,
    groupBy,
    [layerDefinition.metric],
    [...card.baseQuery.filters, ...layerDefinition.filters],
  )
  const key = metricReferenceKey(layerDefinition.metric)
  if (!split || split === category) {
    return {
      maps: [
        {
          series: seriesDefinition(layerDefinition, axis),
          values: new Map(
            result.rows.map((row) => [
              row.dimensions[category] ?? '未填写',
              row.measures[key] ?? null,
            ]),
          ),
        },
      ],
      rowCount: result.rows.length,
      computedAt: result.computedAt,
    }
  }
  const splitValues = [
    ...new Set(
      result.rows.map((row) => row.dimensions[split] ?? '未填写'),
    ),
  ].sort((left, right) => left.localeCompare(right, 'zh-CN'))
  return {
    maps: splitValues.map((splitValue) => ({
      series: seriesDefinition(layerDefinition, axis, splitValue),
      values: new Map(
        result.rows
          .filter((row) => (row.dimensions[split] ?? '未填写') === splitValue)
          .map((row) => [
            row.dimensions[category] ?? '未填写',
            row.measures[key] ?? null,
          ]),
      ),
    })),
    rowCount: result.rows.length,
    computedAt: result.computedAt,
  }
}

async function optionMetricByCategory(
  card: DashboardChartCard,
  layerDefinition: DashboardChartLayer,
  pageQuery: SnapshotQuery,
  option: { label: string; option: string },
  category: Exclude<DashboardChartDimension, 'question-option'>,
): Promise<{
  values: Map<string, number | null>
  rowCount: number
  computedAt: string | null
}> {
  const component = optionRateComponents[layerDefinition.metric.id]
  const filters = [...card.baseQuery.filters, ...layerDefinition.filters]
  if (!component) {
    const reference = referenceWithOption(
      layerDefinition.metric.id,
      option.label,
      option.option,
    )
    const result = await queryAll(
      card,
      pageQuery,
      [category],
      [reference],
      filters,
    )
    return {
      values: groupMeasure(result.rows, category, reference),
      rowCount: result.rows.length,
      computedAt: result.computedAt,
    }
  }
  const numerator = referenceWithOption(
    component.numerator,
    option.label,
    option.option,
  )
  const denominator = component.denominatorUsesOption
    ? referenceWithOption(
        component.denominator,
        option.label,
        option.option,
      )
    : { id: component.denominator }
  const result = await queryAll(
    card,
    pageQuery,
    [category],
    [numerator, denominator],
    filters,
  )
  const numeratorValues = groupMeasure(result.rows, category, numerator)
  const denominatorValues = groupMeasure(result.rows, category, denominator)
  return {
    values: new Map(
      [...new Set([
        ...numeratorValues.keys(),
        ...denominatorValues.keys(),
      ])].map((key) => {
        const denominatorValue = denominatorValues.get(key) ?? 0
        return [
          key,
          denominatorValue
            ? Math.round(
                ((numeratorValues.get(key) ?? 0) / denominatorValue) * 1000,
              ) / 10
            : null,
        ]
      }),
    ),
    rowCount: result.rows.length,
    computedAt: result.computedAt,
  }
}

async function questionOptionLayer(
  card: DashboardChartCard,
  layerDefinition: DashboardChartLayer,
  pageQuery: SnapshotQuery,
): Promise<{ maps: SeriesMap[]; rowCount: number; computedAt: string | null }> {
  if (!layerDefinition.metric.id.startsWith('option.')) {
    throw new Error(
      `图层“${layerDefinition.label}”使用问题选项维度时，必须选择问题选项指标。`,
    )
  }
  const options = await questionOptions(
    card,
    pageQuery,
    layerDefinition.splitBy,
  )
  const axis = card.axes.find((item) => item.id === layerDefinition.axisId)
  if (!axis) throw new Error(`图层“${layerDefinition.label}”引用了不存在的坐标轴。`)
  const category = card.baseQuery.categoryDimension
  if (category === 'question-option') {
    const values = new Map<string, number | null>()
    let rowCount = 0
    let computedAt: string | null = null
    for (const option of options) {
      const component = optionRateComponents[layerDefinition.metric.id]
      const filters = [...card.baseQuery.filters, ...layerDefinition.filters]
      const numerator = referenceWithOption(
        component?.numerator ?? layerDefinition.metric.id,
        option.label,
        option.option,
      )
      const denominator = component
        ? component.denominatorUsesOption
          ? referenceWithOption(
              component.denominator,
              option.label,
              option.option,
            )
          : { id: component.denominator }
        : null
      const result = await queryAll(
        card,
        pageQuery,
        ['project'],
        denominator ? [numerator, denominator] : [numerator],
        filters,
      )
      const numeratorValue = sumMeasure(result.rows, numerator)
      const denominatorValue = denominator
        ? sumMeasure(result.rows, denominator)
        : null
      values.set(
        `${option.label} / ${option.option}`,
        denominator
          ? denominatorValue
            ? Math.round((numeratorValue / denominatorValue) * 1000) / 10
            : null
          : numeratorValue,
      )
      rowCount += result.rows.length
      if (result.computedAt && (!computedAt || result.computedAt > computedAt)) {
        computedAt = result.computedAt
      }
    }
    return {
      maps: [{
        series: seriesDefinition(layerDefinition, axis),
        values,
      }],
      rowCount,
      computedAt,
    }
  }
  const resolved = await Promise.all(
    options.map(async (option) => ({
      option,
      result: await optionMetricByCategory(
        card,
        layerDefinition,
        pageQuery,
        option,
        category,
      ),
    })),
  )
  return {
    maps: resolved.map(({ option, result }) => ({
      series: seriesDefinition(
        layerDefinition,
        axis,
        `${option.label} / ${option.option}`,
      ),
      values: result.values,
    })),
    rowCount: resolved.reduce((sum, item) => sum + item.result.rowCount, 0),
    computedAt:
      resolved
        .map((item) => item.result.computedAt)
        .filter((value): value is string => Boolean(value))
        .sort()
        .at(-1) ?? null,
  }
}

function filterSummary(
  pageQuery: SnapshotQuery,
  filters: DashboardChartFilter[],
): string {
  const parts = [
    pageQuery.stat_date_start && pageQuery.stat_date_end
      ? `${pageQuery.stat_date_start} 至 ${pageQuery.stat_date_end}`
      : '',
    pageQuery.project_name ? `项目：${pageQuery.project_name}` : '',
    pageQuery.scene_name ? `任务：${pageQuery.scene_name}` : '',
    pageQuery.group_name ? `组：${pageQuery.group_name}` : '',
    pageQuery.employee_id ? `标注员：${pageQuery.employee_id}` : '',
    ...filters.map((item) => `${item.target.id} ${item.operator}`),
  ].filter(Boolean)
  return parts.join(' · ') || '全部实验数据'
}

export async function resolveSnapshotChartCard(
  card: DashboardChartCard,
  pageQuery: SnapshotQuery,
): Promise<DashboardChartResult> {
  if (card.baseQuery.sourceId !== SOURCE_ID) {
    throw new Error(`未知统计数据源：${card.baseQuery.sourceId}`)
  }
  const resolved = await Promise.all(
    card.layers.map((item) =>
      item.splitBy?.dimension === 'question-option' ||
      card.baseQuery.categoryDimension === 'question-option'
        ? questionOptionLayer(card, item, pageQuery)
        : regularLayer(card, item, pageQuery),
    ),
  )
  let categories = [
    ...new Set(
      resolved.flatMap((item) =>
        item.maps.flatMap((series) => [...series.values.keys()]),
      ),
    ),
  ].sort((left, right) => left.localeCompare(right, 'zh-CN'))
  const maps = resolved.flatMap((item) => item.maps)
  if (card.presentation.categorySort === 'value-desc' && maps[0]) {
    categories = [...categories].sort(
      (left, right) =>
        (maps[0]!.values.get(right) ?? 0) -
        (maps[0]!.values.get(left) ?? 0),
    )
  }
  if (card.presentation.categoryLimit > 0) {
    categories = categories.slice(0, card.presentation.categoryLimit)
  }
  return {
    categories,
    series: maps.map((item) => ({
      ...item.series,
      values: categories.map((category) => {
        const value = item.values.get(category) ?? null
        return value != null && item.series.unit === '%'
          ? Math.round(value * 10) / 10
          : value
      }),
    })),
    source: {
      sourceId: SOURCE_ID,
      sourceLabel: '人工质检受控分析接口',
      rowCount: resolved.reduce((sum, item) => sum + item.rowCount, 0),
      filterSummary: filterSummary(
        pageQuery,
        card.baseQuery.filters,
      ),
      generatedAt:
        resolved
          .map((item) => item.computedAt)
          .filter((value): value is string => Boolean(value))
          .sort()
          .at(-1) ?? new Date().toISOString(),
    },
  }
}
