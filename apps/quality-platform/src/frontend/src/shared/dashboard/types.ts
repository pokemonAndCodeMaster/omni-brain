export type DashboardChartType = 'bar' | 'line' | 'pie' | 'combo'
export type DashboardPalette = 'business' | 'quality' | 'contrast'
export type DashboardOrientation = 'vertical' | 'horizontal'
export type DashboardLegendPosition = 'top' | 'bottom'
export type DashboardFontScale = 'small' | 'medium' | 'large'
export type LegacyDashboardMetricId =
  | 'annotation_quality'
  | 'acceptance_allocation'
  | 'acceptance_completion'
  | 'acceptance_result'
export type DashboardJumpTarget =
  | 'annotation-quality'
  | 'bad-options'
  | 'acceptance-progress'
  | 'acceptance-result'
  | 'snapshot-detail'

export interface ChartSeries {
  id: string
  name: string
  values: Array<number | null>
  unit?: string
  axis?: 'count' | 'rate'
  axisId?: string
  renderAs?: 'bar' | 'line' | 'area'
  color?: string
  stackGroup?: string | null
  smooth?: boolean
  showLabels?: boolean
}

export interface DashboardCardLayout {
  x: number
  y: number
  w: number
  h: number
  minW: number
  minH: number
}

export interface DashboardChartStyle {
  chartType: DashboardChartType
  stacked: boolean
  showLegend: boolean
  showLabels: boolean
  smooth: boolean
  palette: DashboardPalette
  orientation: DashboardOrientation
  legendPosition: DashboardLegendPosition
  fontScale: DashboardFontScale
  showArea: boolean
  sortDirection: 'natural' | 'value-desc'
  maxCategories: number
}

export interface DashboardCardQuery {
  sourceId: string
  dimensionId: string
  measureIds: string[]
  filters: Record<string, string>
  filterSummary: string
}

export interface LegacyDashboardChartCard {
  id: string
  kind: 'chart'
  title: string
  description: string
  query: DashboardCardQuery
  style: DashboardChartStyle
  layout: DashboardCardLayout
}

export type DashboardChartDimension =
  | 'date'
  | 'project'
  | 'task'
  | 'group'
  | 'employee'
  | 'question-option'

export type DashboardChartFilterOperator =
  | 'equals'
  | 'in'
  | 'contains'
  | 'greater_than'
  | 'less_than'
  | 'between'

export interface DashboardChartFilter {
  target: DashboardMetricReference
  operator: DashboardChartFilterOperator
  value: string | number | string[] | number[]
}

export interface DashboardChartBaseQuery {
  sourceId: string
  scopeMode: 'inherit-page'
  categoryDimension: DashboardChartDimension
  timeGrain: 'day' | null
  questionLabels: string[]
  filters: DashboardChartFilter[]
}

export interface DashboardChartAxis {
  id: string
  side: 'left' | 'right'
  unit: 'count' | 'percent'
  label: string
  minimum: number | null
  maximum: number | null
}

export interface DashboardChartSplit {
  dimension: Exclude<DashboardChartDimension, 'date'>
  questionLabel?: string
  values?: string[]
}

export interface DashboardChartLayerStyle {
  color: string
  smooth: boolean
  showLabels: boolean
}

export interface DashboardChartLayer {
  id: string
  label: string
  metric: DashboardMetricReference
  renderAs: 'bar' | 'line' | 'area'
  axisId: string
  splitBy: DashboardChartSplit | null
  filters: DashboardChartFilter[]
  stackGroup: string | null
  style: DashboardChartLayerStyle
}

export interface DashboardChartPresentation {
  showLegend: boolean
  legendPosition: DashboardLegendPosition
  categorySort: 'natural' | 'value-desc'
  categoryLimit: number
  orientation: DashboardOrientation
  fontScale: DashboardFontScale
}

export interface DashboardChartCard {
  id: string
  kind: 'chart'
  origin: DashboardMetricOrigin
  title: string
  description: string
  baseQuery: DashboardChartBaseQuery
  axes: DashboardChartAxis[]
  layers: DashboardChartLayer[]
  presentation: DashboardChartPresentation
  layout: DashboardCardLayout
}

export interface LegacyDashboardMetricCardStyle {
  accentColor: string
  backgroundColor: string
  textColor: string
  titleSize: number
  valueSize: number
  density: 'compact' | 'comfortable'
  showProjectBreakdown: boolean
}

export interface LegacyDashboardMetricCard {
  id: string
  kind: 'metric'
  title: string
  description: string
  metricId: LegacyDashboardMetricId
  jumpTarget: DashboardJumpTarget
  style: LegacyDashboardMetricCardStyle
  layout: DashboardCardLayout
}

export interface DashboardMetricOrigin {
  type: 'system-preset' | 'user'
  presetId?: string
  presetVersion?: number
}

export interface DashboardMetricReference {
  id: string
  parameters?: Record<string, string>
}

export type DashboardMetricBlockWidth = 'full' | 'half' | 'third'

export interface DashboardMetricValueStyle {
  valueSize: number
  valueColor: string
  labelSize: number
  labelColor: string
}

export interface DashboardMetricValueBlock {
  id: string
  kind: 'metric-value'
  metric: DashboardMetricReference
  label: string
  emphasis: 'primary' | 'supporting'
  width: DashboardMetricBlockWidth
  style: DashboardMetricValueStyle
}

export interface DashboardMetricTextBlock {
  id: string
  kind: 'text'
  content: string
  width: DashboardMetricBlockWidth
  style: {
    fontSize: number
    color: string
  }
}

export interface DashboardMetricBreakdownBlock {
  id: string
  kind: 'breakdown'
  dimension: 'project' | 'task' | 'group'
  metrics: DashboardMetricReference[]
  limit: number
  width: DashboardMetricBlockWidth
}

export type DashboardMetricBlock =
  | DashboardMetricValueBlock
  | DashboardMetricTextBlock
  | DashboardMetricBreakdownBlock

export interface DashboardMetricCardStyle {
  accentColor: string
  backgroundColor: string
  textColor: string
  titleSize: number
  density: 'compact' | 'comfortable'
}

export interface DashboardMetricCard {
  id: string
  kind: 'metric'
  origin: DashboardMetricOrigin
  title: string
  description: string
  query: {
    scopeMode: 'inherit-page'
    filters: Array<Record<string, unknown>>
  }
  blocks: DashboardMetricBlock[]
  action: {
    type: 'jump'
    targetCardId: DashboardJumpTarget
  } | null
  style: DashboardMetricCardStyle
  layout: DashboardCardLayout
}

export type DashboardCard =
  | DashboardChartCard
  | LegacyDashboardChartCard
  | DashboardMetricCard
  | LegacyDashboardMetricCard

export interface DashboardMetricValueResult {
  metricId: string
  label: string
  value: number | null
  formattedValue: string
  unit: 'count' | 'percent'
}

export interface DashboardMetricBreakdownResult {
  label: string
  values: DashboardMetricValueResult[]
}

export interface DashboardMetricResult {
  values: Record<string, DashboardMetricValueResult>
  breakdowns: Record<string, DashboardMetricBreakdownResult[]>
}

export interface ChartSourceContext {
  sourceId: string
  sourceLabel: string
  rowCount: number
  filterSummary: string
  generatedAt: string
}

export interface DashboardChartResult {
  categories: string[]
  series: ChartSeries[]
  source: ChartSourceContext
}

export interface DashboardConfig {
  schemaVersion: 'dashboard-v1' | 'dashboard-v2'
  cards: DashboardCard[]
}

export interface DashboardConfigResponse {
  ownerId: string
  pageKey: string
  viewName: string
  viewType: 'dashboard'
  config: DashboardConfig
  version: number
  createdAt: string
  updatedAt: string
}

export interface ChartBuilderField {
  id: string
  label: string
}

export interface ChartBuilderFilterField extends ChartBuilderField {
  type: 'date' | 'text' | 'select'
  options?: string[]
  placeholder?: string
}

export interface ChartBuilderOptions {
  sourceId: string
  dimensions: Array<ChartBuilderField & { valueType: 'date' | 'text' }>
  metrics: Array<
    ChartBuilderField & {
      unit: 'count' | 'percent'
      requiresQuestionOption: boolean
    }
  >
  questionOptions: Record<string, string[]>
}

export type DashboardCardResolver = (
  card: DashboardChartCard,
) => Promise<DashboardChartResult>
