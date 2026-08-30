import { readonly, shallowRef, watch, type Ref } from 'vue'
import {
  addRequirementMessage,
  createRequirementRevision,
  decideRequirement,
  getRequirement,
  getRequirementRevisions,
  getRequirementTimeline,
  startRequirementAction,
} from '../api/collaboration'
import type { AgentActionInput, RequirementContent, RequirementDecisionInput } from '../types'

export function useRequirementDetail(requirementId: Ref<string>) {
  const requirement = shallowRef<Awaited<ReturnType<typeof getRequirement>> | null>(null)
  const revisions = shallowRef<Awaited<ReturnType<typeof getRequirementRevisions>>>([])
  const timeline = shallowRef<Awaited<ReturnType<typeof getRequirementTimeline>>['items']>([])
  const loading = shallowRef(false)
  const actionPending = shallowRef(false)
  const error = shallowRef('')
  let version = 0

  async function load() {
    const id = requirementId.value
    if (!id) return
    const current = ++version
    loading.value = true
    error.value = ''
    try {
      const [detail, revisionRows, events] = await Promise.all([
        getRequirement(id),
        getRequirementRevisions(id),
        getRequirementTimeline(id),
      ])
      if (current !== version) return
      requirement.value = detail
      revisions.value = revisionRows
      timeline.value = events.items
    } catch (reason) {
      if (current === version) error.value = reason instanceof Error ? reason.message : 'Requirement 加载失败'
    } finally {
      if (current === version) loading.value = false
    }
  }

  async function saveRevision(content: RequirementContent, sourceRunId?: string) {
    await createRequirementRevision(requirementId.value, { content, source_run_id: sourceRunId })
    await load()
  }

  async function addMessage(body: string) {
    await addRequirementMessage(requirementId.value, body)
    await load()
  }

  async function startAction(input: AgentActionInput) {
    actionPending.value = true
    try {
      const run = await startRequirementAction(requirementId.value, input)
      await load()
      return run
    } finally {
      actionPending.value = false
    }
  }

  async function decide(input: RequirementDecisionInput) {
    await decideRequirement(requirementId.value, input)
    await load()
  }

  watch(requirementId, () => void load(), { immediate: true })

  return {
    requirement: readonly(requirement), revisions: readonly(revisions), timeline: readonly(timeline),
    loading: readonly(loading), actionPending: readonly(actionPending), error: readonly(error),
    load, saveRevision, addMessage, startAction, decide,
  }
}
