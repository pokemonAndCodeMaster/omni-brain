<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { EChartsOption } from 'echarts'
import BaseEChart from '@/shared/analysis/components/BaseEChart.vue'
import type { DeliveryRow } from '@/features/manual-qc/types/delivery'
import type {
  AnalysisChartType,
  AnalysisDimension,
  AnalysisMetric,
  ChartSpec,
} from '@/shared/analysis/types/chart'

const props = defineProps<{
  rows: DeliveryRow[]
  filtersSummary: string
}>()

const emit = defineEmits<{
  close: []
  addToDashboard: [chart: ChartSpec]
}>()

const dimension = ref<AnalysisDimension>('project')
const metric = ref<AnalysisMetric>('count')
const chartType = ref<AnalysisChartType>('bar')
const title = ref('按项目统计任务数量')

const dimensionLabels: Record<AnalysisDimension, string> = {
  project: '项目',
  status: '状态',
  owner: '负责人',
  priority: '优先级',
}

const metricLabels: Record<AnalysisMetric, string> = {
  count: '任务数量',
  targetCount: '目标数量合计',
  completedCount: '完成数量合计',
  goodRate: '平均 Good 比例',
}

watch([dimension, metric], () => {
  title.value = `按${dimensionLabels[dimension.value]}统计${metricLabels[metric.value]}`
})

const chartData = computed(() => {
  const buckets = new Map<string, DeliveryRow[]>()
  props.rows.forEach((row) => {
    const key = String(row[dimension.value])
    const bucket = buckets.get(key) ?? []
    bucket.push(row)
    buckets.set(key, bucket)
  })

  return [...buckets.entries()]
    .map(([name, rows]) => {
      let value = 0
      if (metric.value === 'count') value = rows.length
      if (metric.value === 'targetCount') {
        value = rows.reduce((sum, row) => sum + row.targetCount, 0)
      }
      if (metric.value === 'completedCount') {
        value = rows.reduce((sum, row) => sum + row.completedCount, 0)
      }
      if (metric.value === 'goodRate') {
        const validRows = rows.filter((row) => row.goodRate > 0)
        value = validRows.length
          ? Number(
              (
                validRows.reduce((sum, row) => sum + row.goodRate, 0) / validRows.length
              ).toFixed(4),
            )
          : 0
      }
      return { name, value }
    })
    .sort((a, b) => b.value - a.value)
})

const chartOption = computed<EChartsOption>(() => {
  const formatValue = (value: number) =>
    metric.value === 'goodRate' ? `${(value * 100).toFixed(1)}%` : String(value)

  if (chartType.value === 'pie') {
    return {
      tooltip: {
        trigger: 'item',
        valueFormatter: (value) => formatValue(Number(value)),
      },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['40%', '68%'],
          data: chartData.value,
          label: {
            formatter: (params) => `${params.name}: ${formatValue(Number(params.value))}`,
          },
        },
      ],
    }
  }

  return {
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value) => formatValue(Number(value)),
    },
    grid: { top: 18, right: 20, bottom: 42, left: 64 },
    xAxis: {
      type: 'category',
      data: chartData.value.map((item) => item.name),
      axisLabel: { interval: 0 },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: metric.value === 'goodRate' ? (value: number) => `${value * 100}%` : undefined,
      },
    },
    series: [
      {
        type: 'bar',
        data: chartData.value.map((item) => item.value),
        barMaxWidth: 46,
      },
    ],
  }
})

function addToDashboard() {
  const chart: ChartSpec = {
    id: crypto.randomUUID(),
    title: title.value.trim() || '未命名图表',
    description: `由统一数据工作台生成，范围包含 ${props.rows.length} 条叶子数据。`,
    dimension: dimension.value,
    metric: metric.value,
    chartType: chartType.value,
    data: structuredClone(chartData.value),
    filtersSummary: props.filtersSummary,
    createdAt: new Date().toISOString(),
  }
  emit('addToDashboard', chart)
}
</script>

<template>
  <div class="drawer-backdrop" @click.self="emit('close')">
    <aside class="analysis-drawer" aria-label="统计分析构建器">
      <header class="drawer-header">
        <div>
          <p class="eyebrow">ANALYSIS BUILDER</p>
          <h2>一键统计分析</h2>
        </div>
        <button class="button" type="button" @click="emit('close')">关闭</button>
      </header>

      <div class="drawer-body">
        <div class="analysis-form">
          <label>
            图表标题
            <input v-model="title" class="field" />
          </label>
          <label>
            维度
            <select v-model="dimension" class="select-field">
              <option value="project">项目</option>
              <option value="status">状态</option>
              <option value="owner">负责人</option>
              <option value="priority">优先级</option>
            </select>
          </label>
          <label>
            指标
            <select v-model="metric" class="select-field">
              <option value="count">任务数量</option>
              <option value="targetCount">目标数量合计</option>
              <option value="completedCount">完成数量合计</option>
              <option value="goodRate">平均 Good 比例</option>
            </select>
          </label>
          <label>
            图表类型
            <select v-model="chartType" class="select-field">
              <option value="bar">条形图</option>
              <option value="pie">环图</option>
            </select>
          </label>
        </div>

        <div class="analysis-context">
          <strong>分析范围</strong>
          <span>{{ filtersSummary }}</span>
          <span>{{ rows.length }} 条叶子数据</span>
        </div>

        <div class="chart-preview panel">
          <BaseEChart :option="chartOption" />
        </div>

        <div class="analysis-table panel">
          <table>
            <thead>
              <tr><th>维度值</th><th>统计值</th></tr>
            </thead>
            <tbody>
              <tr v-for="item in chartData" :key="item.name">
                <td>{{ item.name }}</td>
                <td>{{ metric === 'goodRate' ? `${(item.value * 100).toFixed(1)}%` : item.value }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <footer class="drawer-footer">
        <button class="button" type="button" @click="emit('close')">取消</button>
        <button class="button primary" type="button" :disabled="chartData.length === 0" @click="addToDashboard">
          添加到个人看板
        </button>
      </footer>
    </aside>
  </div>
</template>

<style scoped>
.drawer-backdrop {
  position: fixed;
  z-index: 100;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  background: rgb(16 24 40 / 36%);
}

.analysis-drawer {
  display: flex;
  width: min(720px, 96vw);
  height: 100%;
  flex-direction: column;
  background: white;
  box-shadow: var(--shadow-md);
}

.drawer-header,
.drawer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--color-border);
}

.drawer-header h2 {
  margin: 3px 0 0;
}

.drawer-body {
  display: grid;
  gap: 16px;
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding: 18px;
}

.analysis-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.analysis-form label {
  display: grid;
  gap: 6px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.analysis-context {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-muted);
}

.chart-preview {
  height: 330px;
  padding: 10px;
}

.analysis-table {
  overflow: auto;
}

.analysis-table table {
  width: 100%;
  border-collapse: collapse;
}

.analysis-table th,
.analysis-table td {
  padding: 9px 12px;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
}

.drawer-footer {
  justify-content: flex-end;
  border-top: 1px solid var(--color-border);
  border-bottom: 0;
}

@media (max-width: 600px) {
  .analysis-form {
    grid-template-columns: 1fr;
  }
}
</style>
