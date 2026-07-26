export type DashboardChartType = 'bar' | 'line' | 'pie' | 'combo'
export type DashboardPalette = 'business' | 'quality' | 'contrast'
export type DashboardOrientation = 'vertical' | 'horizontal'
export type DashboardLegendPosition = 'top' | 'bottom'
export type DashboardFontScale = 'small' | 'medium' | 'large'
export type DashboardMetricId =
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

export interface DashboardMetricCardStyle {
  accentColor: string
  backgroundColor: string
  textColor: string
  titleSize: number
  valueSize: number
  density: 'compact' | 'comfortable'
  showProjectBreakdown: boolean
}

export interface DashboardMetricCard {
  id: string
  kind: 'metric'
  title: string
  description: string
  metricId: DashboardMetricId
  jumpTarget: DashboardJumpTarget
  style: DashboardMetricCardStyle
  layout: DashboardCardLayout
}

export type DashboardCard = DashboardChartCard | DashboardMetricCard

export interface DashboardMetricBreakdown {
  projectName: string
  primaryValue: number
  details: Array<{ label: string; value: string }>
}

export interface DashboardMetricResult {
  primaryValue: number
  primaryUnit: string
  details: Array<{ label: string; value: string }>
  projects: DashboardMetricBreakdown[]
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
  schemaVersion: 'dashboard-v1'
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
