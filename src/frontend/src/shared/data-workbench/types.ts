import type {
  ColumnFiltersState,
  ColumnOrderState,
  ColumnSizingState,
  ExpandedState,
  FilterFn,
  SortingState,
  VisibilityState,
} from '@tanstack/vue-table'

export interface WorkbenchViewState {
  sorting: SortingState
  expanded: ExpandedState
  columnVisibility: VisibilityState
  columnOrder: ColumnOrderState
  columnSizing: ColumnSizingState
  columnFilters: ColumnFiltersState
}

export interface ColumnEditorSpec<TData> {
  type: 'text' | 'number' | 'select'
  options?: string[]
  canEdit?: (row: TData) => boolean
}

export interface WorkbenchFilterSpec {
  type: 'text' | 'select' | 'date-range' | 'number-range'
  options?: string[]
}

export interface WorkbenchColumnControl {
  id: string
  label: string
  visible: boolean
  canMoveLeft: boolean
  canMoveRight: boolean
}

export interface WorkbenchAnalysisRequest<TData> {
  rows: TData[]
  filterSummary: string
  filters: ColumnFiltersState
}

export const multiSelectFilter: FilterFn<unknown> = (
  row,
  columnId,
  filterValue,
) => {
  const selected = String(filterValue ?? '')
    .split('\u0000')
    .filter(Boolean)
  return selected.length === 0 || selected.includes(String(row.getValue(columnId) ?? ''))
}

export const dateRangeFilter: FilterFn<unknown> = (
  row,
  columnId,
  filterValue,
) => {
  const [start = '', end = ''] = String(filterValue ?? '').split('\u0000')
  const value = String(row.getValue(columnId) ?? '')
  if (!value) return false
  return (!start || value >= start) && (!end || value <= end)
}

export const numberRangeFilter: FilterFn<unknown> = (
  row,
  columnId,
  filterValue,
) => {
  const [minimum = '', maximum = ''] = String(filterValue ?? '').split('\u0000')
  const rawValue = row.getValue(columnId)
  if (rawValue == null || rawValue === '') return false
  const value = Number(rawValue)
  if (!Number.isFinite(value)) return false
  const lowerBound = minimum === '' ? null : Number(minimum)
  const upperBound = maximum === '' ? null : Number(maximum)
  return (
    (lowerBound == null || value >= lowerBound) &&
    (upperBound == null || value <= upperBound)
  )
}

declare module '@tanstack/vue-table' {
  interface ColumnMeta<TData, TValue> {
    filter?: WorkbenchFilterSpec
  }
}
