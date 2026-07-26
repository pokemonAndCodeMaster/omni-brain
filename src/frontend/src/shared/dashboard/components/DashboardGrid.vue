<script setup lang="ts">
import ChartCard from './ChartCard.vue'
import type {
  DashboardChartCard,
  DashboardChartType,
} from '../types'

defineProps<{
  cards: DashboardChartCard[]
  canAdd?: boolean
}>()

const emit = defineEmits<{
  add: []
  remove: [cardId: string]
  chartTypeChange: [
    payload: { cardId: string; chartType: DashboardChartType },
  ]
}>()
</script>

<template>
  <section class="dashboard-section" aria-labelledby="dashboard-title">
    <header class="dashboard-header">
      <div>
        <p>01 · PERSONAL ANALYSIS BOARD</p>
        <h2 id="dashboard-title">统计卡片</h2>
        <span>把当前工作数据变成可持续观察的业务问题。</span>
      </div>
      <button
        v-if="canAdd"
        class="button primary"
        type="button"
        @click="emit('add')"
      >
        ＋ 添加图表卡片
      </button>
    </header>

    <div v-if="cards.length" class="dashboard-grid">
      <ChartCard
        v-for="card in cards"
        :key="card.id"
        :card="card"
        @remove="emit('remove', card.id)"
        @chart-type-change="
          emit('chartTypeChange', { cardId: card.id, chartType: $event })
        "
      />
    </div>
    <div v-else class="dashboard-empty">
      <strong>还没有自定义统计卡片</strong>
      <span>
        可点击“添加图表卡片”，或先在下方表格筛选数据，再一键生成卡片。
      </span>
    </div>
  </section>
</template>

<style scoped>
.dashboard-section {
  display: grid;
  min-width: 0;
  gap: 10px;
}

.dashboard-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.dashboard-header p,
.dashboard-header h2,
.dashboard-header span {
  margin: 0;
}

.dashboard-header p {
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 750;
  letter-spacing: 0.08em;
}

.dashboard-header h2 {
  margin-top: 4px;
  font-size: 15px;
}

.dashboard-header span {
  display: block;
  margin-top: 3px;
  color: var(--color-muted);
  font-size: 11px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 460px), 1fr));
  gap: 12px;
}

.dashboard-empty {
  display: grid;
  min-height: 102px;
  place-content: center;
  gap: 4px;
  padding: 18px;
  border: 1px dashed #b9c5d2;
  border-radius: var(--radius-md);
  background: rgb(255 255 255 / 55%);
  color: var(--color-muted);
  text-align: center;
}

.dashboard-empty strong {
  color: var(--color-ink-secondary);
  font-size: 12px;
}

.dashboard-empty span {
  font-size: 11px;
}
</style>
