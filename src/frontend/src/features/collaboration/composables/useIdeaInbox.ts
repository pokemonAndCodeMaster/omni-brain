import { readonly, shallowRef } from 'vue'
import { createIdea, getIdeas } from '../api/collaboration'
import type { IdeaStatus } from '../types'

export function useIdeaInbox() {
  const items = shallowRef<Awaited<ReturnType<typeof getIdeas>>['items']>([])
  const total = shallowRef(0)
  const loading = shallowRef(false)
  const error = shallowRef('')
  const status = shallowRef<IdeaStatus | ''>('')

  async function load() {
    loading.value = true
    error.value = ''
    try {
      const result = await getIdeas({ statuses: status.value ? [status.value] : undefined })
      items.value = result.items
      total.value = result.total
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : 'Idea 列表加载失败'
    } finally {
      loading.value = false
    }
  }

  async function create(input: { title: string; raw_content: string; domain_key?: string }) {
    const result = await createIdea(input)
    await load()
    return result
  }

  return { items: readonly(items), total: readonly(total), loading: readonly(loading), error: readonly(error), status, load, create }
}
