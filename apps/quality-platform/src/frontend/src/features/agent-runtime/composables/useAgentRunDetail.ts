import { onUnmounted, shallowRef, watch, type Ref } from 'vue'
import {
  cancelAgentRun,
  getAgentRun,
  getAgentRunEvents,
} from '../api/agentRuntime'
import type { AgentRun, AgentRunEvent } from '../types'

const ACTIVE_STATUSES = new Set(['queued', 'running'])
const ACTIVE_REFRESH_MS = 8_000

export function useAgentRunDetail(runId: Ref<string>) {
  const run = shallowRef<AgentRun | null>(null)
  const events = shallowRef<AgentRunEvent[]>([])
  const loading = shallowRef(false)
  const cancelling = shallowRef(false)
  const error = shallowRef('')
  let nextSequence = 0
  let timer: ReturnType<typeof setTimeout> | undefined
  let requestVersion = 0

  function clearTimer() {
    if (timer !== undefined) {
      clearTimeout(timer)
      timer = undefined
    }
  }

  function scheduleRefresh(currentRun: AgentRun) {
    clearTimer()
    if (ACTIVE_STATUSES.has(currentRun.status)) {
      timer = setTimeout(() => void refresh(false), ACTIVE_REFRESH_MS)
    }
  }

  async function refresh(resetEvents = false) {
    const selectedId = runId.value
    if (!selectedId) {
      run.value = null
      events.value = []
      return
    }
    const version = ++requestVersion
    loading.value = resetEvents
    error.value = ''
    if (resetEvents) {
      nextSequence = 0
      events.value = []
    }
    try {
      const [detail, eventPage] = await Promise.all([
        getAgentRun(selectedId),
        getAgentRunEvents(selectedId, nextSequence),
      ])
      if (version !== requestVersion || selectedId !== runId.value) return
      run.value = detail
      if (eventPage.items.length) {
        events.value = [...events.value, ...eventPage.items]
      }
      nextSequence = eventPage.next_sequence
      scheduleRefresh(detail)
    } catch (reason) {
      if (version === requestVersion) {
        error.value = reason instanceof Error ? reason.message : 'Run 详情加载失败'
      }
    } finally {
      if (version === requestVersion) loading.value = false
    }
  }

  async function cancel() {
    if (!run.value) return
    cancelling.value = true
    error.value = ''
    try {
      run.value = await cancelAgentRun(run.value.id)
      await refresh(false)
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '取消 Run 失败'
    } finally {
      cancelling.value = false
    }
  }

  watch(
    runId,
    () => {
      clearTimer()
      void refresh(true)
    },
    { immediate: true },
  )

  onUnmounted(() => {
    requestVersion += 1
    clearTimer()
  })

  return { run, events, loading, cancelling, error, refresh, cancel }
}
