<script setup lang="ts">
import { computed, inject } from 'vue'
import MetricCard from './MetricCard.vue'
import { METRIC_DASHBOARD_CONTEXT } from '../metricContext'

const props = defineProps<{ cardId: string }>()
const dashboard = inject(METRIC_DASHBOARD_CONTEXT)
if (!dashboard) {
  throw new Error('MetricCardHost 必须位于 MetricCardGrid 内')
}

const card = computed(() => dashboard.cardById(props.cardId))
const result = computed(() => dashboard.resultById(props.cardId))
</script>

<template>
  <MetricCard
    v-if="card"
    :card="card"
    :result="result"
    @edit="dashboard.edit(card)"
    @duplicate="dashboard.duplicate(card)"
    @restore="dashboard.restore(card)"
    @remove="dashboard.remove(card.id)"
    @jump="dashboard.jump(card)"
    @nudge="dashboard.nudge(card, $event)"
  />
</template>
