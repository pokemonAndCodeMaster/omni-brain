<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import {
  parseTextSelectionFilter,
  type WorkbenchAnalysisRequest,
} from '@/shared/data-workbench/types'
import ChartBuilderDialog from '@/shared/dashboard/components/ChartBuilderDialog.vue'
import DashboardGrid from '@/shared/dashboard/components/DashboardGrid.vue'
import MetricCardEditor from '@/shared/dashboard/components/MetricCardEditor.vue'
import MetricCardGrid from '@/shared/dashboard/components/MetricCardGrid.vue'
import { useDashboardWorkspace } from '@/shared/dashboard/composables/useDashboardWorkspace'
import { useMetricWorkspace } from '@/shared/dashboard/composables/useMetricWorkspace'
import type {
  ChartBuilderValue,
  DashboardChartCard,
  DashboardMetricCard,
  DashboardMetricResult,
} from '@/shared/dashboard/types'
import SnapshotFilters from '../components/SnapshotFilters.vue'
import SnapshotSummaryChart from '../components/SnapshotSummaryChart.vue'
import TaskAnalysisTable from '../analysis/components/TaskAnalysisTable.vue'
import { useAnalysisCatalog } from '../analysis/composables/useAnalysisCatalog'
import { useTaskAnalysis } from '../analysis/composables/useTaskAnalysis'
import { useSnapshotExplorer } from '../composables/useSnapshotExplorer'
import {
  buildSnapshotChartCard,
  chartBuilderValueFromCard,
  createSnapshotChartBuilderOptions,
  resolveSnapshotChartCard,
} from '../utils/snapshotChart'
import {
  defaultOverviewCards,
  nextOverviewCard,
  resolveOverviewMetric,
} from '../utils/snapshotOverview'

const {
  query,
  loading,
  error,
  notice,
  sceneRows,
  snapshotRows,
  computedAt,
  sceneOptions,
  projectOptions,
  filtersSummary,
  load,
  resetAndLoad,
} = useSnapshotExplorer()

const {
  rows: taskAnalysisRows,
  loading: taskAnalysisLoading,
  error: taskAnalysisError,
  total: taskAnalysisTotal,
  load: loadTaskAnalysis,
} = useTaskAnalysis(query)
const {
  catalog: analysisCatalog,
} = useAnalysisCatalog()

const {
  cards: overviewCards,
  loading: overviewLoading,
  saving: overviewSaving,
  dirty: overviewDirty,
  notice: overviewNotice,
  addCard: addOverviewCard,
  updateCard: updateOverviewCard,
  removeCard: removeOverviewCard,
  updateLayouts: updateOverviewLayouts,
  save: saveOverview,
} = useMetricWorkspace(
  'manual-qc-snapshot-overview',
  defaultOverviewCards,
)

const {
  cards,
  results,
  loadingCardIds,
  cardErrors,
  loading: dashboardLoading,
  saving: dashboardSaving,
  dirty: dashboardDirty,
  notice: dashboardNotice,
  addCard,
  updateCard,
  updateLayouts,
  removeCard,
  refreshCard,
  save: saveDashboard,
} = useDashboardWorkspace(
  'manual-qc-snapshots',
  resolveSnapshotChartCard,
)
const builderOpen = ref(false)
const editingCard = ref<DashboardChartCard | null>(null)
const metricEditorOpen = ref(false)
const editingMetricCard = ref<DashboardMetricCard | null>(null)
const tableScopeNotice = ref('')

const overviewResults = computed<Record<string, DashboardMetricResult>>(() =>
  Object.fromEntries(
    overviewCards.value.map((card) => [
      card.id,
      resolveOverviewMetric(card, snapshotRows.value),
    ]),
  ),
)

const freshness = computed(() => {
  if (!computedAt.value) return '尚无快照结果'
  const parsed = new Date(computedAt.value)
  if (Number.isNaN(parsed.valueOf())) return computedAt.value
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(parsed)
})

const chartBuilderOptions = computed(() =>
  createSnapshotChartBuilderOptions(sceneOptions.value),
)

const pageFilterSnapshot = computed<Record<string, string>>(() =>
  Object.fromEntries(
    Object.entries(query)
      .filter(([, value]) => value != null && value !== '')
      .map(([key, value]) => [key, String(value)]),
  ),
)

const editingValue = computed(() =>
  editingCard.value ? chartBuilderValueFromCard(editingCard.value) : null,
)

function openBuilder(card: DashboardChartCard | null = null): void {
  editingCard.value = card
  builderOpen.value = true
}

function submitCard(value: ChartBuilderValue): void {
  const card = buildSnapshotChartCard(value, editingCard.value)
  if (editingCard.value) {
    updateCard(card)
  } else {
    addCard(card)
  }
  editingCard.value = null
}

function openMetricEditor(card?: DashboardMetricCard): void {
  editingMetricCard.value =
    card ?? nextOverviewCard('annotation_quality')
  metricEditorOpen.value = true
}

function submitMetricCard(card: DashboardMetricCard): void {
  if (overviewCards.value.some((current) => current.id === card.id)) {
    updateOverviewCard(card)
  } else {
    addOverviewCard(card)
  }
  editingMetricCard.value = null
}

function jumpFromMetric(card: DashboardMetricCard): void {
  document
    .querySelector(`#${card.jumpTarget}`)
    ?.scrollIntoView({ behavior: 'auto', block: 'start' })
}

function addTableChart<TData>(
  request: WorkbenchAnalysisRequest<TData>,
): void {
  const transferableFilters = new Set([
    'stat_date',
    'project',
    'task',
    'project_name',
    'scene_name',
  ])
  const nonTransferableFilters = request.filters.filter((item) => {
    if (!transferableFilters.has(item.id)) return true
    if (item.id === 'stat_date') return false
    return exactDimensionFilterValue(item) === null
  })
  if (nonTransferableFilters.length) {
    tableScopeNotice.value =
      `当前表格包含${nonTransferableFilters
        .map((item) => tableFilterDescription(item))
        .join('、')}等聚合条件，不能安全转换为 V1 统计卡片的数据范围。请先用项目或任务收窄全页范围，或等待 V2 图表切片支持同口径查询。`
    return
  }
  const filterSummary = [
    filtersSummary.value,
    request.filterSummary,
  ].filter(Boolean).join('；')
  const filters = { ...pageFilterSnapshot.value }
  for (const item of request.filters) {
    if (item.id === 'stat_date') {
      const value = String(item.value ?? '')
      const [start = '', end = ''] = value.split('\u0000')
      if (start) filters.stat_date_start = start
      if (end) filters.stat_date_end = end
    } else if (
      ['project', 'task', 'project_name', 'scene_name'].includes(item.id)
    ) {
      const value = exactDimensionFilterValue(item)
      if (value === null) continue
      const field = {
        project: 'project_name',
        task: 'scene_name',
        project_name: 'project_name',
        scene_name: 'scene_name',
      }[item.id]
      if (field) filters[field] = value
    }
  }
  addCard(
    buildSnapshotChartCard({
      title: '当前表格筛选的验收完成与打回',
      description: `来自明细表筛选：${filterSummary}`,
      sourceId: chartBuilderOptions.value.defaultSourceId,
      chartType: 'bar',
      dimensionId: 'scene_name',
      measureIds: ['accept_completed', 'accept_rejected'],
      filters,
      stacked: false,
      showLegend: true,
      showLabels: false,
      smooth: true,
      palette: 'quality',
      orientation: 'vertical',
      legendPosition: 'top',
      fontScale: 'medium',
      showArea: false,
      sortDirection: 'natural',
      maxCategories: 20,
    }),
  )
  tableScopeNotice.value =
    '已按当前全页范围和可转换的表头条件新增统计卡片；卡片拥有独立筛选，可继续编辑。'
}

async function applyTableFilters<TData>(
  request: WorkbenchAnalysisRequest<TData>,
): Promise<void> {
  const applied: string[] = []
  const retained: string[] = []

  for (const item of request.filters) {
    if (item.id === 'stat_date') {
      const value = String(item.value ?? '')
      const [start = '', end = ''] = value.split('\u0000')
      query.stat_date_start = start
      query.stat_date_end = end
      applied.push('日期')
      continue
    }
    if (
      ['project', 'task', 'project_name', 'scene_name'].includes(item.id)
    ) {
      const field = {
        project: 'project_name',
        task: 'scene_name',
        project_name: 'project_name',
        scene_name: 'scene_name',
      }[item.id]
      const selected = exactDimensionFilterValue(item)
      if (field && selected !== null) {
        query[field as keyof typeof query] = selected
        if (field === 'project_name') query.scene_name = ''
        applied.push(
          {
            project: '项目',
            task: '标注任务',
            project_name: '项目',
            scene_name: '标注任务',
          }[item.id]!,
        )
      } else {
        retained.push(tableFilterDescription(item))
      }
      continue
    }
    retained.push(
      tableFilterLabel(item.id),
    )
  }

  if (applied.length) {
    await loadPage()
    await nextTick()
    document
      .querySelector('#analysis-title')
      ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  tableScopeNotice.value = applied.length
    ? `已把${[...new Set(applied)].join('、')}应用到全页。${
        retained.length
          ? `${retained.join('、')}仍只影响明细，因为当前页面数据接口不支持这些聚合条件。`
          : '概览、统计图和明细已使用同一范围。'
      }`
    : '当前表头条件无法无损转换为全页数据范围，已保留为明细筛选。'
}

function tableFilterLabel(identifier: string): string {
  return {
    project: '项目',
    task: '标注任务',
    project_name: '项目',
    scene_name: '标注任务',
    group_name: '组',
    employee_id: '员工',
    annotation_submitted: '标注提交范围',
    good_rate: 'Good 占比范围',
    acceptance_allocated: '验收分配范围',
    allocation_coverage_rate: '分配覆盖率范围',
    acceptance_completed: '验收完成范围',
    completion_rate: '完成率范围',
    pass_rate: '通过率范围',
    accept_completion_rate: '完成率范围',
    accept_pass_rate: '通过率范围',
  }[identifier] ?? identifier
}

function tableFilterDescription(filter: { id: string; value: unknown }): string {
  if (filter.id === 'project' || filter.id === 'task') {
    const value = parseTextSelectionFilter(filter.value)
    if (value.query.trim()) {
      return `${tableFilterLabel(filter.id)}包含文字`
    }
    if (value.selected.length > 1) {
      return `${tableFilterLabel(filter.id)}多选`
    }
  }
  if (filter.id !== 'stat_date' && String(filter.value ?? '').includes('\u0000')) {
    return `${tableFilterLabel(filter.id)}多选`
  }
  return tableFilterLabel(filter.id)
}

function exactDimensionFilterValue(
  filter: { id: string; value: unknown },
): string | null {
  if (filter.id === 'project' || filter.id === 'task') {
    const value = parseTextSelectionFilter(filter.value)
    return !value.query.trim() && value.selected.length === 1
      ? value.selected[0]!
      : null
  }
  const value = String(filter.value ?? '')
  return value && !value.includes('\u0000') ? value : null
}

async function loadPage(): Promise<void> {
  await Promise.all([load(), loadTaskAnalysis()])
}

async function resetPage(): Promise<void> {
  await resetAndLoad()
  await loadTaskAnalysis()
}

async function drillToDetail(
  field: 'project_name' | 'scene_name',
  value: string,
): Promise<void> {
  if (field === 'project_name') {
    query.project_name = value
    query.scene_name = ''
  } else {
    query.scene_name = value
  }
  await loadPage()
  await nextTick()
  document
    .querySelector('#snapshot-detail')
    ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function drillFromCard(
  card: DashboardChartCard,
  category: string,
): Promise<void> {
  const dimension = card.query.dimensionId
  if (dimension === 'stat_date') {
    query.stat_date_start = category
    query.stat_date_end = category
  } else if (
    dimension === 'project_name' ||
    dimension === 'scene_name' ||
    dimension === 'group_name' ||
    dimension === 'employee_id'
  ) {
    query[dimension] = category
    if (dimension === 'project_name') query.scene_name = ''
  } else {
    return
  }
  await loadPage()
  await nextTick()
  document
    .querySelector('#snapshot-detail')
    ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function drillToDate(date: string): Promise<void> {
  query.stat_date_start = date
  query.stat_date_end = date
  await loadPage()
  await nextTick()
  document
    .querySelector('#snapshot-detail')
    ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="snapshot-page">
    <section class="page-intro">
      <div>
        <p class="page-kicker">人工质检快照</p>
        <h2>从标注产出看到验收结果</h2>
        <p class="page-summary">
          先看不同项目与标注任务做了多少、结果如何分布，再看验收是否分得够、做得完、
          通过或打回多少；当前明细先按任务汇总，日期、组和标注员下钻将在下一切片接入。
        </p>
      </div>
      <dl class="freshness-card">
        <div>
          <dt>数据口径</dt>
          <dd>JSONB · V20260709</dd>
        </div>
        <div>
          <dt>结果生成时间</dt>
          <dd>{{ freshness }}</dd>
        </div>
      </dl>
    </section>

    <SnapshotFilters
      v-model="query"
      :scene-options="sceneOptions"
      :project-options="projectOptions"
      :loading="loading"
      @submit="loadPage"
      @reset="resetPage"
    />

    <div v-if="error" class="message error-message" role="alert">
      <strong>数据读取失败</strong>
      <span>{{ error }}</span>
    </div>
    <div v-else-if="notice" class="message notice-message" role="status">
      <strong>查询结果</strong>
      <span>{{ notice }}</span>
    </div>

    <div v-if="loading" class="loading-strip" role="status">
      <span></span>
      正在读取本地 PostgreSQL 快照…
    </div>

    <MetricCardGrid
      :cards="overviewCards"
      :results="overviewResults"
      :loading="overviewLoading"
      :saving="overviewSaving"
      :dirty="overviewDirty"
      :notice="overviewNotice"
      @add="openMetricEditor()"
      @edit="openMetricEditor"
      @remove="removeOverviewCard"
      @jump="jumpFromMetric"
      @save="saveOverview"
      @layout-change="updateOverviewLayouts"
    />

    <MetricCardEditor
      :open="metricEditorOpen"
      :card="editingMetricCard"
      @close="metricEditorOpen = false; editingMetricCard = null"
      @submit="submitMetricCard"
    />

    <SnapshotSummaryChart
      :rows="sceneRows"
      :snapshot-rows="snapshotRows"
      :filters-summary="filtersSummary"
      @drill-task="drillToDetail('scene_name', $event)"
      @drill-project="drillToDetail('project_name', $event)"
      @drill-date="drillToDate"
    />

    <DashboardGrid
      :cards="cards"
      :results="results"
      :loading-card-ids="loadingCardIds"
      :card-errors="cardErrors"
      :can-add="sceneRows.length > 0"
      :loading="dashboardLoading"
      :saving="dashboardSaving"
      :dirty="dashboardDirty"
      :notice="dashboardNotice"
      @add="openBuilder()"
      @edit="openBuilder"
      @remove="removeCard"
      @refresh="refreshCard"
      @drill="drillFromCard"
      @save="saveDashboard"
      @layout-change="updateLayouts"
    />

    <ChartBuilderDialog
      :open="builderOpen"
      :options="chartBuilderOptions"
      :initial-value="editingValue"
      :initial-filters="pageFilterSnapshot"
      default-title="人工质检自定义统计"
      @close="builderOpen = false; editingCard = null"
      @submit="submitCard"
    />

    <p v-if="tableScopeNotice" class="table-scope-notice" role="status">
      {{ tableScopeNotice }}
    </p>
    <div v-if="taskAnalysisError" class="message error-message" role="alert">
      <strong>任务汇总读取失败</strong>
      <span>{{ taskAnalysisError }}</span>
    </div>
    <TaskAnalysisTable
      id="snapshot-detail"
      :rows="taskAnalysisRows"
      :loading="taskAnalysisLoading"
      :total="taskAnalysisTotal"
      :catalog="analysisCatalog"
      @create-chart="addTableChart"
      @apply-filters="applyTableFilters"
    />
  </div>
</template>

<style scoped>
.snapshot-page {
  display: grid;
  min-width: 0;
  gap: 18px;
}

.snapshot-page > * {
  min-width: 0;
}

.page-intro {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 30px;
}

.page-kicker,
.page-intro h2,
.page-summary,
.freshness-card,
.freshness-card dt,
.freshness-card dd {
  margin: 0;
}

.page-kicker {
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.page-intro h2 {
  margin-top: 7px;
  font-size: clamp(21px, 2.3vw, 30px);
  letter-spacing: -0.025em;
}

.page-summary {
  max-width: 760px;
  margin-top: 9px;
  color: var(--color-ink-secondary);
  line-height: 1.65;
}

.freshness-card {
  display: grid;
  min-width: 248px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.freshness-card div {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 12px;
  padding: 9px 12px;
}

.freshness-card div + div {
  border-top: 1px solid var(--color-line-subtle);
}

.freshness-card dt {
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 700;
}

.freshness-card dd {
  overflow: hidden;
  font-family: var(--font-mono);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  padding: 10px 13px;
  border: 1px solid;
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.notice-message {
  border-color: #c2d0e2;
  background: #f3f6fb;
  color: #455b74;
}

.error-message {
  border-color: #e9bbc0;
  background: #fff4f5;
  color: var(--color-danger);
}

.loading-strip {
  display: flex;
  gap: 8px;
  align-items: center;
  color: var(--color-primary);
  font-size: 12px;
}

.table-scope-notice {
  margin: -10px 0 0;
  padding: 9px 12px;
  border-left: 3px solid var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-ink-secondary);
  font-size: 11px;
  line-height: 1.55;
}

.loading-strip span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentcolor;
  animation: pulse 0.9s ease-in-out infinite alternate;
}

@keyframes pulse {
  to {
    opacity: 0.25;
    transform: scale(0.75);
  }
}

@media (max-width: 880px) {
  .page-intro {
    align-items: stretch;
    flex-direction: column;
  }

  .freshness-card {
    min-width: 0;
  }
}
</style>
