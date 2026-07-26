<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import type { EChartsOption } from 'echarts'
import BaseEChart from '@/shared/analysis/components/BaseEChart.vue'
import type { SceneAggregate, SnapshotRow } from '../types/snapshot'

type GroupMode = 'task' | 'date'

const props = defineProps<{
  rows: SceneAggregate[]
  snapshotRows: SnapshotRow[]
  filtersSummary: string
}>()
const emit = defineEmits<{
  drillTask: [taskName: string]
  drillProject: [projectName: string]
  drillDate: [date: string]
}>()

interface AnalysisGroup {
  label: string
  project: string
  submitted: number
  good: number
  bad: number
  allocated: number
  completed: number
  passed: number
  rejected: number
  options: Map<string, number>
}

const annotationMode = shallowRef<GroupMode>('task')
const progressMode = shallowRef<GroupMode>('task')
const resultMode = shallowRef<GroupMode>('task')

function emptyGroup(label: string, project = ''): AnalysisGroup {
  return {
    label,
    project,
    submitted: 0,
    good: 0,
    bad: 0,
    allocated: 0,
    completed: 0,
    passed: 0,
    rejected: 0,
    options: new Map(),
  }
}

function analysisGroups(mode: GroupMode): AnalysisGroup[] {
  const result = new Map<string, AnalysisGroup>()
  for (const row of props.snapshotRows) {
    const label = mode === 'date' ? row.stat_date : row.scene_name
    const current = result.get(label) ?? emptyGroup(label, row.project_name)
    current.submitted += row.annotation_submitted
    current.good += row.good_metrics.annotation_submitted
    current.bad += row.bad_metrics.annotation_submitted
    current.allocated +=
      row.good_metrics.actual_alloc + row.bad_metrics.actual_alloc
    current.completed +=
      row.good_metrics.actual_complete + row.bad_metrics.actual_complete
    current.passed +=
      row.good_metrics.actual_pass + row.bad_metrics.actual_pass
    current.rejected +=
      row.good_metrics.actual_reject + row.bad_metrics.actual_reject
    for (const [question, options] of Object.entries(row.option_metrics)) {
      for (const [option, metric] of Object.entries(options)) {
        const key = `${question} / ${option}`
        current.options.set(
          key,
          (current.options.get(key) ?? 0) + metric.annotation_submitted,
        )
      }
    }
    result.set(label, current)
  }
  return [...result.values()].sort((left, right) =>
    left.label.localeCompare(right.label, 'zh-CN'),
  )
}

const annotationGroups = computed(() =>
  analysisGroups(annotationMode.value),
)
const progressGroups = computed(() => analysisGroups(progressMode.value))
const resultGroups = computed(() => analysisGroups(resultMode.value))

const optionTotals = computed(() => {
  const totals = new Map<string, number>()
  for (const row of props.snapshotRows) {
    for (const [question, options] of Object.entries(row.option_metrics)) {
      for (const [option, metric] of Object.entries(options)) {
        const key = `${question} / ${option}`
        totals.set(
          key,
          (totals.get(key) ?? 0) + metric.annotation_submitted,
        )
      }
    }
  }
  return [...totals.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((left, right) => right.count - left.count)
})

const visibleOptionNames = computed(() =>
  optionTotals.value.slice(0, 6).map((item) => item.name),
)

const totalBad = computed(() =>
  props.snapshotRows.reduce(
    (sum, row) => sum + row.bad_metrics.annotation_submitted,
    0,
  ),
)

function rate(numerator: number, denominator: number): number {
  return denominator
    ? Math.round((numerator / denominator) * 1000) / 10
    : 0
}

function handleChartClick(mode: GroupMode, name: string): void {
  if (mode === 'date') emit('drillDate', name)
  else emit('drillTask', name)
}

function compactTaskLabel(value: string): string {
  return value.replace(/任务-\d+$/u, '').replace(/任务$/u, '') || value
}

function baseChartOption(
  groups: AnalysisGroup[],
  mode: GroupMode,
): EChartsOption {
  const denseTasks = mode === 'task' && groups.length > 12
  return {
    animationDuration: 260,
    aria: { enabled: true },
    tooltip: { trigger: 'axis', confine: true, axisPointer: { type: 'shadow' } },
    legend: {
      type: 'scroll',
      bottom: 0,
      textStyle: { color: '#667789', fontSize: 10 },
    },
    grid: {
      top: 34,
      right: 52,
      bottom: denseTasks ? 92 : 70,
      left: 48,
    },
    xAxis: {
      type: 'category',
      data: groups.map((group) => group.label),
      axisLabel: {
        color: '#637487',
        interval: 0,
        rotate: denseTasks ? 0 : groups.length > 5 ? 24 : 0,
        hideOverlap: true,
        width: denseTasks ? 72 : undefined,
        overflow: denseTasks ? 'truncate' : undefined,
        formatter:
          mode === 'task'
            ? (value: string) => compactTaskLabel(value)
            : undefined,
      },
    },
    dataZoom: denseTasks
      ? [
          {
            type: 'inside',
            startValue: 0,
            endValue: 9,
            zoomLock: true,
            moveOnMouseWheel: true,
            zoomOnMouseWheel: false,
          },
          {
            type: 'slider',
            startValue: 0,
            endValue: 9,
            zoomLock: true,
            height: 14,
            bottom: 22,
            brushSelect: false,
            showDetail: false,
          },
        ]
      : undefined,
    yAxis: [
      {
        type: 'value',
        name: '数量',
        minInterval: 1,
        axisLabel: { color: '#637487' },
        splitLine: { lineStyle: { color: '#e8ecf1' } },
      },
      {
        type: 'value',
        name: '占比',
        min: 0,
        max: 100,
        alignTicks: true,
        axisLabel: { color: '#637487', formatter: '{value}%' },
        splitLine: { show: false },
      },
    ],
  }
}

const annotationOption = computed<EChartsOption>(() => {
  const groups = annotationGroups.value
  const optionSeries = visibleOptionNames.value.map((option, index) => ({
    name: `Bad · ${option}`,
    type: 'bar' as const,
    stack: 'annotation',
    barMaxWidth: 44,
    itemStyle: {
      color: ['#d5535d', '#e27c55', '#d99a32', '#9a6fba', '#5879c7', '#607d8b'][
        index
      ],
    },
    data: groups.map((group) => group.options.get(option) ?? 0),
  }))
  return {
    ...baseChartOption(groups, annotationMode.value),
    color: ['#268462', '#8794a3', '#2359c4', '#d5535d'],
    series: [
      {
        name: 'Good',
        type: 'bar',
        stack: 'annotation',
        barMaxWidth: 44,
        data: groups.map((group) => group.good),
      },
      ...optionSeries,
      {
        name: 'Bad · 其他',
        type: 'bar',
        stack: 'annotation',
        barMaxWidth: 44,
        itemStyle: { color: '#8794a3' },
        data: groups.map((group) => {
          const shown = visibleOptionNames.value.reduce(
            (sum, option) => sum + (group.options.get(option) ?? 0),
            0,
          )
          return Math.max(0, group.bad - shown)
        }),
      },
      {
        name: 'Good 占比',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbolSize: 7,
        lineStyle: { width: 2 },
        data: groups.map((group) => rate(group.good, group.submitted)),
      },
      {
        name: 'Bad 占比',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbolSize: 6,
        lineStyle: { width: 1.5, type: 'dashed' },
        data: groups.map((group) => rate(group.bad, group.submitted)),
      },
    ],
  }
})

const progressOption = computed<EChartsOption>(() => {
  const groups = progressGroups.value
  return {
    ...baseChartOption(groups, progressMode.value),
    color: ['#315fc4', '#2a8b69', '#e1a33a'],
    series: [
      {
        name: '验收分配',
        type: 'bar',
        barMaxWidth: 28,
        data: groups.map((group) => group.allocated),
      },
      {
        name: '验收完成',
        type: 'bar',
        barMaxWidth: 28,
        data: groups.map((group) => group.completed),
      },
      {
        name: '完成率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbolSize: 7,
        data: groups.map((group) => rate(group.completed, group.allocated)),
      },
    ],
  }
})

const resultOption = computed<EChartsOption>(() => {
  const groups = resultGroups.value
  return {
    ...baseChartOption(groups, resultMode.value),
    color: ['#27805f', '#c64d58', '#315fc4'],
    series: [
      {
        name: '验收通过',
        type: 'bar',
        stack: 'result',
        barMaxWidth: 36,
        data: groups.map((group) => group.passed),
      },
      {
        name: '验收打回',
        type: 'bar',
        stack: 'result',
        barMaxWidth: 36,
        data: groups.map((group) => group.rejected),
      },
      {
        name: '通过率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbolSize: 7,
        data: groups.map((group) => rate(group.passed, group.completed)),
      },
    ],
  }
})
</script>

<template>
  <section class="analysis-section" aria-labelledby="analysis-title">
    <header class="analysis-header">
      <div>
        <p>细分统计</p>
        <h2 id="analysis-title">数量、构成与比率一起看</h2>
      </div>
      <span>{{ filtersSummary }}</span>
    </header>

    <article id="annotation-quality" class="analysis-panel annotation-panel">
      <header class="panel-header">
        <div>
          <h3>标注数量与质量构成</h3>
          <p>
            堆叠柱表示 Good、主要 Bad 选项与其他 Bad；折线使用右轴展示 Good / Bad 占比。
          </p>
        </div>
        <div class="mode-switch" aria-label="标注统计分组">
          <button
            type="button"
            :class="{ active: annotationMode === 'task' }"
            @click="annotationMode = 'task'"
          >
            按任务
          </button>
          <button
            type="button"
            :class="{ active: annotationMode === 'date' }"
            @click="annotationMode = 'date'"
          >
            按天趋势
          </button>
        </div>
      </header>
      <div class="annotation-layout">
        <div class="chart-body">
          <BaseEChart
            :option="annotationOption"
            aria-label="标注数量、Good Bad 构成和占比"
            @chart-click="handleChartClick(annotationMode, $event.name)"
          />
        </div>
        <aside id="bad-options" class="bad-ranking" aria-labelledby="bad-title">
          <header>
            <h4 id="bad-title">Bad 问题排行</h4>
            <span>占全部 Bad 的比例</span>
          </header>
          <ol>
            <li v-for="item in optionTotals.slice(0, 8)" :key="item.name">
              <span>{{ item.name }}</span>
              <strong>{{ item.count }}</strong>
              <small>{{ rate(item.count, totalBad) }}%</small>
            </li>
          </ol>
          <p v-if="!optionTotals.length">当前范围没有问题选项数据。</p>
        </aside>
      </div>
    </article>

    <div class="acceptance-grid">
      <article id="acceptance-progress" class="analysis-panel">
        <header class="panel-header">
          <div>
            <h3>验收分配与完成</h3>
            <p>数量使用左轴，完成率使用右轴，避免量纲互相压缩。</p>
          </div>
          <div class="mode-switch" aria-label="验收完成统计分组">
            <button
              type="button"
              :class="{ active: progressMode === 'task' }"
              @click="progressMode = 'task'"
            >
              按任务
            </button>
            <button
              type="button"
              :class="{ active: progressMode === 'date' }"
              @click="progressMode = 'date'"
            >
              按天趋势
            </button>
          </div>
        </header>
        <div class="chart-body">
          <BaseEChart
            :option="progressOption"
            aria-label="验收分配、完成与完成率"
            @chart-click="handleChartClick(progressMode, $event.name)"
          />
        </div>
      </article>

      <article id="acceptance-result" class="analysis-panel">
        <header class="panel-header">
          <div>
            <h3>验收通过与打回</h3>
            <p>通过、打回堆叠展示，通过率使用右轴。</p>
          </div>
          <div class="mode-switch" aria-label="验收结果统计分组">
            <button
              type="button"
              :class="{ active: resultMode === 'task' }"
              @click="resultMode = 'task'"
            >
              按任务
            </button>
            <button
              type="button"
              :class="{ active: resultMode === 'date' }"
              @click="resultMode = 'date'"
            >
              按天趋势
            </button>
          </div>
        </header>
        <div class="chart-body">
          <BaseEChart
            :option="resultOption"
            aria-label="验收通过、打回与通过率"
            @chart-click="handleChartClick(resultMode, $event.name)"
          />
        </div>
      </article>
    </div>

    <div v-if="!rows.length" class="empty-analysis">
      当前筛选没有可绘制的人工质检快照。
    </div>
  </section>
</template>

<style scoped>
.analysis-section {
  display: grid;
  min-width: 0;
  gap: 12px;
  scroll-margin-top: 80px;
}

.analysis-header,
.panel-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.analysis-header p,
.analysis-header h2,
.analysis-header span,
.panel-header h3,
.panel-header p,
.bad-ranking h4,
.bad-ranking p {
  margin: 0;
}

.analysis-header p {
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 750;
}

.analysis-header h2 {
  margin-top: 3px;
  font-size: 17px;
}

.analysis-header > span {
  color: var(--color-muted);
  font-size: 11px;
}

.analysis-panel {
  min-width: 0;
  overflow: hidden;
  scroll-margin-top: 80px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.panel-header {
  min-height: 66px;
  align-items: flex-start;
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-line);
}

.panel-header h3 {
  font-size: 14px;
}

.panel-header p {
  max-width: 620px;
  margin-top: 4px;
  color: var(--color-muted);
  font-size: 10px;
  line-height: 1.5;
}

.mode-switch {
  display: flex;
  flex: none;
  padding: 2px;
  border: 1px solid var(--color-line);
  border-radius: 5px;
  background: var(--color-surface-subtle);
}

.mode-switch button {
  min-height: 28px;
  padding: 4px 8px;
  border: 0;
  border-radius: 3px;
  background: transparent;
  color: var(--color-muted);
  font-size: 10px;
}

.mode-switch button.active {
  background: white;
  color: var(--color-primary);
  box-shadow: 0 1px 3px rgb(17 24 39 / 12%);
  font-weight: 700;
}

.annotation-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 0.32fr);
}

.chart-body {
  height: 330px;
  min-width: 0;
  padding: 4px 10px 10px;
}

.bad-ranking {
  min-width: 0;
  padding: 14px;
  border-left: 1px solid var(--color-line);
  background: #f8fafc;
}

.bad-ranking header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.bad-ranking h4 {
  font-size: 12px;
}

.bad-ranking header span {
  color: var(--color-muted);
  font-size: 9px;
}

.bad-ranking ol {
  display: grid;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
}

.bad-ranking li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 8px;
  align-items: center;
  padding: 8px 0;
  border-top: 1px solid var(--color-line-subtle);
}

.bad-ranking li > span {
  overflow: hidden;
  color: var(--color-ink-secondary);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bad-ranking strong,
.bad-ranking small {
  font-family: var(--font-mono);
  font-size: 10px;
}

.bad-ranking strong {
  color: var(--color-danger);
}

.bad-ranking small {
  min-width: 42px;
  color: var(--color-muted);
  text-align: right;
}

.acceptance-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.empty-analysis {
  display: grid;
  min-height: 140px;
  place-items: center;
  border: 1px dashed #b9c5d2;
  border-radius: var(--radius-md);
  color: var(--color-muted);
}

@media (max-width: 1080px) {
  .annotation-layout,
  .acceptance-grid {
    grid-template-columns: 1fr;
  }

  .bad-ranking {
    border-top: 1px solid var(--color-line);
    border-left: 0;
  }
}

@media (max-width: 680px) {
  .analysis-header,
  .panel-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .chart-body {
    height: 300px;
  }
}
</style>
