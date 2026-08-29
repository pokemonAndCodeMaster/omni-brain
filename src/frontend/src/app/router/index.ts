import { createRouter, createWebHistory } from 'vue-router'
import SnapshotPage from '@/features/manual-qc/pages/SnapshotPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/manual-qc/snapshots' },
    {
      path: '/manual-qc/snapshots',
      name: 'manual-qc-snapshots',
      component: SnapshotPage,
      meta: { title: '人工质检 · 标注与验收快照' },
    },
    {
      path: '/ai/agents',
      name: 'agent-catalog',
      component: () => import('@/features/agent-runtime/pages/AgentCatalogPage.vue'),
      meta: { title: 'Agent 能力目录', eyebrow: 'AI 协作 / 能力目录' },
    },
    {
      path: '/ai/runs/:runId?',
      name: 'agent-runs',
      component: () => import('@/features/agent-runtime/pages/AgentRunsPage.vue'),
      meta: { title: 'Run 记录', eyebrow: 'AI 协作 / 执行记录' },
    },
  ],
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? '人工质检')} - 质检一站式平台`
})

export default router
