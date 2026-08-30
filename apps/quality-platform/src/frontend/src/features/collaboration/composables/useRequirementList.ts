import { readonly, shallowRef } from 'vue'
import { createRequirement, getRequirements } from '../api/collaboration'
import type { Commitment, RequirementContent, RequirementStatus } from '../types'

export function useRequirementList() {
  const items = shallowRef<Awaited<ReturnType<typeof getRequirements>>['items']>([])
  const total = shallowRef(0)
  const loading = shallowRef(false)
  const error = shallowRef('')
  const status = shallowRef<RequirementStatus | ''>('')
  const commitment = shallowRef<Commitment | ''>('')
  const query = shallowRef('')

  async function load() {
    loading.value = true
    error.value = ''
    try {
      const result = await getRequirements({
        statuses: status.value ? [status.value] : undefined,
        commitments: commitment.value ? [commitment.value] : undefined,
        query: query.value,
      })
      items.value = result.items
      total.value = result.total
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : 'Requirement 列表加载失败'
    } finally {
      loading.value = false
    }
  }

  async function create(input: { title: string; content: RequirementContent }) {
    const result = await createRequirement(input)
    await load()
    return result
  }

  return {
    items: readonly(items), total: readonly(total), loading: readonly(loading), error: readonly(error),
    status, commitment, query, load, create,
  }
}
