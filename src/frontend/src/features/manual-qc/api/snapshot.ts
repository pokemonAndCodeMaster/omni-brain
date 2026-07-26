import { http } from '@/shared/api/http'
import type {
  DataResponse,
  EmployeeAggregate,
  GroupAggregate,
  ProjectAggregate,
  SceneAggregate,
  SnapshotRow,
  SnapshotQuery,
} from '../types/snapshot'

export async function getProjectAggregate(
  query: SnapshotQuery,
): Promise<DataResponse<ProjectAggregate>> {
  const response = await http.get<DataResponse<ProjectAggregate>>(
    '/snapshots/aggregate/project',
    { params: query },
  )
  return response.data
}

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

export async function getSnapshotRows(
  query: SnapshotQuery,
): Promise<DataResponse<SnapshotRow>> {
  const response = await http.get<DataResponse<SnapshotRow>>(
    '/snapshots/rows',
    { params: { ...query, limit: 1000 } },
  )
  return response.data
}
