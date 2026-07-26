import { describe, expect, it, vi } from 'vitest'
import { http } from '@/shared/api/http'
import { getSnapshotRows } from './snapshot'
import type { DataResponse, SnapshotRow } from '../types/snapshot'

vi.mock('@/shared/api/http', () => ({
  http: {
    get: vi.fn(),
  },
}))

function response(
  ids: number[],
  total: number,
): { data: DataResponse<SnapshotRow> } {
  return {
    data: {
      schema_version: 'snapshot-jsonb-v20260709',
      items: ids.map((id) => ({ id }) as SnapshotRow),
      total,
      computed_at: '2026-07-26T18:18:00+08:00',
    },
  }
}

describe('getSnapshotRows', () => {
  it('为旧浏览器聚合分页取齐超过 1000 行的当前数据范围', async () => {
    vi.mocked(http.get)
      .mockResolvedValueOnce(response([1, 2], 3000))
      .mockResolvedValueOnce(response([3], 3000))
      .mockResolvedValueOnce(response([4], 3000))

    const result = await getSnapshotRows({
      stat_date_start: '2026-07-13',
      stat_date_end: '2026-07-26',
    })

    expect(http.get).toHaveBeenCalledTimes(3)
    expect(vi.mocked(http.get).mock.calls.map((call) => call[1])).toEqual([
      {
        params: {
          stat_date_start: '2026-07-13',
          stat_date_end: '2026-07-26',
          limit: 1000,
          offset: 0,
        },
      },
      {
        params: {
          stat_date_start: '2026-07-13',
          stat_date_end: '2026-07-26',
          limit: 1000,
          offset: 1000,
        },
      },
      {
        params: {
          stat_date_start: '2026-07-13',
          stat_date_end: '2026-07-26',
          limit: 1000,
          offset: 2000,
        },
      },
    ])
    expect(result.items.map((item) => item.id)).toEqual([1, 2, 3, 4])
    expect(result.total).toBe(3000)
  })

  it('范围超过临时兼容上限时明确失败，不返回部分统计', async () => {
    vi.mocked(http.get).mockResolvedValueOnce(response([1], 10_001))

    await expect(getSnapshotRows({})).rejects.toThrow(
      '超过浏览器端临时兼容上限 10000 行',
    )
  })
})
