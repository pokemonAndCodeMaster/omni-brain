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
  values: number[]
  unit?: string
  axis?: 'count' | 'rate'
  renderAs?: 'bar' | 'line'
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

export interface DashboardChartCard {
  id: string
  kind: 'chart'
  title: string
  description: string
  query: DashboardCardQuery
  style: DashboardChartStyle
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
  sources: ChartBuilderField[]
  dimensions: ChartBuilderField[]
  measures: ChartBuilderField[]
  filters: ChartBuilderFilterField[]
  defaultSourceId: string
  defaultDimensionId: string
  defaultMeasureIds: string[]
}

export interface ChartBuilderValue {
  title: string
  description: string
  sourceId: string
  chartType: DashboardChartType
  dimensionId: string
  measureIds: string[]
  filters: Record<string, string>
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

export type DashboardCardResolver = (
  card: DashboardChartCard,
) => Promise<DashboardChartResult>
