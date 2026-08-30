import { describe, expect, it } from 'vitest'
import { toTaskAnalysisRows } from './utils'
import type { AnalysisRow } from './types/analysis'

describe('任务分析结果转换', () => {
  it('把后端任务聚合映射为表格需要的明确字段，并保留空百分比', () => {
    const rows: AnalysisRow[] = [
      {
        key: '园区::园区通行任务-C',
        dimensions: { project: '园区', task: '园区通行任务-C' },
        measures: {
          'annotation.submitted': 400,
          'annotation.good_rate': 75.75,
          'acceptance.allocated': 52,
          'acceptance.allocation_coverage_rate': 13,
          'acceptance.completed': 50,
          'acceptance.completion_rate': 96.1538,
          'acceptance.pass_rate': null,
        },
        computedAt: '2026-07-26T10:00:00+08:00',
      },
    ]

    expect(toTaskAnalysisRows(rows)).toEqual([
      {
        id: 'task:园区:园区通行任务-C',
        level: 'task',
        objectLabel: '园区通行任务-C',
        objectType: '标注任务',
        project: '园区',
        task: '园区通行任务-C',
        statDate: '',
        group: '',
        employee: '',
        path: {
          project: '园区',
          task: '园区通行任务-C',
        },
        annotationSubmitted: 400,
        goodRate: 75.75,
        acceptanceAllocated: 52,
        allocationCoverageRate: 13,
        acceptanceCompleted: 50,
        completionRate: 96.1538,
        passRate: null,
        dynamicMeasures: {},
        hasChildren: true,
        children: [],
      },
    ])
  })
})
