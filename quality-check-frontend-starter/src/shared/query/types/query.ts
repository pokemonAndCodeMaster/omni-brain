export type FilterOperator =
  | 'eq'
  | 'ne'
  | 'in'
  | 'not_in'
  | 'contains'
  | 'between'
  | 'is_null'
  | 'is_not_null'

export type FilterNode =
  | {
      type: 'condition'
      field: string
      operator: FilterOperator
      value?: unknown
    }
  | {
      type: 'group'
      logic: 'and' | 'or'
      children: FilterNode[]
    }

export interface QuerySpec {
  dataSourceId: string
  filters: FilterNode
  search?: string
  sorts: Array<{ field: string; direction: 'asc' | 'desc' }>
  groupBy: string[]
}
