<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import BaseEChart from '@/shared/analysis/components/BaseEChart.vue'
import type {
  DashboardChartAxis,
  DashboardChartCard,
  DashboardChartResult,
} from '../types'

const props = withDefaults(
  defineProps<{
    card: DashboardChartCard
    result: DashboardChartResult
    preview?: boolean
  }>(),
  {
    preview: false,
  },
)

const emit = defineEmits<{
  drill: [category: string]
}>()

const fontSizes = {
  small: { axis: 9, legend: 9, label: 8 },
  medium: { axis: 10, legend: 10, label: 9 },
  large: { axis: 12, legend: 12, label: 11 },
}

function valueAxis(axis: DashboardChartAxis, index: number) {
  const percent = axis.unit === 'percent'
  return {
    type: 'value' as const,
    name: axis.label,
    position: axis.side,
    offset: index > 1 ? (index - 1) * 44 : 0,
    min: axis.minimum ?? undefined,
    max: axis.maximum ?? undefined,
    minInterval: percent ? undefined : 1,
    alignTicks: true,
    axisLabel: {
      color: '#667789',
      fontSize: fontSizes[props.card.presentation.fontScale].axis,
      formatter: percent ? '{value}%' : '{value}',
    },
    splitLine: {
      show: index === 0,
      lineStyle: { color: '#e7ebf0' },
    },
  }
}

const option = computed<EChartsOption>(() => {
  const categories = props.result.categories
  const presentation = props.card.presentation
  const horizontal = presentation.orientation === 'horizontal'
  const legendAtBottom = presentation.legendPosition === 'bottom'
  const denseCategories = categories.length > 12
  const fontSize = fontSizes[presentation.fontScale]
  const categoryAxis = {
    type: 'category' as const,
    data: categories,
    axisLabel: {
      color: '#667789',
      fontSize: fontSize.axis,
      interval: 0,
      rotate:
        !horizontal && !denseCategories && categories.length > 6
          ? 24
          : 0,
      hideOverlap: true,
      width: denseCategories ? (horizontal ? 132 : 78) : undefined,
      overflow: denseCategories ? 'truncate' as const : undefined,
    },
  }
  const axes = props.card.axes.map(valueAxis)
  const axisIndex = new Map(
    props.card.axes.map((axis, index) => [axis.id, index]),
  )
  return {
    animationDuration: 260,
    aria: { enabled: true },
    tooltip: {
      trigger: 'axis',
      confine: true,
      axisPointer: { type: 'shadow' },
    },
    legend: presentation.showLegend
      ? {
          type: 'scroll',
          left: 0,
          ...(legendAtBottom ? { bottom: 2 } : { top: 2 }),
          textStyle: { color: '#526274', fontSize: fontSize.legend },
        }
      : { show: false },
    grid: {
      left: horizontal ? 150 : 52,
      right: props.card.axes.some((axis) => axis.side === 'right') ? 58 : 20,
      top: presentation.showLegend && !legendAtBottom ? 46 : 28,
      bottom:
        denseCategories && !horizontal
          ? legendAtBottom ? 96 : 76
          : presentation.showLegend && legendAtBottom ? 72 : 46,
      containLabel: false,
    },
    dataZoom: denseCategories
      ? horizontal
        ? [
            {
              type: 'inside',
              yAxisIndex: 0,
              startValue: 0,
              endValue: 9,
              moveOnMouseWheel: false,
              zoomOnMouseWheel: true,
            },
            {
              type: 'slider',
              yAxisIndex: 0,
              orient: 'vertical',
              startValue: 0,
              endValue: 9,
              width: 14,
              right: 4,
              brushSelect: false,
              showDetail: false,
            },
          ]
        : [
            {
              type: 'inside',
              xAxisIndex: 0,
              startValue: 0,
              endValue: 9,
              moveOnMouseWheel: false,
              zoomOnMouseWheel: true,
            },
            {
              type: 'slider',
              xAxisIndex: 0,
              startValue: 0,
              endValue: 9,
              height: 14,
              bottom: legendAtBottom ? 24 : 8,
              brushSelect: false,
              showDetail: false,
            },
          ]
      : undefined,
    xAxis: horizontal ? axes : categoryAxis,
    yAxis: horizontal ? categoryAxis : axes,
    series: props.result.series.map((series) => {
      const renderAs = series.renderAs ?? 'bar'
      return {
        id: series.id,
        name: series.name,
        type: renderAs === 'bar' ? 'bar' : 'line',
        data: series.values,
        xAxisIndex: horizontal
          ? axisIndex.get(series.axisId ?? '') ?? 0
          : undefined,
        yAxisIndex: horizontal
          ? undefined
          : axisIndex.get(series.axisId ?? '') ?? 0,
        itemStyle: series.color ? { color: series.color } : undefined,
        lineStyle: series.color ? { color: series.color, width: 2 } : undefined,
        areaStyle:
          renderAs === 'area'
            ? { color: series.color, opacity: 0.16 }
            : undefined,
        stack: series.stackGroup ?? undefined,
        smooth: renderAs !== 'bar' && series.smooth,
        symbolSize: 7,
        barMaxWidth: 32,
        label: {
          show: series.showLabels,
          position: horizontal ? 'right' : 'top',
          fontSize: fontSize.label,
          formatter: series.unit === '%' ? '{c}%' : '{c}',
        },
      }
    }),
  }
})

const ariaLabel = computed(
  () =>
    `${props.card.title}；按${props.result.categories.join('、')}展示` +
    props.result.series.map((item) => item.name).join('、'),
)
</script>

<template>
  <div class="visualization">
    <div class="chart-region">
      <BaseEChart
        :option="option"
        :aria-label="ariaLabel"
        :min-height="preview ? 240 : 180"
        @chart-click="emit('drill', $event.name)"
      />
    </div>

    <details class="chart-data" :open="preview">
      <summary>查看图表数据</summary>
      <div class="data-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">分组</th>
              <th
                v-for="series in result.series"
                :key="series.id"
                scope="col"
              >
                {{ series.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(category, index) in result.categories"
              :key="category"
            >
              <th scope="row">{{ category }}</th>
              <td v-for="series in result.series" :key="series.id">
                {{ series.values[index] ?? '—' }}{{ series.values[index] == null ? '' : series.unit ?? '' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </details>
  </div>
</template>

<style scoped>
.visualization {
  display: grid;
  height: 100%;
  grid-template-rows: minmax(180px, 1fr) auto;
  min-height: 0;
  gap: 6px;
}

.chart-region {
  height: 100%;
  min-width: 0;
  min-height: 180px;
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
  cursor: pointer;
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
</style>
