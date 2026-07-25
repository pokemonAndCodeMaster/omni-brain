export interface SnapshotQuery {
  stat_date_start?: string
  stat_date_end?: string
  scene_name?: string
  group_name?: string
  employee_id?: string
}

export interface SnapshotCounts {
  annotation_total: number
  annotation_submitted: number
  good_annotation_submitted: number
  bad_annotation_submitted: number
  total_accept_assigned: number
  total_accept_completed: number
  total_accept_passed: number
  total_accept_rejected: number
  good_accept_assigned: number
  good_accept_completed: number
  good_accept_passed: number
  good_accept_rejected: number
  bad_accept_assigned: number
  bad_accept_completed: number
  bad_accept_passed: number
  bad_accept_rejected: number
}

export interface SceneAggregate extends SnapshotCounts {
  stat_date: string
  scene_name: string
  computed_at: string
}

export interface GroupAggregate extends SceneAggregate {
  group_name: string
}

export interface EmployeeAggregate extends GroupAggregate {
  employee_id: string
}

export interface DataResponse<T> {
  schema_version: 'lab-v1'
  items: T[]
  total: number
  computed_at: string | null
}

export type AggregateLevel = 'scene' | 'group' | 'employee'

export interface AggregateNode extends EmployeeAggregate {
  id: string
  level: AggregateLevel
  group_name: string
  employee_id: string
  children?: AggregateNode[]
  loading?: boolean
}
