import type {
  AnalysisMetricReference,
  AnalysisRow,
  TaskAnalysisLevel,
  TaskAnalysisPath,
  TaskAnalysisRow,
} from './types/analysis'

function metric(
  row: AnalysisRow,
  identifier: string,
): number | null {
  return row.measures[identifier] ?? null
}

function count(row: AnalysisRow, identifier: string): number {
  return metric(row, identifier) ?? 0
}

export function toTaskAnalysisRows(rows: AnalysisRow[]): TaskAnalysisRow[] {
  return toTaskAnalysisNodes(rows, {
    level: 'task',
    pinnedMetrics: [],
  })
}

export function metricReferenceKey(
  reference: AnalysisMetricReference,
): string {
  const questionLabel =
    reference.parameters?.questionLabel ??
    reference.parameters?.question_label
  const questionOption =
    reference.parameters?.questionOption ??
    reference.parameters?.question_option
  return questionLabel && questionOption
    ? `${reference.id}:${questionLabel}/${questionOption}`
    : reference.id
}

function nodePath(
  row: AnalysisRow,
  level: TaskAnalysisLevel,
  parent?: TaskAnalysisPath,
): TaskAnalysisPath {
  if (level === 'task') {
    return {
      project: row.dimensions.project ?? '未填写项目',
      task: row.dimensions.task ?? '未填写任务',
    }
  }
  if (!parent) throw new Error(`${level} 节点缺少父级路径`)
  if (level === 'date') {
    return { ...parent, date: row.dimensions.date ?? '' }
  }
  if (level === 'group') {
    return { ...parent, group: row.dimensions.group ?? '' }
  }
  return { ...parent, employee: row.dimensions.employee ?? '' }
}

function objectLabel(path: TaskAnalysisPath, level: TaskAnalysisLevel): string {
  return {
    task: path.task,
    date: path.date ?? '',
    group: path.group ?? '',
    employee: path.employee ?? '',
  }[level]
}

export function toTaskAnalysisNodes(
  rows: AnalysisRow[],
  context: {
    level: TaskAnalysisLevel
    parent?: TaskAnalysisPath
    pinnedMetrics: AnalysisMetricReference[]
  },
): TaskAnalysisRow[] {
  return rows.map((row) => {
    const path = nodePath(row, context.level, context.parent)
    const id = [
      `task:${path.project}:${path.task}`,
      path.date ? `date:${path.date}` : '',
      path.group ? `group:${path.group}` : '',
      path.employee ? `employee:${path.employee}` : '',
    ].filter(Boolean).join('::')
    return {
      id,
      level: context.level,
      objectLabel: objectLabel(path, context.level),
      objectType: {
        task: '标注任务',
        date: '日期',
        group: '组',
        employee: '标注员',
      }[context.level],
      project: path.project,
      task: path.task,
      statDate: path.date ?? '',
      group: path.group ?? '',
      employee: path.employee ?? '',
      path,
      annotationSubmitted: count(row, 'annotation.submitted'),
      goodRate: metric(row, 'annotation.good_rate'),
      acceptanceAllocated: count(row, 'acceptance.allocated'),
      allocationCoverageRate: metric(
        row,
        'acceptance.allocation_coverage_rate',
      ),
      acceptanceCompleted: count(row, 'acceptance.completed'),
      completionRate: metric(row, 'acceptance.completion_rate'),
      passRate: metric(row, 'acceptance.pass_rate'),
      dynamicMeasures: Object.fromEntries(
        context.pinnedMetrics.map((reference) => {
          const key = metricReferenceKey(reference)
          return [key, metric(row, key)]
        }),
      ),
      hasChildren: context.level !== 'employee',
      ...(context.level === 'employee' ? {} : { children: [] }),
    }
  })
}
