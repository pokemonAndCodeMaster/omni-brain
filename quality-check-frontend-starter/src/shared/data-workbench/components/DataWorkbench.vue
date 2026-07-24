<script setup lang="ts" generic="TData extends { id: string; children?: TData[] }">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue'
import {
  FlexRender,
  functionalUpdate,
  getCoreRowModel,
  getExpandedRowModel,
  getSortedRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import type {
  ColumnDef,
  ColumnOrderState,
  ColumnSizingState,
  ExpandedState,
  RowSelectionState,
  SortingState,
  Updater,
  VisibilityState,
} from '@tanstack/vue-table'
import BaseCheckbox from '@/shared/data-workbench/components/BaseCheckbox.vue'
import type {
  ColumnEditorSpec,
  WorkbenchViewState,
} from '@/shared/data-workbench/types/workbench'

const props = withDefaults(
  defineProps<{
    rows: TData[]
    columns: ColumnDef<TData, any>[]
    editors?: Record<string, ColumnEditorSpec<TData>>
    emptyText?: string
  }>(),
  {
    editors: () => ({}),
    emptyText: '没有符合条件的数据',
  },
)

const emit = defineEmits<{
  cellEdit: [payload: { row: TData; columnId: string; value: string | number }]
  selectionChange: [rows: TData[]]
  stateChange: [state: WorkbenchViewState]
}>()

const sorting = ref<SortingState>([])
const expanded = ref<ExpandedState>({})
const rowSelection = ref<RowSelectionState>({})
const columnVisibility = ref<VisibilityState>({})
const columnOrder = ref<ColumnOrderState>([])
const columnSizing = ref<ColumnSizingState>({})

const utilityColumns: ColumnDef<TData, any>[] = [
  { id: '__select', size: 44, enableResizing: false, enableSorting: false },
  { id: '__expand', size: 48, enableResizing: false, enableSorting: false },
]

const mergedColumns = computed<ColumnDef<TData, any>[]>(() => [
  ...utilityColumns,
  ...props.columns,
])

function updateRef<T>(state: { value: T }, updater: Updater<T>) {
  state.value = functionalUpdate(updater, state.value)
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
  columnResizeMode: 'onChange',
  state: {
    get sorting() {
      return sorting.value
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
  onExpandedChange: (updater) => updateRef(expanded, updater),
  onRowSelectionChange: (updater) => updateRef(rowSelection, updater),
  onColumnVisibilityChange: (updater) => updateRef(columnVisibility, updater),
  onColumnOrderChange: (updater) => updateRef(columnOrder, updater),
  onColumnSizingChange: (updater) => updateRef(columnSizing, updater),
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getExpandedRowModel: getExpandedRowModel(),
})

function exportState(): WorkbenchViewState {
  return {
    sorting: structuredClone(sorting.value),
    expanded: structuredClone(expanded.value),
    columnVisibility: structuredClone(columnVisibility.value),
    columnOrder: structuredClone(columnOrder.value),
    columnSizing: structuredClone(columnSizing.value),
  }
}

function applyState(state: WorkbenchViewState) {
  sorting.value = structuredClone(state.sorting)
  expanded.value = structuredClone(state.expanded)
  columnVisibility.value = structuredClone(state.columnVisibility)
  const businessOrder = state.columnOrder.filter(
    (id) => id !== '__select' && id !== '__expand',
  )
  columnOrder.value = businessOrder.length
    ? ['__select', '__expand', ...businessOrder]
    : []
  columnSizing.value = structuredClone(state.columnSizing)
}

function selectedRows() {
  return table.getSelectedRowModel().flatRows.map((row) => row.original)
}

defineExpose({ exportState, applyState, selectedRows })

watch(
  [sorting, expanded, columnVisibility, columnOrder, columnSizing],
  () => emit('stateChange', exportState()),
  { deep: true },
)

watch(
  rowSelection,
  () => emit('selectionChange', selectedRows()),
  { deep: true },
)

function changeColumnVisibility(id: string, value: boolean) {
  table.getColumn(id)?.toggleVisibility(value)
}

function moveColumn(id: string, direction: -1 | 1) {
  const visibleOrder = table
    .getAllLeafColumns()
    .map((column) => column.id)
    .filter((columnId) => columnId !== '__select' && columnId !== '__expand')
  const index = visibleOrder.indexOf(id)
  const target = index + direction
  if (index < 0 || target < 0 || target >= visibleOrder.length) return
  ;[visibleOrder[index], visibleOrder[target]] = [visibleOrder[target]!, visibleOrder[index]!]
  columnOrder.value = ['__select', '__expand', ...visibleOrder]
}

function getEventValue(event: Event) {
  return (event.target as HTMLInputElement | HTMLSelectElement).value
}

function editCell(row: TData, columnId: string, event: Event) {
  const editor = props.editors[columnId]
  if (!editor) return
  const rawValue = getEventValue(event)
  emit('cellEdit', {
    row,
    columnId,
    value: editor.type === 'number' ? Number(rawValue) : rawValue,
  })
}

function canEdit(row: TData, columnId: string) {
  const editor = props.editors[columnId]
  return Boolean(editor && (!editor.canEdit || editor.canEdit(row)))
}

const bodyScroll = ref<HTMLDivElement | null>(null)
const topScroll = ref<HTMLDivElement | null>(null)
const bottomScroll = ref<HTMLDivElement | null>(null)
const tableElement = ref<HTMLTableElement | null>(null)
const scrollWidth = ref(0)
let scrollLock = false
let resizeObserver: ResizeObserver | null = null

function syncScroll(source: 'top' | 'body' | 'bottom') {
  if (scrollLock) return
  const sourceElement =
    source === 'top' ? topScroll.value : source === 'body' ? bodyScroll.value : bottomScroll.value
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
    <div class="workbench-meta">
      <div class="toolbar-group">
        <span class="badge">{{ rows.length }} 个顶层对象</span>
        <span class="badge">已选择 {{ table.getSelectedRowModel().flatRows.length }} 行</span>
        <button class="button" type="button" @click="table.toggleAllRowsExpanded(true)">全部展开</button>
        <button class="button" type="button" @click="table.toggleAllRowsExpanded(false)">全部折叠</button>
      </div>

      <details class="column-manager">
        <summary class="button">列配置</summary>
        <div class="column-popover">
          <div
            v-for="column in table.getAllLeafColumns().filter((item) => !item.id.startsWith('__'))"
            :key="column.id"
            class="column-config-row"
          >
            <BaseCheckbox
              :model-value="column.getIsVisible()"
              :label="String(column.columnDef.header ?? column.id)"
              @update:model-value="changeColumnVisibility(column.id, $event)"
            />
            <span class="column-move-actions">
              <button type="button" @click="moveColumn(column.id, -1)">←</button>
              <button type="button" @click="moveColumn(column.id, 1)">→</button>
            </span>
          </div>
        </div>
      </details>
    </div>

    <div ref="topScroll" class="scroll-mirror" @scroll="syncScroll('top')">
      <div :style="{ width: `${scrollWidth}px`, height: '1px' }"></div>
    </div>

    <div ref="bodyScroll" class="table-scroll" @scroll="syncScroll('body')">
      <table ref="tableElement" class="data-table" :style="{ width: `${table.getTotalSize()}px` }">
        <thead>
          <tr v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
            <th
              v-for="header in headerGroup.headers"
              :key="header.id"
              :style="{ width: `${header.getSize()}px` }"
            >
              <template v-if="header.column.id === '__select'">
                <BaseCheckbox
                  :model-value="table.getIsAllRowsSelected()"
                  :indeterminate="table.getIsSomeRowsSelected()"
                  @update:model-value="table.toggleAllRowsSelected($event)"
                />
              </template>
              <span v-else-if="header.column.id === '__expand'">层级</span>
              <button
                v-else
                class="header-button"
                type="button"
                :disabled="!header.column.getCanSort()"
                @click="header.column.getToggleSortingHandler()?.($event)"
              >
                <FlexRender :render="header.column.columnDef.header" :props="header.getContext()" />
                <span v-if="header.column.getIsSorted() === 'asc'">↑</span>
                <span v-else-if="header.column.getIsSorted() === 'desc'">↓</span>
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
                  @update:model-value="row.toggleSelected($event)"
                />
              </template>

              <template v-else-if="cell.column.id === '__expand'">
                <div class="expand-cell" :style="{ paddingLeft: `${row.depth * 12}px` }">
                  <button
                    v-if="row.getCanExpand()"
                    class="expand-button"
                    type="button"
                    @click="row.toggleExpanded()"
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

              <FlexRender v-else :render="cell.column.columnDef.cell" :props="cell.getContext()" />
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

    <div ref="bottomScroll" class="scroll-mirror bottom" @scroll="syncScroll('bottom')">
      <div :style="{ width: `${scrollWidth}px`, height: '1px' }"></div>
    </div>
  </section>
</template>

<style scoped>
.workbench-shell {
  position: relative;
  overflow: visible;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: white;
}

.workbench-meta {
  display: flex;
  min-height: 50px;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-bottom: 1px solid var(--color-border);
}

.column-manager {
  position: relative;
}

.column-manager summary {
  list-style: none;
}

.column-manager summary::-webkit-details-marker {
  display: none;
}

.column-popover {
  position: absolute;
  z-index: 15;
  top: 42px;
  right: 0;
  width: 270px;
  max-height: 380px;
  overflow: auto;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: white;
  box-shadow: var(--shadow-md);
}

.column-config-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 7px 4px;
  border-bottom: 1px solid var(--color-border);
}

.column-move-actions {
  display: flex;
  gap: 3px;
}

.column-move-actions button {
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: white;
}

.scroll-mirror {
  overflow-x: auto;
  overflow-y: hidden;
  height: 13px;
  background: #fafbfc;
}

.scroll-mirror.bottom {
  position: sticky;
  z-index: 9;
  bottom: 0;
  border-top: 1px solid var(--color-border);
}

.table-scroll {
  overflow: auto;
  max-height: 62vh;
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
  border-right: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.data-table th {
  position: sticky;
  z-index: 5;
  top: 0;
  background: #f4f6f9;
  color: #344054;
  font-weight: 600;
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

.column-resizer {
  position: absolute;
  top: 0;
  right: -2px;
  width: 5px;
  height: 100%;
  cursor: col-resize;
  user-select: none;
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
  border: 1px solid var(--color-border-strong);
  border-radius: 4px;
  background: white;
}

.leaf-dot {
  display: inline-block;
  width: 22px;
  text-align: center;
}

.cell-editor {
  width: 100%;
  min-height: 28px;
  border: 1px solid var(--color-border-strong);
  border-radius: 4px;
  background: white;
}

.empty-cell {
  padding: 40px !important;
  color: var(--color-text-muted);
  text-align: center !important;
}
</style>
