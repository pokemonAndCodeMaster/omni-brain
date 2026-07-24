<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createColumnHelper } from '@tanstack/vue-table'
import type { ColumnDef } from '@tanstack/vue-table'
import DataWorkbench from '@/shared/data-workbench/components/DataWorkbench.vue'
import AnalysisBuilder from '@/shared/analysis/components/AnalysisBuilder.vue'
import { useWorkbenchViews } from '@/shared/data-workbench/composables/useWorkbenchViews'
import { useDashboardStore } from '@/shared/dashboard/stores/dashboard'
import { getDeliveries, updateDeliveryCell } from '@/features/manual-qc/api/deliveries'
import type {
  DeliveryPriority,
  DeliveryQuery,
  DeliveryRow,
  DeliveryStatus,
  DeliveryUpdate,
} from '@/features/manual-qc/types/delivery'
import type {
  ColumnEditorSpec,
  WorkbenchViewState,
} from '@/shared/data-workbench/types/workbench'
import type { ChartSpec } from '@/shared/analysis/types/chart'

interface WorkbenchExpose {
  exportState: () => WorkbenchViewState
  applyState: (state: WorkbenchViewState) => void
}

const router = useRouter()
const dashboard = useDashboardStore()
const workbenchRef = ref<WorkbenchExpose | null>(null)
const rows = ref<DeliveryRow[]>([])
const loading = ref(true)
const errorMessage = ref('')
const notice = ref('')
const analysisOpen = ref(false)
const selectedRows = ref<DeliveryRow[]>([])
const viewName = ref('')
const selectedViewId = ref('')

const query = ref<DeliveryQuery>({
  keyword: '',
  project: '',
  status: '',
})

const { views, saveView, removeView } = useWorkbenchViews('quality-check.delivery-workbench.views')

const columnHelper = createColumnHelper<DeliveryRow>()
const columns: ColumnDef<DeliveryRow, any>[] = [
  columnHelper.accessor('name', {
    header: '任务 / 日期',
    size: 250,
    minSize: 170,
  }),
  columnHelper.accessor('project', {
    header: '项目',
    size: 90,
  }),
  columnHelper.accessor('scene', {
    header: 'Scene',
    size: 120,
  }),
  columnHelper.accessor('owner', {
    header: '负责人',
    size: 105,
  }),
  columnHelper.accessor('status', {
    header: '状态',
    size: 105,
  }),
  columnHelper.accessor('priority', {
    header: '优先级',
    size: 85,
  }),
  columnHelper.accessor('targetCount', {
    header: '目标量',
    size: 105,
    cell: (info) => info.getValue().toLocaleString('zh-CN'),
  }),
  columnHelper.accessor('completedCount', {
    header: '完成量',
    size: 105,
    cell: (info) => info.getValue().toLocaleString('zh-CN'),
  }),
  columnHelper.accessor(
    (row) => (row.targetCount > 0 ? row.completedCount / row.targetCount : 0),
    {
      id: 'progress',
      header: '完成率',
      size: 100,
      cell: (info) => `${(info.getValue() * 100).toFixed(1)}%`,
    },
  ),
  columnHelper.accessor('goodRate', {
    header: 'Good 比例',
    size: 110,
    cell: (info) => (info.getValue() > 0 ? `${(info.getValue() * 100).toFixed(1)}%` : '—'),
  }),
  columnHelper.accessor('updatedAt', {
    header: '更新时间',
    size: 155,
  }),
]

const editors: Record<string, ColumnEditorSpec<DeliveryRow>> = {
  owner: {
    type: 'select',
    options: ['张晨', '李珊', '王凯', '周宁', '陈曦'],
  },
  status: {
    type: 'select',
    options: ['待对齐', '生产中', '标注中', '验收中', '风险', '已完成'],
  },
  priority: {
    type: 'select',
    options: ['P0', 'P1', 'P2'],
  },
  targetCount: {
    type: 'number',
  },
}

function rowMatches(row: DeliveryRow) {
  const keyword = query.value.keyword.trim().toLowerCase()
  const keywordMatch =
    !keyword ||
    [row.name, row.project, row.scene, row.owner, row.status]
      .join(' ')
      .toLowerCase()
      .includes(keyword)
  const projectMatch = !query.value.project || row.project === query.value.project
  const statusMatch = !query.value.status || row.status === query.value.status
  return keywordMatch && projectMatch && statusMatch
}

function filterTree(source: DeliveryRow[]): DeliveryRow[] {
  return source.flatMap((row) => {
    const children = row.children ? filterTree(row.children) : []
    if (rowMatches(row)) {
      return [{ ...row, children: row.children ? structuredClone(row.children) : undefined }]
    }
    if (children.length > 0) return [{ ...row, children }]
    return []
  })
}

const filteredRows = computed(() => filterTree(rows.value))

function flattenLeaves(source: DeliveryRow[]): DeliveryRow[] {
  return source.flatMap((row) =>
    row.children?.length ? flattenLeaves(row.children) : [row],
  )
}

const analysisRows = computed(() => flattenLeaves(filteredRows.value))

const projects = computed(() => [...new Set(rows.value.map((row) => row.project))].sort())
const statuses = computed(() => [...new Set(rows.value.map((row) => row.status))].sort())

const filtersSummary = computed(() => {
  const parts = [
    query.value.keyword ? `关键词=${query.value.keyword}` : '',
    query.value.project ? `项目=${query.value.project}` : '',
    query.value.status ? `状态=${query.value.status}` : '',
  ].filter(Boolean)
  return parts.length ? parts.join('；') : '全部数据'
})

function updateTree(
  source: DeliveryRow[],
  id: string,
  field: DeliveryUpdate['field'],
  value: string | number,
): DeliveryRow[] {
  return source.map((row) => {
    const updatedChildren = row.children
      ? updateTree(row.children, id, field, value)
      : undefined
    if (row.id !== id) return { ...row, children: updatedChildren }

    const next = { ...row, children: updatedChildren }
    if (field === 'owner') next.owner = String(value)
    if (field === 'status') next.status = String(value) as DeliveryStatus
    if (field === 'priority') next.priority = String(value) as DeliveryPriority
    if (field === 'targetCount') next.targetCount = Number(value)
    next.updatedAt = new Date().toLocaleString('zh-CN', { hour12: false })
    return next
  })
}

async function handleCellEdit(payload: {
  row: DeliveryRow
  columnId: string
  value: string | number
}) {
  const field = payload.columnId as DeliveryUpdate['field']
  try {
    await updateDeliveryCell({ id: payload.row.id, field, value: payload.value })
    rows.value = updateTree(rows.value, payload.row.id, field, payload.value)
    notice.value = `已更新 ${payload.row.name} 的 ${payload.columnId}`
  } catch (error) {
    console.error(error)
    notice.value = '保存失败，请检查后端连接或浏览器控制台。'
  }
}

function saveCurrentView() {
  if (!workbenchRef.value) return
  try {
    const saved = saveView(viewName.value, workbenchRef.value.exportState(), {
      keyword: query.value.keyword,
      project: query.value.project,
      status: query.value.status,
    })
    selectedViewId.value = saved.id
    viewName.value = ''
    notice.value = `视图“${saved.name}”已保存到本地浏览器。`
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '保存视图失败'
  }
}

function applySelectedView() {
  const view = views.value.find((item) => item.id === selectedViewId.value)
  if (!view || !workbenchRef.value) return
  workbenchRef.value.applyState(view.state)
  query.value = {
    keyword: view.context?.keyword ?? '',
    project: view.context?.project ?? '',
    status: view.context?.status ?? '',
  }
  notice.value = `已加载视图“${view.name}”。`
}

function deleteSelectedView() {
  if (!selectedViewId.value) return
  removeView(selectedViewId.value)
  selectedViewId.value = ''
  notice.value = '已删除个人视图。'
}

function addChart(chart: ChartSpec) {
  dashboard.addChartCard(chart)
  analysisOpen.value = false
  notice.value = `图表“${chart.title}”已添加到个人看板。`
}

function resetFilters() {
  query.value = { keyword: '', project: '', status: '' }
}

onMounted(async () => {
  loading.value = true
  try {
    rows.value = await getDeliveries()
  } catch (error) {
    console.error(error)
    errorMessage.value = '加载交付数据失败，请检查 API 配置。'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <div class="page-toolbar">
      <div>
        <h2 style="margin: 0">统一数据工作台：第一纵切</h2>
        <p class="help-text" style="margin: 6px 0 0">
          业务页面只提供数据、列定义、编辑规则和动作；排序、展开、选择、列布局和分析由共享组件负责。
        </p>
      </div>
      <div class="toolbar-group">
        <button class="button" type="button" :disabled="selectedRows.length === 0" @click="notice = `已选择 ${selectedRows.length} 行；这里可接入 preview → execute。`">
          批量动作（{{ selectedRows.length }}）
        </button>
        <button class="button primary" type="button" @click="analysisOpen = true">一键统计分析</button>
      </div>
    </div>

    <div class="panel filter-panel">
      <div class="filter-grid">
        <label>
          搜索
          <input v-model="query.keyword" class="field" placeholder="任务、scene、负责人……" />
        </label>
        <label>
          项目
          <select v-model="query.project" class="select-field">
            <option value="">全部项目</option>
            <option v-for="project in projects" :key="project" :value="project">{{ project }}</option>
          </select>
        </label>
        <label>
          状态
          <select v-model="query.status" class="select-field">
            <option value="">全部状态</option>
            <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
          </select>
        </label>
        <div class="filter-actions">
          <button class="button" type="button" @click="resetFilters">重置筛选</button>
        </div>
      </div>

      <div class="view-manager">
        <strong>个人视图</strong>
        <input v-model="viewName" class="field" placeholder="例如：本周 P0 风险" />
        <button class="button" type="button" @click="saveCurrentView">保存当前视图</button>
        <select v-model="selectedViewId" class="select-field">
          <option value="">选择已保存视图</option>
          <option v-for="view in views" :key="view.id" :value="view.id">{{ view.name }}</option>
        </select>
        <button class="button" type="button" :disabled="!selectedViewId" @click="applySelectedView">加载</button>
        <button class="button danger" type="button" :disabled="!selectedViewId" @click="deleteSelectedView">删除</button>
      </div>
    </div>

    <p v-if="notice" class="inline-notice">{{ notice }}</p>
    <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
    <div v-if="loading" class="panel loading-panel">正在加载 Mock 数据……</div>

    <DataWorkbench
      v-else
      ref="workbenchRef"
      :rows="filteredRows"
      :columns="columns"
      :editors="editors"
      @cell-edit="handleCellEdit"
      @selection-change="selectedRows = $event"
    />

    <div class="after-table-actions">
      <span class="help-text">当前分析范围：{{ filtersSummary }}；共 {{ analysisRows.length }} 条叶子数据。</span>
      <button class="button" type="button" @click="router.push('/dashboard')">打开个人看板</button>
    </div>

    <AnalysisBuilder
      v-if="analysisOpen"
      :rows="analysisRows"
      :filters-summary="filtersSummary"
      @close="analysisOpen = false"
      @add-to-dashboard="addChart"
    />
  </div>
</template>

<style scoped>
.filter-panel {
  margin-bottom: 14px;
  padding: 14px;
}

.filter-grid {
  display: grid;
  grid-template-columns: minmax(240px, 1.5fr) repeat(2, minmax(150px, 0.7fr)) auto;
  gap: 10px;
  align-items: end;
}

.filter-grid label {
  display: grid;
  gap: 5px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.filter-actions {
  display: flex;
  align-items: end;
}

.view-manager {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.inline-notice,
.inline-error,
.loading-panel {
  margin: 0 0 12px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
}

.inline-notice {
  background: #edf8f3;
  color: var(--color-success);
}

.inline-error {
  background: #fff0f0;
  color: var(--color-danger);
}

.loading-panel {
  color: var(--color-text-muted);
}

.after-table-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
}

@media (max-width: 900px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }

  .after-table-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
