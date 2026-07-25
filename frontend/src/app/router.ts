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
      meta: { title: '人工质检 · 验收快照' },
    },
  ],
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? '人工质检')} - 质检一站式平台`
})

export default router
