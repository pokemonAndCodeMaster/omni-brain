import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import TaskAnalysisTable from './TaskAnalysisTable.vue'
import type { TaskAnalysisRow } from '../types/analysis'

function taskRow(
  task: string,
  project: string,
  values: {
    submitted: number
    goodRate: number | null
    allocated: number
    completed: number
    completionRate: number | null
    passRate: number | null
  },
): TaskAnalysisRow {
  return {
    id: `task:${project}:${task}`,
    level: 'task',
    objectLabel: task,
    objectType: '标注任务',
    project,
    task,
    statDate: '',
    group: '',
    employee: '',
    path: { project, task },
    annotationSubmitted: values.submitted,
    goodRate: values.goodRate,
    acceptanceAllocated: values.allocated,
    allocationCoverageRate:
      values.submitted ? values.allocated / values.submitted * 100 : null,
    acceptanceCompleted: values.completed,
    completionRate: values.completionRate,
    passRate: values.passRate,
    dynamicMeasures: {},
    hasChildren: true,
    children: [],
  }
}

function analysisChild(
  parent: TaskAnalysisRow,
  level: TaskAnalysisRow['level'],
  objectLabel: string,
  statDate: string,
): TaskAnalysisRow {
  return {
    ...parent,
    id: `${parent.id}:${level}:${objectLabel}`,
    level,
    objectLabel,
    objectType: {
      task: '标注任务',
      date: '日期',
      group: '组',
      employee: '标注员',
    }[level],
    statDate,
    group: level === 'group' || level === 'employee' ? objectLabel : '',
    employee: level === 'employee' ? objectLabel : '',
    path: {
      ...parent.path,
      statDate: statDate || undefined,
      group: level === 'group' || level === 'employee' ? objectLabel : undefined,
      employee: level === 'employee' ? objectLabel : undefined,
    },
    children: [],
    hasChildren: level !== 'employee',
  }
}

function taskTree(): TaskAnalysisRow {
  const task = taskRow('城区交互任务-A', '城区/高速', {
    submitted: 447,
    goodRate: 75.4,
    allocated: 102,
    completed: 93,
    completionRate: 91.2,
    passRate: 90.3,
  })
  const firstDate = analysisChild(task, 'date', '2026-07-13', '2026-07-13')
  const secondDate = analysisChild(task, 'date', '2026-07-20', '2026-07-20')
  const group = analysisChild(firstDate, 'group', '质检一组', '2026-07-13')
  const employee = analysisChild(group, 'employee', '标注员-001', '2026-07-13')
  group.children = [employee]
  firstDate.children = [group]
  task.children = [firstDate, secondDate]
  return task
}

const rows: TaskAnalysisRow[] = [
  taskRow('城区交互任务-A', '城区/高速', {
    submitted: 447,
    goodRate: 75.4,
    allocated: 102,
    completed: 93,
    completionRate: 91.2,
    passRate: 90.3,
  }),
  taskRow('园区泊车任务-D', '园区', {
    submitted: 198,
    goodRate: 62.6,
    allocated: 30,
    completed: 35,
    completionRate: null,
    passRate: 68.6,
  }),
]

const baseProps = {
  rows,
  loading: false,
  total: 2,
  periodLabel: '2026-07-13 至 2026-07-26',
  pinnedMetrics: [],
  initialViewState: null,
  savingConfig: false,
  configDirty: false,
  configNotice: '',
  loadChildren: vi.fn(async () => false),
}

afterEach(cleanup)

describe('TaskAnalysisTable', () => {
  it('默认只展示任务层，并提供日期、组、标注员逐级下钻入口', () => {
    render(TaskAnalysisTable, {
      props: baseProps,
    })

    expect(
      screen.getByRole('heading', {
        name: '按标注任务定位到日期、组和标注员',
      }),
    ).toBeTruthy()
    expect(screen.getByText('任务与下钻路径')).toBeTruthy()
    expect(screen.getByText('标注情况')).toBeTruthy()
    expect(screen.getByText('验收进度')).toBeTruthy()
    expect(screen.getByText('验收结果')).toBeTruthy()
    expect(screen.getByText('城区交互任务-A')).toBeTruthy()
    expect(screen.queryByText('2026-07-13')).toBeNull()
    expect(screen.queryByLabelText(/选择/)).toBeNull()
    expect(screen.getAllByRole('button', { name: /展开/ })).toHaveLength(2)
    expect(
      screen.getByLabelText('当前显示 2 个标注任务'),
    ).toBeTruthy()
  })

  it('任务文本列同时支持输入包含筛选和精确勾选', async () => {
    render(TaskAnalysisTable, {
      props: baseProps,
    })

    await fireEvent.click(
      screen.getByRole('button', { name: '标注任务 / 下钻对象筛选' }),
    )
    expect(screen.getByRole('searchbox')).toBeTruthy()
    expect(
      screen.getByRole('checkbox', { name: '园区泊车任务-D' }),
    ).toBeTruthy()

    await fireEvent.update(screen.getByRole('searchbox'), '泊车')

    await waitFor(() => expect(screen.queryByText('城区交互任务-A')).toBeNull())
    expect(
      screen.getByRole('cell', { name: '园区泊车任务-D' }),
    ).toBeTruthy()
    expect(
      screen.getByLabelText('当前显示 1 / 2 个标注任务'),
    ).toBeTruthy()
  })

  it('精确筛选任务后仍可展开其日期下钻', async () => {
    const tree = taskTree()
    render(TaskAnalysisTable, {
      props: {
        ...baseProps,
        rows: [tree, rows[1]!],
        total: 2,
      },
    })

    await fireEvent.click(
      screen.getByRole('button', { name: '标注任务 / 下钻对象筛选' }),
    )
    await fireEvent.click(
      screen.getByRole('checkbox', { name: '城区交互任务-A' }),
    )
    await fireEvent.click(
      screen.getByRole('button', { name: `展开 ${tree.id}` }),
    )

    expect(screen.getAllByRole('cell', { name: '2026-07-13' })).toHaveLength(2)
    expect(screen.getAllByRole('cell', { name: '2026-07-20' })).toHaveLength(2)
    expect(
      screen.queryByRole('cell', { name: '园区泊车任务-D' }),
    ).toBeNull()
  })

  it('按对象类型筛选时保留上级路径，并可下钻到目标层级', async () => {
    const tree = taskTree()
    const firstDate = tree.children![0]!
    render(TaskAnalysisTable, {
      props: {
        ...baseProps,
        rows: [tree],
        total: 1,
      },
    })

    await fireEvent.click(
      screen.getByRole('button', { name: '对象类型筛选' }),
    )
    await fireEvent.click(screen.getByRole('checkbox', { name: '组' }))
    await fireEvent.click(
      screen.getByRole('button', { name: `展开 ${tree.id}` }),
    )
    await fireEvent.click(
      screen.getByRole('button', { name: `展开 ${firstDate.id}` }),
    )

    expect(screen.getByRole('cell', { name: '城区交互任务-A' })).toBeTruthy()
    expect(screen.getAllByRole('cell', { name: '2026-07-13' })).toHaveLength(3)
    expect(screen.getByRole('cell', { name: '质检一组' })).toBeTruthy()
    expect(screen.queryByText('标注员-001')).toBeNull()
  })

  it('统计日期使用时间段筛选，并在任务下只保留命中日期', async () => {
    const tree = taskTree()
    render(TaskAnalysisTable, {
      props: {
        ...baseProps,
        rows: [tree],
        total: 1,
      },
    })

    await fireEvent.click(
      screen.getByRole('button', { name: '统计日期筛选' }),
    )
    expect(screen.queryByRole('searchbox')).toBeNull()
    await fireEvent.update(screen.getByLabelText('起始日期'), '2026-07-20')
    await fireEvent.update(screen.getByLabelText('截止日期'), '2026-07-20')
    await fireEvent.click(
      screen.getByRole('button', { name: `展开 ${tree.id}` }),
    )

    expect(screen.getAllByRole('cell', { name: '2026-07-20' })).toHaveLength(2)
    expect(screen.queryByRole('cell', { name: '2026-07-13' })).toBeNull()
  })

  it('可按 Good 占比筛选，并点击业务指标打开构成详情', async () => {
    const rendered = render(TaskAnalysisTable, {
      props: baseProps,
    })

    await fireEvent.click(screen.getByRole('button', { name: 'Good 占比筛选' }))
    const inputs = screen.getAllByRole('spinbutton')
    await fireEvent.update(inputs[0]!, '70')

    await waitFor(() => expect(screen.queryByText('园区泊车任务-D')).toBeNull())
    await fireEvent.click(
      screen.getByRole('button', {
        name: '查看 城区交互任务-A Good 占比详情',
      }),
    )
    expect(rendered.emitted().openMetricDetail?.[0]?.[0]).toMatchObject({
      metricId: 'annotation.good_rate',
      row: { task: '城区交互任务-A' },
    })
  })
})
