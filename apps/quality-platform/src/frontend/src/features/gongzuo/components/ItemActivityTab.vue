<script setup lang="ts">
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import type { WorkItem } from '../types'

const props = defineProps<{ item: WorkItem; rootItem: WorkItem }>()
const { runs, openModal } = useGongzuoWorkspace()
const itemRuns = computed(() => runs.value.filter((run) => run.itemId === props.item.id || run.itemId === props.rootItem.id))
</script>

<template>
  <section class="gz-panel pad"><h2>推进记录</h2><p class="gz-small gz-sub">聚合有意义的变化、决定与运行；不要求所有工作经过同一套阶段。</p><div class="gz-timeline"><div v-for="activity in [...rootItem.activities].reverse()" :key="activity.id ?? `${activity.time}-${activity.title}`" class="gz-timeline-event"><time>{{ activity.time }}</time><h3>{{ activity.title }}</h3><p>{{ activity.text }}</p></div><div v-if="!rootItem.activities.length" class="gz-empty">事项已建立，等待下一动作。</div></div></section>
  <div class="gz-section-title"><h2>执行尝试与原生会话</h2></div>
  <section class="gz-panel pad"><article v-for="run in itemRuns" :key="run.id" class="gz-run-row"><div class="gz-between"><strong class="gz-mono">{{ run.id }}</strong><StatusBadge :value="run.state" /></div><p class="gz-small">{{ run.instruction || run.result || '本次委托' }}</p><div class="gz-mono gz-muted">{{ run.engine }} · {{ run.session || '会话尚未建立' }} · 上下文 v{{ run.rev }}</div><div class="gz-between gz-mt-10"><span class="gz-tiny gz-muted">{{ run.directory || '工作目录尚未分配' }}</span><button class="gz-btn sm" type="button" @click="openModal('run-detail', { runId: run.id })">查看详情</button></div></article><div v-if="!itemRuns.length" class="gz-empty">尚无运行记录。手工完成的工作也可以关联成果。</div></section>
</template>
