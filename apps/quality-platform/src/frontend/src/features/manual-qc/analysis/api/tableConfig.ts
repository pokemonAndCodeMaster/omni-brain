import { http } from '@/shared/api/http'
import type {
  TaskTableConfig,
  TaskTableConfigResponse,
} from '../types/analysis'

export async function getTaskTableConfig(
  pageKey: string,
): Promise<TaskTableConfigResponse | null> {
  const response = await http.get<TaskTableConfigResponse | ''>(
    `/view-configs/data-workbench/${encodeURIComponent(pageKey)}`,
  )
  return response.status === 204 || !response.data
    ? null
    : response.data
}

export async function saveTaskTableConfig(
  pageKey: string,
  config: TaskTableConfig,
): Promise<TaskTableConfigResponse> {
  const response = await http.put<TaskTableConfigResponse>(
    `/view-configs/data-workbench/${encodeURIComponent(pageKey)}`,
    config,
  )
  return response.data
}
