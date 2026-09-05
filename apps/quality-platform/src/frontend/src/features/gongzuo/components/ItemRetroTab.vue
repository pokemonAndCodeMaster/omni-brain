<script setup lang="ts">
import GongzuoIcon from './GongzuoIcon.vue'
import StatusBadge from './StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import type { WorkItem } from '../types'

defineProps<{ item: WorkItem; rootItem: WorkItem }>()
const { openModal } = useGongzuoWorkspace()
</script>

<template>
  <div class="gz-notice gz-mb-18"><GongzuoIcon name="refresh" /><div><strong>复盘让这次工作，改变下一次的做法。</strong><br />只有有复用价值且经过验证的部分，才进入知识、Skill 或 Harness。</div></div>
  <article class="gz-panel gz-article"><h2>从本次工作中提取什么</h2><h3>可复用经验</h3><p>把真实工作里反复出现的问题、有效方法和适用边界保留下来。</p><h3>需要改进的做法</h3><p>记录是哪一段能力导致问题，以及用什么案例证明修改有用。</p><div class="gz-inline"><button class="gz-btn primary" type="button" @click="openModal('improvement-create', { item: rootItem })">形成改进候选</button><button class="gz-btn" type="button" @click="openModal('feedback', { item: rootItem, anchor: '复盘' })">保留复盘记录</button></div></article>
  <div class="gz-section-title"><h2>本事项的能力改进候选</h2></div>
  <article v-for="improvement in rootItem.improvements" :key="improvement.id" class="gz-retro-row"><div class="gz-between"><div class="gz-inline"><StatusBadge :value="improvement.kind" /><span class="gz-mono gz-tiny gz-muted">来自 {{ rootItem.id }}</span></div><StatusBadge :value="improvement.state" /></div><h3>{{ improvement.title }}</h3><p>{{ improvement.body }}</p><div class="gz-tiny gz-muted">目标：{{ improvement.target }} · {{ improvement.version }}</div><div class="gz-step-chips"><span class="on">来源问题</span><b>→</b><span class="on">改进候选</span><b>→</b><span :class="{ on: improvement.checks }">回归验证</span><b>→</b><span :class="{ on: improvement.state === '已发布' }">受审发布</span></div><button class="gz-btn sm" type="button" @click="openModal('improvement-detail', { improvement, item: rootItem })">查看改进与验证</button></article>
  <div v-if="!rootItem.improvements.length" class="gz-panel gz-empty">还没有候选。不要求每件小事都进行完整复盘。</div>
</template>
