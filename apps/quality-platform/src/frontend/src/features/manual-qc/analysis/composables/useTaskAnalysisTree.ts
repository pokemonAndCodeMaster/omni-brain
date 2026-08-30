import { readonly, shallowRef, watch } from 'vue'
import axios from 'axios'
import type { SnapshotQuery } from '../../types/snapshot'
import { postAnalysisQuery } from '../api/analysis'
import {
  metricReferenceKey,
  toTaskAnalysisNodes,
} from '../utils'
import type {
  AnalysisMetricReference,
  AnalysisScope,
  TaskAnalysisLevel,
  TaskAnalysisPath,
  TaskAnalysisRow,
} from '../types/analysis'

const SOURCE_ID = 'manual_qc.snapshot.v20260709'

export const TASK_TABLE_BASE_MEASURES: AnalysisMetricReference[] = [
  { id: 'annotation.submitted' },
  { id: 'annotation.good_rate' },
  { id: 'acceptance.allocated' },
  { id: 'acceptance.allocation_coverage_rate' },
  { id: 'acceptance.completed' },
  { id: 'acceptance.completion_rate' },
  { id: 'acceptance.pass_rate' },
]

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (!error.response) return '无法连接人工质检分析接口，请确认 FastAPI 已启动。'
    return `人工质检分析接口返回 ${error.response.status}。`
  }
  return error instanceof Error ? error.message : '任务明细读取失败。'
}

function nextLevel(level: TaskAnalysisLevel): TaskAnalysisLevel | null {
  return {
    task: 'date',
    date: 'group',
    group: 'employee',
    employee: null,
  }[level] as TaskAnalysisLevel | null
}

function groupBy(level: TaskAnalysisLevel): string[] {
  return level === 'task' ? ['project', 'task'] : [level]
}

function replaceChildren(
  rows: TaskAnalysisRow[],
  rowId: string,
  children: TaskAnalysisRow[],
): TaskAnalysisRow[] {
  return rows.map((row) => {
    if (row.id === rowId) return { ...row, children }
    if (!row.children?.length) return row
    return {
      ...row,
      children: replaceChildren(row.children, rowId, children),
    }
  })
}

export function useTaskAnalysisTree(pageQuery: SnapshotQuery) {
  const rows = shallowRef<TaskAnalysisRow[]>([])
  const loading = shallowRef(false)
  const error = shallowRef('')
  const computedAt = shallowRef<string | null>(null)
  const total = shallowRef(0)
  const loadingRowIds = shallowRef<Set<string>>(new Set())
  const pinnedMetrics = shallowRef<AnalysisMetricReference[]>([])
  let rootRequestId = 0

  function baseScope(): AnalysisScope {
    return {
      dateStart: pageQuery.stat_date_start || undefined,
      dateEnd: pageQuery.stat_date_end || undefined,
      projectNames: pageQuery.project_name ? [pageQuery.project_name] : [],
      taskNames: pageQuery.scene_name ? [pageQuery.scene_name] : [],
      groupNames: pageQuery.group_name ? [pageQuery.group_name] : [],
      employeeIds: pageQuery.employee_id ? [pageQuery.employee_id] : [],
    }
  }

  function pathScope(path: TaskAnalysisPath): AnalysisScope {
    const scope = baseScope()
    scope.projectNames = [path.project]
    scope.taskNames = [path.task]
    if (path.date) {
      scope.dateStart = path.date
      scope.dateEnd = path.date
    }
    if (path.group) scope.groupNames = [path.group]
    if (path.employee) scope.employeeIds = [path.employee]
    return scope
  }

  function measures(): AnalysisMetricReference[] {
    const unique = new Map<string, AnalysisMetricReference>()
    for (const reference of [
      ...TASK_TABLE_BASE_MEASURES,
      ...pinnedMetrics.value,
    ]) {
      unique.set(metricReferenceKey(reference), reference)
    }
    return [...unique.values()]
  }

  async function queryLevel(
    level: TaskAnalysisLevel,
    scope: AnalysisScope,
    parent?: TaskAnalysisPath,
  ): Promise<{
    rows: TaskAnalysisRow[]
    total: number
    computedAt: string | null
  }> {
    const result = await postAnalysisQuery({
      sourceId: SOURCE_ID,
      scope,
      groupBy: groupBy(level),
      measures: measures(),
      sort: level === 'task'
        ? [
            {
              target: { id: 'annotation.submitted' },
              direction: 'descending',
            },
          ]
        : [
            {
              target: { id: level },
              direction: 'ascending',
            },
          ],
      page: { number: 1, size: 200 },
    })
    return {
      rows: toTaskAnalysisNodes(result.rows, {
        level,
        parent,
        pinnedMetrics: pinnedMetrics.value,
      }),
      total: result.total,
      computedAt: result.computedAt,
    }
  }

  async function load(): Promise<void> {
    const requestId = ++rootRequestId
    loading.value = true
    error.value = ''
    try {
      const result = await queryLevel('task', baseScope())
      if (requestId !== rootRequestId) return
      rows.value = result.rows
      total.value = result.total
      computedAt.value = result.computedAt
    } catch (caught) {
      if (requestId !== rootRequestId) return
      rows.value = []
      total.value = 0
      computedAt.value = null
      error.value = errorMessage(caught)
    } finally {
      if (requestId === rootRequestId) loading.value = false
    }
  }

  async function loadChildren(row: TaskAnalysisRow): Promise<boolean> {
    const level = nextLevel(row.level)
    if (!level || loadingRowIds.value.has(row.id)) return false
    if (row.children?.length) return true

    loadingRowIds.value = new Set([...loadingRowIds.value, row.id])
    error.value = ''
    try {
      const result = await queryLevel(level, pathScope(row.path), row.path)
      rows.value = replaceChildren(rows.value, row.id, result.rows)
      return result.rows.length > 0
    } catch (caught) {
      error.value = `“${row.objectLabel}”下层数据读取失败：${errorMessage(caught)}`
      return false
    } finally {
      const next = new Set(loadingRowIds.value)
      next.delete(row.id)
      loadingRowIds.value = next
    }
  }

  async function setPinnedMetrics(
    references: AnalysisMetricReference[],
  ): Promise<void> {
    pinnedMetrics.value = references.slice(0, 5)
    await load()
  }

  watch(
    () => [
      pageQuery.stat_date_start,
      pageQuery.stat_date_end,
      pageQuery.project_name,
      pageQuery.scene_name,
      pageQuery.group_name,
      pageQuery.employee_id,
    ],
    () => void load(),
    { immediate: true },
  )

  return {
    rows: readonly(rows),
    loading: readonly(loading),
    error: readonly(error),
    computedAt: readonly(computedAt),
    total: readonly(total),
    pinnedMetrics: readonly(pinnedMetrics),
    loadingRowIds: readonly(loadingRowIds),
    load,
    loadChildren,
    setPinnedMetrics,
  }
}
