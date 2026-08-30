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

const SNAPSHOT_PAGE_SIZE = 1000
const SNAPSHOT_BROWSER_LIMIT = 10_000

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
  const first = await http.get<DataResponse<SnapshotRow>>(
    '/snapshots/rows',
    { params: { ...query, limit: SNAPSHOT_PAGE_SIZE, offset: 0 } },
  )
  if (first.data.total > SNAPSHOT_BROWSER_LIMIT) {
    throw new Error(
      `当前范围命中 ${first.data.total} 行，超过浏览器端临时兼容上限 ${SNAPSHOT_BROWSER_LIMIT} 行；请缩小顶部范围。`,
    )
  }
  if (first.data.items.length >= first.data.total) return first.data

  // V1 总览和统计卡片仍在浏览器聚合快照行。这里分页取齐是规模种子的
  // 正确性兼容层；总览/图表 V2 应改用受控后端聚合后删除这段分页。
  const offsets = Array.from(
    {
      length: Math.ceil(first.data.total / SNAPSHOT_PAGE_SIZE) - 1,
    },
    (_, index) => (index + 1) * SNAPSHOT_PAGE_SIZE,
  )
  const pages = await Promise.all(
    offsets.map((offset) =>
      http.get<DataResponse<SnapshotRow>>('/snapshots/rows', {
        params: { ...query, limit: SNAPSHOT_PAGE_SIZE, offset },
      }),
    ),
  )
  const responses = [first.data, ...pages.map((response) => response.data)]
  return {
    ...first.data,
    items: responses.flatMap((response) => response.items),
    computed_at:
      responses
        .map((response) => response.computed_at)
        .filter((value): value is string => Boolean(value))
        .sort()
        .at(-1) ?? null,
  }
}
