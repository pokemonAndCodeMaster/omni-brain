<script setup lang="ts">
import { onBeforeUnmount, onMounted, useTemplateRef, watch } from 'vue'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  AriaComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { init, use } from 'echarts/core'
import type { ECharts, EChartsOption } from 'echarts'

use([
  BarChart,
  LineChart,
  PieChart,
  AriaComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
])

const props = withDefaults(
  defineProps<{ option: EChartsOption; ariaLabel?: string; minHeight?: number }>(),
  {
    ariaLabel: '统计图表',
    minHeight: 280,
  },
)
const host = useTemplateRef<HTMLDivElement>('host')
let chart: ECharts | null = null
let observer: ResizeObserver | null = null

function render() {
  chart?.setOption(props.option, { notMerge: true })
}

onMounted(() => {
  if (!host.value) return
  chart = init(host.value)
  render()
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(host.value)
})

watch(() => props.option, render, { deep: true })

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div
    ref="host"
    class="chart-host"
    role="img"
    :aria-label="ariaLabel"
    :style="{ minHeight: `${minHeight}px` }"
  ></div>
</template>

<style scoped>
.chart-host {
  width: 100%;
  height: 100%;
}
</style>
