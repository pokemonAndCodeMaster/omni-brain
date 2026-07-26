import { computed, onMounted, readonly, shallowRef } from 'vue'
import axios from 'axios'
import type { SnapshotQuery } from '../../types/snapshot'
import { postAnalysisQuery } from '../api/analysis'
import { toTaskAnalysisRows } from '../utils'
import type { TaskAnalysisRow } from '../types/analysis'

const SOURCE_ID = 'manual_qc.snapshot.v20260709'

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (!error.response) return '无法连接人工质检分析接口，请确认 FastAPI 已启动。'
    return `人工质检分析接口返回 ${error.response.status}。`
  }
  return error instanceof Error ? error.message : '任务汇总读取失败。'
}

export function useTaskAnalysis(pageQuery: SnapshotQuery) {
  const rows = shallowRef<TaskAnalysisRow[]>([])
  const loading = shallowRef(false)
  const error = shallowRef('')
  const computedAt = shallowRef<string | null>(null)
  const total = shallowRef(0)

  const taskNames = computed(() => rows.value.map((row) => row.task))

  function scope() {
    return {
      dateStart: pageQuery.stat_date_start || undefined,
      dateEnd: pageQuery.stat_date_end || undefined,
      projectNames: pageQuery.project_name ? [pageQuery.project_name] : [],
      taskNames: pageQuery.scene_name ? [pageQuery.scene_name] : [],
      groupNames: pageQuery.group_name ? [pageQuery.group_name] : [],
      employeeIds: pageQuery.employee_id ? [pageQuery.employee_id] : [],
    }
  }

  async function load(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const result = await postAnalysisQuery({
        sourceId: SOURCE_ID,
        scope: scope(),
        groupBy: ['project', 'task'],
        measures: [
          { id: 'annotation.submitted' },
          { id: 'annotation.good_rate' },
          { id: 'acceptance.allocated' },
          { id: 'acceptance.allocation_coverage_rate' },
          { id: 'acceptance.completed' },
          { id: 'acceptance.completion_rate' },
          { id: 'acceptance.pass_rate' },
        ],
        sort: [
          {
            target: { id: 'annotation.submitted' },
            direction: 'descending',
          },
        ],
        page: { number: 1, size: 200 },
      })
      rows.value = toTaskAnalysisRows(result.rows)
      total.value = result.total
      computedAt.value = result.computedAt
    } catch (caught) {
      rows.value = []
      total.value = 0
      computedAt.value = null
      error.value = errorMessage(caught)
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    void load()
  })

  return {
    rows: readonly(rows),
    loading: readonly(loading),
    error: readonly(error),
    computedAt: readonly(computedAt),
    total: readonly(total),
    taskNames,
    load,
  }
}
