<script setup lang="ts" generic="TData extends { id: string; children?: TData[] }">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  shallowRef,
  useTemplateRef,
  watch,
} from 'vue'
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
  RowSelectionState,
  SortingState,
  Updater,
  VisibilityState,
} from '@tanstack/vue-table'
import BaseCheckbox from './BaseCheckbox.vue'
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
  }>(),
  {
    editors: () => ({}),
    emptyText: '没有符合条件的数据',
    canExpand: undefined,
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
    size: 64,
    enableResizing: false,
    enableSorting: false,
    enableColumnFilter: false,
  },
]

const mergedColumns = computed<ColumnDef<TData, unknown>[]>(() => [
  ...utilityColumns,
  ...props.columns,
])

function updateRef<T>(state: { value: T }, updater: Updater<T>) {
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
  enableRowSelection: true,
  enableSubRowSelection: true,
  getRowCanExpand: props.canExpand
    ? (row) => props.canExpand!(row.original)
    : undefined,
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

function applyState(state: WorkbenchViewState) {
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

function toggleColumn(payload: { id: string; visible: boolean }) {
  table.getColumn(payload.id)?.toggleVisibility(payload.visible)
}

function moveColumn(payload: { id: string; direction: -1 | 1 }) {
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

function setFilterValue(columnId: string, value: string) {
  table.getColumn(columnId)?.setFilterValue(value || undefined)
}

function getSelectValues(columnId: string): string[] {
  return getFilterValue(columnId).split('\u0000').filter(Boolean)
}

function toggleSelectValue(columnId: string, option: string, checked: boolean) {
  const current = new Set(getSelectValues(columnId))
  if (checked) current.add(option)
  else current.delete(option)
  setFilterValue(columnId, [...current].join('\u0000'))
}

function getRangePart(columnId: string, index: number): string {
  return getFilterValue(columnId).split('\u0000')[index] ?? ''
}

function setRangePart(columnId: string, index: number, value: string) {
  const parts = [getRangePart(columnId, 0), getRangePart(columnId, 1)]
  parts[index] = value
  setFilterValue(columnId, parts.join('\u0000'))
}

function canEdit(row: TData, columnId: string) {
  const editor = props.editors[columnId]
  return Boolean(editor && (!editor.canEdit || editor.canEdit(row)))
}

function editCell(row: TData, columnId: string, event: Event) {
  const editor = props.editors[columnId]
  if (!editor) return
  const rawValue = (event.target as HTMLInputElement | HTMLSelectElement).value
  emit('cellEdit', {
    row,
    columnId,
    value: editor.type === 'number' ? Number(rawValue) : rawValue,
  })
}

function toggleExpanded(
  row: {
    original: TData
    getIsExpanded: () => boolean
    toggleExpanded: () => void
  },
) {
  const willExpand = !row.getIsExpanded()
  row.toggleExpanded()
  if (willExpand) emit('rowExpand', row.original)
}

const bodyScroll = useTemplateRef<HTMLDivElement>('bodyScroll')
const topScroll = useTemplateRef<HTMLDivElement>('topScroll')
const bottomScroll = useTemplateRef<HTMLDivElement>('bottomScroll')
const tableElement = useTemplateRef<HTMLTableElement>('tableElement')
const scrollWidth = shallowRef(0)
let scrollLock = false
let resizeObserver: ResizeObserver | null = null

function syncScroll(source: 'top' | 'body' | 'bottom') {
  if (scrollLock) return
  const sourceElement =
    source === 'top'
      ? topScroll.value
      : source === 'body'
        ? bodyScroll.value
        : bottomScroll.value
  if (!sourceElement) return

  scrollLock = true
  const left = sourceElement.scrollLeft
  if (source !== 'top' && topScroll.value) topScroll.value.scrollLeft = left
  if (source !== 'body' && bodyScroll.value) bodyScroll.value.scrollLeft = left
  if (source !== 'bottom' && bottomScroll.value) bottomScroll.value.scrollLeft = left
  window.requestAnimationFrame(() => {
    scrollLock = false
  })
}

function measureTable() {
  scrollWidth.value = tableElement.value?.scrollWidth ?? 0
}

onMounted(async () => {
  await nextTick()
  measureTable()
  if (tableElement.value) {
    resizeObserver = new ResizeObserver(measureTable)
    resizeObserver.observe(tableElement.value)
  }
})

onBeforeUnmount(() => resizeObserver?.disconnect())
</script>

<template>
  <section class="workbench-shell">
    <WorkbenchToolbar
      :row-count="rows.length"
      :selected-count="selectedRows.length"
      :active-filter-count="columnFilters.length"
      :columns="columnControls"
      @clear-filters="table.resetColumnFilters()"
      @expand-all="table.toggleAllRowsExpanded(true)"
      @collapse-all="table.toggleAllRowsExpanded(false)"
      @toggle-column="toggleColumn"
      @move-column="moveColumn"
    />

    <div ref="topScroll" class="scroll-mirror" @scroll="syncScroll('top')">
      <div :style="{ width: `${scrollWidth}px`, height: '1px' }"></div>
    </div>

    <div ref="bodyScroll" class="table-scroll" @scroll="syncScroll('body')">
      <table
        ref="tableElement"
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
                  aria-label="选择所有行"
                  @update:model-value="table.toggleAllRowsSelected($event)"
                />
              </template>
              <span v-else-if="header.column.id === '__expand'">层级</span>
              <button
                v-else
                class="header-button"
                :class="{ 'is-sortable': header.column.getCanSort() }"
                type="button"
                :disabled="!header.column.getCanSort()"
                @click="header.column.getToggleSortingHandler()?.($event)"
              >
                <FlexRender
                  :render="header.column.columnDef.header"
                  :props="header.getContext()"
                />
                <span class="sort-indicator">
                  <template v-if="header.column.getIsSorted() === 'asc'">↑</template>
                  <template v-else-if="header.column.getIsSorted() === 'desc'">↓</template>
                  <template v-else-if="header.column.getCanSort()">↕</template>
                </span>
              </button>
              <div
                v-if="header.column.getCanResize()"
                class="column-resizer"
                :class="{ resizing: header.column.getIsResizing() }"
                @mousedown="header.getResizeHandler()($event)"
                @touchstart="header.getResizeHandler()($event)"
              ></div>
            </th>
          </tr>

          <tr class="filter-row">
            <th
              v-for="header in table.getHeaderGroups()[0]?.headers ?? []"
              :key="header.id"
              :style="{ width: `${header.getSize()}px` }"
            >
              <template
                v-if="
                  header.column.id === '__select' ||
                  header.column.id === '__expand'
                "
              ></template>
              <input
                v-else-if="getFilterSpec(header.column.id)?.type === 'text'"
                class="filter-input"
                type="text"
                placeholder="筛选…"
                :value="getFilterValue(header.column.id)"
                @input="
                  setFilterValue(
                    header.column.id,
                    ($event.target as HTMLInputElement).value,
                  )
                "
              />
              <details
                v-else-if="getFilterSpec(header.column.id)?.type === 'select'"
                class="filter-select"
              >
                <summary class="filter-select-trigger">
                  {{
                    getSelectValues(header.column.id).length
                      ? `已选 ${getSelectValues(header.column.id).length} 项`
                      : '筛选…'
                  }}
                </summary>
                <div class="filter-select-popover">
                  <button
                    type="button"
                    class="clear-filter"
                    @click="setFilterValue(header.column.id, '')"
                  >
                    清除
                  </button>
                  <BaseCheckbox
                    v-for="option in getFilterSpec(header.column.id)?.options ?? []"
                    :key="option"
                    :model-value="getSelectValues(header.column.id).includes(option)"
                    :label="option"
                    @update:model-value="
                      toggleSelectValue(header.column.id, option, $event)
                    "
                  />
                </div>
              </details>
              <div
                v-else-if="getFilterSpec(header.column.id)?.type === 'date-range'"
                class="filter-date-range"
              >
                <input
                  class="filter-input"
                  type="date"
                  :value="getRangePart(header.column.id, 0)"
                  @input="
                    setRangePart(
                      header.column.id,
                      0,
                      ($event.target as HTMLInputElement).value,
                    )
                  "
                />
                <input
                  class="filter-input"
                  type="date"
                  :value="getRangePart(header.column.id, 1)"
                  @input="
                    setRangePart(
                      header.column.id,
                      1,
                      ($event.target as HTMLInputElement).value,
                    )
                  "
                />
              </div>
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
                <div class="expand-cell" :style="{ paddingLeft: `${row.depth * 12}px` }">
                  <button
                    v-if="row.getCanExpand()"
                    class="expand-button"
                    type="button"
                    :aria-expanded="row.getIsExpanded()"
                    @click="toggleExpanded(row)"
                  >
                    {{ row.getIsExpanded() ? '−' : '+' }}
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
                  :type="editors[cell.column.id]?.type === 'number' ? 'number' : 'text'"
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
            <td :colspan="table.getVisibleLeafColumns().length" class="empty-cell">
              {{ emptyText }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      ref="bottomScroll"
      class="scroll-mirror bottom"
      @scroll="syncScroll('bottom')"
    >
      <div :style="{ width: `${scrollWidth}px`, height: '1px' }"></div>
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

.scroll-mirror {
  height: 13px;
  overflow-x: auto;
  overflow-y: hidden;
  background: #fafbfc;
}

.scroll-mirror.bottom {
  position: sticky;
  z-index: 9;
  bottom: 0;
  border-top: 1px solid var(--color-line);
}

.table-scroll {
  max-height: 62vh;
  overflow: auto;
}

.data-table {
  table-layout: fixed;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  position: relative;
  overflow: hidden;
  padding: 8px 9px;
  border-right: 1px solid var(--color-line-subtle);
  border-bottom: 1px solid var(--color-line-subtle);
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.data-table th {
  position: sticky;
  z-index: 5;
  top: 0;
  height: 38px;
  background: #f4f6f9;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.filter-row th {
  top: 38px;
  z-index: 4;
  padding: 4px 6px;
  background: #fafbfd;
  font-weight: 400;
}

.data-table tbody tr:hover td {
  background: #f8faff;
}

.header-button {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 5px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font-weight: inherit;
  text-align: left;
}

.sort-indicator {
  flex: none;
  color: var(--color-muted);
  font-size: 10px;
}

.column-resizer {
  position: absolute;
  inset: 0 -2px 0 auto;
  width: 5px;
  cursor: col-resize;
  touch-action: none;
}

.column-resizer:hover,
.column-resizer.resizing {
  background: var(--color-primary);
}

.filter-input {
  width: 100%;
  min-height: 26px;
  padding: 2px 5px;
  border: 1px solid var(--color-line);
  border-radius: 3px;
  font-size: 11px;
}

.filter-date-range {
  display: grid;
  gap: 2px;
}

.filter-select {
  position: relative;
}

.filter-select-trigger {
  overflow: hidden;
  padding: 4px 5px;
  border: 1px solid var(--color-line);
  border-radius: 3px;
  color: var(--color-muted);
  font-size: 11px;
  list-style: none;
  text-overflow: ellipsis;
}

.filter-select-trigger::-webkit-details-marker {
  display: none;
}

.filter-select-popover {
  position: absolute;
  z-index: 25;
  top: 29px;
  left: 0;
  display: grid;
  min-width: 170px;
  max-height: 260px;
  gap: 3px;
  overflow: auto;
  padding: 8px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  background: white;
  box-shadow: var(--shadow-md);
}

.clear-filter {
  justify-self: start;
  padding: 2px 0;
  border: 0;
  background: transparent;
  color: var(--color-primary);
  font-size: 10px;
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
