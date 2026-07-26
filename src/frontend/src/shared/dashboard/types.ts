export type DashboardChartType = 'bar' | 'line' | 'pie'
export type DashboardPalette = 'business' | 'quality' | 'contrast'
export type DashboardOrientation = 'vertical' | 'horizontal'

export interface ChartSeries {
  id: string
  name: string
  values: number[]
  unit?: string
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
  cards: DashboardChartCard[]
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
}

export type DashboardCardResolver = (
  card: DashboardChartCard,
) => Promise<DashboardChartResult>
