import type {
  ColumnOrderState,
  ColumnSizingState,
  ExpandedState,
  SortingState,
  VisibilityState,
} from '@tanstack/vue-table'

export interface WorkbenchBaseRow {
  id: string
  children?: WorkbenchBaseRow[]
}

export interface WorkbenchViewState {
  sorting: SortingState
  expanded: ExpandedState
  columnVisibility: VisibilityState
  columnOrder: ColumnOrderState
  columnSizing: ColumnSizingState
}

export interface SavedWorkbenchView {
  id: string
  name: string
  savedAt: string
  state: WorkbenchViewState
  context?: Record<string, string>
}

export interface ColumnEditorSpec<TData> {
  type: 'text' | 'number' | 'select'
  options?: string[]
  canEdit?: (row: TData) => boolean
}
