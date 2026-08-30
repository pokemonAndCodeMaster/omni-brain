<script setup lang="ts">
import { computed } from 'vue'
import type {
  DashboardMetricCard,
  DashboardMetricResult,
  DashboardMetricValueBlock,
} from '../types'

const props = defineProps<{
  card: DashboardMetricCard
  result?: DashboardMetricResult
}>()

const emit = defineEmits<{
  edit: []
  duplicate: []
  restore: []
  remove: []
  jump: []
  nudge: [value: { dx?: number; dy?: number; dw?: number; dh?: number }]
}>()

const cardStyle = computed(() => ({
  '--metric-accent': props.card.style.accentColor,
  '--metric-background': props.card.style.backgroundColor,
  '--metric-text': props.card.style.textColor,
  '--metric-title-size': `${props.card.style.titleSize}px`,
}))

function metricBlockStyle(block: DashboardMetricValueBlock) {
  return {
    '--block-value-size': `${block.style.valueSize}px`,
    '--block-value-color': block.style.valueColor,
    '--block-label-size': `${block.style.labelSize}px`,
    '--block-label-color': block.style.labelColor,
  }
}
</script>

<template>
  <article
    class="metric-card"
    :class="`density-${card.style.density}`"
    :style="cardStyle"
  >
    <header class="metric-header">
      <span
        class="metric-drag-handle"
        role="button"
        tabindex="0"
        :aria-label="`拖动总览卡片：${card.title}`"
        title="按住拖动卡片"
      >
        ⠿
      </span>
      <div class="metric-copy">
        <h3>{{ card.title }}</h3>
        <p>{{ card.description }}</p>
      </div>
      <div class="metric-actions">
        <details class="layout-menu">
          <summary :aria-label="`调整${card.title}的位置和尺寸`">↔</summary>
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
        <button type="button" aria-label="编辑总览卡片" @click="emit('edit')">
          ✎
        </button>
        <button type="button" aria-label="复制总览卡片" @click="emit('duplicate')">
          ⧉
        </button>
        <button
          v-if="card.origin.presetId"
          type="button"
          aria-label="恢复系统默认总览"
          @click="emit('restore')"
        >
          ↺
        </button>
        <button type="button" aria-label="删除总览卡片" @click="emit('remove')">
          ×
        </button>
      </div>
    </header>

    <button
      class="metric-body"
      type="button"
      :disabled="!card.action"
      @click="emit('jump')"
    >
      <span class="block-grid">
        <template v-for="block in card.blocks" :key="block.id">
          <span
            v-if="block.kind === 'metric-value'"
            class="content-block metric-value-block"
            :class="[
              `width-${block.width}`,
              { primary: block.emphasis === 'primary' },
            ]"
            :style="metricBlockStyle(block)"
          >
            <small>{{ block.label }}</small>
            <strong>
              {{ result?.values[block.id]?.formattedValue ?? '—' }}
            </strong>
          </span>

          <span
            v-else-if="block.kind === 'text'"
            class="content-block text-block"
            :class="`width-${block.width}`"
            :style="{ fontSize: `${block.style.fontSize}px`, color: block.style.color }"
          >
            {{ block.content }}
          </span>

          <span
            v-else
            class="content-block breakdown-block"
            :class="`width-${block.width}`"
          >
            <span
              v-for="item in result?.breakdowns[block.id] ?? []"
              :key="item.label"
              class="breakdown-item"
            >
              <strong>{{ item.label }}</strong>
              <span>
                <small v-for="value in item.values" :key="value.metricId">
                  {{ value.label }}
                  <b>{{ value.formattedValue }}</b>
                </small>
              </span>
            </span>
          </span>
        </template>
      </span>
      <span v-if="card.action" class="jump-hint">查看细分统计 →</span>
    </button>
  </article>
</template>

<style scoped>
.metric-card {
  --metric-accent: #2458d3;
  --metric-background: #fff;
  --metric-text: #17212b;

  display: grid;
  height: 100%;
  grid-template-rows: auto minmax(0, 1fr);
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--metric-accent) 28%, #d7dde5);
  border-top: 4px solid var(--metric-accent);
  border-radius: var(--radius-md);
  background: var(--metric-background);
  color: var(--metric-text);
  box-shadow: var(--shadow-sm);
}

.metric-header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 8px;
  align-items: start;
  padding: 10px 11px 6px;
}

.metric-drag-handle {
  display: grid;
  width: 24px;
  height: 26px;
  place-items: center;
  color: color-mix(in srgb, var(--metric-text) 48%, transparent);
  cursor: grab;
}

.metric-copy,
.metric-copy h3,
.metric-copy p {
  min-width: 0;
  margin: 0;
}

.metric-copy h3 {
  font-size: var(--metric-title-size);
  line-height: 1.25;
}

.metric-copy p {
  overflow: hidden;
  margin-top: 3px;
  color: color-mix(in srgb, var(--metric-text) 68%, transparent);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-actions {
  display: flex;
  gap: 4px;
}

.metric-actions > button,
.layout-menu summary {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  padding: 0;
  border: 1px solid color-mix(in srgb, var(--metric-accent) 22%, #d7dde5);
  border-radius: 4px;
  background: color-mix(in srgb, var(--metric-background) 88%, white);
  color: var(--metric-text);
  cursor: pointer;
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
  top: 32px;
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
  color: var(--color-ink);
}

.layout-popover strong {
  grid-column: 1 / -1;
  font-size: 9px;
}

.layout-popover button {
  min-height: 30px;
  border: 1px solid var(--color-line);
  border-radius: 3px;
  background: var(--color-surface-subtle);
}

.metric-body {
  display: grid;
  min-width: 0;
  align-content: start;
  gap: 7px;
  padding: 3px 13px 12px;
  overflow: auto;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
}

.metric-body:not(:disabled):hover,
.metric-body:not(:disabled):focus-visible {
  background: color-mix(in srgb, var(--metric-accent) 6%, transparent);
}

.block-grid {
  display: grid;
  min-width: 0;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}

.content-block {
  min-width: 0;
}

.width-full {
  grid-column: span 6;
}

.width-half {
  grid-column: span 3;
}

.width-third {
  grid-column: span 2;
}

.metric-value-block {
  display: grid;
  align-content: start;
  gap: 2px;
}

.metric-value-block small {
  color: var(--block-label-color);
  font-size: var(--block-label-size);
}

.metric-value-block strong {
  overflow: hidden;
  color: var(--block-value-color);
  font-family: var(--font-mono);
  font-size: var(--block-value-size);
  line-height: 1.05;
  text-overflow: ellipsis;
}

.metric-value-block.primary strong {
  color: var(--block-value-color, var(--metric-accent));
}

.text-block {
  line-height: 1.5;
}

.breakdown-block {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
  gap: 6px;
}

.breakdown-item {
  display: grid;
  gap: 4px;
  padding: 7px 8px;
  border: 1px solid color-mix(in srgb, var(--metric-accent) 15%, #d7dde5);
  border-radius: 5px;
  background: color-mix(in srgb, var(--metric-background) 80%, white);
}

.breakdown-item > strong {
  font-size: 10px;
}

.breakdown-item > span {
  display: flex;
  flex-wrap: wrap;
  gap: 3px 8px;
}

.breakdown-item small {
  color: color-mix(in srgb, var(--metric-text) 65%, transparent);
  font-size: 9px;
}

.breakdown-item b {
  color: var(--metric-text);
  font-family: var(--font-mono);
  font-size: 10px;
}

.jump-hint {
  color: var(--metric-accent);
  font-size: 9px;
  font-weight: 700;
}

.density-compact .metric-header {
  padding-block: 6px 3px;
}

.density-compact .metric-body {
  gap: 4px;
  padding-block-end: 7px;
}
</style>
