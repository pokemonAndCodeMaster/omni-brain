import { readonly, shallowRef, watch, type Ref } from 'vue'
import {
  addIdeaMessage,
  archiveIdea,
  convertIdeaToRequirement,
  getIdea,
  getIdeaTimeline,
  startIdeaAction,
} from '../api/collaboration'
import type { AgentActionInput, RequirementContent } from '../types'

export function useIdeaDetail(ideaId: Ref<string>) {
  const idea = shallowRef<Awaited<ReturnType<typeof getIdea>> | null>(null)
  const timeline = shallowRef<Awaited<ReturnType<typeof getIdeaTimeline>>['items']>([])
  const loading = shallowRef(false)
  const actionPending = shallowRef(false)
  const error = shallowRef('')
  let version = 0

  async function load() {
    const id = ideaId.value
    if (!id) return
    const current = ++version
    loading.value = true
    error.value = ''
    try {
      const [detail, events] = await Promise.all([getIdea(id), getIdeaTimeline(id)])
      if (current !== version) return
      idea.value = detail
      timeline.value = events.items
    } catch (reason) {
      if (current === version) error.value = reason instanceof Error ? reason.message : 'Idea 加载失败'
    } finally {
      if (current === version) loading.value = false
    }
  }

  async function addMessage(body: string) {
    await addIdeaMessage(ideaId.value, body)
    await load()
  }

  async function startAction(input: AgentActionInput) {
    actionPending.value = true
    try {
      const run = await startIdeaAction(ideaId.value, input)
      await load()
      return run
    } finally {
      actionPending.value = false
    }
  }

  async function convert(input: { title: string; content: RequirementContent; source_run_id?: string }) {
    const result = await convertIdeaToRequirement(ideaId.value, input)
    await load()
    return result
  }

  async function archive() {
    idea.value = await archiveIdea(ideaId.value)
    await load()
  }

  watch(ideaId, () => void load(), { immediate: true })

  return {
    idea: readonly(idea),
    timeline: readonly(timeline),
    loading: readonly(loading),
    actionPending: readonly(actionPending),
    error: readonly(error),
    load,
    addMessage,
    startAction,
    convert,
    archive,
  }
}
