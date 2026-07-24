export type DeliveryStatus = '待对齐' | '生产中' | '标注中' | '验收中' | '风险' | '已完成'
export type DeliveryPriority = 'P0' | 'P1' | 'P2'

export interface DeliveryRow {
  id: string
  name: string
  project: string
  scene: string
  owner: string
  status: DeliveryStatus
  priority: DeliveryPriority
  targetCount: number
  completedCount: number
  goodRate: number
  updatedAt: string
  children?: DeliveryRow[]
}

export interface DeliveryQuery {
  keyword: string
  project: string
  status: string
}

export interface DeliveryUpdate {
  id: string
  field: keyof Pick<DeliveryRow, 'owner' | 'priority' | 'targetCount' | 'status'>
  value: string | number
}
