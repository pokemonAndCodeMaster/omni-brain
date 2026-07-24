export type AnalysisDimension = 'project' | 'status' | 'owner' | 'priority'
export type AnalysisMetric = 'count' | 'targetCount' | 'completedCount' | 'goodRate'
export type AnalysisChartType = 'bar' | 'pie'

export interface ChartDataPoint {
  name: string
  value: number
}

export interface ChartSpec {
  id: string
  title: string
  description: string
  dimension: AnalysisDimension
  metric: AnalysisMetric
  chartType: AnalysisChartType
  data: ChartDataPoint[]
  filtersSummary: string
  createdAt: string
}
