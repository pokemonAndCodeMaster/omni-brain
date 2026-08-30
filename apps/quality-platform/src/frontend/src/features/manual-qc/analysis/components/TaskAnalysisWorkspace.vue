<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import type {
  WorkbenchAnalysisRequest,
  WorkbenchViewState,
} from '@/shared/data-workbench/types'
import type { SnapshotQuery } from '../../types/snapshot'
import { useTaskAnalysisTree } from '../composables/useTaskAnalysisTree'
import { useTaskMetricDetail } from '../composables/useTaskMetricDetail'
import { useTaskTableWorkspace } from '../composables/useTaskTableWorkspace'
import { metricReferenceKey } from '../utils'
import type {
  AnalysisCatalog,
  AnalysisMetricReference,
  TaskAnalysisRow,
  TaskMetricDetailSelection,
} from '../types/analysis'
import TaskAnalysisTable from './TaskAnalysisTable.vue'
import TaskMetricDetailDrawer from './TaskMetricDetailDrawer.vue'

const props = defineProps<{
  pageQuery: SnapshotQuery
  catalog?: AnalysisCatalog | null
}>()

const emit = defineEmits<{
  createChart: [request: WorkbenchAnalysisRequest<TaskAnalysisRow>]
  applyFilters: [request: WorkbenchAnalysisRequest<TaskAnalysisRow>]
}>()

const selection = ref<TaskMetricDetailSelection | null>(null)
const configReady = ref(false)
const acceptViewStateChanges = ref(false)
const localNotice = ref('')

const tree = useTaskAnalysisTree(props.pageQuery)
const tableWorkspace = useTaskTableWorkspace()
const metricDetail = useTaskMetricDetail(selection, props.pageQuery)

const periodLabel = computed(() => {
  const start = props.pageQuery.stat_date_start
  const end = props.pageQuery.stat_date_end
  if (start && end) return start === end ? start : `${start} 至 ${end}`
  if (start) return `${start} 起`
  if (end) return `${end} 止`
  return '当前周期'
})

const initialViewState = computed<WorkbenchViewState | null>(() => {
  if (!configReady.value) return null
  const columns = tableWorkspace.config.value.columns
  return {
    sorting: [],
    expanded: {},
    columnFilters: [],
    columnVisibility: columns.visibility,
    columnOrder: columns.order,
    columnSizing: columns.sizing,
  }
})

const notice = computed(() =>
  [
    tree.error.value,
    tableWorkspace.notice.value,
    localNotice.value,
  ].filter(Boolean).join(' '),
)

function captureViewState(state: WorkbenchViewState): void {
  if (acceptViewStateChanges.value) {
    tableWorkspace.captureViewState(state)
  }
}

async function updatePinnedMetrics(
  references: AnalysisMetricReference[],
): Promise<void> {
  tableWorkspace.setPinnedMetrics(references)
  await tree.setPinnedMetrics(references)
}

async function pinMetric(reference: AnalysisMetricReference): Promise<void> {
  const current = tableWorkspace.config.value.pinnedMetrics
  const key = metricReferenceKey(reference)
  if (current.some((item) => metricReferenceKey(item) === key)) {
    localNotice.value = '这个问题选项已经固定在任务表中。'
    return
  }
  if (current.length >= 5) {
    localNotice.value = '任务表最多固定 5 个问题选项，请先移除一个已有列。'
    return
  }
  localNotice.value = '已固定为任务表新列；保存表格后刷新页面仍会恢复。'
  await updatePinnedMetrics([...current, reference])
}

async function removePinnedMetric(
  reference: AnalysisMetricReference,
): Promise<void> {
  const key = metricReferenceKey(reference)
  const next = tableWorkspace.config.value.pinnedMetrics.filter(
    (item) => metricReferenceKey(item) !== key,
  )
  localNotice.value = '已从任务表移除该问题选项列。'
  await updatePinnedMetrics(next)
}

onMounted(async () => {
  await tableWorkspace.load()
  await tree.setPinnedMetrics(tableWorkspace.config.value.pinnedMetrics)
  configReady.value = true
  await nextTick()
  await nextTick()
  acceptViewStateChanges.value = true
})
</script>

<template>
  <div id="snapshot-detail" class="task-analysis-workspace">
    <TaskAnalysisTable
      :rows="tree.rows.value"
      :loading="tree.loading.value"
      :total="tree.total.value"
      :period-label="periodLabel"
      :pinned-metrics="tableWorkspace.config.value.pinnedMetrics"
      :initial-view-state="initialViewState"
      :saving-config="tableWorkspace.saving.value"
      :config-dirty="tableWorkspace.dirty.value"
      :config-notice="notice"
      :catalog="catalog"
      :load-children="tree.loadChildren"
      @create-chart="emit('createChart', $event)"
      @apply-filters="emit('applyFilters', $event)"
      @open-metric-detail="selection = $event"
      @state-change="captureViewState"
      @save-config="tableWorkspace.save"
      @remove-pinned-metric="removePinnedMetric"
    />

    <TaskMetricDetailDrawer
      :selection="selection"
      :detail="metricDetail.detail.value"
      :loading="metricDetail.loading.value"
      :error="metricDetail.error.value"
      @close="selection = null"
      @pin-metric="pinMetric"
    />
  </div>
</template>

<style scoped>
.task-analysis-workspace {
  min-width: 0;
}
</style>
