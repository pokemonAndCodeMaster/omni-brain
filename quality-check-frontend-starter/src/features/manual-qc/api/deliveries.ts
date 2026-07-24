import { http } from '@/shared/api/http'
import { mockDeliveries } from '@/features/manual-qc/mocks/deliveries'
import type { DeliveryQuery, DeliveryRow, DeliveryUpdate } from '@/features/manual-qc/types/delivery'

const useMock = import.meta.env.VITE_USE_MOCK !== 'false'

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

export async function getDeliveries(_query?: Partial<DeliveryQuery>): Promise<DeliveryRow[]> {
  if (useMock) {
    await delay(250)
    return structuredClone(mockDeliveries)
  }

  const response = await http.get<DeliveryRow[]>('/manual-qc/deliveries', {
    params: _query,
  })
  return response.data
}

export async function updateDeliveryCell(update: DeliveryUpdate): Promise<DeliveryUpdate> {
  if (useMock) {
    await delay(180)
    return update
  }

  const response = await http.patch<DeliveryUpdate>(`/manual-qc/deliveries/${update.id}`, {
    [update.field]: update.value,
  })
  return response.data
}
