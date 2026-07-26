<script setup lang="ts">
import { computed } from 'vue'
import CardShell from './CardShell.vue'
import ChartVisualization from './ChartVisualization.vue'
import type {
  DashboardChartCard,
  DashboardChartResult,
} from '../types'

const props = defineProps<{
  card: DashboardChartCard
  result?: DashboardChartResult
  loading?: boolean
  error?: string
}>()

const emit = defineEmits<{
  remove: []
  edit: []
  duplicate: []
  restore: []
  refresh: []
  drill: [category: string]
  nudge: [value: { dx?: number; dy?: number; dw?: number; dh?: number }]
}>()

const generatedAt = computed(() => {
  const value = props.result?.source.generatedAt
  if (!value) return '尚未生成'
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
})
</script>

<template>
  <CardShell
    :anchor-id="card.id"
    :title="card.title"
    :description="card.description"
    removable
    editable
    @remove="emit('remove')"
    @edit="emit('edit')"
  >
    <template #actions>
      <button
        class="card-action"
        type="button"
        :aria-label="`刷新卡片：${card.title}`"
        title="刷新数据"
        @click="emit('refresh')"
      >
        ↻
      </button>
      <button
        class="card-action"
        type="button"
        :aria-label="`复制卡片：${card.title}`"
        title="复制卡片"
        @click="emit('duplicate')"
      >
        ⧉
      </button>
      <button
        v-if="card.origin.presetId"
        class="card-action"
        type="button"
        :aria-label="`恢复系统预设：${card.title}`"
        title="恢复系统预设"
        @click="emit('restore')"
      >
        ↺
      </button>
      <details class="layout-menu">
        <summary :aria-label="`调整卡片位置和尺寸：${card.title}`" title="调整布局">
          ↔
        </summary>
        <div class="layout-popover">
          <strong>位置</strong>
          <button type="button" @click="emit('nudge', { dx: -1 })">左移</button>
          <button type="button" @click="emit('nudge', { dx: 1 })">右移</button>
          <button type="button" @click="emit('nudge', { dy: -1 })">上移</button>
          <button type="button" @click="emit('nudge', { dy: 1 })">下移</button>
          <strong>尺寸</strong>
          <button type="button" @click="emit('nudge', { dw: 1 })">加宽</button>
          <button type="button" @click="emit('nudge', { dw: -1 })">缩窄</button>
          <button type="button" @click="emit('nudge', { dh: 1 })">增高</button>
          <button type="button" @click="emit('nudge', { dh: -1 })">降低</button>
        </div>
      </details>
    </template>

    <div v-if="loading" class="card-state" role="status">
      正在读取受控分析结果…
    </div>
    <div v-else-if="error" class="card-state is-error" role="alert">
      {{ error }}
    </div>
    <div
      v-else-if="!result?.categories.length"
      class="card-state"
      role="status"
    >
      当前筛选范围没有可绘制数据。
    </div>
    <ChartVisualization
      v-else
      :card="card"
      :result="result"
      @drill="emit('drill', $event)"
    />

    <template #footer>
      <dl class="source-context">
        <div>
          <dt>来源</dt>
          <dd>{{ result?.source.sourceLabel ?? card.baseQuery.sourceId }}</dd>
        </div>
        <div>
          <dt>筛选</dt>
          <dd>{{ result?.source.filterSummary ?? '使用全页范围' }}</dd>
        </div>
        <div>
          <dt>聚合行</dt>
          <dd>{{ result?.source.rowCount ?? 0 }}</dd>
        </div>
        <div>
          <dt>刷新</dt>
          <dd>{{ generatedAt }}</dd>
        </div>
      </dl>
    </template>
  </CardShell>
</template>

<style scoped>
.card-action,
.layout-menu summary {
  display: grid;
  width: 29px;
  height: 29px;
  place-items: center;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  background: white;
  color: var(--color-muted);
  cursor: pointer;
  font-size: 15px;
  list-style: none;
}

.layout-menu {
  position: relative;
}

.layout-menu summary::-webkit-details-marker {
  display: none;
}

.layout-popover {
  position: absolute;
  z-index: 30;
  top: 34px;
  right: 0;
  display: grid;
  width: 176px;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
  padding: 9px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  background: white;
  box-shadow: var(--shadow-md);
}

.layout-popover strong {
  grid-column: 1 / -1;
  color: var(--color-muted);
  font-size: 9px;
}

.layout-popover button {
  min-height: 30px;
  border: 1px solid var(--color-line);
  border-radius: 3px;
  background: var(--color-surface-subtle);
  color: var(--color-ink-secondary);
  font-size: 10px;
}

.card-state {
  display: grid;
  min-height: 180px;
  place-items: center;
  color: var(--color-muted);
  font-size: 11px;
}

.card-state.is-error {
  color: var(--color-danger);
}

.source-context {
  display: grid;
  grid-template-columns: minmax(110px, 1fr) minmax(150px, 2fr) auto auto;
  gap: 8px 14px;
  margin: 0;
}

.source-context div {
  min-width: 0;
}

.source-context dt,
.source-context dd {
  margin: 0;
}

.source-context dt {
  color: var(--color-muted);
  font-size: 9px;
  font-weight: 700;
}

.source-context dd {
  overflow: hidden;
  margin-top: 2px;
  color: var(--color-ink-secondary);
  font-family: var(--font-mono);
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 760px) {
  .source-context {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
