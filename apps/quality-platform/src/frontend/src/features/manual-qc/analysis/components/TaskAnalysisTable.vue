<script setup lang="ts">
import { computed, h } from 'vue'
import { createColumnHelper } from '@tanstack/vue-table'
import type { ColumnDef, FilterFn } from '@tanstack/vue-table'
import DataWorkbench from '@/shared/data-workbench/components/DataWorkbench.vue'
import type {
  WorkbenchAnalysisRequest,
  WorkbenchViewState,
} from '@/shared/data-workbench/types'
import {
  dateRangeFilter,
  numberRangeFilter,
  parseTextSelectionFilter,
  textSelectionFilter,
} from '@/shared/data-workbench/types'
import {
  metricReferenceKey,
} from '../utils'
import type {
  AnalysisCatalog,
  AnalysisMetricReference,
  TaskAnalysisRow,
  TaskMetricDetailSelection,
} from '../types/analysis'

const props = defineProps<{
  rows: TaskAnalysisRow[]
  loading: boolean
  total: number
  periodLabel: string
  pinnedMetrics: AnalysisMetricReference[]
  initialViewState: WorkbenchViewState | null
  savingConfig: boolean
  configDirty: boolean
  configNotice: string
  catalog?: AnalysisCatalog | null
  loadChildren: (row: TaskAnalysisRow) => Promise<boolean>
}>()

const emit = defineEmits<{
  createChart: [request: WorkbenchAnalysisRequest<TaskAnalysisRow>]
  applyFilters: [request: WorkbenchAnalysisRequest<TaskAnalysisRow>]
  openMetricDetail: [selection: TaskMetricDetailSelection]
  stateChange: [state: WorkbenchViewState]
  saveConfig: []
  removePinnedMetric: [reference: AnalysisMetricReference]
}>()

const columnHelper = createColumnHelper<TaskAnalysisRow>()
const levelLabels = ['标注任务', '日期', '组', '标注员'] as const
const levelOrder = {
  task: 0,
  date: 1,
  group: 2,
  employee: 3,
} as const

const taskBranchFilter: FilterFn<TaskAnalysisRow> = (
  row,
  _columnId,
  filterValue,
) => {
  const filter = parseTextSelectionFilter(filterValue)
  const query = filter.query.trim().toLocaleLowerCase()
  const matchesQuery =
    !query ||
    row.original.task.toLocaleLowerCase().includes(query) ||
    row.original.objectLabel.toLocaleLowerCase().includes(query)
  const matchesSelection =
    !filter.selected.length || filter.selected.includes(row.original.task)
  return matchesQuery && matchesSelection
}

const hierarchyLevelFilter: FilterFn<TaskAnalysisRow> = (
  row,
  _columnId,
  filterValue,
) => {
  const filter = parseTextSelectionFilter(filterValue)
  const query = filter.query.trim().toLocaleLowerCase()
  const targetDepths = levelLabels
    .map((label, depth) => ({ label, depth }))
    .filter(({ label }) => {
      const matchesQuery =
        !query || label.toLocaleLowerCase().includes(query)
      const matchesSelection =
        !filter.selected.length || filter.selected.includes(label)
      return matchesQuery && matchesSelection
    })
    .map(({ depth }) => depth)
  if (!targetDepths.length) return false
  return levelOrder[row.original.level] <= Math.max(...targetDepths)
}

const hierarchyDateRangeFilter: FilterFn<TaskAnalysisRow> = (
  row,
  columnId,
  filterValue,
) => {
  if (row.original.level === 'task') return true
  return dateRangeFilter(row, columnId, filterValue, () => undefined)
}

function countCell(value: number): ReturnType<typeof h> {
  return h('span', { class: value === 0 ? 'zero-count' : 'count-value' }, value)
}

function percentCell(value: number | null): ReturnType<typeof h> {
  return h(
    'span',
    { class: value == null ? 'zero-count' : 'rate-value' },
    value == null ? '—' : `${value.toFixed(1)}%`,
  )
}

function detailCell(
  row: TaskAnalysisRow,
  value: number | null,
  metricId: TaskMetricDetailSelection['metricId'],
  metricLabel: string,
): ReturnType<typeof h> {
  return h(
    'button',
    {
      class: 'metric-detail-button',
      type: 'button',
      'aria-label': `查看 ${row.objectLabel} ${metricLabel}详情`,
      onClick: () => emit('openMetricDetail', { row, metricId }),
    },
    value == null ? '—' : `${value.toFixed(1)}%`,
  )
}

function label(identifier: string, fallback: string): string {
  return (
    props.catalog?.dimensions.find((item) => item.id === identifier)?.label ??
    props.catalog?.metrics.find((item) => item.id === identifier)?.label ??
    fallback
  )
}

function dynamicColumnId(reference: AnalysisMetricReference): string {
  return `option:${metricReferenceKey(reference)}`
}

function dynamicColumnLabel(reference: AnalysisMetricReference): string {
  const option =
    reference.parameters?.questionOption ??
    reference.parameters?.question_option ??
    '问题选项'
  const metricLabel = label(reference.id, reference.id)
  return `${option} · ${metricLabel.replace('问题选项', '')}`
}

function dynamicColumn(
  reference: AnalysisMetricReference,
): ColumnDef<TaskAnalysisRow, unknown> {
  const key = metricReferenceKey(reference)
  const metric = props.catalog?.metrics.find((item) => item.id === reference.id)
  return columnHelper.accessor(
    (row) => row.dynamicMeasures[key] ?? null,
    {
      id: dynamicColumnId(reference),
      header: dynamicColumnLabel(reference),
      size: 156,
      sortDescFirst: true,
      sortUndefined: 'last',
      filterFn: numberRangeFilter,
      meta: { filter: { type: 'number-range' } },
      cell: (context) => metric?.unit === 'percent'
        ? percentCell(context.getValue() as number | null)
        : countCell((context.getValue() as number | null) ?? 0),
    },
  )
}

const projectOptions = computed(() =>
  [...new Set(props.rows.map((row) => row.project))].sort(),
)

const taskOptions = computed(() =>
  [...new Set(props.rows.map((row) => row.task))].sort(),
)

const columns = computed<ColumnDef<TaskAnalysisRow, unknown>[]>(() => [
  columnHelper.group({
    id: 'task-identity',
    header: '任务与下钻路径',
    columns: [
      columnHelper.accessor('objectLabel', {
        id: 'object_label',
        header: '标注任务 / 下钻对象',
        size: 230,
        filterFn: taskBranchFilter,
        meta: {
          filter: {
            type: 'text-select',
            options: taskOptions.value,
          },
        },
      }),
      columnHelper.accessor('objectType', {
        id: 'object_type',
        header: '对象类型',
        size: 88,
        filterFn: hierarchyLevelFilter,
        meta: {
          filter: {
            type: 'text-select',
            options: [...levelLabels],
          },
        },
      }),
      columnHelper.accessor('project', {
        id: 'project',
        header: label('project', '项目'),
        size: 128,
        filterFn: textSelectionFilter,
        meta: { filter: { type: 'text-select', options: projectOptions.value } },
      }),
      columnHelper.accessor('statDate', {
        id: 'stat_date',
        header: '统计日期',
        size: 122,
        filterFn: hierarchyDateRangeFilter,
        meta: { filter: { type: 'date-range' } },
        cell: (context) => context.getValue() || props.periodLabel,
      }),
    ],
  }),
  columnHelper.group({
    id: 'annotation',
    header: '标注情况',
    columns: [
      columnHelper.accessor('annotationSubmitted', {
        id: 'annotation_submitted',
        header: label('annotation.submitted', '标注提交'),
        size: 112,
        sortDescFirst: true,
        filterFn: numberRangeFilter,
        meta: { filter: { type: 'number-range' } },
        cell: (context) => countCell(context.getValue()),
      }),
      columnHelper.accessor('goodRate', {
        id: 'good_rate',
        header: label('annotation.good_rate', 'Good 占比'),
        size: 112,
        sortDescFirst: true,
        sortUndefined: 'last',
        filterFn: numberRangeFilter,
        meta: { filter: { type: 'number-range' } },
        cell: (context) => detailCell(
          context.row.original,
          context.getValue(),
          'annotation.good_rate',
          'Good 占比',
        ),
      }),
    ],
  }),
  columnHelper.group({
    id: 'acceptance-progress',
    header: '验收进度',
    columns: [
      columnHelper.accessor('acceptanceAllocated', {
        id: 'acceptance_allocated',
        header: label('acceptance.allocated', '验收分配'),
        size: 112,
        sortDescFirst: true,
        filterFn: numberRangeFilter,
        meta: { filter: { type: 'number-range' } },
        cell: (context) => countCell(context.getValue()),
      }),
      columnHelper.accessor('allocationCoverageRate', {
        id: 'allocation_coverage_rate',
        header: label('acceptance.allocation_coverage_rate', '分配覆盖率'),
        size: 120,
        sortDescFirst: true,
        sortUndefined: 'last',
        filterFn: numberRangeFilter,
        meta: { filter: { type: 'number-range' } },
        cell: (context) => percentCell(context.getValue()),
      }),
      columnHelper.accessor('acceptanceCompleted', {
        id: 'acceptance_completed',
        header: label('acceptance.completed', '验收完成'),
        size: 112,
        sortDescFirst: true,
        filterFn: numberRangeFilter,
        meta: { filter: { type: 'number-range' } },
        cell: (context) => countCell(context.getValue()),
      }),
      columnHelper.accessor('completionRate', {
        id: 'completion_rate',
        header: label('acceptance.completion_rate', '完成率'),
        size: 104,
        sortDescFirst: true,
        sortUndefined: 'last',
        filterFn: numberRangeFilter,
        meta: { filter: { type: 'number-range' } },
        cell: (context) => detailCell(
          context.row.original,
          context.getValue(),
          'acceptance.completion_rate',
          '验收完成率',
        ),
      }),
    ],
  }),
  columnHelper.group({
    id: 'acceptance-result',
    header: '验收结果',
    columns: [
      columnHelper.accessor('passRate', {
        id: 'pass_rate',
        header: label('acceptance.pass_rate', '通过率'),
        size: 104,
        sortDescFirst: true,
        sortUndefined: 'last',
        filterFn: numberRangeFilter,
        meta: { filter: { type: 'number-range' } },
        cell: (context) => detailCell(
          context.row.original,
          context.getValue(),
          'acceptance.pass_rate',
          '验收通过率',
        ),
      }),
    ],
  }),
  ...(props.pinnedMetrics.length
    ? [
        columnHelper.group({
          id: 'pinned-options',
          header: '固定问题选项',
          columns: props.pinnedMetrics.map(dynamicColumn),
        }),
      ]
    : []),
])
</script>

<template>
  <section class="task-analysis-table" aria-labelledby="task-analysis-title">
    <header class="table-header">
      <div>
        <p class="section-index">任务汇总与下钻</p>
        <h2 id="task-analysis-title">按标注任务定位到日期、组和标注员</h2>
      </div>
      <div class="table-actions">
        <p class="table-summary">
          当前范围内共有 {{ total }} 个任务。展开任务后按日期、组和标注员逐级查看。
        </p>
        <button
          class="save-table-button"
          type="button"
          :disabled="savingConfig || !configDirty"
          @click="emit('saveConfig')"
        >
          {{ savingConfig ? '保存中…' : configDirty ? '保存表格' : '表格已保存' }}
        </button>
      </div>
    </header>

    <div v-if="pinnedMetrics.length" class="pinned-metrics">
      <strong>已固定问题选项列</strong>
      <button
        v-for="reference in pinnedMetrics"
        :key="metricReferenceKey(reference)"
        type="button"
        :aria-label="`移除 ${dynamicColumnLabel(reference)}`"
        @click="emit('removePinnedMetric', reference)"
      >
        {{ dynamicColumnLabel(reference) }} ×
      </button>
    </div>
    <p v-if="configNotice" class="table-notice" role="status">
      {{ configNotice }}
    </p>
    <p v-if="loading" class="table-status" role="status">正在汇总任务数据…</p>

    <DataWorkbench
      :rows="rows"
      :columns="columns"
      :can-expand="(row) => row.hasChildren"
      :load-children="loadChildren"
      :initial-view-state="initialViewState"
      :enable-row-selection="false"
      filter-scope-label="层级筛选保留上级路径；展开后自动筛选新加载明细"
      row-count-label="个标注任务"
      enable-analysis
      empty-text="当前范围没有可汇总的标注任务。"
      @state-change="emit('stateChange', $event)"
      @create-chart="emit('createChart', $event)"
      @apply-filters="emit('applyFilters', $event)"
    />
  </section>
</template>

<style scoped>
.task-analysis-table {
  display: grid;
  min-width: 0;
  gap: 10px;
}

.table-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.section-index,
.table-header h2,
.table-summary,
.table-status,
.table-notice {
  margin: 0;
}

.section-index {
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.table-header h2 {
  margin-top: 4px;
  font-size: 15px;
}

.table-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.table-summary,
.table-status,
.table-notice {
  color: var(--color-muted);
  font-size: 11px;
  line-height: 1.55;
}

.table-summary {
  max-width: 500px;
  text-align: right;
}

.save-table-button,
.pinned-metrics button {
  min-height: 32px;
  padding: 6px 10px;
  border: 1px solid var(--color-line);
  border-radius: 5px;
  background: white;
  color: var(--color-ink);
  cursor: pointer;
}

.save-table-button:disabled {
  cursor: default;
  opacity: 0.55;
}

.pinned-metrics {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #cbd8ee;
  border-radius: 6px;
  background: #f5f8ff;
  font-size: 11px;
}

.pinned-metrics button {
  min-height: 26px;
  padding: 3px 8px;
  color: var(--color-primary);
}

.table-status,
.table-notice {
  padding: 8px 10px;
  border-left: 3px solid var(--color-primary);
  background: var(--color-primary-soft);
}

:deep(.count-value) {
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-weight: 650;
}

:deep(.zero-count) {
  color: #8c98a6;
  font-family: var(--font-mono);
}

:deep(.rate-value) {
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-weight: 700;
}

:deep(.metric-detail-button) {
  padding: 0;
  border: 0;
  border-bottom: 1px dotted currentColor;
  background: transparent;
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-weight: 700;
  cursor: pointer;
}

@media (max-width: 760px) {
  .table-header,
  .table-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .table-summary {
    text-align: left;
  }
}
</style>
