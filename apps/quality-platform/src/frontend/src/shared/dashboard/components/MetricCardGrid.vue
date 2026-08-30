<script setup lang="ts">
import {
  computed,
  markRaw,
  nextTick,
  onMounted,
  provide,
  useTemplateRef,
  watch,
} from 'vue'
import {
  GridStack as GridStackVue,
  type GridStackOptions,
} from 'gridstack/dist/vue'
import type { GridStack as GridStackInstance } from 'gridstack'
import 'gridstack/dist/gridstack.css'
import MetricCardHost from './MetricCardHost.vue'
import { METRIC_DASHBOARD_CONTEXT } from '../metricContext'
import type {
  DashboardCardLayout,
  DashboardMetricCard,
  DashboardMetricResult,
} from '../types'

const props = defineProps<{
  cards: DashboardMetricCard[]
  results: Record<string, DashboardMetricResult>
  loading?: boolean
  saving?: boolean
  dirty?: boolean
  notice?: string
}>()

const emit = defineEmits<{
  add: []
  edit: [card: DashboardMetricCard]
  duplicate: [card: DashboardMetricCard]
  restore: [card: DashboardMetricCard]
  remove: [cardId: string]
  jump: [card: DashboardMetricCard]
  save: []
  layoutChange: [layouts: Record<string, DashboardCardLayout>]
}>()

const gridRef =
  useTemplateRef<{ getGrid: () => GridStackInstance | null }>('metricGrid')
const baseOptions: GridStackOptions = {
  column: 12,
  cellHeight: 58,
  margin: 6,
  float: true,
  animate: true,
  handle: '.metric-drag-handle',
  minRow: 1,
  columnOpts: {
    breakpoints: [
      { w: 720, c: 1 },
      { w: 1120, c: 6 },
    ],
  },
}

function itemOptions(card: DashboardMetricCard) {
  return {
    id: card.id,
    x: card.layout.x,
    y: card.layout.y,
    w: card.layout.w,
    h: card.layout.h,
    minW: card.layout.minW,
    minH: card.layout.minH,
  }
}

const options = computed<GridStackOptions>(() =>
  markRaw({
    ...baseOptions,
    children: props.cards.map((card) => ({
      ...itemOptions(card),
      component: 'MetricCardHost',
      props: { cardId: card.id },
    })),
  }),
)
const components = markRaw({ MetricCardHost })

function currentLayouts(): Record<string, DashboardCardLayout> {
  const nodes = gridRef.value?.getGrid()?.engine.nodes ?? []
  return Object.fromEntries(
    nodes
      .filter((node) => node.id)
      .map((node) => {
        const card = props.cards.find((item) => item.id === String(node.id))
        return [
          String(node.id),
          {
            x: node.x ?? 0,
            y: node.y ?? 0,
            w: node.w ?? 4,
            h: node.h ?? 4,
            minW: card?.layout.minW ?? 3,
            minH: card?.layout.minH ?? 3,
          },
        ]
      }),
  )
}

function handleGridChange(): void {
  emit('layoutChange', currentLayouts())
}

function refreshDragHandles(): void {
  const grid = gridRef.value?.getGrid()
  if (!grid) return
  for (const node of grid.engine.nodes) {
    if (node.el) grid.refreshDragHandles(node.el)
  }
}

async function nudgeCard(
  card: DashboardMetricCard,
  delta: { dx?: number; dy?: number; dw?: number; dh?: number },
): Promise<void> {
  const grid = gridRef.value?.getGrid()
  const node = grid?.engine.nodes.find(
    (candidate) => String(candidate.id) === card.id,
  )
  if (!grid || !node?.el) return
  const w = Math.max(
    card.layout.minW,
    Math.min(12, (node.w ?? 4) + (delta.dw ?? 0)),
  )
  const h = Math.max(
    card.layout.minH,
    (node.h ?? 4) + (delta.dh ?? 0),
  )
  const x = Math.max(
    0,
    Math.min(12 - w, (node.x ?? 0) + (delta.dx ?? 0)),
  )
  const y = Math.max(0, (node.y ?? 0) + (delta.dy ?? 0))
  grid.update(node.el, { x, y, w, h })
  await nextTick()
  handleGridChange()
}

provide(METRIC_DASHBOARD_CONTEXT, {
  cardById: (cardId) => props.cards.find((card) => card.id === cardId),
  resultById: (cardId) => props.results[cardId],
  edit: (card) => emit('edit', card),
  duplicate: (card) => emit('duplicate', card),
  restore: (card) => emit('restore', card),
  remove: (cardId) => emit('remove', cardId),
  jump: (card) => emit('jump', card),
  nudge: (card, value) => void nudgeCard(card, value),
})

watch(
  () => props.cards.map((card) => card.id).join('\u0000'),
  async () => {
    await nextTick()
    const grid = gridRef.value?.getGrid()
    if (!grid) return
    const cardIds = new Set(props.cards.map((card) => card.id))
    const nodeIds = new Set(
      grid.engine.nodes.map((node) => String(node.id ?? '')),
    )
    for (const card of props.cards) {
      if (nodeIds.has(card.id)) continue
      grid.addWidget({
        ...itemOptions(card),
        component: 'MetricCardHost',
        props: { cardId: card.id },
      })
    }
    for (const node of [...grid.engine.nodes]) {
      const id = String(node.id ?? '')
      if (id && !cardIds.has(id) && node.el) grid.removeWidget(node.el)
    }
    await nextTick()
    refreshDragHandles()
  },
  { flush: 'post' },
)

onMounted(async () => {
  await nextTick()
  await nextTick()
  refreshDragHandles()
})
</script>

<template>
  <section class="metric-workspace" aria-labelledby="metric-workspace-title">
    <header class="metric-workspace-header">
      <div>
        <p>业务总览</p>
        <h2 id="metric-workspace-title">选定周期的关键结果</h2>
        <span>指标、说明与项目/任务/组拆分可组合；点击卡片进入对应细分图。</span>
      </div>
      <div class="metric-toolbar">
        <span v-if="dirty" class="dirty-state">有未保存修改</span>
        <button
          class="button"
          type="button"
          :disabled="!dirty || saving"
          @click="emit('save')"
        >
          {{ saving ? '保存中…' : '保存总览' }}
        </button>
        <button class="button primary" type="button" @click="emit('add')">
          ＋ 添加总览卡片
        </button>
      </div>
    </header>

    <p v-if="notice" class="metric-notice" role="status">{{ notice }}</p>

    <div v-if="loading" class="metric-loading" role="status">
      正在恢复已保存总览…
    </div>
    <GridStackVue
      v-else-if="cards.length"
      ref="metricGrid"
      :options="options"
      :components="components"
      @added="refreshDragHandles"
      @change="handleGridChange"
    />
    <div v-else class="metric-loading">还没有总览卡片。</div>
  </section>
</template>

<style scoped>
.metric-workspace {
  display: grid;
  min-width: 0;
  gap: 8px;
}

.metric-workspace-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.metric-workspace-header p,
.metric-workspace-header h2,
.metric-workspace-header span,
.metric-notice {
  margin: 0;
}

.metric-workspace-header p {
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 750;
}

.metric-workspace-header h2 {
  margin-top: 3px;
  font-size: 17px;
}

.metric-workspace-header > div:first-child > span {
  display: block;
  margin-top: 4px;
  color: var(--color-muted);
  font-size: 11px;
}

.metric-toolbar {
  display: flex;
  align-items: center;
  gap: 7px;
}

.dirty-state {
  color: #a66300;
  font-size: 10px;
}

.metric-notice {
  color: var(--color-muted);
  font-size: 10px;
}

.metric-loading {
  display: grid;
  min-height: 130px;
  place-items: center;
  border: 1px dashed #bec8d3;
  border-radius: var(--radius-md);
  color: var(--color-muted);
  font-size: 11px;
}

:deep(.grid-stack) {
  min-height: 230px;
}

:deep(.grid-stack-item-content) {
  overflow: visible;
}

@media (max-width: 760px) {
  .metric-workspace-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-toolbar {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
