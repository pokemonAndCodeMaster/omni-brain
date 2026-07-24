import type { ChartSpec } from '@/shared/analysis/types/chart'

export interface GridPosition {
  x: number
  y: number
  w: number
  h: number
}

export type DashboardCardType = 'kpi' | 'chart' | 'text' | 'table'

export interface KpiContent {
  value: string
  label: string
  helper: string
}

export interface DashboardCard {
  id: string
  title: string
  description?: string
  type: DashboardCardType
  layout: GridPosition
  system?: boolean
  kpi?: KpiContent
  chart?: ChartSpec
  text?: string
  tableRows?: Array<Record<string, string | number>>
}
