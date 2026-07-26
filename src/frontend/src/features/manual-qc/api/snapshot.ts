import { http } from '@/shared/api/http'
import type {
  DataResponse,
  EmployeeAggregate,
  GroupAggregate,
  SceneAggregate,
  SnapshotQuery,
} from '../types/snapshot'

export async function getSceneAggregate(
  query: SnapshotQuery,
): Promise<DataResponse<SceneAggregate>> {
  const response = await http.get<DataResponse<SceneAggregate>>(
    '/snapshots/aggregate/scene',
    { params: query },
  )
  return response.data
}

export async function getGroupAggregate(
  query: SnapshotQuery & { scene_name: string },
): Promise<DataResponse<GroupAggregate>> {
  const response = await http.get<DataResponse<GroupAggregate>>(
    '/snapshots/aggregate/group',
    { params: query },
  )
  return response.data
}

export async function getEmployeeAggregate(
  query: SnapshotQuery & { scene_name: string; group_name: string },
): Promise<DataResponse<EmployeeAggregate>> {
  const response = await http.get<DataResponse<EmployeeAggregate>>(
    '/snapshots/aggregate/employee',
    { params: query },
  )
  return response.data
}
