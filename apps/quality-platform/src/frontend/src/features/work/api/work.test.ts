import { beforeEach, describe, expect, it, vi } from 'vitest'
import { http } from '@/shared/api/http'
import { createWork, getWork, getWorks, startWorkStep } from './work'

vi.mock('@/shared/api/http', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}))

describe('work api progressive reads', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(http.get).mockResolvedValue({ data: { items: [], total: 0, limit: 30, offset: 0 } })
    vi.mocked(http.post).mockResolvedValue({ data: { id: 'work-1' } })
  })

  it('列表只查询 Work 摘要，详情只在进入对象后读取', async () => {
    await getWorks({ statuses: ['in_progress'] })
    await getWork('work-1')

    expect(vi.mocked(http.get).mock.calls).toEqual([
      ['/works', { params: { status: ['in_progress'], limit: 30, offset: 0 } }],
      ['/works/work-1'],
    ])
  })

  it('从 Requirement 创建 Work，步骤重试始终走新增 Run 端点', async () => {
    await createWork('req-1')
    await startWorkStep('work-1', 'step-1', { executor: 'codex', instruction: '限定范围' })

    expect(vi.mocked(http.post).mock.calls).toEqual([
      ['/requirements/req-1/work', {}],
      ['/works/work-1/steps/step-1/runs', { executor: 'codex', instruction: '限定范围' }],
    ])
  })
})
