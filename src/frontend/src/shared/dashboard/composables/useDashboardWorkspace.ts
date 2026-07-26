import {
  computed,
  onMounted,
  readonly,
  shallowRef,
} from 'vue'
import {
  getDashboardConfig,
  saveDashboardConfig,
} from '../api/viewConfig'
import type {
  DashboardCardLayout,
  DashboardCardResolver,
  DashboardChartCard,
  DashboardChartResult,
} from '../types'

export function useDashboardWorkspace(
  pageKey: string,
  resolveCard: DashboardCardResolver,
) {
  const cards = shallowRef<DashboardChartCard[]>([])
  const results = shallowRef<Record<string, DashboardChartResult>>({})
  const loadingCardIds = shallowRef<Set<string>>(new Set())
  const cardErrors = shallowRef<Record<string, string>>({})
  const loading = shallowRef(false)
  const saving = shallowRef(false)
  const dirty = shallowRef(false)
  const notice = shallowRef('')
  const version = shallowRef<number | null>(null)
  const updatedAt = shallowRef<string | null>(null)

  const canSave = computed(
    () => dirty.value && !loading.value && !saving.value,
  )

  function errorText(error: unknown): string {
    return error instanceof Error ? error.message : '统计卡片读取失败。'
  }

  async function refreshCard(card: DashboardChartCard): Promise<void> {
    loadingCardIds.value = new Set([...loadingCardIds.value, card.id])
    const nextErrors = { ...cardErrors.value }
    delete nextErrors[card.id]
    cardErrors.value = nextErrors
    try {
      const result = await resolveCard(card)
      results.value = { ...results.value, [card.id]: result }
    } catch (error) {
      cardErrors.value = {
        ...cardErrors.value,
        [card.id]: errorText(error),
      }
    } finally {
      const next = new Set(loadingCardIds.value)
      next.delete(card.id)
      loadingCardIds.value = next
    }
  }

  async function refreshAll(): Promise<void> {
    await Promise.all(cards.value.map(refreshCard))
  }

  async function load(): Promise<void> {
    loading.value = true
    notice.value = ''
    try {
      const saved = await getDashboardConfig(pageKey)
      cards.value = saved?.config.cards ?? []
      version.value = saved?.version ?? null
      updatedAt.value = saved?.updatedAt ?? null
      dirty.value = false
      if (cards.value.length) {
        await refreshAll()
        notice.value = `已恢复 ${cards.value.length} 张已保存卡片。`
      }
    } catch (error) {
      notice.value = `看板恢复失败：${errorText(error)}`
    } finally {
      loading.value = false
    }
  }

  function addCard(card: DashboardChartCard): void {
    cards.value = [card, ...cards.value]
    dirty.value = true
    void refreshCard(card)
  }

  function updateCard(card: DashboardChartCard): void {
    cards.value = cards.value.map((current) =>
      current.id === card.id ? card : current,
    )
    dirty.value = true
    void refreshCard(card)
  }

  function updateLayouts(
    layouts: Record<string, DashboardCardLayout>,
  ): void {
    let changed = false
    cards.value = cards.value.map((card) => {
      const layout = layouts[card.id]
      if (!layout) return card
      const same = Object.entries(layout).every(
        ([key, value]) =>
          card.layout[key as keyof DashboardCardLayout] === value,
      )
      if (same) return card
      changed = true
      return { ...card, layout }
    })
    if (changed) dirty.value = true
  }

  function removeCard(cardId: string): void {
    cards.value = cards.value.filter((card) => card.id !== cardId)
    const nextResults = { ...results.value }
    const nextErrors = { ...cardErrors.value }
    delete nextResults[cardId]
    delete nextErrors[cardId]
    results.value = nextResults
    cardErrors.value = nextErrors
    dirty.value = true
  }

  async function save(): Promise<void> {
    if (!canSave.value) return
    saving.value = true
    notice.value = ''
    try {
      const saved = await saveDashboardConfig(pageKey, {
        schemaVersion: 'dashboard-v1',
        cards: cards.value,
      })
      version.value = saved.version
      updatedAt.value = saved.updatedAt
      dirty.value = false
      notice.value = `已保存 ${cards.value.length} 张卡片；下次打开页面会自动恢复。`
    } catch (error) {
      notice.value = `保存失败：${errorText(error)}`
    } finally {
      saving.value = false
    }
  }

  onMounted(load)

  return {
    cards: readonly(cards),
    results: readonly(results),
    loadingCardIds: readonly(loadingCardIds),
    cardErrors: readonly(cardErrors),
    loading: readonly(loading),
    saving: readonly(saving),
    dirty: readonly(dirty),
    canSave,
    notice: readonly(notice),
    version: readonly(version),
    updatedAt: readonly(updatedAt),
    addCard,
    updateCard,
    updateLayouts,
    removeCard,
    refreshCard,
    refreshAll,
    save,
  }
}
