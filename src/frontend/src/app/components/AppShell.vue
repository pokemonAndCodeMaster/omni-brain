<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()
const mobileNavOpen = shallowRef(false)
const pageTitle = computed(() => String(route.meta.title ?? '质检一站式平台'))

function closeMobileNav() {
  mobileNavOpen.value = false
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ 'is-open': mobileNavOpen }">
      <div class="brand">
        <span class="brand-mark">QC</span>
        <span class="brand-copy">
          <strong>质检一站式平台</strong>
          <small>LOCAL LAB · JSONB SNAPSHOT</small>
        </span>
      </div>

      <nav class="main-nav" aria-label="主要导航">
        <p class="nav-group">人工质检</p>
        <RouterLink to="/manual-qc/snapshots" @click="closeMobileNav">
          <span class="nav-index">01</span>
          <span>验收快照</span>
        </RouterLink>
        <div class="nav-placeholder">
          <span class="nav-index">02</span>
          <span>验收操作闭环</span>
          <small>下一纵切</small>
        </div>
      </nav>

      <div class="sidebar-note">
        <span class="status-dot"></span>
        <span>仅连接本地实验数据</span>
      </div>
    </aside>

    <header class="topbar">
      <button
        class="mobile-menu"
        type="button"
        :aria-expanded="mobileNavOpen"
        aria-label="切换导航"
        @click="mobileNavOpen = !mobileNavOpen"
      >
        ☰
      </button>
      <div>
        <p class="topbar-eyebrow">人工质检 / 本地实验</p>
        <h1>{{ pageTitle }}</h1>
      </div>
      <span class="environment-badge">LOCAL · V20260709</span>
    </header>

    <main id="main-content" class="main-content">
      <RouterView />
    </main>

    <button
      v-if="mobileNavOpen"
      class="nav-backdrop"
      type="button"
      aria-label="关闭导航"
      @click="closeMobileNav"
    ></button>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  z-index: 30;
  inset: 0 auto 0 0;
  display: flex;
  width: var(--sidebar-width);
  flex-direction: column;
  border-right: 1px solid var(--color-line);
  background: var(--color-ink);
  color: white;
}

.brand {
  display: flex;
  min-height: var(--topbar-height);
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid rgb(255 255 255 / 12%);
}

.brand-mark {
  display: grid;
  width: 34px;
  height: 34px;
  flex: none;
  place-items: center;
  border: 1px solid rgb(255 255 255 / 32%);
  border-radius: 4px;
  color: #b8cbff;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 800;
}

.brand-copy {
  display: grid;
  gap: 3px;
}

.brand-copy strong {
  font-size: 14px;
  letter-spacing: 0.02em;
}

.brand-copy small {
  color: #91a1b5;
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.08em;
}

.main-nav {
  padding: 24px 12px;
}

.nav-group {
  margin: 0 10px 8px;
  color: #7f90a5;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.main-nav a,
.nav-placeholder {
  position: relative;
  display: grid;
  grid-template-columns: 26px 1fr auto;
  gap: 8px;
  align-items: center;
  min-height: 42px;
  padding: 0 12px;
  border-radius: 4px;
  color: #d9e1eb;
  text-decoration: none;
}

.main-nav a.router-link-active {
  background: rgb(64 103 202 / 28%);
  color: white;
}

.main-nav a.router-link-active::before {
  position: absolute;
  left: -12px;
  width: 3px;
  height: 24px;
  background: #7ea1ff;
  content: "";
}

.nav-index {
  color: #8090a5;
  font-family: var(--font-mono);
  font-size: 10px;
}

.nav-placeholder {
  margin-top: 3px;
  color: #7d8da1;
}

.nav-placeholder small {
  padding: 2px 5px;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 3px;
  font-size: 9px;
}

.sidebar-note {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: auto;
  padding: 18px 22px;
  color: #91a1b5;
  font-size: 11px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #4fc89a;
  box-shadow: 0 0 0 3px rgb(79 200 154 / 12%);
}

.topbar {
  position: fixed;
  z-index: 20;
  inset: 0 0 auto var(--sidebar-width);
  display: flex;
  height: var(--topbar-height);
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  border-bottom: 1px solid var(--color-line);
  background: rgb(255 255 255 / 96%);
  backdrop-filter: blur(10px);
}

.topbar h1,
.topbar-eyebrow {
  margin: 0;
}

.topbar h1 {
  margin-top: 2px;
  font-size: 18px;
  letter-spacing: -0.01em;
}

.topbar-eyebrow {
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.environment-badge {
  padding: 5px 8px;
  border: 1px solid #bdd7ce;
  border-radius: 3px;
  background: #edf8f3;
  color: var(--color-success);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
}

.main-content {
  width: calc(100% - var(--sidebar-width));
  min-width: 0;
  min-height: 100vh;
  margin-left: var(--sidebar-width);
  padding: calc(var(--topbar-height) + 26px) 28px 40px;
}

.mobile-menu,
.nav-backdrop {
  display: none;
}

@media (max-width: 900px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 180ms ease;
  }

  .sidebar.is-open {
    transform: translateX(0);
  }

  .topbar {
    left: 0;
    padding: 0 18px;
  }

  .main-content {
    width: 100%;
    margin-left: 0;
    padding-inline: 16px;
  }

  .mobile-menu {
    display: inline-grid;
    width: 36px;
    height: 36px;
    place-items: center;
    border: 1px solid var(--color-line);
    border-radius: 4px;
    background: white;
  }

  .topbar {
    justify-content: flex-start;
    gap: 12px;
  }

  .environment-badge {
    margin-left: auto;
  }

  .nav-backdrop {
    position: fixed;
    z-index: 25;
    inset: 0;
    display: block;
    border: 0;
    background: rgb(23 32 43 / 35%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar {
    transition: none;
  }
}
</style>
