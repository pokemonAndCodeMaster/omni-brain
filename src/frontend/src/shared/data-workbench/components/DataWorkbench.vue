<script setup lang="ts" generic="TData extends { id: string; children?: TData[] }">
import { computed, nextTick, ref, shallowRef, watch } from 'vue'
import {
  FlexRender,
  functionalUpdate,
  getCoreRowModel,
  getExpandedRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import type {
  ColumnDef,
  ColumnFiltersState,
  ColumnOrderState,
  ColumnSizingState,
  ExpandedState,
  Row,
  RowSelectionState,
  SortingState,
  Updater,
  VisibilityState,
} from '@tanstack/vue-table'
import BaseCheckbox from './BaseCheckbox.vue'
import HeaderFilter from './HeaderFilter.vue'
import WorkbenchToolbar from './WorkbenchToolbar.vue'
import type {
  ColumnEditorSpec,
  WorkbenchColumnControl,
  WorkbenchFilterSpec,
  WorkbenchViewState,
} from '../types'

const props = withDefaults(
  defineProps<{
    rows: TData[]
    columns: ColumnDef<TData, unknown>[]
    editors?: Record<string, ColumnEditorSpec<TData>>
    emptyText?: string
    canExpand?: (row: TData) => boolean
    loadChildren?: (row: TData) => Promise<boolean>
  }>(),
  {
    editors: () => ({}),
    emptyText: '没有符合条件的数据',
    canExpand: undefined,
    loadChildren: undefined,
  },
)

const emit = defineEmits<{
  cellEdit: [payload: { row: TData; columnId: string; value: string | number }]
  selectionChange: [rows: TData[]]
  stateChange: [state: WorkbenchViewState]
  rowExpand: [row: TData]
}>()

const sorting = ref<SortingState>([])
const columnFilters = ref<ColumnFiltersState>([])
const expanded = ref<ExpandedState>({})
const rowSelection = ref<RowSelectionState>({})
const columnVisibility = ref<VisibilityState>({})
const columnOrder = ref<ColumnOrderState>([])
const columnSizing = ref<ColumnSizingState>({})
const loadingRowIds = shallowRef<Set<string>>(new Set())

const utilityColumns: ColumnDef<TData, unknown>[] = [
  {
    id: '__select',
    size: 44,
    enableResizing: false,
    enableSorting: false,
    enableColumnFilter: false,
  },
  {
    id: '__expand',
    size: 58,
    enableResizing: false,
    enableSorting: false,
    enableColumnFilter: false,
  },
]

const mergedColumns = computed<ColumnDef<TData, unknown>[]>(() => [
  ...utilityColumns,
  ...props.columns,
])

function updateRef<T>(state: { value: T }, updater: Updater<T>): void {
  state.value = functionalUpdate(updater, state.value)
}

function cloneSerializable<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

const table = useVueTable<TData>({
  get data() {
    return props.rows
  },
  get columns() {
    return mergedColumns.value
  },
  getRowId: (row) => row.id,
  getSubRows: (row) => row.children,
  getRowCanExpand: props.canExpand
    ? (row) => props.canExpand!(row.original)
    : undefined,
  enableRowSelection: true,
  enableSubRowSelection: true,
  columnResizeMode: 'onChange',
  state: {
    get sorting() {
      return sorting.value
    },
    get columnFilters() {
      return columnFilters.value
    },
    get expanded() {
      return expanded.value
    },
    get rowSelection() {
      return rowSelection.value
    },
    get columnVisibility() {
      return columnVisibility.value
    },
    get columnOrder() {
      return columnOrder.value
    },
    get columnSizing() {
      return columnSizing.value
    },
  },
  onSortingChange: (updater) => updateRef(sorting, updater),
  onColumnFiltersChange: (updater) => updateRef(columnFilters, updater),
  onExpandedChange: (updater) => updateRef(expanded, updater),
  onRowSelectionChange: (updater) => updateRef(rowSelection, updater),
  onColumnVisibilityChange: (updater) => updateRef(columnVisibility, updater),
  onColumnOrderChange: (updater) => updateRef(columnOrder, updater),
  onColumnSizingChange: (updater) => updateRef(columnSizing, updater),
  getCoreRowModel: getCoreRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getExpandedRowModel: getExpandedRowModel(),
})

const selectedRows = computed(() =>
  table.getSelectedRowModel().flatRows.map((row) => row.original),
)

const hasExpandedRows = computed(() =>
  expanded.value === true
    ? true
    : Object.values(expanded.value).some(Boolean),
)

const columnControls = computed<WorkbenchColumnControl[]>(() => {
  const columns = table
    .getAllLeafColumns()
    .filter((column) => !column.id.startsWith('__'))
  return columns.map((column, index) => ({
    id: column.id,
    label:
      typeof column.columnDef.header === 'string'
        ? column.columnDef.header
        : column.id,
    visible: column.getIsVisible(),
    canMoveLeft: index > 0,
    canMoveRight: index < columns.length - 1,
  }))
})

function exportState(): WorkbenchViewState {
  return {
    sorting: cloneSerializable(sorting.value),
    expanded: cloneSerializable(expanded.value),
    columnVisibility: cloneSerializable(columnVisibility.value),
    columnOrder: cloneSerializable(columnOrder.value),
    columnSizing: cloneSerializable(columnSizing.value),
    columnFilters: cloneSerializable(columnFilters.value),
  }
}

function applyState(state: WorkbenchViewState): void {
  sorting.value = cloneSerializable(state.sorting)
  expanded.value = cloneSerializable(state.expanded)
  columnVisibility.value = cloneSerializable(state.columnVisibility)
  const businessOrder = state.columnOrder.filter(
    (id) => id !== '__select' && id !== '__expand',
  )
  columnOrder.value = businessOrder.length
    ? ['__select', '__expand', ...businessOrder]
    : []
  columnSizing.value = cloneSerializable(state.columnSizing)
  columnFilters.value = cloneSerializable(state.columnFilters)
}

defineExpose({ exportState, applyState, selectedRows })

watch(
  [sorting, columnFilters, expanded, columnVisibility, columnOrder, columnSizing],
  () => emit('stateChange', exportState()),
  { deep: true },
)

watch(
  rowSelection,
  () => emit('selectionChange', selectedRows.value),
  { deep: true },
)

function toggleColumn(payload: { id: string; visible: boolean }): void {
  table.getColumn(payload.id)?.toggleVisibility(payload.visible)
}

function moveColumn(payload: { id: string; direction: -1 | 1 }): void {
  const businessOrder = table
    .getAllLeafColumns()
    .map((column) => column.id)
    .filter((id) => !id.startsWith('__'))
  const index = businessOrder.indexOf(payload.id)
  const target = index + payload.direction
  if (index < 0 || target < 0 || target >= businessOrder.length) return
  ;[businessOrder[index], businessOrder[target]] = [
    businessOrder[target]!,
    businessOrder[index]!,
  ]
  columnOrder.value = ['__select', '__expand', ...businessOrder]
}

function getFilterSpec(columnId: string): WorkbenchFilterSpec | undefined {
  if (columnId.startsWith('__')) return undefined
  return table.getColumn(columnId)?.columnDef.meta?.filter
}

function getFilterValue(columnId: string): string {
  return String(table.getColumn(columnId)?.getFilterValue() ?? '')
}

function setFilterValue(columnId: string, value: string): void {
  table.getColumn(columnId)?.setFilterValue(value || undefined)
}

function getColumnLabel(columnId: string): string {
  const header = table.getColumn(columnId)?.columnDef.header
  return typeof header === 'string' ? header : columnId
}

function canEdit(row: TData, columnId: string): boolean {
  const editor = props.editors[columnId]
  return Boolean(editor && (!editor.canEdit || editor.canEdit(row)))
}

function editCell(row: TData, columnId: string, event: Event): void {
  const editor = props.editors[columnId]
  if (!editor) return
  const rawValue = (event.target as HTMLInputElement | HTMLSelectElement).value
  emit('cellEdit', {
    row,
    columnId,
    value: editor.type === 'number' ? Number(rawValue) : rawValue,
  })
}

function setRowLoading(rowId: string, value: boolean): void {
  const next = new Set(loadingRowIds.value)
  if (value) next.add(rowId)
  else next.delete(rowId)
  loadingRowIds.value = next
}

async function toggleExpanded(row: Row<TData>): Promise<void> {
  if (row.getIsExpanded()) {
    row.toggleExpanded(false)
    return
  }

  if (row.subRows.length || !props.loadChildren) {
    row.toggleExpanded(true)
    emit('rowExpand', row.original)
    return
  }

  setRowLoading(row.id, true)
  try {
    const loaded = await props.loadChildren(row.original)
    await nextTick()
    const currentRow = table.getRow(row.id)
    if (loaded && currentRow.subRows.length > 0) {
      currentRow.toggleExpanded(true)
      emit('rowExpand', currentRow.original)
    }
  } finally {
    setRowLoading(row.id, false)
  }
}
</script>

<template>
  <section class="workbench-shell" aria-label="数据工作台">
    <WorkbenchToolbar
      :row-count="rows.length"
      :selected-count="selectedRows.length"
      :active-filter-count="columnFilters.length"
      :columns="columnControls"
      :has-expanded-rows="hasExpandedRows"
      @clear-filters="table.resetColumnFilters()"
      @collapse-all="table.toggleAllRowsExpanded(false)"
      @toggle-column="toggleColumn"
      @move-column="moveColumn"
    />

    <div class="table-scroll" data-testid="table-scroll">
      <table
        class="data-table"
        :style="{ width: `${table.getTotalSize()}px` }"
      >
        <thead>
          <tr
            v-for="headerGroup in table.getHeaderGroups()"
            :key="headerGroup.id"
            class="header-row"
          >
            <th
              v-for="header in headerGroup.headers"
              :key="header.id"
              :style="{ width: `${header.getSize()}px` }"
            >
              <template v-if="header.column.id === '__select'">
                <BaseCheckbox
                  :model-value="table.getIsAllRowsSelected()"
                  :indeterminate="table.getIsSomeRowsSelected()"
                  aria-label="选择所有已加载行"
                  @update:model-value="table.toggleAllRowsSelected($event)"
                />
              </template>
              <span v-else-if="header.column.id === '__expand'">层级</span>
              <div v-else class="header-content">
                <button
                  class="header-button"
                  :class="{ 'is-sortable': header.column.getCanSort() }"
                  type="button"
                  :disabled="!header.column.getCanSort()"
                  @click="
                    header.column.getToggleSortingHandler()?.($event)
                  "
                >
                  <FlexRender
                    :render="header.column.columnDef.header"
                    :props="header.getContext()"
                  />
                  <span class="sort-indicator" aria-hidden="true">
                    <template v-if="header.column.getIsSorted() === 'asc'">↑</template>
                    <template v-else-if="header.column.getIsSorted() === 'desc'">↓</template>
                    <template v-else-if="header.column.getCanSort()">↕</template>
                  </span>
                </button>
                <HeaderFilter
                  v-if="getFilterSpec(header.column.id)"
                  :label="getColumnLabel(header.column.id)"
                  :spec="getFilterSpec(header.column.id)!"
                  :model-value="getFilterValue(header.column.id)"
                  @update:model-value="
                    setFilterValue(header.column.id, $event)
                  "
                />
              </div>
              <div
                v-if="header.column.getCanResize()"
                class="column-resizer"
                :class="{ resizing: header.column.getIsResizing() }"
                @mousedown="header.getResizeHandler()($event)"
                @touchstart="header.getResizeHandler()($event)"
              />
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="row in table.getRowModel().rows" :key="row.id">
            <td
              v-for="cell in row.getVisibleCells()"
              :key="cell.id"
              :style="{ width: `${cell.column.getSize()}px` }"
            >
              <template v-if="cell.column.id === '__select'">
                <BaseCheckbox
                  :model-value="row.getIsSelected()"
                  :indeterminate="row.getIsSomeSelected()"
                  :disabled="!row.getCanSelect()"
                  :aria-label="`选择 ${row.id}`"
                  @update:model-value="row.toggleSelected($event)"
                />
              </template>
              <template v-else-if="cell.column.id === '__expand'">
                <div
                  class="expand-cell"
                  :style="{ paddingLeft: `${row.depth * 12}px` }"
                >
                  <button
                    v-if="row.getCanExpand()"
                    class="expand-button"
                    type="button"
                    :disabled="loadingRowIds.has(row.id)"
                    :aria-expanded="row.getIsExpanded()"
                    :aria-label="
                      loadingRowIds.has(row.id)
                        ? `正在加载 ${row.id}`
                        : `${row.getIsExpanded() ? '折叠' : '展开'} ${row.id}`
                    "
                    @click="toggleExpanded(row)"
                  >
                    {{
                      loadingRowIds.has(row.id)
                        ? '…'
                        : row.getIsExpanded()
                          ? '−'
                          : '+'
                    }}
                  </button>
                  <span v-else class="leaf-dot">·</span>
                  <small>L{{ row.depth + 1 }}</small>
                </div>
              </template>
              <template v-else-if="canEdit(row.original, cell.column.id)">
                <select
                  v-if="editors[cell.column.id]?.type === 'select'"
                  class="cell-editor"
                  :value="String(cell.getValue() ?? '')"
                  @change="editCell(row.original, cell.column.id, $event)"
                >
                  <option
                    v-for="option in editors[cell.column.id]?.options ?? []"
                    :key="option"
                    :value="option"
                  >
                    {{ option }}
                  </option>
                </select>
                <input
                  v-else
                  class="cell-editor"
                  :type="
                    editors[cell.column.id]?.type === 'number'
                      ? 'number'
                      : 'text'
                  "
                  :value="String(cell.getValue() ?? '')"
                  @change="editCell(row.original, cell.column.id, $event)"
                />
              </template>
              <FlexRender
                v-else
                :render="cell.column.columnDef.cell"
                :props="cell.getContext()"
              />
            </td>
          </tr>
          <tr v-if="table.getRowModel().rows.length === 0">
            <td
              :colspan="table.getVisibleLeafColumns().length"
              class="empty-cell"
            >
              {{ emptyText }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.workbench-shell {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  overflow: visible;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: white;
}

.table-scroll {
  max-width: 100%;
  max-height: 62vh;
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

.data-table {
  min-width: 100%;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}

.data-table th,
.data-table td {
  position: relative;
  padding: 8px 9px;
  border-right: 1px solid var(--color-line-subtle);
  border-bottom: 1px solid var(--color-line-subtle);
  text-align: left;
  white-space: nowrap;
}

.data-table th {
  position: sticky;
  z-index: 10;
  top: 0;
  height: 42px;
  overflow: visible;
  background: #f4f6f9;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.data-table td {
  overflow: hidden;
  text-overflow: ellipsis;
}

.data-table tbody tr:hover td {
  background: #f8faff;
}

.header-content {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: 3px;
}

.header-button {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  justify-content: space-between;
  gap: 5px;
  overflow: hidden;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font-weight: inherit;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-button:disabled {
  opacity: 1;
}

.header-button.is-sortable {
  cursor: pointer;
}

.sort-indicator {
  flex: none;
  color: var(--color-muted);
  font-size: 10px;
}

.column-resizer {
  position: absolute;
  z-index: 2;
  inset: 0 -2px 0 auto;
  width: 5px;
  cursor: col-resize;
  touch-action: none;
}

.column-resizer:hover,
.column-resizer.resizing {
  background: var(--color-primary);
}

.expand-cell {
  display: flex;
  gap: 5px;
  align-items: center;
}

.expand-button {
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border: 1px solid #bdc7d2;
  border-radius: 3px;
  background: white;
  color: var(--color-primary);
}

.expand-button:disabled {
  cursor: wait;
  opacity: 0.75;
}

.leaf-dot {
  width: 22px;
  text-align: center;
}

.expand-cell small {
  color: var(--color-muted);
  font-family: var(--font-mono);
  font-size: 9px;
}

.cell-editor {
  width: 100%;
  min-height: 28px;
  border: 1px solid #bdc7d2;
  border-radius: 3px;
  background: white;
}

.empty-cell {
  padding: 42px !important;
  color: var(--color-muted);
  text-align: center !important;
}
</style>
