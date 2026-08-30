import { http } from '@/shared/api/http'
import type {
  DashboardConfig,
  DashboardConfigResponse,
} from '../types'

export async function getDashboardConfig(
  pageKey: string,
): Promise<DashboardConfigResponse | null> {
  const response = await http.get<DashboardConfigResponse | ''>(
    `/view-configs/dashboard/${encodeURIComponent(pageKey)}`,
  )
  return response.status === 204 || !response.data
    ? null
    : response.data
}

export async function saveDashboardConfig(
  pageKey: string,
  config: DashboardConfig,
): Promise<DashboardConfigResponse> {
  const response = await http.put<DashboardConfigResponse>(
    `/view-configs/dashboard/${encodeURIComponent(pageKey)}`,
    config,
  )
  return response.data
}
