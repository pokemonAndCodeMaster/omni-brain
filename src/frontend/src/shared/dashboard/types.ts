export type DashboardChartType = 'bar' | 'line' | 'pie'

export interface ChartSeries {
  id: string
  name: string
  values: number[]
  unit?: string
}

export interface ChartSourceContext {
  sourceId: string
  sourceLabel: string
  rowCount: number
  filterSummary: string
  generatedAt: string
}

export interface DashboardChartCard {
  id: string
  kind: 'chart'
  title: string
  description: string
  chartType: DashboardChartType
  categories: string[]
  series: ChartSeries[]
  source: ChartSourceContext
}

export interface ChartBuilderField {
  id: string
  label: string
}

export interface ChartBuilderOptions {
  dimensions: ChartBuilderField[]
  measures: ChartBuilderField[]
  defaultDimensionId: string
  defaultMeasureIds: string[]
}

export interface ChartBuilderValue {
  title: string
  chartType: DashboardChartType
  dimensionId: string
  measureIds: string[]
}
