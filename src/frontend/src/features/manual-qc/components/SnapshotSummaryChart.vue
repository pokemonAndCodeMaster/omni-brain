<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import BaseEChart from '@/shared/analysis/components/BaseEChart.vue'
import type { SceneAggregate } from '../types/snapshot'

const props = defineProps<{ rows: SceneAggregate[]; filtersSummary: string }>()

const option = computed<EChartsOption>(() => {
  const totals = new Map<
    string,
    { assigned: number; completed: number; passed: number; rejected: number }
  >()
  for (const row of props.rows) {
    const current = totals.get(row.scene_name) ?? {
      assigned: 0,
      completed: 0,
      passed: 0,
      rejected: 0,
    }
    current.assigned += row.good_metrics.actual_alloc + row.bad_metrics.actual_alloc
    current.completed +=
      row.good_metrics.actual_complete + row.bad_metrics.actual_complete
    current.passed += row.good_metrics.actual_pass + row.bad_metrics.actual_pass
    current.rejected +=
      row.good_metrics.actual_reject + row.bad_metrics.actual_reject
    totals.set(row.scene_name, current)
  }

  const scenes = [...totals.keys()].sort()
  return {
    animationDuration: 260,
    aria: { show: true },
    color: ['#2458d3', '#5f83df', '#15805f', '#c53b45'],
    tooltip: { trigger: 'axis', confine: true, axisPointer: { type: 'shadow' } },
    legend: {
      bottom: 0,
      textStyle: { color: '#667789', fontSize: 11 },
    },
    grid: { top: 24, right: 16, bottom: 48, left: 52 },
    xAxis: {
      type: 'category',
      data: scenes,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#bdc7d2' } },
      axisLabel: { color: '#637487', rotate: scenes.length > 6 ? 30 : 0 },
    },
    yAxis: {
      type: 'value',
      name: '任务数',
      axisLabel: { color: '#637487' },
      splitLine: { lineStyle: { color: '#e8ecf1' } },
    },
    series: [
      {
        name: '验收分配',
        type: 'bar',
        barMaxWidth: 34,
        data: scenes.map((scene) => totals.get(scene)!.assigned),
      },
      {
        name: '验收完成',
        type: 'bar',
        barMaxWidth: 34,
        data: scenes.map((scene) => totals.get(scene)!.completed),
      },
      {
        name: '验收通过',
        type: 'bar',
        barMaxWidth: 34,
        data: scenes.map((scene) => totals.get(scene)!.passed),
      },
      {
        name: '验收打回',
        type: 'bar',
        barMaxWidth: 34,
        data: scenes.map((scene) => totals.get(scene)!.rejected),
      },
    ],
  }
})
</script>

<template>
  <section class="chart-card panel">
    <header class="chart-header">
      <div>
        <p class="section-index">01 · SCENE COMPARISON</p>
        <h2>场景验收量对比</h2>
      </div>
      <p class="chart-context">{{ filtersSummary }}</p>
    </header>
    <div v-if="rows.length" class="chart-body">
      <BaseEChart :option="option" />
    </div>
    <div v-else class="empty-chart">
      当前筛选没有可绘制的场景聚合。
    </div>
  </section>
</template>

<style scoped>
.chart-card {
  overflow: hidden;
}

.chart-header {
  display: flex;
  min-height: 66px;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 15px;
  border-bottom: 1px solid var(--color-line);
}

.section-index,
.chart-header h2,
.chart-context {
  margin: 0;
}

.section-index {
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.chart-header h2 {
  margin-top: 4px;
  font-size: 15px;
}

.chart-context {
  max-width: 48%;
  color: var(--color-muted);
  font-size: 11px;
  text-align: right;
}

.chart-body {
  height: 330px;
  padding: 8px 12px 12px;
}

.empty-chart {
  display: grid;
  height: 220px;
  place-items: center;
  color: var(--color-muted);
}
</style>
