import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/vue'
import { createColumnHelper } from '@tanstack/vue-table'
import { afterEach, describe, expect, it, vi } from 'vitest'

import DataWorkbench from './DataWorkbench.vue'
import { numberRangeFilter } from '../types'

interface TestRow {
  id: string
  name: string
  group: string
  statDate: string
  hasChildren?: boolean
  children?: TestRow[]
}

const helper = createColumnHelper<TestRow>()
const columns = [
  helper.accessor('name', {
    header: '名称',
    size: 160,
  }),
  helper.accessor('group', {
    header: '组别',
    size: 130,
    meta: { filter: { type: 'text' as const } },
  }),
  helper.accessor('statDate', {
    header: '日期',
    size: 130,
    meta: { filter: { type: 'date-range' as const } },
  }),
]

const groupedColumns = [
  helper.group({
    id: 'identity',
    header: '对象信息',
    columns: [
      helper.accessor('name', {
        header: '名称',
        size: 160,
      }),
      helper.accessor('group', {
        header: '组别',
        size: 130,
      }),
    ],
  }),
  helper.group({
    id: 'time',
    header: '时间信息',
    columns: [
      helper.accessor('statDate', {
        header: '日期',
        size: 130,
      }),
    ],
  }),
]

const baseRows: TestRow[] = [
  {
    id: 'parent-a',
    name: '场景 A',
    group: '一组',
    statDate: '2026-07-25',
    hasChildren: true,
    children: [],
  },
  {
    id: 'parent-b',
    name: '场景 B',
    group: '二组',
    statDate: '2026-07-26',
    hasChildren: false,
  },
]

afterEach(cleanup)

describe('DataWorkbench', () => {
  it('数值范围筛选支持仅上限、仅下限和闭区间', () => {
    const row = { getValue: () => 78.5 }
    expect(numberRangeFilter(row as never, 'rate', '\u000080')).toBe(true)
    expect(numberRangeFilter(row as never, 'rate', '79\u0000')).toBe(false)
    expect(numberRangeFilter(row as never, 'rate', '70\u000080')).toBe(true)
  })

  it('只渲染一个可横向滚动的表格视口', () => {
    const { container } = render(DataWorkbench<TestRow>, {
      props: {
        rows: baseRows,
        columns,
        canExpand: (row) => Boolean(row.hasChildren),
      },
    })

    expect(container.querySelectorAll('[data-testid="table-scroll"]')).toHaveLength(1)
    expect(container.querySelectorAll('.scroll-mirror')).toHaveLength(0)
  })

  it('用真实列跨度表达分组表头与子列的对应关系', () => {
    render(DataWorkbench<TestRow>, {
      props: {
        rows: baseRows,
        columns: groupedColumns,
        enableRowSelection: false,
        showExpandColumn: false,
      },
    })

    const identityHeader = screen.getByRole('columnheader', {
      name: '对象信息',
    })
    const timeHeader = screen.getByRole('columnheader', {
      name: '时间信息',
    })
    expect(identityHeader.getAttribute('colspan')).toBe('2')
    expect(identityHeader.getAttribute('scope')).toBe('colgroup')
    expect(timeHeader.getAttribute('colspan')).toBe('1')
    expect(timeHeader.getAttribute('scope')).toBe('colgroup')
  })

  it('单列拖动只改变目标叶子列宽，不把其他列同步拉宽', async () => {
    const { container } = render(DataWorkbench<TestRow>, {
      props: {
        rows: baseRows,
        columns,
        enableRowSelection: false,
        showExpandColumn: false,
      },
    })

    const columnElements = [...container.querySelectorAll('col')]
    const resizers = [...container.querySelectorAll<HTMLElement>('.column-resizer')]
    expect(columnElements.map((column) => column.getAttribute('style'))).toEqual([
      'width: 160px;',
      'width: 130px;',
      'width: 130px;',
    ])

    await fireEvent.mouseDown(resizers[0]!, { clientX: 160 })
    await fireEvent.mouseMove(document, { clientX: 210 })
    await fireEvent.mouseUp(document, { clientX: 210 })

    await waitFor(() => {
      expect(columnElements[0]?.getAttribute('style')).toBe('width: 210px;')
    })
    expect(columnElements.slice(1).map((column) => column.getAttribute('style'))).toEqual([
      'width: 130px;',
      'width: 130px;',
    ])
  })

  it('懒加载完成前不把加号切成减号，完成后再展开子行', async () => {
    let finishLoad: (() => void) | undefined
    const waiting = new Promise<void>((resolve) => {
      finishLoad = resolve
    })
    let rerender: ReturnType<typeof render>['rerender']
    const loadChildren = vi.fn(async () => {
      await waiting
      await rerender({
        rows: [
          {
            ...baseRows[0]!,
            children: [
              {
                id: 'child-a',
                name: '一组明细',
                group: '一组',
                statDate: '2026-07-25',
                hasChildren: false,
              },
            ],
          },
          baseRows[1]!,
        ],
        columns,
        canExpand: (row: TestRow) => Boolean(row.hasChildren),
        loadChildren,
      })
      return true
    })

    const result = render(DataWorkbench<TestRow>, {
      props: {
        rows: baseRows,
        columns,
        canExpand: (row) => Boolean(row.hasChildren),
        loadChildren,
      },
    })
    rerender = result.rerender

    await fireEvent.click(screen.getByRole('button', { name: '展开 parent-a' }))
    expect(
      screen.getByRole('button', { name: '正在加载 parent-a' }).textContent,
    ).toBe('…')
    expect(screen.queryByText('一组明细')).toBeNull()

    finishLoad?.()
    await waitFor(() => expect(screen.getByText('一组明细')).toBeTruthy())
    expect(
      screen.getByRole('button', { name: '折叠 parent-a' }).textContent,
    ).toBe('−')
  })

  it('子行加载失败时保持折叠状态', async () => {
    const loadChildren = vi.fn(async () => false)
    render(DataWorkbench<TestRow>, {
      props: {
        rows: baseRows,
        columns,
        canExpand: (row) => Boolean(row.hasChildren),
        loadChildren,
      },
    })

    await fireEvent.click(screen.getByRole('button', { name: '展开 parent-a' }))
    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: '展开 parent-a' }).textContent,
      ).toBe('+')
    })
  })

  it('在表头中按字段类型展示筛选入口并立即过滤当前行', async () => {
    render(DataWorkbench<TestRow>, {
      props: {
        rows: baseRows,
        columns,
        canExpand: (row) => Boolean(row.hasChildren),
      },
    })

    expect(screen.getByRole('button', { name: '组别筛选' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '日期筛选' })).toBeTruthy()

    await fireEvent.click(screen.getByRole('button', { name: '组别筛选' }))
    const dialog = screen.getByRole('dialog', { name: '组别筛选条件' })
    expect(dialog.parentElement).toBe(document.body)
    await fireEvent.update(screen.getByRole('searchbox'), '二组')

    await waitFor(() => expect(screen.queryByText('场景 A')).toBeNull())
    expect(screen.getByText('场景 B')).toBeTruthy()
    expect(screen.getByRole('button', { name: '组别（已筛选）筛选' })).toBeTruthy()
  })

  it('只把当前表格筛选结果交给统计卡片动作', async () => {
    const result = render(DataWorkbench<TestRow>, {
      props: {
        rows: baseRows,
        columns,
        canExpand: (row) => Boolean(row.hasChildren),
        enableAnalysis: true,
      },
    })

    await fireEvent.click(screen.getByRole('button', { name: '组别筛选' }))
    await fireEvent.update(screen.getByRole('searchbox'), '二组')
    await waitFor(() => expect(screen.queryByText('场景 A')).toBeNull())
    await fireEvent.click(
      screen.getByRole('button', { name: /生成统计卡片/ }),
    )

    const event = result.emitted().createChart?.[0]?.[0] as {
      rows: TestRow[]
      filterSummary: string
    }
    expect(event.rows.map((row) => row.id)).toEqual(['parent-b'])
    expect(event.filterSummary).toBe('组别=二组')
  })

  it('明确把表头条件交给全页筛选动作', async () => {
    const result = render(DataWorkbench<TestRow>, {
      props: {
        rows: baseRows,
        columns,
        canExpand: (row) => Boolean(row.hasChildren),
        enableAnalysis: true,
      },
    })

    await fireEvent.click(screen.getByRole('button', { name: '组别筛选' }))
    await fireEvent.update(screen.getByRole('searchbox'), '二组')
    await fireEvent.click(screen.getByRole('button', { name: '应用到全页' }))

    const event = result.emitted().applyFilters?.[0]?.[0] as {
      rows: TestRow[]
      filterSummary: string
    }
    expect(event.rows.map((row) => row.id)).toEqual(['parent-b'])
    expect(event.filterSummary).toBe('组别=二组')
  })
})
