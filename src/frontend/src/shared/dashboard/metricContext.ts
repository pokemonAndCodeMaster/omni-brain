import type { InjectionKey } from 'vue'
import type {
  DashboardMetricCard,
  DashboardMetricResult,
} from './types'

export interface MetricDashboardContext {
  cardById: (cardId: string) => DashboardMetricCard | undefined
  resultById: (cardId: string) => DashboardMetricResult | undefined
  edit: (card: DashboardMetricCard) => void
  remove: (cardId: string) => void
  jump: (card: DashboardMetricCard) => void
  nudge: (
    card: DashboardMetricCard,
    value: { dx?: number; dy?: number; dw?: number; dh?: number },
  ) => void
}

export const METRIC_DASHBOARD_CONTEXT: InjectionKey<MetricDashboardContext> =
  Symbol('metric-dashboard-context')
