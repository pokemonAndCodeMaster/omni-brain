import { computed, onMounted, readonly, shallowRef } from 'vue'
import {
  getDashboardConfig,
  saveDashboardConfig,
} from '../api/viewConfig'
import type {
  DashboardCardLayout,
  DashboardMetricCard,
} from '../types'

export function useMetricWorkspace(
  pageKey: string,
  createDefaults: () => DashboardMetricCard[],
) {
  const cards = shallowRef<DashboardMetricCard[]>([])
  const loading = shallowRef(false)
  const saving = shallowRef(false)
  const dirty = shallowRef(false)
  const notice = shallowRef('')

  const canSave = computed(
    () => dirty.value && !loading.value && !saving.value,
  )

  function errorText(error: unknown): string {
    return error instanceof Error ? error.message : '总览卡片读取失败。'
  }

  async function load(): Promise<void> {
    loading.value = true
    notice.value = ''
    try {
      const saved = await getDashboardConfig(pageKey)
      const savedCards = (saved?.config.cards ?? []).filter(
        (card): card is DashboardMetricCard => card.kind === 'metric',
      )
      cards.value = savedCards.length ? savedCards : createDefaults()
      dirty.value = false
      if (savedCards.length) {
        notice.value = `已恢复 ${savedCards.length} 张总览卡片。`
      }
    } catch (error) {
      cards.value = createDefaults()
      notice.value = `总览恢复失败，已使用默认布局：${errorText(error)}`
    } finally {
      loading.value = false
    }
  }

  function addCard(card: DashboardMetricCard): void {
    cards.value = [...cards.value, card]
    dirty.value = true
  }

  function updateCard(card: DashboardMetricCard): void {
    cards.value = cards.value.map((current) =>
      current.id === card.id ? card : current,
    )
    dirty.value = true
  }

  function removeCard(cardId: string): void {
    cards.value = cards.value.filter((card) => card.id !== cardId)
    dirty.value = true
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

  async function save(): Promise<void> {
    if (!canSave.value) return
    saving.value = true
    notice.value = ''
    try {
      await saveDashboardConfig(pageKey, {
        schemaVersion: 'dashboard-v1',
        cards: cards.value,
      })
      dirty.value = false
      notice.value = `已保存 ${cards.value.length} 张总览卡片。`
    } catch (error) {
      notice.value = `总览保存失败：${errorText(error)}`
    } finally {
      saving.value = false
    }
  }

  onMounted(load)

  return {
    cards: readonly(cards),
    loading: readonly(loading),
    saving: readonly(saving),
    dirty: readonly(dirty),
    canSave,
    notice: readonly(notice),
    addCard,
    updateCard,
    removeCard,
    updateLayouts,
    save,
  }
}
