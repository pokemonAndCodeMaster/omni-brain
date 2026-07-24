import { createRouter, createWebHistory } from 'vue-router'
export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/app/pages/DashboardPage.vue'),
      meta: { title: '业务看板' },
    },
    {
      path: '/manual-qc/deliveries',
      name: 'manual-qc-deliveries',
      component: () => import('@/features/manual-qc/pages/DeliveryWorkbenchPage.vue'),
      meta: { title: '人工质检交付中心' },
    },
  ],
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? '质检平台')} - 质检一站式平台`
})
