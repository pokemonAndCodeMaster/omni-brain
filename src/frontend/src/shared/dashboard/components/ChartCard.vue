<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption, PieSeriesOption } from 'echarts'
import BaseEChart from '@/shared/analysis/components/BaseEChart.vue'
import CardShell from './CardShell.vue'
import type {
  DashboardChartCard,
  DashboardChartType,
} from '../types'

const props = defineProps<{ card: DashboardChartCard }>()

const emit = defineEmits<{
  remove: []
  chartTypeChange: [chartType: DashboardChartType]
}>()

const generatedAt = computed(() =>
  new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(props.card.source.generatedAt)),
)

const option = computed<EChartsOption>(() => {
  const shared: EChartsOption = {
    animationDuration: 350,
    aria: { enabled: true },
    color: ['#2458d3', '#d5535d', '#15805f', '#a66300'],
    tooltip: { trigger: 'axis' },
    legend: {
      top: 2,
      left: 0,
      textStyle: { color: '#526274', fontSize: 10 },
    },
  }

  if (props.card.chartType === 'pie') {
    const selected = props.card.series[0]
    const data = props.card.categories.map((category, index) => ({
      name: category,
      value: selected?.values[index] ?? 0,
    }))
    return {
      ...shared,
      tooltip: { trigger: 'item' },
      legend: { type: 'scroll', bottom: 0, left: 'center' },
      series: [
        {
          type: 'pie',
          name: selected?.name ?? '统计值',
          radius: ['42%', '68%'],
          center: ['50%', '45%'],
          data,
          label: { formatter: '{b}\n{c}', fontSize: 10 },
        } satisfies PieSeriesOption,
      ],
    }
  }

  return {
    ...shared,
    grid: { left: 42, right: 14, top: 42, bottom: 42 },
    xAxis: {
      type: 'category',
      data: props.card.categories,
      axisLabel: {
        color: '#667789',
        fontSize: 10,
        interval: 0,
        rotate: props.card.categories.length > 6 ? 24 : 0,
      },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#667789', fontSize: 10 },
      splitLine: { lineStyle: { color: '#e7ebf0' } },
    },
    series: props.card.series.map((series) => ({
      id: series.id,
      name: series.name,
      type: props.card.chartType,
      data: series.values,
      smooth: props.card.chartType === 'line',
      symbolSize: 7,
      barMaxWidth: 28,
    })),
  }
})

const ariaLabel = computed(() => {
  const series = props.card.series.map((item) => item.name).join('、')
  return `${props.card.title}；按${props.card.categories.join('、')}展示${series}`
})
</script>

<template>
  <CardShell
    :title="card.title"
    :description="card.description"
    removable
    @remove="emit('remove')"
  >
    <template #actions>
      <label class="chart-type-field">
        <span>图形</span>
        <select
          :value="card.chartType"
          :aria-label="`切换${card.title}的图表类型`"
          @change="
            emit(
              'chartTypeChange',
              ($event.target as HTMLSelectElement).value as DashboardChartType,
            )
          "
        >
          <option value="bar">柱状</option>
          <option value="line">折线</option>
          <option value="pie">饼图</option>
        </select>
      </label>
    </template>

    <div class="chart-region">
      <BaseEChart :option="option" :aria-label="ariaLabel" :min-height="265" />
    </div>

    <details class="chart-data">
      <summary>查看图表数据</summary>
      <div class="data-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">分组</th>
              <th v-for="series in card.series" :key="series.id" scope="col">
                {{ series.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(category, index) in card.categories" :key="category">
              <th scope="row">{{ category }}</th>
              <td v-for="series in card.series" :key="series.id">
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
          <dd>{{ card.source.sourceLabel }}</dd>
        </div>
        <div>
          <dt>筛选</dt>
          <dd>{{ card.source.filterSummary || '无额外筛选' }}</dd>
        </div>
        <div>
          <dt>样本</dt>
          <dd>{{ card.source.rowCount }} 行</dd>
        </div>
        <div>
          <dt>生成</dt>
          <dd>{{ generatedAt }}</dd>
        </div>
      </dl>
    </template>
  </CardShell>
</template>

<style scoped>
.chart-type-field {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--color-muted);
  font-size: 10px;
}

.chart-type-field select {
  min-height: 29px;
  padding: 3px 6px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  background: white;
  color: var(--color-ink-secondary);
  font-size: 11px;
}

.chart-region {
  height: 290px;
}

.chart-data {
  margin-top: 4px;
  border-top: 1px solid var(--color-line-subtle);
  color: var(--color-muted);
  font-size: 10px;
}

.chart-data summary {
  width: max-content;
  padding: 8px 0 2px;
  color: var(--color-primary);
}

.data-scroll {
  max-height: 170px;
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
  grid-template-columns: minmax(120px, 1fr) minmax(180px, 2fr) auto auto;
  gap: 10px 18px;
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
