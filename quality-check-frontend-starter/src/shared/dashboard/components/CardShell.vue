<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import BaseEChart from '@/shared/analysis/components/BaseEChart.vue'
import type { DashboardCard } from '@/shared/dashboard/types/dashboard'

const props = defineProps<{
  card: DashboardCard
  editMode: boolean
}>()

const emit = defineEmits<{
  remove: [id: string]
  duplicate: [id: string]
}>()

const chartOption = computed<EChartsOption>(() => {
  const chart = props.card.chart
  if (!chart) return {}

  if (chart.chartType === 'pie') {
    return {
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['42%', '68%'],
          data: chart.data.map((item) => ({ name: item.name, value: item.value })),
          label: { formatter: '{b}: {c}' },
        },
      ],
    }
  }

  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 18, right: 16, bottom: 36, left: 54 },
    xAxis: {
      type: 'category',
      data: chart.data.map((item) => item.name),
      axisLabel: { interval: 0 },
    },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        data: chart.data.map((item) => item.value),
        barMaxWidth: 44,
      },
    ],
  }
})
</script>

<template>
  <article class="card-shell">
    <header class="card-header">
      <div>
        <h3>{{ card.title }}</h3>
        <p v-if="card.description">{{ card.description }}</p>
      </div>
      <div v-if="editMode" class="card-actions">
        <button class="icon-button" type="button" title="复制卡片" @click="emit('duplicate', card.id)">复制</button>
        <button
          class="icon-button danger"
          type="button"
          title="删除卡片"
          :disabled="card.system"
          @click="emit('remove', card.id)"
        >
          删除
        </button>
      </div>
    </header>

    <div class="card-body">
      <template v-if="card.type === 'kpi' && card.kpi">
        <div class="kpi-value">{{ card.kpi.value }}</div>
        <div class="kpi-label">{{ card.kpi.label }}</div>
        <div class="kpi-helper">{{ card.kpi.helper }}</div>
      </template>

      <BaseEChart v-else-if="card.type === 'chart' && card.chart" :option="chartOption" />

      <p v-else-if="card.type === 'text'" class="text-card">{{ card.text }}</p>

      <div v-else-if="card.type === 'table'" class="mini-table-wrap">
        <table class="mini-table">
          <thead>
            <tr>
              <th v-for="key in Object.keys(card.tableRows?.[0] ?? {})" :key="key">{{ key }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in card.tableRows" :key="index">
              <td v-for="key in Object.keys(row)" :key="key">{{ row[key] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <footer v-if="card.chart" class="card-footer">
      筛选：{{ card.chart.filtersSummary }} · {{ new Date(card.chart.createdAt).toLocaleString('zh-CN') }}
    </footer>
  </article>
</template>

<style scoped>
.card-shell {
  display: flex;
  height: 100%;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  min-height: 58px;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px 10px;
  border-bottom: 1px solid var(--color-border);
}

.card-header h3,
.card-header p {
  margin: 0;
}

.card-header h3 {
  font-size: 15px;
}

.card-header p {
  margin-top: 4px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.card-actions {
  display: flex;
  gap: 6px;
}

.icon-button {
  padding: 4px 7px;
  border: 1px solid var(--color-border);
  border-radius: 5px;
  background: white;
  font-size: 12px;
}

.icon-button.danger {
  color: var(--color-danger);
}

.card-body {
  min-height: 0;
  flex: 1;
  padding: 12px 14px;
}

.kpi-value {
  margin-top: 4px;
  color: var(--color-primary);
  font-size: 34px;
  font-weight: 700;
}

.kpi-label {
  margin-top: 3px;
  font-weight: 600;
}

.kpi-helper,
.text-card {
  margin-top: 8px;
  color: var(--color-text-muted);
  line-height: 1.6;
}

.card-footer {
  padding: 8px 14px;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 11px;
}

.mini-table-wrap {
  overflow: auto;
}

.mini-table {
  width: 100%;
  border-collapse: collapse;
}

.mini-table th,
.mini-table td {
  padding: 8px;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
}
</style>
