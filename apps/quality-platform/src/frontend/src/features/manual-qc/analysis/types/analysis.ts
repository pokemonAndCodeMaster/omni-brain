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

export interface AnalysisFacetRequest {
  sourceId: string
  scope: AnalysisScope
  dimensionId:
    | 'project'
    | 'task'
    | 'group'
    | 'employee'
    | 'question_label'
    | 'question_option'
  questionLabel?: string
}

export interface AnalysisFacetResult {
  dimensionId: string
  values: string[]
}

export type TaskAnalysisLevel = 'task' | 'date' | 'group' | 'employee'

export interface TaskAnalysisPath {
  project: string
  task: string
  date?: string
  group?: string
  employee?: string
}

export interface TaskAnalysisRow {
  id: string
  level: TaskAnalysisLevel
  objectLabel: string
  objectType: string
  project: string
  task: string
  statDate: string
  group: string
  employee: string
  path: TaskAnalysisPath
  annotationSubmitted: number
  goodRate: number | null
  acceptanceAllocated: number
  allocationCoverageRate: number | null
  acceptanceCompleted: number
  completionRate: number | null
  passRate: number | null
  dynamicMeasures: Record<string, number | null>
  hasChildren: boolean
  children?: TaskAnalysisRow[]
}

export interface TaskTableColumnState {
  visibility: Record<string, boolean>
  order: string[]
  sizing: Record<string, number>
}

export interface TaskTableConfig {
  schemaVersion: 'manual-qc-task-table-v1'
  pinnedMetrics: AnalysisMetricReference[]
  columns: TaskTableColumnState
}

export interface TaskTableConfigResponse {
  ownerId: string
  pageKey: string
  viewName: string
  viewType: 'data_workbench'
  config: TaskTableConfig
  version: number
  createdAt: string
  updatedAt: string
}

export interface TaskMetricDetailSelection {
  row: TaskAnalysisRow
  metricId:
    | 'annotation.good_rate'
    | 'acceptance.completion_rate'
    | 'acceptance.pass_rate'
}

export interface TaskMetricDetailOption {
  questionLabel: string
  questionOption: string
  annotationSubmitted: number
  annotationRateOfBad: number | null
  allocated: number
  completed: number
  completionRate: number | null
  passed: number
  rejected: number
  passRate: number | null
}

export interface TaskMetricDetail {
  selection: TaskMetricDetailSelection
  summary: Record<string, number | null>
  trend: Array<{
    date: string
    measures: Record<string, number | null>
  }>
  options: TaskMetricDetailOption[]
}
