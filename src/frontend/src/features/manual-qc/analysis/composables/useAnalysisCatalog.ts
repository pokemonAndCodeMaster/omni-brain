import { onMounted, readonly, shallowRef } from 'vue'
import axios from 'axios'
import { getAnalysisCatalog } from '../api/analysis'
import type { AnalysisCatalog } from '../types/analysis'

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (!error.response) return '无法读取人工质检指标目录，请确认 FastAPI 已启动。'
    return `人工质检指标目录接口返回 ${error.response.status}。`
  }
  return error instanceof Error ? error.message : '人工质检指标目录读取失败。'
}

export function useAnalysisCatalog() {
  const catalog = shallowRef<AnalysisCatalog | null>(null)
  const loading = shallowRef(false)
  const error = shallowRef('')

  async function load(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      catalog.value = await getAnalysisCatalog()
    } catch (caught) {
      catalog.value = null
      error.value = errorMessage(caught)
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    void load()
  })

  return {
    catalog: readonly(catalog),
    loading: readonly(loading),
    error: readonly(error),
    load,
  }
}
