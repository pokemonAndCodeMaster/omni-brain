import { beforeEach, describe, expect, it, vi } from 'vitest'

const { get, post } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }))
vi.mock('@/shared/api/http', () => ({ http: { get, post, request: vi.fn() } }))

import { createRun, getRunArtifactResult, getRunEvents, machineAction, runAction } from './gongzuo'

describe('gongzuo runtime API contract', () => {
  beforeEach(() => { get.mockReset(); post.mockReset() })

  it('从独立事件与固定结果端点读取真实运行数据', async () => {
    get.mockResolvedValueOnce({ data: { items: [{ sequence: 1, type: 'started' }], nextSequence: 2 } })
      .mockResolvedValueOnce({ data: 'verified output', headers: { 'x-artifact-version': 'sha256:abc' } })
    expect(await getRunEvents('personal', 'run/1')).toEqual([{ sequence: 1, type: 'started' }])
    expect(get).toHaveBeenNthCalledWith(1, '/gongzuo/personal/runs/run%2F1/events', { params: { afterSequence: 0, limit: 200 } })
    expect(await getRunArtifactResult('personal', 'run/1')).toEqual({ content: 'verified output', version: 'sha256:abc' })
  })

  it('使用最终机器状态和按当前上下文重试契约', async () => {
    post.mockResolvedValue({ data: {} })
    await machineAction('team', 'node-1', 'pause')
    expect(post).toHaveBeenCalledWith('/gongzuo/team/machines/node-1/state', { action: 'pause' })
    await runAction('team', 'run-1', 'retry')
    expect(post).toHaveBeenCalledWith('/gongzuo/team/runs/run-1/retry', { syncContext: true })
    await createRun('team', { itemId: 'item-1', instruction: '验证', engine: 'codex', runtime: 'native', model: 'gpt-5.6-luna', permission: 'workspace-write', capabilityCandidateId: 'cap-1' })
    expect(post).toHaveBeenLastCalledWith('/gongzuo/team/runs', expect.objectContaining({ model: 'gpt-5.6-luna', permission: 'workspace-write', capabilityCandidateId: 'cap-1' }))
  })
})
