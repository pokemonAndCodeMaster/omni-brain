<script setup lang="ts">
import { computed } from 'vue'
import SnapshotDataTable from '../components/SnapshotDataTable.vue'
import SnapshotFilters from '../components/SnapshotFilters.vue'
import SnapshotSummaryChart from '../components/SnapshotSummaryChart.vue'
import { useSnapshotExplorer } from '../composables/useSnapshotExplorer'

const {
  query,
  loading,
  error,
  notice,
  sceneRows,
  tree,
  loadingKeys,
  computedAt,
  sceneOptions,
  filtersSummary,
  load,
  expand,
  resetAndLoad,
} = useSnapshotExplorer()

const freshness = computed(() => {
  if (!computedAt.value) return '尚无快照结果'
  const parsed = new Date(computedAt.value)
  if (Number.isNaN(parsed.valueOf())) return computedAt.value
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(parsed)
})
</script>

<template>
  <div class="snapshot-page">
    <section class="page-intro">
      <div>
        <p class="page-kicker">MANUAL QC · ACCEPTANCE SNAPSHOT</p>
        <h2>从交付目标下钻到员工验收结果</h2>
        <p class="page-summary">
          这是人工质检验收的首个本地纵向切片：使用固定口径快照回答任务做了多少、验了多少、
          通过与打回多少，并保留继续下钻和后续执行闭环的入口。
        </p>
      </div>
      <dl class="freshness-card">
        <div>
          <dt>数据口径</dt>
          <dd>lab-v1</dd>
        </div>
        <div>
          <dt>结果生成时间</dt>
          <dd>{{ freshness }}</dd>
        </div>
      </dl>
    </section>

    <SnapshotFilters
      v-model="query"
      :scene-options="sceneOptions"
      :loading="loading"
      @submit="load"
      @reset="resetAndLoad"
    />

    <div v-if="error" class="message error-message" role="alert">
      <strong>数据读取失败</strong>
      <span>{{ error }}</span>
    </div>
    <div v-else-if="notice" class="message notice-message" role="status">
      <strong>查询结果</strong>
      <span>{{ notice }}</span>
    </div>

    <div v-if="loading" class="loading-strip" role="status">
      <span></span>
      正在读取本地 PostgreSQL 快照…
    </div>

    <SnapshotSummaryChart
      :rows="sceneRows"
      :filters-summary="filtersSummary"
    />

    <SnapshotDataTable
      :rows="tree"
      :loading-keys="loadingKeys"
      :scene-options="sceneOptions"
      @expand="expand"
    />
  </div>
</template>

<style scoped>
.snapshot-page {
  display: grid;
  min-width: 0;
  gap: 18px;
}

.snapshot-page > * {
  min-width: 0;
}

.page-intro {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 30px;
}

.page-kicker,
.page-intro h2,
.page-summary,
.freshness-card,
.freshness-card dt,
.freshness-card dd {
  margin: 0;
}

.page-kicker {
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.page-intro h2 {
  margin-top: 7px;
  font-size: clamp(21px, 2.3vw, 30px);
  letter-spacing: -0.025em;
}

.page-summary {
  max-width: 760px;
  margin-top: 9px;
  color: var(--color-ink-secondary);
  line-height: 1.65;
}

.freshness-card {
  display: grid;
  min-width: 248px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.freshness-card div {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 12px;
  padding: 9px 12px;
}

.freshness-card div + div {
  border-top: 1px solid var(--color-line-subtle);
}

.freshness-card dt {
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 700;
}

.freshness-card dd {
  overflow: hidden;
  font-family: var(--font-mono);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  padding: 10px 13px;
  border: 1px solid;
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.notice-message {
  border-color: #c2d0e2;
  background: #f3f6fb;
  color: #455b74;
}

.error-message {
  border-color: #e9bbc0;
  background: #fff4f5;
  color: var(--color-danger);
}

.loading-strip {
  display: flex;
  gap: 8px;
  align-items: center;
  color: var(--color-primary);
  font-size: 12px;
}

.loading-strip span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentcolor;
  animation: pulse 0.9s ease-in-out infinite alternate;
}

@keyframes pulse {
  to {
    opacity: 0.25;
    transform: scale(0.75);
  }
}

@media (max-width: 880px) {
  .page-intro {
    align-items: stretch;
    flex-direction: column;
  }

  .freshness-card {
    min-width: 0;
  }
}
</style>
