export interface SnapshotQuery {
  stat_date_start?: string
  stat_date_end?: string
  scene_name?: string
  group_name?: string
  employee_id?: string
  project_name?: string
}

export interface MetricTotals {
  annotation_total: number
  annotation_submitted: number
  expect_alloc: number
  actual_alloc: number
  actual_complete: number
  correct: number
  incorrect: number
  expect_pass: number
  expect_reject: number
  actual_pass: number
  actual_reject: number
}

export interface MetricState extends MetricTotals {
  conclusion: 'pass' | 'reject' | 'pending' | null
  exec_status:
    | 'PENDING'
    | 'PASS_EXECUTING'
    | 'PASS_DONE'
    | 'REJECT_EXECUTING'
    | 'REJECT_DONE'
    | null
}

export interface ProjectAggregate {
  stat_date: string
  project_name: string
  annotation_total: number
  annotation_submitted: number
  good_metrics: MetricTotals
  bad_metrics: MetricTotals
  computed_at: string
}

export interface SceneAggregate extends ProjectAggregate {
  scene_name: string
}

export interface GroupAggregate extends SceneAggregate {
  group_name: string
}

export interface EmployeeAggregate extends GroupAggregate {
  employee_id: string
}

export interface SnapshotRow {
  id: number
  stat_date: string
  scene_name: string
  group_name: string
  employee_id: string
  project_name: string
  annotation_total: number
  annotation_submitted: number
  good_metrics: MetricState
  bad_metrics: MetricState
  option_metrics: Record<string, Record<string, MetricState>>
  confirmed_by: string | null
  confirmed_at: string | null
  executed_by: string | null
  executed_at: string | null
  execution_note: string | null
  computed_at: string
  updated_at: string
}

export interface DataResponse<T> {
  schema_version: 'snapshot-jsonb-v20260709'
  items: T[]
  total: number
  computed_at: string | null
}

export type AggregateLevel = 'project' | 'scene' | 'group' | 'employee'

export interface AggregateNode extends ProjectAggregate {
  id: string
  level: AggregateLevel
  scene_name: string
  group_name: string
  employee_id: string
  children?: AggregateNode[]
  hasChildren: boolean
  loading?: boolean
}
