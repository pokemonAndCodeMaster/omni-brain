<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption, PieSeriesOption } from 'echarts'
import BaseEChart from '@/shared/analysis/components/BaseEChart.vue'
import CardShell from './CardShell.vue'
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
  refresh: []
  drill: [category: string]
  nudge: [value: { dx?: number; dy?: number; dw?: number; dh?: number }]
}>()

const palettes = {
  business: ['#2458d3', '#5f83df', '#15805f', '#a66300', '#7451b8'],
  quality: ['#15805f', '#d5535d', '#e09b2d', '#5272bb', '#8b5a9f'],
  contrast: ['#173e9e', '#e24a33', '#2a9d8f', '#f2a900', '#6f42c1'],
}

const generatedAt = computed(() => {
  const value = props.result?.source.generatedAt
  if (!value) return '尚未生成'
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
})

const option = computed<EChartsOption>(() => {
  const categories = props.result?.categories ?? []
  const series = props.result?.series ?? []
  const style = props.card.style
  const shared: EChartsOption = {
    animationDuration: 280,
    aria: { enabled: true },
    color: palettes[style.palette],
    tooltip: { trigger: 'axis', confine: true },
    legend: style.showLegend
      ? {
          top: 2,
          left: 0,
          textStyle: { color: '#526274', fontSize: 10 },
        }
      : { show: false },
  }

  if (style.chartType === 'pie') {
    const selected = series[0]
    const data = categories.map((category, index) => ({
      name: category,
      value: selected?.values[index] ?? 0,
    }))
    return {
      ...shared,
      tooltip: { trigger: 'item', confine: true },
      legend: style.showLegend
        ? { type: 'scroll', bottom: 0, left: 'center' }
        : { show: false },
      series: [
        {
          type: 'pie',
          name: selected?.name ?? '统计值',
          radius: ['42%', '68%'],
          center: ['50%', style.showLegend ? '44%' : '50%'],
          data,
          label: {
            show: style.showLabels,
            formatter: '{b}\n{c}',
            fontSize: 10,
          },
        } satisfies PieSeriesOption,
      ],
    }
  }

  const horizontal =
    style.chartType === 'bar' && style.orientation === 'horizontal'
  const categoryAxis = {
    type: 'category' as const,
    data: categories,
    axisLabel: {
      color: '#667789',
      fontSize: 10,
      interval: 0,
      rotate: !horizontal && categories.length > 6 ? 24 : 0,
    },
  }
  const valueAxis = {
    type: 'value' as const,
    minInterval: 1,
    axisLabel: { color: '#667789', fontSize: 10 },
    splitLine: { lineStyle: { color: '#e7ebf0' } },
  }
  return {
    ...shared,
    grid: {
      left: horizontal ? 112 : 48,
      right: 18,
      top: style.showLegend ? 42 : 18,
      bottom: horizontal ? 30 : 58,
      containLabel: false,
    },
    xAxis: horizontal ? valueAxis : categoryAxis,
    yAxis: horizontal ? categoryAxis : valueAxis,
    series: series.map((item) => ({
      id: item.id,
      name: item.name,
      type: style.chartType,
      data: item.values,
      smooth: style.chartType === 'line' && style.smooth,
      symbolSize: 7,
      barMaxWidth: 28,
      stack: style.stacked ? 'total' : undefined,
      label: {
        show: style.showLabels,
        position: horizontal ? 'right' : 'top',
        fontSize: 9,
      },
    })),
  }
})

const ariaLabel = computed(() => {
  const categories = props.result?.categories ?? []
  const series = props.result?.series.map((item) => item.name) ?? []
  return `${props.card.title}；按${categories.join('、')}展示${series.join('、')}`
})
</script>

<template>
  <CardShell
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
      正在读取最新快照…
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
    <div v-else class="chart-region">
      <BaseEChart
        :option="option"
        :aria-label="ariaLabel"
        :min-height="170"
        @chart-click="emit('drill', $event.name)"
      />
    </div>

    <details v-if="result?.categories.length" class="chart-data">
      <summary>查看图表数据</summary>
      <div class="data-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">分组</th>
              <th v-for="series in result.series" :key="series.id" scope="col">
                {{ series.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(category, index) in result.categories" :key="category">
              <th scope="row">{{ category }}</th>
              <td v-for="series in result.series" :key="series.id">
                {{ series.values[index] ?? 0 }}{{ series.unit ?? '' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </details>

    <template #footer>
      <dl class="source-context">
        <div>
          <dt>来源</dt>
          <dd>{{ result?.source.sourceLabel ?? card.query.sourceId }}</dd>
        </div>
        <div>
          <dt>筛选</dt>
          <dd>{{ card.query.filterSummary || '无额外筛选' }}</dd>
        </div>
        <div>
          <dt>样本</dt>
          <dd>{{ result?.source.rowCount ?? 0 }} 行</dd>
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
  font-size: 16px;
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
  z-index: 20;
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

.chart-region {
  height: 100%;
  min-height: 170px;
}

.card-state {
  display: grid;
  min-height: 170px;
  place-items: center;
  color: var(--color-muted);
  font-size: 11px;
}

.card-state.is-error {
  color: var(--color-danger);
}

.chart-data {
  border-top: 1px solid var(--color-line-subtle);
  color: var(--color-muted);
  font-size: 10px;
}

.chart-data summary {
  width: max-content;
  padding: 7px 0 1px;
  color: var(--color-primary);
}

.data-scroll {
  max-height: 150px;
  margin-top: 5px;
  overflow: auto;
  border: 1px solid var(--color-line-subtle);
}

.chart-data table {
  width: 100%;
  border-collapse: collapse;
}

.chart-data th,
.chart-data td {
  padding: 5px 7px;
  border-bottom: 1px solid var(--color-line-subtle);
  text-align: right;
  white-space: nowrap;
}

.chart-data th:first-child {
  text-align: left;
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
