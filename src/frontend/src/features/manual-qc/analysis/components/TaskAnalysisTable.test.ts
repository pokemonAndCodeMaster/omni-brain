import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/vue'
import { afterEach, describe, expect, it } from 'vitest'
import TaskAnalysisTable from './TaskAnalysisTable.vue'
import type { TaskAnalysisRow } from '../types/analysis'

const rows: TaskAnalysisRow[] = [
  {
    id: '城区/高速::城区交互任务-A',
    project: '城区/高速',
    task: '城区交互任务-A',
    annotationSubmitted: 447,
    goodRate: 75.4,
    acceptanceAllocated: 102,
    allocationCoverageRate: 22.8,
    acceptanceCompleted: 93,
    completionRate: 91.2,
    passRate: 90.3,
  },
  {
    id: '园区::园区泊车任务-D',
    project: '园区',
    task: '园区泊车任务-D',
    annotationSubmitted: 198,
    goodRate: 62.6,
    acceptanceAllocated: 30,
    allocationCoverageRate: 15.2,
    acceptanceCompleted: 35,
    completionRate: null,
    passRate: 68.6,
  },
]

afterEach(cleanup)

describe('TaskAnalysisTable', () => {
  it('按任务展示逐步组织的标注和验收指标，不显示无意义的选择和展开列', () => {
    render(TaskAnalysisTable, {
      props: { rows, loading: false, total: 2 },
    })

    expect(screen.getByRole('heading', { name: '按标注任务比较产出与验收' })).toBeTruthy()
    expect(screen.getByText('任务信息')).toBeTruthy()
    expect(screen.getByText('标注情况')).toBeTruthy()
    expect(screen.getByText('验收进度')).toBeTruthy()
    expect(screen.getByText('验收结果')).toBeTruthy()
    expect(screen.getByText('城区交互任务-A')).toBeTruthy()
    expect(screen.queryByText('层级')).toBeNull()
    expect(screen.queryByLabelText(/选择/)).toBeNull()
  })

  it('可按 Good 占比这一业务列筛选任务', async () => {
    render(TaskAnalysisTable, {
      props: { rows, loading: false, total: 2 },
    })

    await fireEvent.click(screen.getByRole('button', { name: 'Good 占比筛选' }))
    const inputs = screen.getAllByRole('spinbutton')
    await fireEvent.update(inputs[0]!, '70')

    await waitFor(() => expect(screen.queryByText('园区泊车任务-D')).toBeNull())
    expect(screen.getByText('城区交互任务-A')).toBeTruthy()
  })
})
