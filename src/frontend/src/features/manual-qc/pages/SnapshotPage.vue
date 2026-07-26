<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import type { WorkbenchAnalysisRequest } from '@/shared/data-workbench/types'
import ChartBuilderDialog from '@/shared/dashboard/components/ChartBuilderDialog.vue'
import DashboardGrid from '@/shared/dashboard/components/DashboardGrid.vue'
import { useDashboardWorkspace } from '@/shared/dashboard/composables/useDashboardWorkspace'
import type {
  ChartBuilderValue,
  DashboardChartCard,
} from '@/shared/dashboard/types'
import SnapshotDataTable from '../components/SnapshotDataTable.vue'
import SnapshotFilters from '../components/SnapshotFilters.vue'
import SnapshotSummaryChart from '../components/SnapshotSummaryChart.vue'
import { useSnapshotExplorer } from '../composables/useSnapshotExplorer'
import type { AggregateNode } from '../types/snapshot'
import {
  buildSnapshotChartCard,
  chartBuilderValueFromCard,
  createSnapshotChartBuilderOptions,
  resolveSnapshotChartCard,
} from '../utils/snapshotChart'

const {
  query,
  loading,
  error,
  notice,
  sceneRows,
  tree,
  loadingKeys,
  computedAt,
  sceneOptions,
  projectOptions,
  filtersSummary,
  load,
  expand,
  resetAndLoad,
} = useSnapshotExplorer()

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

function addTableChart(
  request: WorkbenchAnalysisRequest<AggregateNode>,
): void {
  const filterSummary = [
    filtersSummary.value,
    request.filterSummary,
  ].filter(Boolean).join('；')
  const filters = { ...pageFilterSnapshot.value }
  for (const item of request.filters) {
    const value = String(item.value ?? '')
    if (!value) continue
    if (item.id === 'stat_date') {
      const [start = '', end = ''] = value.split('\u0000')
      if (start) filters.stat_date_start = start
      if (end) filters.stat_date_end = end
    } else if (
      ['project_name', 'scene_name', 'group_name', 'employee_id'].includes(
        item.id,
      ) &&
      !value.includes('\u0000')
    ) {
      filters[item.id] = value
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
    }),
  )
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
  await load()
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
  await load()
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
          通过或打回多少；图表可点击下钻，明细可逐级展开到组和员工。
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
      @submit="load"
      @reset="resetAndLoad"
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

    <SnapshotSummaryChart
      :rows="sceneRows"
      :filters-summary="filtersSummary"
      @drill-task="drillToDetail('scene_name', $event)"
      @drill-project="drillToDetail('project_name', $event)"
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

    <SnapshotDataTable
      id="snapshot-detail"
      :rows="tree"
      :loading-keys="loadingKeys"
      :scene-options="sceneOptions"
      :load-children="expand"
      @create-chart="addTableChart"
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
