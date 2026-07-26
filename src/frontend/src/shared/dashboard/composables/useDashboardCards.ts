import { shallowRef } from 'vue'
import type {
  DashboardChartCard,
  DashboardChartType,
} from '../types'

export function useDashboardCards() {
  const cards = shallowRef<DashboardChartCard[]>([])

  function addCard(card: DashboardChartCard): void {
    cards.value = [card, ...cards.value]
  }

  function removeCard(cardId: string): void {
    cards.value = cards.value.filter((card) => card.id !== cardId)
  }

  function changeChartType(
    cardId: string,
    chartType: DashboardChartType,
  ): void {
    cards.value = cards.value.map((card) =>
      card.id === cardId ? { ...card, chartType } : card,
    )
  }

  return {
    cards,
    addCard,
    removeCard,
    changeChartType,
  }
}
