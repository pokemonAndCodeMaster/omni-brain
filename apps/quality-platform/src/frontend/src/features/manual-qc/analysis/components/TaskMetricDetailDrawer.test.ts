import { cleanup, fireEvent, render, screen } from '@testing-library/vue'
import { afterEach, describe, expect, it } from 'vitest'
import TaskMetricDetailDrawer from './TaskMetricDetailDrawer.vue'
import type {
  TaskAnalysisRow,
  TaskMetricDetail,
  TaskMetricDetailSelection,
} from '../types/analysis'

const row: TaskAnalysisRow = {
  id: 'task:城区/高速:拥堵跟车任务-08',
  level: 'task',
  objectLabel: '拥堵跟车任务-08',
  objectType: '标注任务',
  project: '城区/高速',
  task: '拥堵跟车任务-08',
  statDate: '',
  group: '',
  employee: '',
  path: {
    project: '城区/高速',
    task: '拥堵跟车任务-08',
  },
  annotationSubmitted: 10978,
  goodRate: 72.3,
  acceptanceAllocated: 2674,
  allocationCoverageRate: 24.4,
  acceptanceCompleted: 937,
  completionRate: 35,
  passRate: 88.8,
  dynamicMeasures: {},
  hasChildren: true,
  children: [],
}

const selection: TaskMetricDetailSelection = {
  row,
  metricId: 'acceptance.completion_rate',
}

const detail: TaskMetricDetail = {
  selection,
  summary: {
    'acceptance.allocated': 2674,
    'acceptance.completed': 937,
    'acceptance.pending': 1737,
    'acceptance.completion_rate': 35,
    'good.acceptance.completion_rate': 40.6,
    'bad.acceptance.completion_rate': 30,
  },
  trend: [
    {
      date: '2026-07-13',
      measures: { 'acceptance.completion_rate': 34.2 },
    },
  ],
  options: [
    {
      questionLabel: '驾驶行为分类',
      questionOption: 'YIELD',
      annotationSubmitted: 43,
      annotationRateOfBad: 1.2,
      allocated: 24,
      completed: 3,
      completionRate: 12.5,
      passed: 2,
      rejected: 1,
      passRate: 66.7,
    },
  ],
}

afterEach(cleanup)

describe('TaskMetricDetailDrawer', () => {
  it('展示整体、Good/Bad 和问题选项口径，并可把选项固定为列', async () => {
    const rendered = render(TaskMetricDetailDrawer, {
      props: {
        selection,
        detail,
        loading: false,
        error: '',
      },
      global: {
        stubs: {
          BaseEChart: {
            props: ['ariaLabel'],
            template: '<div role="img" :aria-label="ariaLabel"></div>',
          },
        },
      },
    })

    expect(
      screen.getByRole('heading', {
        name: '拥堵跟车任务-08 · 验收分配与完成详情',
      }),
    ).toBeTruthy()
    expect(screen.getByText('整体完成率')).toBeTruthy()
    expect(screen.getByText('Good 完成率')).toBeTruthy()
    expect(screen.getByText('Bad 完成率')).toBeTruthy()
    expect(screen.getByRole('cell', { name: 'YIELD' })).toBeTruthy()

    await fireEvent.click(
      screen.getByRole('button', {
        name: '固定 驾驶行为分类 YIELD 为表格列',
      }),
    )

    expect(rendered.emitted().pinMetric?.[0]?.[0]).toEqual({
      id: 'option.acceptance.completion_rate',
      parameters: {
        questionLabel: '驾驶行为分类',
        questionOption: 'YIELD',
      },
    })
  })
})
