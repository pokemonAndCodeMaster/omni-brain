import { render, screen } from '@testing-library/vue'
import { describe, expect, it, vi } from 'vitest'

const load = vi.fn()

vi.mock('../composables/useAgentCatalog', async () => {
  const { shallowRef } = await import('vue')
  return {
    useAgentCatalog: () => ({
      agents: shallowRef([
        {
          id: 'knowledge-assistant',
          name: '知识问答 Agent',
          category: '知识管理',
          description: '从正式知识入口回答问题。',
          state: 'verified',
          default_executor: 'codex',
          supported_executors: ['codex', 'opencode'],
          revision_short: 'abc1234',
          run_counts: { total: 8, active: 1, succeeded: 6, failed: 1 },
        },
      ]),
      health: shallowRef({
        executors: [
          {
            name: 'codex',
            available: true,
            command: '/usr/bin/codex',
            version: 'codex-cli 0.144.1',
            reason: null,
            details: {},
          },
          {
            name: 'opencode',
            available: true,
            command: '/usr/bin/opencode',
            version: '1.18.10',
            reason: null,
            details: {},
          },
        ],
      }),
      loading: shallowRef(false),
      error: shallowRef(''),
      load,
    }),
  }
})

vi.mock('../api/agentRuntime', () => ({
  createAgentRun: vi.fn(),
  getAgent: vi.fn(),
}))

vi.mock('vue-router', async () => {
  const actual = await vi.importActual<typeof import('vue-router')>('vue-router')
  return {
    ...actual,
    useRouter: () => ({ push: vi.fn() }),
  }
})

import AgentCatalogPage from './AgentCatalogPage.vue'

describe('AgentCatalogPage', () => {
  it('首屏只展示注册摘要、双执行器状态和 Run 计数', async () => {
    render(AgentCatalogPage, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    expect(await screen.findByText('知识问答 Agent')).toBeTruthy()
    expect(screen.getByText('codex-cli 0.144.1')).toBeTruthy()
    expect(screen.getByText('1.18.10')).toBeTruthy()
    expect(screen.getByText('codex 默认 · codex / opencode')).toBeTruthy()
    expect(screen.getByText('8')).toBeTruthy()
    expect(screen.getByText('6')).toBeTruthy()
    expect(load).toHaveBeenCalledOnce()
  })
})
