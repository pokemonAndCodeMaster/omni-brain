import type { InjectionKey } from 'vue'
import type {
  DashboardChartCard,
  DashboardChartResult,
} from './types'

export interface DashboardContext {
  cardById: (cardId: string) => DashboardChartCard | undefined
  resultById: (cardId: string) => DashboardChartResult | undefined
  isLoading: (cardId: string) => boolean
  errorById: (cardId: string) => string
  edit: (card: DashboardChartCard) => void
  remove: (cardId: string) => void
  refresh: (card: DashboardChartCard) => void
  drill: (card: DashboardChartCard, category: string) => void
  nudge: (
    card: DashboardChartCard,
    value: { dx?: number; dy?: number; dw?: number; dh?: number },
  ) => void
}

export const DASHBOARD_CONTEXT: InjectionKey<DashboardContext> =
  Symbol('dashboard-context')
