<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import BaseEChart from '@/shared/analysis/components/BaseEChart.vue'
import type { SceneAggregate } from '../types/snapshot'

const props = defineProps<{ rows: SceneAggregate[]; filtersSummary: string }>()
const emit = defineEmits<{
  drillTask: [taskName: string]
  drillProject: [projectName: string]
}>()

interface TaskSummary {
  task: string
  project: string
  annotationSubmitted: number
  goodSubmitted: number
  badSubmitted: number
  allocated: number
  completed: number
  passed: number
  rejected: number
}

const tasks = computed<TaskSummary[]>(() => {
  const result = new Map<string, TaskSummary>()
  for (const row of props.rows) {
    const current = result.get(row.scene_name) ?? {
      task: row.scene_name,
      project: row.project_name,
      annotationSubmitted: 0,
      goodSubmitted: 0,
      badSubmitted: 0,
      allocated: 0,
      completed: 0,
      passed: 0,
      rejected: 0,
    }
    current.annotationSubmitted += row.annotation_submitted
    current.goodSubmitted += row.good_metrics.annotation_submitted
    current.badSubmitted += row.bad_metrics.annotation_submitted
    current.allocated +=
      row.good_metrics.actual_alloc + row.bad_metrics.actual_alloc
    current.completed +=
      row.good_metrics.actual_complete + row.bad_metrics.actual_complete
    current.passed +=
      row.good_metrics.actual_pass + row.bad_metrics.actual_pass
    current.rejected +=
      row.good_metrics.actual_reject + row.bad_metrics.actual_reject
    result.set(row.scene_name, current)
  }
  return [...result.values()].sort((left, right) =>
    left.task.localeCompare(right.task, 'zh-CN'),
  )
})

const projects = computed(() => {
  const result = new Map<
    string,
    {
      project: string
      taskCount: number
      submitted: number
      allocated: number
      completed: number
      passed: number
    }
  >()
  const taskSets = new Map<string, Set<string>>()
  for (const task of tasks.value) {
    const current = result.get(task.project) ?? {
      project: task.project,
      taskCount: 0,
      submitted: 0,
      allocated: 0,
      completed: 0,
      passed: 0,
    }
    const names = taskSets.get(task.project) ?? new Set<string>()
    names.add(task.task)
    taskSets.set(task.project, names)
    current.taskCount = names.size
    current.submitted += task.annotationSubmitted
    current.allocated += task.allocated
    current.completed += task.completed
    current.passed += task.passed
    result.set(task.project, current)
  }
  return [...result.values()].sort((left, right) =>
    left.project.localeCompare(right.project, 'zh-CN'),
  )
})

const totals = computed(() =>
  tasks.value.reduce(
    (total, task) => ({
      submitted: total.submitted + task.annotationSubmitted,
      good: total.good + task.goodSubmitted,
      bad: total.bad + task.badSubmitted,
      allocated: total.allocated + task.allocated,
      completed: total.completed + task.completed,
      passed: total.passed + task.passed,
      rejected: total.rejected + task.rejected,
    }),
    {
      submitted: 0,
      good: 0,
      bad: 0,
      allocated: 0,
      completed: 0,
      passed: 0,
      rejected: 0,
    },
  ),
)

function rate(numerator: number, denominator: number): string {
  return denominator ? `${((numerator / denominator) * 100).toFixed(1)}%` : '—'
}

const annotationOption = computed<EChartsOption>(() => ({
  animationDuration: 260,
  aria: { enabled: true },
  color: ['#2458d3', '#d18a22'],
  tooltip: { trigger: 'axis', confine: true, axisPointer: { type: 'shadow' } },
  legend: {
    bottom: 0,
    textStyle: { color: '#667789', fontSize: 10 },
  },
  grid: { top: 18, right: 16, bottom: 58, left: 50 },
  xAxis: {
    type: 'category',
    data: tasks.value.map((task) => task.task),
    axisLabel: {
      color: '#637487',
      interval: 0,
      rotate: tasks.value.length > 4 ? 24 : 0,
    },
  },
  yAxis: {
    type: 'value',
    name: '条',
    minInterval: 1,
    axisLabel: { color: '#637487' },
    splitLine: { lineStyle: { color: '#e8ecf1' } },
  },
  series: [
    {
      name: 'Good',
      type: 'bar',
      stack: 'annotation',
      barMaxWidth: 38,
      data: tasks.value.map((task) => task.goodSubmitted),
    },
    {
      name: 'Bad',
      type: 'bar',
      stack: 'annotation',
      barMaxWidth: 38,
      data: tasks.value.map((task) => task.badSubmitted),
    },
  ],
}))

const acceptanceOption = computed<EChartsOption>(() => ({
  animationDuration: 260,
  aria: { enabled: true },
  color: ['#2458d3', '#6383d5', '#15805f', '#c53b45'],
  tooltip: { trigger: 'axis', confine: true, axisPointer: { type: 'shadow' } },
  legend: {
    bottom: 0,
    textStyle: { color: '#667789', fontSize: 10 },
  },
  grid: { top: 18, right: 16, bottom: 58, left: 50 },
  xAxis: {
    type: 'category',
    data: tasks.value.map((task) => task.task),
    axisLabel: {
      color: '#637487',
      interval: 0,
      rotate: tasks.value.length > 4 ? 24 : 0,
    },
  },
  yAxis: {
    type: 'value',
    name: '条',
    minInterval: 1,
    axisLabel: { color: '#637487' },
    splitLine: { lineStyle: { color: '#e8ecf1' } },
  },
  series: [
    {
      name: '验收分配',
      type: 'bar',
      barMaxWidth: 24,
      data: tasks.value.map((task) => task.allocated),
    },
    {
      name: '验收完成',
      type: 'bar',
      barMaxWidth: 24,
      data: tasks.value.map((task) => task.completed),
    },
    {
      name: '验收通过',
      type: 'bar',
      barMaxWidth: 24,
      data: tasks.value.map((task) => task.passed),
    },
    {
      name: '验收打回',
      type: 'bar',
      barMaxWidth: 24,
      data: tasks.value.map((task) => task.rejected),
    },
  ],
}))
</script>

<template>
  <section class="overview-section" aria-labelledby="overview-title">
    <header class="overview-header">
      <div>
        <p>业务总览</p>
        <h2 id="overview-title">先看标注，再看验收</h2>
      </div>
      <span>{{ filtersSummary }}</span>
    </header>

    <div class="metric-strip">
      <article>
        <span>标注提交</span>
        <strong>{{ totals.submitted }}</strong>
        <small>Good {{ totals.good }} · Bad {{ totals.bad }}</small>
      </article>
      <article>
        <span>验收分配</span>
        <strong>{{ totals.allocated }}</strong>
        <small>覆盖已提交标注的 {{ rate(totals.allocated, totals.submitted) }}</small>
      </article>
      <article>
        <span>验收完成</span>
        <strong>{{ totals.completed }}</strong>
        <small>完成率 {{ rate(totals.completed, totals.allocated) }}</small>
      </article>
      <article>
        <span>验收结论</span>
        <strong>{{ totals.passed }} / {{ totals.rejected }}</strong>
        <small>通过 / 打回 · 通过率 {{ rate(totals.passed, totals.completed) }}</small>
      </article>
    </div>

    <div v-if="rows.length" class="overview-grid">
      <article class="chart-panel panel">
        <header>
          <div>
            <h3>标注结果分布</h3>
            <p>按标注任务比较提交量及 Good / Bad 构成。</p>
          </div>
          <span>点击任务下钻</span>
        </header>
        <div class="chart-body">
          <BaseEChart
            :option="annotationOption"
            aria-label="各标注任务的 Good 与 Bad 提交量"
            @chart-click="emit('drillTask', $event.name)"
          />
        </div>
      </article>

      <article class="chart-panel panel">
        <header>
          <div>
            <h3>验收进度与结果</h3>
            <p>按标注任务比较分配、完成、通过和打回数量。</p>
          </div>
          <span>点击任务下钻</span>
        </header>
        <div class="chart-body">
          <BaseEChart
            :option="acceptanceOption"
            aria-label="各标注任务的验收分配、完成、通过与打回"
            @chart-click="emit('drillTask', $event.name)"
          />
        </div>
      </article>
    </div>

    <div v-else class="empty-overview">
      当前筛选没有可绘制的人工质检快照。
    </div>

    <div v-if="projects.length" class="project-table panel">
      <table>
        <thead>
          <tr>
            <th scope="col">项目</th>
            <th scope="col">标注任务数</th>
            <th scope="col">标注提交</th>
            <th scope="col">验收分配</th>
            <th scope="col">验收完成</th>
            <th scope="col">完成率</th>
            <th scope="col">通过率</th>
            <th scope="col"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="project in projects" :key="project.project">
            <th scope="row">{{ project.project }}</th>
            <td>{{ project.taskCount }}</td>
            <td>{{ project.submitted }}</td>
            <td>{{ project.allocated }}</td>
            <td>{{ project.completed }}</td>
            <td>{{ rate(project.completed, project.allocated) }}</td>
            <td>{{ rate(project.passed, project.completed) }}</td>
            <td>
              <button type="button" @click="emit('drillProject', project.project)">
                查看明细
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.overview-section {
  display: grid;
  min-width: 0;
  gap: 10px;
}

.overview-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.overview-header p,
.overview-header h2,
.overview-header span,
.chart-panel h3,
.chart-panel p {
  margin: 0;
}

.overview-header p {
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 750;
}

.overview-header h2 {
  margin-top: 3px;
  font-size: 16px;
}

.overview-header > span {
  color: var(--color-muted);
  font-size: 11px;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.metric-strip article {
  display: grid;
  gap: 4px;
  padding: 13px 15px;
}

.metric-strip article + article {
  border-left: 1px solid var(--color-line);
}

.metric-strip span,
.metric-strip small {
  color: var(--color-muted);
  font-size: 10px;
}

.metric-strip strong {
  font-family: var(--font-mono);
  font-size: 20px;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.chart-panel {
  overflow: hidden;
}

.chart-panel > header {
  display: flex;
  min-height: 62px;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-line);
}

.chart-panel h3 {
  font-size: 14px;
}

.chart-panel p,
.chart-panel header > span {
  margin-top: 4px;
  color: var(--color-muted);
  font-size: 10px;
}

.chart-body {
  height: 310px;
  padding: 4px 10px 10px;
}

.project-table {
  overflow: auto;
}

.project-table table {
  width: 100%;
  border-collapse: collapse;
}

.project-table th,
.project-table td {
  padding: 9px 12px;
  border-bottom: 1px solid var(--color-line-subtle);
  text-align: right;
  white-space: nowrap;
}

.project-table th:first-child {
  text-align: left;
}

.project-table button {
  border: 0;
  background: transparent;
  color: var(--color-primary);
  font-size: 10px;
}

.empty-overview {
  display: grid;
  min-height: 160px;
  place-items: center;
  border: 1px dashed #b9c5d2;
  border-radius: var(--radius-md);
  color: var(--color-muted);
}

@media (max-width: 980px) {
  .metric-strip {
    grid-template-columns: 1fr 1fr;
  }

  .metric-strip article:nth-child(3) {
    border-top: 1px solid var(--color-line);
    border-left: 0;
  }

  .metric-strip article:nth-child(4) {
    border-top: 1px solid var(--color-line);
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .overview-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-strip {
    grid-template-columns: 1fr;
  }

  .metric-strip article + article {
    border-top: 1px solid var(--color-line);
    border-left: 0;
  }
}
</style>
