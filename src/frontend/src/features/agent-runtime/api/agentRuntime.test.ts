import { beforeEach, describe, expect, it, vi } from 'vitest'
import { http } from '@/shared/api/http'
import { getAgent, getAgentRunEvents, getAgentRuns } from './agentRuntime'

vi.mock('@/shared/api/http', () => ({
  http: {
    get: vi.fn(),
  },
}))

describe('agent runtime api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('Run 列表只使用摘要接口和显式分页筛选', async () => {
    vi.mocked(http.get).mockResolvedValue({
      data: { items: [], total: 0, limit: 30, offset: 0 },
    })

    await getAgentRuns({ statuses: ['running'], limit: 30 })

    expect(http.get).toHaveBeenCalledWith('/agent-runs', {
      params: {
        agent_id: undefined,
        status: ['running'],
        limit: 30,
        offset: 0,
      },
    })
  })

  it('Agent 详情和 Run 事件只在指定对象后读取', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: { items: [], next_sequence: 12 } })

    await getAgent('knowledge-assistant')
    await getAgentRunEvents('run-1', 12)

    expect(vi.mocked(http.get).mock.calls).toEqual([
      ['/agents/knowledge-assistant'],
      ['/agent-runs/run-1/events', { params: { after_sequence: 12, limit: 200 } }],
    ])
  })
})
