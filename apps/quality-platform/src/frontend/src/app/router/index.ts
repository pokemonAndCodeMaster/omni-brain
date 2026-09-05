import { createRouter, createWebHistory } from 'vue-router'
import SnapshotPage from '@/features/manual-qc/pages/SnapshotPage.vue'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition ?? { top: 0 }
  },
  routes: [
    { path: '/', redirect: '/gongzuo/personal/home' },
    { path: '/gongzuo', redirect: '/gongzuo/personal/home' },
    { path: '/gongzuo/:workspace(personal|team)/home', name: 'home', component: () => import('@/features/gongzuo/pages/HomePage.vue'), meta: { gongzuo: true, title: '我的工作' } },
    { path: '/gongzuo/:workspace(personal|team)/items', name: 'items', component: () => import('@/features/gongzuo/pages/ItemsPage.vue'), meta: { gongzuo: true, title: '工作事项' } },
    { path: '/gongzuo/:workspace(personal|team)/ideas', name: 'ideas', component: () => import('@/features/gongzuo/pages/IdeasPage.vue'), meta: { gongzuo: true, title: '灵感与讨论' } },
    { path: '/gongzuo/:workspace(personal|team)/knowledge', name: 'knowledge', component: () => import('@/features/gongzuo/pages/KnowledgePage.vue'), meta: { gongzuo: true, title: '知识' } },
    { path: '/gongzuo/:workspace(personal|team)/meeting', name: 'meeting', component: () => import('@/features/gongzuo/pages/MeetingPage.vue'), meta: { gongzuo: true, title: '组会 / 回顾' } },
    { path: '/gongzuo/:workspace(personal|team)/maintenance', name: 'maintenance', component: () => import('@/features/gongzuo/pages/MaintenancePage.vue'), meta: { gongzuo: true, title: '维护中心' } },
    { path: '/gongzuo/:workspace(personal|team)/items/:itemId/:tab(overview|context|outputs|activity|retro)?', name: 'item-detail', component: () => import('@/features/gongzuo/pages/ItemDetailPage.vue'), meta: { gongzuo: true, title: '事项' } },
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
      path: '/ai/works',
      name: 'work-list',
      component: () => import('@/features/work/pages/WorkListPage.vue'),
      meta: { title: 'Work', eyebrow: 'AI 协作 / 交付控制' },
    },
    {
      path: '/ai/works/:workId',
      name: 'work-detail',
      component: () => import('@/features/work/pages/WorkDetailPage.vue'),
      meta: { title: 'Work 详情', eyebrow: 'AI 协作 / 交付控制' },
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
