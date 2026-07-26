<script setup lang="ts">
import { computed } from 'vue'
import type {
  DashboardMetricCard,
  DashboardMetricResult,
} from '../types'

const props = defineProps<{
  card: DashboardMetricCard
  result?: DashboardMetricResult
}>()

const emit = defineEmits<{
  edit: []
  remove: []
  jump: []
  nudge: [value: { dx?: number; dy?: number; dw?: number; dh?: number }]
}>()

const cardStyle = computed(() => ({
  '--metric-accent': props.card.style.accentColor,
  '--metric-background': props.card.style.backgroundColor,
  '--metric-text': props.card.style.textColor,
  '--metric-title-size': `${props.card.style.titleSize}px`,
  '--metric-value-size': `${props.card.style.valueSize}px`,
}))
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
        <button type="button" aria-label="删除总览卡片" @click="emit('remove')">
          ×
        </button>
      </div>
    </header>

    <button class="metric-body" type="button" @click="emit('jump')">
      <span class="primary-metric">
        <strong>{{ result?.primaryValue ?? 0 }}</strong>
        <small>{{ result?.primaryUnit ?? '' }}</small>
      </span>
      <span class="metric-details">
        <span v-for="item in result?.details ?? []" :key="item.label">
          <small>{{ item.label }}</small>
          <strong>{{ item.value }}</strong>
        </span>
      </span>

      <span
        v-if="card.style.showProjectBreakdown"
        class="project-breakdown"
      >
        <span
          v-for="project in result?.projects ?? []"
          :key="project.projectName"
          class="project-metric"
        >
          <span class="project-title">
            <strong>{{ project.projectName }}</strong>
            <b>{{ project.primaryValue }}</b>
          </span>
          <span class="project-details">
            <small v-for="detail in project.details" :key="detail.label">
              {{ detail.label }} <b>{{ detail.value }}</b>
            </small>
          </span>
        </span>
      </span>
      <span class="jump-hint">查看细分统计 →</span>
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
  gap: 9px;
  padding: 3px 13px 12px;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
}

.metric-body:hover,
.metric-body:focus-visible {
  background: color-mix(in srgb, var(--metric-accent) 6%, transparent);
}

.primary-metric {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.primary-metric strong {
  color: var(--metric-accent);
  font-family: var(--font-mono);
  font-size: var(--metric-value-size);
  line-height: 1;
}

.primary-metric small {
  color: color-mix(in srgb, var(--metric-text) 68%, transparent);
  font-size: 10px;
}

.metric-details {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
}

.metric-details > span {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.metric-details small,
.project-details small {
  color: color-mix(in srgb, var(--metric-text) 65%, transparent);
  font-size: 9px;
}

.metric-details strong,
.project-details b {
  color: var(--metric-text);
  font-family: var(--font-mono);
  font-size: 11px;
}

.project-breakdown {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
  gap: 6px;
}

.project-metric {
  display: grid;
  gap: 4px;
  padding: 7px 8px;
  border: 1px solid color-mix(in srgb, var(--metric-accent) 15%, #d7dde5);
  border-radius: 5px;
  background: color-mix(in srgb, var(--metric-background) 80%, white);
}

.project-title {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 10px;
}

.project-title b {
  color: var(--metric-accent);
  font-family: var(--font-mono);
  font-size: 13px;
}

.project-details {
  display: flex;
  flex-wrap: wrap;
  gap: 3px 8px;
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
  gap: 5px;
  padding-block-end: 7px;
}
</style>
