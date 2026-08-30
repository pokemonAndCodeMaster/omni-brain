<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import type { EChartsOption } from 'echarts'
import BaseEChart from '@/shared/analysis/components/BaseEChart.vue'
import type {
  AnalysisMetricReference,
  TaskMetricDetail,
  TaskMetricDetailSelection,
} from '../types/analysis'

const props = defineProps<{
  selection: TaskMetricDetailSelection | null
  detail: TaskMetricDetail | null
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  close: []
  pinMetric: [reference: AnalysisMetricReference]
}>()

interface SummaryItem {
  id: string
  label: string
  unit: 'count' | 'percent'
}

const summaryItems = computed<SummaryItem[]>(() => {
  const metricId = props.selection?.metricId
  if (metricId === 'annotation.good_rate') {
    return [
      { id: 'annotation.submitted', label: '标注提交', unit: 'count' },
      { id: 'annotation.good_submitted', label: 'Good', unit: 'count' },
      { id: 'annotation.bad_submitted', label: 'Bad', unit: 'count' },
      { id: 'annotation.good_rate', label: 'Good 占比', unit: 'percent' },
      { id: 'annotation.bad_rate', label: 'Bad 占比', unit: 'percent' },
    ]
  }
  if (metricId === 'acceptance.completion_rate') {
    return [
      { id: 'acceptance.allocated', label: '验收分配', unit: 'count' },
      { id: 'acceptance.completed', label: '验收完成', unit: 'count' },
      { id: 'acceptance.pending', label: '验收未完成', unit: 'count' },
      { id: 'acceptance.completion_rate', label: '整体完成率', unit: 'percent' },
      { id: 'good.acceptance.completion_rate', label: 'Good 完成率', unit: 'percent' },
      { id: 'bad.acceptance.completion_rate', label: 'Bad 完成率', unit: 'percent' },
    ]
  }
  return [
    { id: 'acceptance.completed', label: '验收完成', unit: 'count' },
    { id: 'acceptance.passed', label: '验收通过', unit: 'count' },
    { id: 'acceptance.rejected', label: '验收打回', unit: 'count' },
    { id: 'acceptance.pass_rate', label: '整体通过率', unit: 'percent' },
    { id: 'good.acceptance.pass_rate', label: 'Good 通过率', unit: 'percent' },
    { id: 'bad.acceptance.pass_rate', label: 'Bad 通过率', unit: 'percent' },
  ]
})

const title = computed(() => {
  const label = {
    'annotation.good_rate': 'Good / Bad 与问题分布',
    'acceptance.completion_rate': '验收分配与完成详情',
    'acceptance.pass_rate': '验收通过与打回详情',
  }[props.selection?.metricId ?? 'annotation.good_rate']
  return `${props.selection?.row.objectLabel ?? ''} · ${label}`
})

const mainMetric = computed(() =>
  props.selection?.metricId ?? 'annotation.good_rate',
)

const trendOption = computed<EChartsOption>(() => {
  const values = props.detail?.trend ?? []
  const isRate = true
  return {
    animation: false,
    grid: { left: 42, right: 18, top: 24, bottom: 36 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: values.map((item) => item.date.slice(5)),
      axisLabel: { fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: isRate ? '%' : '',
      axisLabel: { fontSize: 10 },
    },
    series: [
      {
        name: summaryItems.value.find((item) => item.id === mainMetric.value)?.label,
        type: 'line',
        smooth: false,
        symbolSize: 6,
        data: values.map((item) => item.measures[mainMetric.value]),
        lineStyle: { width: 2, color: '#2458d3' },
        itemStyle: { color: '#2458d3' },
        areaStyle: { color: 'rgba(36, 88, 211, 0.08)' },
      },
    ],
  }
})

const groupedOptions = computed(() => {
  const groups = new Map<string, TaskMetricDetail['options']>()
  for (const option of props.detail?.options ?? []) {
    const current = groups.get(option.questionLabel) ?? []
    current.push(option)
    groups.set(option.questionLabel, current)
  }
  return [...groups.entries()].map(([label, options]) => ({
    label,
    options: [...options].sort(
      (left, right) => right.annotationSubmitted - left.annotationSubmitted,
    ),
  }))
})

function formatValue(
  identifier: string,
  unit: 'count' | 'percent',
): string {
  const value = props.detail?.summary[identifier]
  if (value == null) return '—'
  return unit === 'percent' ? `${value.toFixed(1)}%` : String(value)
}

function formatRate(value: number | null): string {
  return value == null ? '—' : `${value.toFixed(1)}%`
}

function pinReference(
  questionLabel: string,
  questionOption: string,
): AnalysisMetricReference {
  const id = {
    'annotation.good_rate': 'option.annotation_rate_of_bad',
    'acceptance.completion_rate': 'option.acceptance.completion_rate',
    'acceptance.pass_rate': 'option.acceptance.pass_rate',
  }[mainMetric.value]
  return {
    id,
    parameters: { questionLabel, questionOption },
  }
}

function handleKeyDown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && props.selection) emit('close')
}

onMounted(() => document.addEventListener('keydown', handleKeyDown))
onBeforeUnmount(() => document.removeEventListener('keydown', handleKeyDown))
</script>

<template>
  <Teleport to="body">
    <div
      v-if="selection"
      class="drawer-backdrop"
      role="presentation"
      @click.self="emit('close')"
    >
      <aside
        class="detail-drawer"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
      >
        <header class="drawer-header">
          <div>
            <p>{{ selection.row.objectType }}指标详情</p>
            <h2>{{ title }}</h2>
          </div>
          <button type="button" aria-label="关闭指标详情" @click="emit('close')">
            关闭
          </button>
        </header>

        <div v-if="loading" class="drawer-status" role="status">
          正在读取构成、趋势和问题选项…
        </div>
        <div v-else-if="error" class="drawer-error" role="alert">
          {{ error }}
        </div>
        <template v-else-if="detail">
          <section class="drawer-section" aria-labelledby="detail-summary-title">
            <div class="section-heading">
              <h3 id="detail-summary-title">当前范围汇总</h3>
              <p>数量先汇总，再计算比例；空分母显示为“—”。</p>
            </div>
            <dl class="summary-grid">
              <div v-for="item in summaryItems" :key="item.id">
                <dt>{{ item.label }}</dt>
                <dd>{{ formatValue(item.id, item.unit) }}</dd>
              </div>
            </dl>
          </section>

          <section class="drawer-section" aria-labelledby="detail-trend-title">
            <div class="section-heading">
              <h3 id="detail-trend-title">按日趋势</h3>
              <p>沿用当前任务及下钻路径，仅按日期重新聚合。</p>
            </div>
            <BaseEChart
              :option="trendOption"
              :aria-label="`${selection.row.objectLabel}按日趋势`"
              :min-height="230"
            />
          </section>

          <section class="drawer-section" aria-labelledby="detail-option-title">
            <div class="section-heading">
              <h3 id="detail-option-title">问题标签与选项</h3>
              <p>
                问题选项可能多选，各选项占 Bad 比例之和不要求等于 100%。
                可把当前关注的选项固定为任务表新列。
              </p>
            </div>
            <article
              v-for="group in groupedOptions"
              :key="group.label"
              class="option-group"
            >
              <h4>{{ group.label }}</h4>
              <div class="option-table-wrap">
                <table class="option-table">
                  <thead>
                    <tr>
                      <th>问题选项</th>
                      <th>标注量</th>
                      <th>占 Bad</th>
                      <th>验收分配</th>
                      <th>完成率</th>
                      <th>通过率</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="option in group.options" :key="option.questionOption">
                      <td>{{ option.questionOption }}</td>
                      <td>{{ option.annotationSubmitted }}</td>
                      <td>{{ formatRate(option.annotationRateOfBad) }}</td>
                      <td>{{ option.allocated }}</td>
                      <td>{{ formatRate(option.completionRate) }}</td>
                      <td>{{ formatRate(option.passRate) }}</td>
                      <td>
                        <button
                          type="button"
                          :aria-label="`固定 ${group.label} ${option.questionOption} 为表格列`"
                          @click="
                            emit(
                              'pinMetric',
                              pinReference(group.label, option.questionOption),
                            )
                          "
                        >
                          固定为列
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>
          </section>
        </template>
      </aside>
    </div>
  </Teleport>
</template>

<style scoped>
.drawer-backdrop {
  position: fixed;
  z-index: 300;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  background: rgb(16 24 40 / 24%);
}

.detail-drawer {
  width: min(760px, calc(100vw - 32px));
  height: 100vh;
  overflow: auto;
  padding: 20px;
  background: #f7f9fc;
  box-shadow: -18px 0 48px rgb(16 24 40 / 18%);
}

.drawer-header,
.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.drawer-header {
  position: sticky;
  z-index: 2;
  top: -20px;
  margin: -20px -20px 16px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--color-line);
  background: white;
}

.drawer-header p,
.drawer-header h2,
.section-heading h3,
.section-heading p,
.option-group h4 {
  margin: 0;
}

.drawer-header p {
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 700;
}

.drawer-header h2 {
  margin-top: 4px;
  font-size: 17px;
}

.drawer-header button,
.option-table button {
  min-height: 30px;
  padding: 5px 9px;
  border: 1px solid var(--color-line);
  border-radius: 5px;
  background: white;
  color: var(--color-primary);
  cursor: pointer;
}

.drawer-status,
.drawer-error,
.drawer-section {
  padding: 14px;
  border: 1px solid var(--color-line);
  border-radius: 8px;
  background: white;
}

.drawer-error {
  color: #a33a3a;
}

.drawer-section + .drawer-section {
  margin-top: 14px;
}

.section-heading h3 {
  font-size: 14px;
}

.section-heading p {
  max-width: 480px;
  color: var(--color-muted);
  font-size: 11px;
  line-height: 1.6;
  text-align: right;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 12px 0 0;
}

.summary-grid div {
  padding: 10px;
  border-radius: 6px;
  background: #f3f6fb;
}

.summary-grid dt {
  color: var(--color-muted);
  font-size: 10px;
}

.summary-grid dd {
  margin: 5px 0 0;
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 750;
}

.option-group {
  margin-top: 14px;
}

.option-group h4 {
  margin-bottom: 7px;
  font-size: 12px;
}

.option-table-wrap {
  overflow-x: auto;
}

.option-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  white-space: nowrap;
}

.option-table th,
.option-table td {
  padding: 7px 8px;
  border-bottom: 1px solid var(--color-line-subtle);
  text-align: right;
}

.option-table th:first-child,
.option-table td:first-child {
  text-align: left;
}

@media (max-width: 640px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .section-heading {
    flex-direction: column;
  }

  .section-heading p {
    text-align: left;
  }
}
</style>
