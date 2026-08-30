import { computed, onBeforeUnmount, readonly, shallowRef, watch, type Ref } from 'vue'
import {
  completeWorkStep,
  decideWork,
  getWork,
  recordWorkEvidence,
  startWorkStep,
  updateWork,
} from '../api/work'
import type { WorkEvidenceInput, WorkStepRunInput, WorkUpdateInput } from '../types'

export function useWorkDetail(workId: Ref<string>) {
  const work = shallowRef<Awaited<ReturnType<typeof getWork>> | null>(null)
  const loading = shallowRef(false)
  const acting = shallowRef(false)
  const error = shallowRef('')
  let version = 0
  let timer: number | undefined

  const hasActiveRun = computed(() =>
    work.value?.plan.steps.some((step) => step.runs.some((run) => ['queued', 'running'].includes(run.status))) ?? false,
  )

  function schedule() {
    window.clearTimeout(timer)
    if (hasActiveRun.value) timer = window.setTimeout(() => void load(true), 2500)
  }

  async function load(background = false) {
    const id = workId.value
    if (!id) return
    const current = ++version
    if (!background) loading.value = true
    if (!background) error.value = ''
    try {
      const detail = await getWork(id)
      if (current === version) work.value = detail
    } catch (reason) {
      if (current === version) error.value = reason instanceof Error ? reason.message : 'Work 加载失败'
    } finally {
      if (current === version) {
        loading.value = false
        schedule()
      }
    }
  }

  async function act(action: () => Promise<unknown>) {
    acting.value = true
    error.value = ''
    try {
      const result = await action()
      await load()
      return result
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '操作失败'
      throw reason
    } finally {
      acting.value = false
    }
  }

  function startStep(stepId: string, input: WorkStepRunInput) {
    return act(() => startWorkStep(workId.value, stepId, input))
  }

  function saveMetadata(input: WorkUpdateInput) {
    return act(() => updateWork(workId.value, input))
  }

  function completeStep(stepId: string, note: string) {
    return act(() => completeWorkStep(workId.value, stepId, note))
  }

  function saveEvidence(input: WorkEvidenceInput) {
    return act(() => recordWorkEvidence(workId.value, input))
  }

  function decide(decisionType: 'accept' | 'request_changes', reason: string) {
    return act(() => decideWork(workId.value, { decision_type: decisionType, reason }))
  }

  watch(workId, () => void load(), { immediate: true })
  watch(hasActiveRun, schedule)
  onBeforeUnmount(() => window.clearTimeout(timer))

  return {
    work: readonly(work),
    loading: readonly(loading),
    acting: readonly(acting),
    error: readonly(error),
    hasActiveRun,
    load,
    saveMetadata,
    startStep,
    completeStep,
    saveEvidence,
    decide,
  }
}
