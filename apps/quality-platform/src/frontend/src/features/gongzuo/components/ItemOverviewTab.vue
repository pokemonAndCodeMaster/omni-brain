<script setup lang="ts">
import { computed } from 'vue'
import GongzuoIcon from './GongzuoIcon.vue'
import StatusBadge from './StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import type { WorkItem } from '../types'

const props = defineProps<{ item: WorkItem; rootItem: WorkItem }>()
defineEmits<{ tab: [value: string]; feedback: [anchor: string] }>()
const { state, openModal } = useGongzuoWorkspace()
const children = computed(() => props.rootItem.id === props.item.id
  ? (state.value?.items ?? []).filter((candidate) => candidate.parentId === props.rootItem.id || candidate.relations?.some((relation) => relation.relationType === 'contributes_to' && relation.toId === props.rootItem.id))
  : [props.rootItem])
</script>

<template>
  <div v-if="item.attention" class="gz-notice warning gz-mb-17"><GongzuoIcon name="flag" /><div><strong>{{ item.context.proposals.length ? '有上下文修改等待确认' : '当前需要补充条件' }}</strong><br />{{ item.update }}</div></div>
  <article class="gz-panel gz-article">
    <h2>这次要得到什么</h2><p>{{ item.goal }}</p>
    <h3>本轮范围</h3><p>{{ item.scope }}</p>
    <h3>当前结果，而不是一个百分比</h3><blockquote>{{ item.update }}</blockquote>
    <h3>怎样判断可以接受</h3>
    <div class="gz-accept-list">
      <div v-for="evidence in item.evidence" :key="evidence.id ?? evidence.name" class="gz-accept-row" :class="{ todo: evidence.result !== '已证明' }">
        <GongzuoIcon :name="evidence.result === '已证明' ? 'check' : 'circle'" /><div><strong>{{ evidence.name }}</strong> · {{ evidence.purpose }} <StatusBadge :value="evidence.result" /></div>
      </div>
      <div v-if="!item.evidence.length" class="gz-muted gz-small">尚未登记验收要求。</div>
    </div>
    <button class="gz-btn gz-mt-20" type="button" @click="$emit('tab', 'outputs')">查看成果与证据 <GongzuoIcon name="arrow" /></button>
  </article>
  <div class="gz-section-title"><h2>{{ item.parentId ? '关联的上层结果' : '分工与贡献' }}</h2><div class="gz-inline"><StatusBadge value="责任人 ≠ AI 执行者" /><button v-if="!item.parentId" class="gz-btn sm" type="button" @click="openModal('contribution-create', { item: rootItem })"><GongzuoIcon name="plus" />创建贡献</button></div></div>
  <div class="gz-panel">
    <div v-for="related in children" :key="related.id" class="gz-list-row"><span class="gz-mono gz-muted">{{ related.id }}</span><div class="gz-grow"><strong>{{ related.title }}</strong><div class="gz-list-sub">{{ related.update }}</div></div><StatusBadge :value="related.state" /></div>
    <div v-if="!children.length" class="gz-list-row"><div class="gz-grow"><strong class="gz-small">本轮尚未拆出具体贡献</strong><div class="gz-list-sub">足够简单时可以直接推进；需要分工时创建独立负责人和结果。</div></div><span class="gz-owner"><span class="gz-avatar me">{{ item.owner.slice(-1) }}</span>{{ item.owner }}</span></div>
  </div>
</template>
