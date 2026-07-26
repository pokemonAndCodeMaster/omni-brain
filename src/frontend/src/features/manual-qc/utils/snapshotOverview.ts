import type { SnapshotRow } from '../types/snapshot'
import type {
  DashboardMetricCard,
  DashboardMetricId,
  DashboardMetricResult,
} from '@/shared/dashboard/types'

interface Totals {
  submitted: number
  good: number
  bad: number
  allocated: number
  completed: number
  passed: number
  rejected: number
}

function emptyTotals(): Totals {
  return {
    submitted: 0,
    good: 0,
    bad: 0,
    allocated: 0,
    completed: 0,
    passed: 0,
    rejected: 0,
  }
}

function addRow(total: Totals, row: SnapshotRow): void {
  total.submitted += row.annotation_submitted
  total.good += row.good_metrics.annotation_submitted
  total.bad += row.bad_metrics.annotation_submitted
  total.allocated +=
    row.good_metrics.actual_alloc + row.bad_metrics.actual_alloc
  total.completed +=
    row.good_metrics.actual_complete + row.bad_metrics.actual_complete
  total.passed += row.good_metrics.actual_pass + row.bad_metrics.actual_pass
  total.rejected +=
    row.good_metrics.actual_reject + row.bad_metrics.actual_reject
}

function percentage(numerator: number, denominator: number): string {
  return denominator
    ? `${((numerator / denominator) * 100).toFixed(1)}%`
    : '—'
}

function metricDetails(
  metricId: DashboardMetricId,
  total: Totals,
): {
  primaryValue: number
  primaryUnit: string
  details: Array<{ label: string; value: string }>
} {
  if (metricId === 'annotation_quality') {
    return {
      primaryValue: total.submitted,
      primaryUnit: '条标注',
      details: [
        { label: 'Good', value: String(total.good) },
        { label: 'Bad', value: String(total.bad) },
        { label: 'Good 占比', value: percentage(total.good, total.submitted) },
      ],
    }
  }
  if (metricId === 'acceptance_allocation') {
    return {
      primaryValue: total.allocated,
      primaryUnit: '条已分配',
      details: [
        { label: '标注提交', value: String(total.submitted) },
        {
          label: '分配覆盖',
          value: percentage(total.allocated, total.submitted),
        },
      ],
    }
  }
  if (metricId === 'acceptance_completion') {
    return {
      primaryValue: total.completed,
      primaryUnit: '条已完成',
      details: [
        { label: '已分配', value: String(total.allocated) },
        {
          label: '未完成',
          value: String(Math.max(0, total.allocated - total.completed)),
        },
        {
          label: '完成率',
          value: percentage(total.completed, total.allocated),
        },
      ],
    }
  }
  return {
    primaryValue: total.passed,
    primaryUnit: '条通过',
    details: [
      { label: '打回', value: String(total.rejected) },
      {
        label: '通过率',
        value: percentage(total.passed, total.completed),
      },
    ],
  }
}

export function resolveOverviewMetric(
  card: DashboardMetricCard,
  rows: SnapshotRow[],
): DashboardMetricResult {
  const total = emptyTotals()
  const byProject = new Map<string, Totals>()
  for (const row of rows) {
    addRow(total, row)
    const project = byProject.get(row.project_name) ?? emptyTotals()
    addRow(project, row)
    byProject.set(row.project_name, project)
  }
  const primary = metricDetails(card.metricId, total)
  return {
    ...primary,
    projects: [...byProject.entries()]
      .sort(([left], [right]) => left.localeCompare(right, 'zh-CN'))
      .map(([projectName, values]) => {
        const metric = metricDetails(card.metricId, values)
        return {
          projectName,
          primaryValue: metric.primaryValue,
          details: metric.details,
        }
      }),
  }
}

export function defaultOverviewCards(): DashboardMetricCard[] {
  return [
    {
      id: 'overview-annotation-quality',
      kind: 'metric',
      title: '标注产出与质量构成',
      description: '选定周期内的总标注量、Good / Bad 数量与 Good 占比',
      metricId: 'annotation_quality',
      jumpTarget: 'annotation-quality',
      style: {
        accentColor: '#2d63d7',
        backgroundColor: '#f5f8ff',
        textColor: '#16233a',
        titleSize: 15,
        valueSize: 38,
        density: 'comfortable',
        showProjectBreakdown: true,
      },
      layout: { x: 0, y: 0, w: 4, h: 4, minW: 3, minH: 3 },
    },
    {
      id: 'overview-acceptance-completion',
      kind: 'metric',
      title: '验收分配与完成',
      description: '分配、完成、未完成及完成率',
      metricId: 'acceptance_completion',
      jumpTarget: 'acceptance-progress',
      style: {
        accentColor: '#1b8a66',
        backgroundColor: '#f2fbf7',
        textColor: '#152b24',
        titleSize: 15,
        valueSize: 38,
        density: 'comfortable',
        showProjectBreakdown: true,
      },
      layout: { x: 4, y: 0, w: 4, h: 4, minW: 3, minH: 3 },
    },
    {
      id: 'overview-acceptance-result',
      kind: 'metric',
      title: '验收通过与打回',
      description: '验收完成任务中的通过量、打回量与通过率',
      metricId: 'acceptance_result',
      jumpTarget: 'acceptance-result',
      style: {
        accentColor: '#c24a56',
        backgroundColor: '#fff6f7',
        textColor: '#351b20',
        titleSize: 15,
        valueSize: 38,
        density: 'comfortable',
        showProjectBreakdown: true,
      },
      layout: { x: 8, y: 0, w: 4, h: 4, minW: 3, minH: 3 },
    },
  ]
}

export function nextOverviewCard(
  metricId: DashboardMetricId,
): DashboardMetricCard {
  const labels: Record<DashboardMetricId, string> = {
    annotation_quality: '标注产出与质量构成',
    acceptance_allocation: '验收分配',
    acceptance_completion: '验收分配与完成',
    acceptance_result: '验收通过与打回',
  }
  return {
    ...structuredClone(defaultOverviewCards()[0]!),
    id: `overview-${Date.now()}`,
    title: labels[metricId],
    metricId,
    jumpTarget:
      metricId === 'annotation_quality'
        ? 'annotation-quality'
        : metricId === 'acceptance_result'
          ? 'acceptance-result'
          : 'acceptance-progress',
    layout: { x: 0, y: 0, w: 4, h: 4, minW: 3, minH: 3 },
  }
}
