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
  type: 'text' | 'select' | 'date-range'
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

declare module '@tanstack/vue-table' {
  interface ColumnMeta<TData, TValue> {
    filter?: WorkbenchFilterSpec
  }
}
