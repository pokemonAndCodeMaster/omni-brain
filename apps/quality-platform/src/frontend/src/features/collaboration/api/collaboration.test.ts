import { beforeEach, describe, expect, it, vi } from 'vitest'
import { http } from '@/shared/api/http'
import {
  getIdea,
  getIdeas,
  getIdeaTimeline,
  getRequirement,
  getRequirements,
} from './collaboration'

vi.mock('@/shared/api/http', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

describe('collaboration api progressive reads', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(http.get).mockResolvedValue({ data: { items: [], total: 0, limit: 30, offset: 0 } })
  })

  it('Idea 和 Requirement 列表只调用摘要端点', async () => {
    await getIdeas({ statuses: ['discussing'] })
    await getRequirements({ statuses: ['candidate'], commitments: ['NEXT'], query: '平台' })

    expect(vi.mocked(http.get).mock.calls).toEqual([
      ['/ideas', { params: { status: ['discussing'], limit: 30, offset: 0 } }],
      ['/requirements', {
        params: {
          status: ['candidate'],
          commitment: ['NEXT'],
          query: '平台',
          limit: 30,
          offset: 0,
        },
      }],
    ])
  })

  it('正文和时间线只在进入明确对象后读取', async () => {
    await getIdea('idea-1')
    await getIdeaTimeline('idea-1')
    await getRequirement('req-1')

    expect(vi.mocked(http.get).mock.calls).toEqual([
      ['/ideas/idea-1'],
      ['/ideas/idea-1/timeline', { params: { cursor: 0, limit: 30 } }],
      ['/requirements/req-1'],
    ])
  })
})
