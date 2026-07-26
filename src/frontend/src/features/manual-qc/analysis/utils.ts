import type { AnalysisRow, TaskAnalysisRow } from './types/analysis'

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
  return rows.map((row) => ({
    id: row.key,
    project: row.dimensions.project ?? '未填写项目',
    task: row.dimensions.task ?? '未填写任务',
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
  }))
}
