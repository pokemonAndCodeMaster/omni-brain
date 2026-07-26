export interface AnalysisMetricReference {
  id: string
  parameters?: Record<string, string>
}

export interface AnalysisScope {
  dateStart?: string
  dateEnd?: string
  projectNames?: string[]
  taskNames?: string[]
  groupNames?: string[]
  employeeIds?: string[]
}

export interface AnalysisFilter {
  target: AnalysisMetricReference
  operator:
    | 'equals'
    | 'in'
    | 'contains'
    | 'greater_than'
    | 'less_than'
    | 'between'
  value: string | number | string[] | number[]
}

export interface AnalysisSort {
  target: AnalysisMetricReference
  direction: 'ascending' | 'descending'
}

export interface AnalysisQuery {
  sourceId: string
  scope: AnalysisScope
  groupBy: string[]
  measures: AnalysisMetricReference[]
  filters?: AnalysisFilter[]
  sort?: AnalysisSort[]
  page?: { number: number; size: number }
}

export interface AnalysisDimension {
  id: string
  label: string
  valueType: 'date' | 'text'
  filterOperators: string[]
  groupable: boolean
  sortable: boolean
}

export interface AnalysisMetric {
  id: string
  label: string
  unit: 'count' | 'percent'
  description: string
  filterOperators: string[]
  sortable: boolean
  requiresQuestionOption: boolean
}

export interface AnalysisCatalog {
  sourceId: string
  dimensions: AnalysisDimension[]
  metrics: AnalysisMetric[]
}

export interface AnalysisRow {
  key: string
  dimensions: Record<string, string>
  measures: Record<string, number | null>
  computedAt: string
}

export interface AnalysisQueryResult {
  sourceId: string
  groupBy: string[]
  rows: AnalysisRow[]
  total: number
  page: { number: number; size: number }
  computedAt: string | null
  warnings: string[]
}

export interface TaskAnalysisRow {
  id: string
  project: string
  task: string
  annotationSubmitted: number
  goodRate: number | null
  acceptanceAllocated: number
  allocationCoverageRate: number | null
  acceptanceCompleted: number
  completionRate: number | null
  passRate: number | null
}
