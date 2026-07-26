import { readonly, shallowRef } from 'vue'
import axios from 'axios'
import type { WorkbenchViewState } from '@/shared/data-workbench/types'
import {
  getTaskTableConfig,
  saveTaskTableConfig,
} from '../api/tableConfig'
import type {
  AnalysisMetricReference,
  TaskTableConfig,
} from '../types/analysis'

const PAGE_KEY = 'manual-qc-task-analysis'

const defaultConfig: TaskTableConfig = {
  schemaVersion: 'manual-qc-task-table-v1',
  pinnedMetrics: [],
  columns: {
    visibility: {},
    order: [],
    sizing: {},
  },
}

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (!error.response) return '无法连接表格配置接口。'
    return `表格配置接口返回 ${error.response.status}。`
  }
  return error instanceof Error ? error.message : '表格配置操作失败。'
}

export function useTaskTableWorkspace() {
  const config = shallowRef<TaskTableConfig>(structuredClone(defaultConfig))
  const loading = shallowRef(false)
  const saving = shallowRef(false)
  const dirty = shallowRef(false)
  const notice = shallowRef('')
  const currentViewState = shallowRef<WorkbenchViewState | null>(null)

  async function load(): Promise<void> {
    loading.value = true
    notice.value = ''
    try {
      const response = await getTaskTableConfig(PAGE_KEY)
      config.value = response?.config ?? structuredClone(defaultConfig)
      dirty.value = false
    } catch (caught) {
      config.value = structuredClone(defaultConfig)
      notice.value = `${errorMessage(caught)}已使用默认表格。`
    } finally {
      loading.value = false
    }
  }

  function captureViewState(state: WorkbenchViewState): void {
    currentViewState.value = state
    dirty.value = true
  }

  function setPinnedMetrics(references: AnalysisMetricReference[]): void {
    config.value = {
      ...config.value,
      pinnedMetrics: references.slice(0, 5),
    }
    dirty.value = true
  }

  async function save(): Promise<void> {
    saving.value = true
    notice.value = ''
    try {
      const state = currentViewState.value
      const payload: TaskTableConfig = {
        ...config.value,
        columns: state
          ? {
              visibility: state.columnVisibility,
              order: state.columnOrder.filter(
                (identifier) => !identifier.startsWith('__'),
              ),
              sizing: state.columnSizing,
            }
          : config.value.columns,
      }
      const response = await saveTaskTableConfig(PAGE_KEY, payload)
      config.value = response.config
      dirty.value = false
      notice.value = '表格列配置已保存，刷新页面后仍会恢复。'
    } catch (caught) {
      notice.value = errorMessage(caught)
    } finally {
      saving.value = false
    }
  }

  return {
    config: readonly(config),
    loading: readonly(loading),
    saving: readonly(saving),
    dirty: readonly(dirty),
    notice: readonly(notice),
    load,
    save,
    captureViewState,
    setPinnedMetrics,
  }
}
