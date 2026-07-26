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
  DashboardChartCard,
  DashboardChartFilter,
  DashboardMetricCard,
  DashboardMetricResult,
} from '@/shared/dashboard/types'
import SnapshotFilters from '../components/SnapshotFilters.vue'
import TaskAnalysisWorkspace from '../analysis/components/TaskAnalysisWorkspace.vue'
import { useAnalysisCatalog } from '../analysis/composables/useAnalysisCatalog'
import { useSnapshotExplorer } from '../composables/useSnapshotExplorer'
import {
  createSnapshotChartBuilderOptions,
  defaultSnapshotChartCards,
  duplicateSnapshotChartCard,
  nextSnapshotChartCard,
  normalizeSnapshotChartCard,
  resolveSnapshotChartCard,
  restoreSnapshotChartPreset,
} from '../utils/snapshotChart'
import {
  defaultOverviewCards,
  duplicateOverviewCard,
  nextOverviewCard,
  normalizeOverviewCard,
  resolveOverviewMetric,
  restoreOverviewPreset,
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
  normalizeOverviewCard,
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
  refreshAll,
  save: saveDashboard,
} = useDashboardWorkspace(
  'manual-qc-snapshots',
  (card) => resolveSnapshotChartCard(card, query),
  defaultSnapshotChartCards,
  normalizeSnapshotChartCard,
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
      resolveOverviewMetric(
        card,
        snapshotRows.value,
        analysisCatalog.value?.metrics ?? [],
      ),
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
  createSnapshotChartBuilderOptions(
    analysisCatalog.value,
    snapshotRows.value,
  ),
)

function openBuilder(card: DashboardChartCard | null = null): void {
  editingCard.value = card ?? nextSnapshotChartCard()
  builderOpen.value = true
}

function submitCard(card: DashboardChartCard): void {
  if (cards.value.some((current) => current.id === card.id)) {
    updateCard(card)
  } else {
    addCard(card)
  }
  editingCard.value = null
}

function duplicateChartCard(card: DashboardChartCard): void {
  addCard(duplicateSnapshotChartCard(card))
}

function restoreChartCard(card: DashboardChartCard): void {
  const restored = restoreSnapshotChartPreset(card)
  if (restored) updateCard(restored)
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

function duplicateMetricCard(card: DashboardMetricCard): void {
  addOverviewCard(duplicateOverviewCard(card))
}

function restoreMetricCard(card: DashboardMetricCard): void {
  const restored = restoreOverviewPreset(card)
  if (restored) updateOverviewCard(restored)
}

function jumpFromMetric(card: DashboardMetricCard): void {
  if (!card.action) return
  document
    .querySelector(`#${card.action.targetCardId}`)
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
  const filters: DashboardChartFilter[] = []
  for (const item of request.filters) {
    if (item.id === 'stat_date') {
      const value = String(item.value ?? '')
      const [start = '', end = ''] = value.split('\u0000')
      if (start && end) {
        filters.push({
          target: { id: 'date' },
          operator: 'between',
          value: [start, end],
        })
      }
    } else if (
      ['project', 'task', 'project_name', 'scene_name'].includes(item.id)
    ) {
      const value = exactDimensionFilterValue(item)
      if (value === null) continue
      const field = {
        project: 'project',
        task: 'task',
        project_name: 'project',
        scene_name: 'task',
      }[item.id]
      if (field) {
        filters.push({
          target: { id: field },
          operator: 'equals',
          value,
        })
      }
    }
  }
  const card = nextSnapshotChartCard()
  card.title = '当前表格筛选的验收完成与打回'
  card.description = `来自明细表筛选：${filterSummary}`
  card.baseQuery.categoryDimension = 'task'
  card.baseQuery.filters = filters
  card.layers = [
    {
      id: 'completed',
      label: '验收完成量',
      metric: { id: 'acceptance.completed' },
      renderAs: 'bar',
      axisId: 'count-axis',
      splitBy: null,
      filters: [],
      stackGroup: null,
      style: { color: '#268462', smooth: true, showLabels: false },
    },
    {
      id: 'rejected',
      label: '验收打回量',
      metric: { id: 'acceptance.rejected' },
      renderAs: 'bar',
      axisId: 'count-axis',
      splitBy: null,
      filters: [],
      stackGroup: null,
      style: { color: '#d5535d', smooth: true, showLabels: false },
    },
  ]
  addCard(card)
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
  await load()
  await refreshAll()
}

async function resetPage(): Promise<void> {
  await resetAndLoad()
}

async function drillFromCard(
  card: DashboardChartCard,
  category: string,
): Promise<void> {
  const dimension = card.baseQuery.categoryDimension
  if (dimension === 'date') {
    query.stat_date_start = category
    query.stat_date_end = category
  } else if (dimension !== 'question-option') {
    const field = {
      project: 'project_name',
      task: 'scene_name',
      group: 'group_name',
      employee: 'employee_id',
    }[dimension]
    if (!field) return
    query[field as keyof typeof query] = category
    if (dimension === 'project') query.scene_name = ''
  } else {
    return
  }
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
          通过或打回多少；任务明细可继续下钻到日期、组和标注员，并查看 Good / Bad
          及问题选项详情。
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
      @duplicate="duplicateMetricCard"
      @restore="restoreMetricCard"
      @remove="removeOverviewCard"
      @jump="jumpFromMetric"
      @save="saveOverview"
      @layout-change="updateOverviewLayouts"
    />

    <MetricCardEditor
      :open="metricEditorOpen"
      :card="editingMetricCard"
      :metrics="analysisCatalog?.metrics.filter((metric) => !metric.requiresQuestionOption) ?? []"
      @close="metricEditorOpen = false; editingMetricCard = null"
      @submit="submitMetricCard"
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
      @duplicate="duplicateChartCard"
      @restore="restoreChartCard"
      @remove="removeCard"
      @refresh="refreshCard"
      @drill="drillFromCard"
      @save="saveDashboard"
      @layout-change="updateLayouts"
    />

    <ChartBuilderDialog
      :open="builderOpen"
      :card="editingCard"
      :options="chartBuilderOptions"
      :mode="cards.some((card) => card.id === editingCard?.id) ? 'edit' : 'create'"
      :preview-resolver="(card) => resolveSnapshotChartCard(card, query)"
      @close="builderOpen = false; editingCard = null"
      @submit="submitCard"
    />

    <p v-if="tableScopeNotice" class="table-scope-notice" role="status">
      {{ tableScopeNotice }}
    </p>
    <TaskAnalysisWorkspace
      :page-query="query"
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
