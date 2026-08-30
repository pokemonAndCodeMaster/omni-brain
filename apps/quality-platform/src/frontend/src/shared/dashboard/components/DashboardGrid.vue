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
import DashboardCardHost from './DashboardCardHost.vue'
import { DASHBOARD_CONTEXT } from '../context'
import type {
  DashboardCardLayout,
  DashboardChartCard,
  DashboardChartResult,
} from '../types'

const props = defineProps<{
  cards: DashboardChartCard[]
  results: Record<string, DashboardChartResult>
  loadingCardIds: Set<string>
  cardErrors: Record<string, string>
  canAdd?: boolean
  loading?: boolean
  saving?: boolean
  dirty?: boolean
  notice?: string
}>()

const emit = defineEmits<{
  add: []
  edit: [card: DashboardChartCard]
  duplicate: [card: DashboardChartCard]
  restore: [card: DashboardChartCard]
  remove: [cardId: string]
  refresh: [card: DashboardChartCard]
  drill: [card: DashboardChartCard, category: string]
  save: []
  layoutChange: [layouts: Record<string, DashboardCardLayout>]
}>()

const gridRef = useTemplateRef<{ getGrid: () => GridStackInstance | null }>('grid')
const baseOptions: GridStackOptions = {
  column: 12,
  cellHeight: 58,
  margin: 6,
  float: true,
  animate: true,
  handle: '.card-drag-handle',
  minRow: 1,
  columnOpts: {
    breakpoints: [
      { w: 720, c: 1 },
      { w: 1120, c: 6 },
    ],
  },
}

const options = computed<GridStackOptions>(() =>
  markRaw({
    ...baseOptions,
    children: props.cards.map((card) => ({
      ...itemOptions(card),
      component: 'DashboardCardHost',
      props: { cardId: card.id },
    })),
  }),
)
const components = markRaw({ DashboardCardHost })

function itemOptions(card: DashboardChartCard) {
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

function currentLayouts(): Record<string, DashboardCardLayout> {
  const nodes = gridRef.value?.getGrid()?.engine.nodes ?? []
  return Object.fromEntries(
    nodes
      .filter((node) => node.id)
      .map((node) => {
        const card = props.cards.find((item) => item.id === String(node.id))
        const minW = card?.layout.minW ?? 3
        const minH = card?.layout.minH ?? 4
        return [
          String(node.id),
          {
            x: node.x ?? 0,
            y: node.y ?? 0,
            w: node.w ?? 6,
            h: node.h ?? 6,
            minW,
            minH,
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
  card: DashboardChartCard,
  delta: { dx?: number; dy?: number; dw?: number; dh?: number },
): Promise<void> {
  const grid = gridRef.value?.getGrid()
  const node = grid?.engine.nodes.find(
    (candidate) => String(candidate.id) === card.id,
  )
  if (!grid || !node?.el) return
  const w = Math.max(card.layout.minW, Math.min(12, (node.w ?? 6) + (delta.dw ?? 0)))
  const h = Math.max(card.layout.minH, (node.h ?? 6) + (delta.dh ?? 0))
  const x = Math.max(0, Math.min(12 - w, (node.x ?? 0) + (delta.dx ?? 0)))
  const y = Math.max(0, (node.y ?? 0) + (delta.dy ?? 0))
  grid.update(node.el, { x, y, w, h })
  await nextTick()
  handleGridChange()
}

provide(DASHBOARD_CONTEXT, {
  cardById: (cardId) => props.cards.find((card) => card.id === cardId),
  resultById: (cardId) => props.results[cardId],
  isLoading: (cardId) => props.loadingCardIds.has(cardId),
  errorById: (cardId) => props.cardErrors[cardId] ?? '',
  edit: (card) => emit('edit', card),
  duplicate: (card) => emit('duplicate', card),
  restore: (card) => emit('restore', card),
  remove: (cardId) => emit('remove', cardId),
  refresh: (card) => emit('refresh', card),
  drill: (card, category) => emit('drill', card, category),
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
        component: 'DashboardCardHost',
        props: { cardId: card.id },
      })
    }
    for (const node of [...grid.engine.nodes]) {
      const id = String(node.id ?? '')
      if (id && !cardIds.has(id) && node.el) {
        grid.removeWidget(node.el)
      }
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
  <section class="dashboard-section" aria-labelledby="dashboard-title">
    <header class="dashboard-header">
      <div>
        <p>个人统计看板</p>
        <h2 id="dashboard-title">可编辑统计卡片</h2>
        <span>
          拖动标题左侧手柄调整位置，拖动卡片边缘调整尺寸；编辑后保存即可跨页面恢复。
        </span>
      </div>
      <div class="dashboard-actions">
        <span v-if="dirty" class="save-state">有未保存修改</span>
        <button
          class="button"
          type="button"
          :disabled="!dirty || saving"
          @click="emit('save')"
        >
          {{ saving ? '保存中…' : '保存看板' }}
        </button>
        <button
          v-if="canAdd"
          class="button primary"
          type="button"
          @click="emit('add')"
        >
          ＋ 添加统计卡片
        </button>
      </div>
    </header>

    <p v-if="notice" class="dashboard-notice" role="status">{{ notice }}</p>

    <div v-if="loading" class="dashboard-empty" role="status">
      <strong>正在恢复已保存看板…</strong>
    </div>
    <GridStackVue
      v-else-if="cards.length"
      ref="grid"
      :options="options"
      :components="components"
      @added="refreshDragHandles"
      @change="handleGridChange"
    />
    <div v-else class="dashboard-empty">
      <strong>还没有统计卡片</strong>
      <span>
        可点击“添加统计卡片”，或在下方表格筛选数据后生成卡片。
      </span>
    </div>
  </section>
</template>

<style scoped>
.dashboard-section {
  display: grid;
  min-width: 0;
  gap: 10px;
}

.dashboard-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.dashboard-header p,
.dashboard-header h2,
.dashboard-header span,
.dashboard-notice {
  margin: 0;
}

.dashboard-header p {
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 750;
}

.dashboard-header h2 {
  margin-top: 4px;
  font-size: 16px;
}

.dashboard-header > div:first-child > span {
  display: block;
  margin-top: 3px;
  color: var(--color-muted);
  font-size: 11px;
}

.dashboard-actions {
  display: flex;
  align-items: center;
  gap: 7px;
}

.save-state {
  color: var(--color-warning);
  font-size: 10px;
}

.dashboard-notice {
  padding: 8px 11px;
  border: 1px solid #c7d3e3;
  border-radius: var(--radius-sm);
  background: #f3f6fb;
  color: #455b74;
  font-size: 11px;
}

.dashboard-empty {
  display: grid;
  min-height: 102px;
  place-content: center;
  gap: 4px;
  padding: 18px;
  border: 1px dashed #b9c5d2;
  border-radius: var(--radius-md);
  background: rgb(255 255 255 / 55%);
  color: var(--color-muted);
  text-align: center;
}

.dashboard-empty strong {
  color: var(--color-ink-secondary);
  font-size: 12px;
}

.dashboard-empty span {
  font-size: 11px;
}

:deep(.gs-wrapper) {
  min-width: 0;
}

:deep(.grid-stack) {
  min-height: 120px;
}

:deep(.grid-stack-item-content) {
  overflow: visible;
}

:deep(.grid-stack-placeholder > .placeholder-content) {
  border: 1px dashed #6f8fdc;
  border-radius: var(--radius-md);
  background: rgb(111 143 220 / 10%);
}

@media (max-width: 760px) {
  .dashboard-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .dashboard-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
