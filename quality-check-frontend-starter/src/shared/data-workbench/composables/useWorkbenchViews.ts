import { ref, watch } from 'vue'
import { loadPersisted, savePersisted } from '@/shared/persistence/storage'
import type { SavedWorkbenchView, WorkbenchViewState } from '@/shared/data-workbench/types/workbench'

const SCHEMA_VERSION = 1

export function useWorkbenchViews(storageKey: string) {
  const views = ref<SavedWorkbenchView[]>(loadPersisted(storageKey, SCHEMA_VERSION, []))

  watch(
    views,
    (value) => savePersisted(storageKey, SCHEMA_VERSION, value),
    { deep: true },
  )

  function saveView(name: string, state: WorkbenchViewState, context: Record<string, string> = {}) {
    const cleanName = name.trim()
    if (!cleanName) throw new Error('视图名称不能为空')

    const existing = views.value.find((view) => view.name === cleanName)
    if (existing) {
      existing.state = structuredClone(state)
      existing.context = structuredClone(context)
      existing.savedAt = new Date().toISOString()
      return existing
    }

    const view: SavedWorkbenchView = {
      id: crypto.randomUUID(),
      name: cleanName,
      savedAt: new Date().toISOString(),
      state: structuredClone(state),
      context: structuredClone(context),
    }
    views.value.push(view)
    return view
  }

  function removeView(id: string) {
    views.value = views.value.filter((view) => view.id !== id)
  }

  return { views, saveView, removeView }
}
