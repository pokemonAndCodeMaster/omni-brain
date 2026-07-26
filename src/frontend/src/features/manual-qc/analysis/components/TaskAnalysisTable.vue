<script setup lang="ts">
import { computed, h } from 'vue'
import { createColumnHelper } from '@tanstack/vue-table'
import type { ColumnDef } from '@tanstack/vue-table'
import DataWorkbench from '@/shared/data-workbench/components/DataWorkbench.vue'
import type { WorkbenchAnalysisRequest } from '@/shared/data-workbench/types'
import {
  numberRangeFilter,
  textSelectionFilter,
} from '@/shared/data-workbench/types'
import type { AnalysisCatalog, TaskAnalysisRow } from '../types/analysis'

const props = defineProps<{
  rows: TaskAnalysisRow[]
  loading: boolean
  total: number
  catalog?: AnalysisCatalog | null
}>()

const emit = defineEmits<{
  createChart: [request: WorkbenchAnalysisRequest<TaskAnalysisRow>]
  applyFilters: [request: WorkbenchAnalysisRequest<TaskAnalysisRow>]
}>()

const columnHelper = createColumnHelper<TaskAnalysisRow>()

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

function label(identifier: string, fallback: string): string {
  return (
    props.catalog?.dimensions.find((item) => item.id === identifier)?.label ??
    props.catalog?.metrics.find((item) => item.id === identifier)?.label ??
    fallback
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
    header: '任务信息',
    columns: [
      columnHelper.accessor('task', {
        id: 'task',
        header: label('task', '标注任务'),
        size: 210,
        filterFn: textSelectionFilter,
        meta: { filter: { type: 'text-select', options: taskOptions.value } },
      }),
      columnHelper.accessor('project', {
        id: 'project',
        header: label('project', '项目'),
        size: 128,
        filterFn: textSelectionFilter,
        meta: { filter: { type: 'text-select', options: projectOptions.value } },
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
        cell: (context) => percentCell(context.getValue()),
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
        cell: (context) => percentCell(context.getValue()),
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
        cell: (context) => percentCell(context.getValue()),
      }),
    ],
  }),
])
</script>

<template>
  <section class="task-analysis-table" aria-labelledby="task-analysis-title">
    <header class="table-header">
      <div>
        <p class="section-index">任务汇总</p>
        <h2 id="task-analysis-title">按标注任务比较产出与验收</h2>
      </div>
      <p class="table-summary">
        当前范围内共有 {{ total }} 个任务。先比较任务，再在后续切片展开日期、组和标注员。
      </p>
    </header>
    <p v-if="loading" class="table-status" role="status">正在汇总任务数据…</p>
    <DataWorkbench
      :rows="rows"
      :columns="columns"
      :enable-row-selection="false"
      :show-expand-column="false"
      filter-scope-label="表头筛选默认只影响当前任务比较"
      row-count-label="个标注任务"
      enable-analysis
      empty-text="当前范围没有可汇总的标注任务。"
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
.table-status {
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

.table-summary,
.table-status {
  color: var(--color-muted);
  font-size: 11px;
  line-height: 1.55;
}

.table-summary {
  max-width: 500px;
  text-align: right;
}

.table-status {
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

@media (max-width: 760px) {
  .table-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .table-summary {
    text-align: left;
  }
}
</style>
