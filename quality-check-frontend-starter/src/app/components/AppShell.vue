<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()
const currentTitle = computed(() => String(route.meta.title ?? '质检一站式平台'))
</script>

<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand-block">
        <div class="brand-mark">QC</div>
        <div>
          <strong>质检一站式平台</strong>
          <small>Frontend Starter</small>
        </div>
      </div>

      <nav class="main-nav" aria-label="主导航">
        <RouterLink to="/dashboard">业务看板</RouterLink>
        <RouterLink to="/manual-qc/deliveries">人工质检 · 交付中心</RouterLink>
      </nav>

      <div class="sidebar-note">
        <strong>当前模式</strong>
        <span>Mock 数据</span>
        <small>通过 .env.development 切换真实 API</small>
      </div>
    </aside>

    <main class="app-main">
      <header class="topbar">
        <div>
          <p class="eyebrow">QUALITY CHECK PORTAL</p>
          <h1>{{ currentTitle }}</h1>
        </div>
        <div class="topbar-meta">
          <span class="status-dot"></span>
          本地开发环境
        </div>
      </header>

      <section class="page-container">
        <RouterView />
      </section>
    </main>
  </div>
</template>
