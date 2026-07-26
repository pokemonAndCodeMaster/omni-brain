<script setup lang="ts">
import { computed, h } from 'vue'
import { createColumnHelper } from '@tanstack/vue-table'
import type { ColumnDef } from '@tanstack/vue-table'
import DataWorkbench from '@/shared/data-workbench/components/DataWorkbench.vue'
import {
  dateRangeFilter,
  multiSelectFilter,
} from '@/shared/data-workbench/types'
import type { AggregateNode } from '../types/snapshot'

const props = defineProps<{
  rows: AggregateNode[]
  loadingKeys: Set<string>
  sceneOptions: string[]
  loadChildren: (node: AggregateNode) => Promise<boolean>
}>()

const columnHelper = createColumnHelper<AggregateNode>()

function countCell(value: number) {
  return h('span', { class: value === 0 ? 'zero-count' : 'count-value' }, value)
}

function statusCell(node: AggregateNode) {
  if (props.loadingKeys.has(node.id)) {
    return h('span', { class: 'load-status is-loading' }, '读取中')
  }
  if (node.level === 'employee') {
    return h('span', { class: 'load-status is-leaf' }, '员工')
  }
  return h('span', { class: 'load-status' }, node.level === 'scene' ? '场景' : '组')
}

const columns = computed<ColumnDef<AggregateNode, unknown>[]>(() => [
  columnHelper.accessor('stat_date', {
    id: 'stat_date',
    header: '快照日期',
    size: 116,
    filterFn: dateRangeFilter,
    meta: { filter: { type: 'date-range' } },
  }),
  columnHelper.accessor('scene_name', {
    id: 'scene_name',
    header: '场景',
    size: 148,
    filterFn: multiSelectFilter,
    meta: {
      filter: {
        type: 'select',
        options: props.sceneOptions,
      },
    },
  }),
  columnHelper.accessor('group_name', {
    id: 'group_name',
    header: '组别',
    size: 142,
    cell: (context) => context.getValue() || '—',
    meta: { filter: { type: 'text' } },
  }),
  columnHelper.accessor('employee_id', {
    id: 'employee_id',
    header: '员工',
    size: 128,
    cell: (context) => context.getValue() || '—',
    meta: { filter: { type: 'text' } },
  }),
  columnHelper.display({
    id: 'node_status',
    header: '数据层级',
    size: 88,
    cell: (context) => statusCell(context.row.original),
    enableSorting: false,
  }),
  columnHelper.accessor('annotation_submitted', {
    id: 'annotation_submitted',
    header: '标注提交',
    size: 105,
    cell: (context) => countCell(context.getValue()),
  }),
  columnHelper.accessor((row) => row.good_metrics.annotation_submitted, {
    id: 'good_annotation_submitted',
    header: 'Good 提交',
    size: 105,
    cell: (context) => countCell(context.getValue()),
  }),
  columnHelper.accessor((row) => row.bad_metrics.annotation_submitted, {
    id: 'bad_annotation_submitted',
    header: 'Bad 提交',
    size: 105,
    cell: (context) => countCell(context.getValue()),
  }),
  columnHelper.accessor(
    (row) => row.good_metrics.actual_alloc + row.bad_metrics.actual_alloc,
    {
    id: 'total_accept_assigned',
    header: '验收分配',
    size: 105,
    cell: (context) => countCell(context.getValue()),
    },
  ),
  columnHelper.accessor(
    (row) => row.good_metrics.actual_complete + row.bad_metrics.actual_complete,
    {
    id: 'total_accept_completed',
    header: '验收完成',
    size: 105,
    cell: (context) => countCell(context.getValue()),
    },
  ),
  columnHelper.accessor(
    (row) => row.good_metrics.actual_pass + row.bad_metrics.actual_pass,
    {
    id: 'total_accept_passed',
    header: '验收通过',
    size: 105,
    cell: (context) => countCell(context.getValue()),
    },
  ),
  columnHelper.accessor(
    (row) => row.good_metrics.actual_reject + row.bad_metrics.actual_reject,
    {
    id: 'total_accept_rejected',
    header: '验收打回',
    size: 105,
    cell: (context) => countCell(context.getValue()),
    },
  ),
  columnHelper.accessor((row) => row.good_metrics.actual_complete, {
    id: 'good_accept_completed',
    header: 'Good 完成',
    size: 108,
    cell: (context) => countCell(context.getValue()),
  }),
  columnHelper.accessor((row) => row.good_metrics.actual_pass, {
    id: 'good_accept_passed',
    header: 'Good 通过',
    size: 108,
    cell: (context) => countCell(context.getValue()),
  }),
  columnHelper.accessor((row) => row.good_metrics.actual_reject, {
    id: 'good_accept_rejected',
    header: 'Good 打回',
    size: 108,
    cell: (context) => countCell(context.getValue()),
  }),
  columnHelper.accessor((row) => row.bad_metrics.actual_complete, {
    id: 'bad_accept_completed',
    header: 'Bad 完成',
    size: 108,
    cell: (context) => countCell(context.getValue()),
  }),
  columnHelper.accessor((row) => row.bad_metrics.actual_pass, {
    id: 'bad_accept_passed',
    header: 'Bad 通过',
    size: 108,
    cell: (context) => countCell(context.getValue()),
  }),
  columnHelper.accessor((row) => row.bad_metrics.actual_reject, {
    id: 'bad_accept_rejected',
    header: 'Bad 打回',
    size: 108,
    cell: (context) => countCell(context.getValue()),
  }),
])
</script>

<template>
  <section class="snapshot-table-section">
    <header class="table-section-header">
      <div>
        <p class="section-index">02 · SNAPSHOT DRILL-DOWN</p>
        <h2>验收快照明细</h2>
      </div>
      <p>
        数据按“日期—场景—组—员工”逐级展开；表头支持排序、筛选、调列和调宽。
      </p>
    </header>
    <DataWorkbench
      :rows="rows"
      :columns="columns"
      :can-expand="(row) => row.hasChildren"
      :load-children="loadChildren"
      empty-text="当前筛选没有验收快照。"
    />
  </section>
</template>

<style scoped>
.snapshot-table-section {
  display: grid;
  min-width: 0;
  gap: 10px;
}

.table-section-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.section-index,
.table-section-header h2,
.table-section-header p {
  margin: 0;
}

.section-index {
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.table-section-header h2 {
  margin-top: 4px;
  font-size: 15px;
}

.table-section-header > p {
  max-width: 520px;
  color: var(--color-muted);
  font-size: 11px;
  text-align: right;
}

:deep(.count-value) {
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-weight: 650;
}

:deep(.zero-count) {
  color: #b0bac5;
  font-family: var(--font-mono);
}

:deep(.load-status) {
  display: inline-flex;
  padding: 2px 5px;
  border: 1px solid #cbd5df;
  border-radius: 3px;
  color: var(--color-muted);
  font-size: 10px;
}

:deep(.load-status.is-loading) {
  border-color: #b7c9f6;
  background: #edf2ff;
  color: var(--color-primary);
}

:deep(.load-status.is-leaf) {
  border-color: #badccc;
  background: #edf8f3;
  color: var(--color-success);
}

@media (max-width: 760px) {
  .table-section-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .table-section-header > p {
    text-align: left;
  }
}
</style>
