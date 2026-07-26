<script setup lang="ts">
import { computed, inject } from 'vue'
import ChartCard from './ChartCard.vue'
import { DASHBOARD_CONTEXT } from '../context'

const props = defineProps<{ cardId: string }>()
const dashboard = inject(DASHBOARD_CONTEXT)
if (!dashboard) {
  throw new Error('DashboardCardHost 必须位于 DashboardGrid 内')
}

const card = computed(() => dashboard.cardById(props.cardId))
const result = computed(() => dashboard.resultById(props.cardId))
const loading = computed(() => dashboard.isLoading(props.cardId))
const error = computed(() => dashboard.errorById(props.cardId))
</script>

<template>
  <ChartCard
    v-if="card"
    :card="card"
    :result="result"
    :loading="loading"
    :error="error"
    @edit="dashboard.edit(card)"
    @duplicate="dashboard.duplicate(card)"
    @restore="dashboard.restore(card)"
    @remove="dashboard.remove(card.id)"
    @refresh="dashboard.refresh(card)"
    @drill="dashboard.drill(card, $event)"
    @nudge="dashboard.nudge(card, $event)"
  />
</template>
