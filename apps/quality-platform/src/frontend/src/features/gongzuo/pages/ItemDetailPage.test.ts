import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/vue'
import { defineComponent } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { get, post } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }))
vi.mock('@/shared/api/http', () => ({ http: { get, post, request: vi.fn() } }))

import GongzuoModalHost from '../components/GongzuoModalHost.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import ItemDetailPage from './ItemDetailPage.vue'

const Harness = defineComponent({
  components: { ItemDetailPage, GongzuoModalHost },
  template: '<ItemDetailPage /><GongzuoModalHost />',
})

function fixture(id: string, parentId?: string, established = true) {
  return {
    id, title: parentId ? '解释分配缺口' : '改善验收体验', itemType: 'research', status: 'in_progress',
    payload: { parentId, goal: parentId ? '说明每个未分配原因' : '让验收人员看懂结果', scope: '只解释，不改分配规则' },
    context: established ? {
      id: 'context-' + id, currentVersionId: 'version-' + id,
      revisionNo: parentId ? 1 : 7,
      content: { goal: parentId ? '说明每个未分配原因' : '让验收人员看懂结果', scope: '只解释，不改分配规则' },
    } : null,
  }
}

async function openPage(id = 'child-1', parentEstablished = true) {
  const parent = fixture('parent-1', undefined, parentEstablished)
  const child = fixture('child-1', 'parent-1')
  const items = [parent, child]
  get.mockImplementation(async (url: string) => {
    if (url.endsWith('/state')) return { data: { items, ideas: [], topics: [], domains: [], resources: [], relations: [] } }
    if (url.endsWith('/runs') || url.endsWith('/machines')) return { data: { items: [] } }
    return { data: items.find((entry) => url.endsWith('/items/' + entry.id)) }
  })
  post.mockResolvedValue({ data: { id: 'run-1' } })
  const workspace = useGongzuoWorkspace()
  await workspace.load('personal')
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/gongzuo/:workspace/items/:itemId/:tab', component: Harness }],
  })
  await router.push('/gongzuo/personal/items/' + id + '/overview')
  await router.isReady()
  render(Harness, { global: { plugins: [router] } })
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  const workspace = useGongzuoWorkspace()
  workspace.closeModal()
  workspace.itemDetails.value = {}
  workspace.state.value = null
  workspace.runs.value = []
})
afterEach(cleanup)

describe('事项页委托', () => {
  it('子事项委托提交子标识，同时清楚展示子目标和父共同背景', async () => {
    await openPage()
    await waitFor(() => expect(screen.getByRole('button', { name: '委托 AI' })).toBeTruthy())
    await fireEvent.click(screen.getByRole('button', { name: '委托 AI' }))
    const dialog = within(screen.getByRole('dialog', { name: '委托一次工作' }))
    expect(dialog.getByText('本次事项：child-1 · 解释分配缺口')).toBeTruthy()
    expect(dialog.getByText(/目标：说明每个未分配原因/)).toBeTruthy()
    expect(dialog.getByText(/共同背景：parent-1 · v7/)).toBeTruthy()
    await fireEvent.update(dialog.getByRole('textbox', { name: '这次具体做什么' }), '检查缺口解释是否完整')
    await fireEvent.click(dialog.getByRole('button', { name: '开始委托' }))
    await waitFor(() => expect(post).toHaveBeenCalledWith('/gongzuo/personal/runs', expect.objectContaining({
      itemId: 'child-1', instruction: '检查缺口解释是否完整', engine: 'codex',
    })))
  })

  it('主事项仍委托自己并显示自己的共同背景版本', async () => {
    await openPage('parent-1')
    await waitFor(() => expect(screen.getByRole('button', { name: '委托 AI' })).toBeTruthy())
    await fireEvent.click(screen.getByRole('button', { name: '委托 AI' }))
    const dialog = within(screen.getByRole('dialog'))
    expect(dialog.getByText('本次事项：parent-1 · 改善验收体验')).toBeTruthy()
    expect(dialog.getByText(/使用共享上下文 v7/)).toBeTruthy()
    await fireEvent.click(dialog.getByRole('button', { name: '开始委托' }))
    await waitFor(() => expect(post).toHaveBeenCalledWith('/gongzuo/personal/runs', expect.objectContaining({ itemId: 'parent-1' })))
  })

  it('父共同背景缺失时，仍在父事项建立背景，不误发子事项运行', async () => {
    await openPage('child-1', false)
    await waitFor(() => expect(screen.getByRole('button', { name: '先建立上下文' })).toBeTruthy())
    await fireEvent.click(screen.getByRole('button', { name: '先建立上下文' }))
    expect(screen.getByRole('dialog', { name: '建立初始共享上下文' })).toBeTruthy()
    expect((screen.getByRole('textbox', { name: '目标' }) as HTMLTextAreaElement).value).toBe('让验收人员看懂结果')
    expect(post).not.toHaveBeenCalled()
  })
})
