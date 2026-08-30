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
      path: '/ai/ideas',
      name: 'idea-inbox',
      component: () => import('@/features/collaboration/pages/IdeaInboxPage.vue'),
      meta: { title: '灵感', eyebrow: 'AI 协作 / Idea Inbox' },
    },
    {
      path: '/ai/ideas/:ideaId',
      name: 'idea-detail',
      component: () => import('@/features/collaboration/pages/IdeaDetailPage.vue'),
      meta: { title: 'Idea 详情', eyebrow: 'AI 协作 / 灵感' },
    },
    {
      path: '/ai/requirements',
      name: 'requirement-list',
      component: () => import('@/features/collaboration/pages/RequirementListPage.vue'),
      meta: { title: '需求', eyebrow: 'AI 协作 / Requirement Pipeline' },
    },
    {
      path: '/ai/requirements/:requirementId',
      name: 'requirement-detail',
      component: () => import('@/features/collaboration/pages/RequirementDetailPage.vue'),
      meta: { title: 'Requirement 详情', eyebrow: 'AI 协作 / 需求' },
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
  document.title = `${String(to.meta.title ?? '工作台')} - Omni-Brain`
})

export default router
