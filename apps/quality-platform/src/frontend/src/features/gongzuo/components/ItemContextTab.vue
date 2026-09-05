<script setup lang="ts">
import GongzuoIcon from './GongzuoIcon.vue'
import StatusBadge from './StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import type { WorkItem } from '../types'

defineProps<{ item: WorkItem; rootItem: WorkItem }>()
const { openModal, decideProposal } = useGongzuoWorkspace()
</script>

<template>
  <div v-if="!rootItem.context.established" class="gz-notice warning gz-mb-18"><GongzuoIcon name="flag" /><div><strong>这个历史事项尚未建立共享上下文</strong><br />当前目标只是事项字段，不是已版本化共识。<button class="gz-btn sm gz-mt-8" type="button" @click="openModal('context-establish', { item: rootItem })">确认并建立 v1</button></div></div>
  <div v-else class="gz-notice gz-mb-18"><GongzuoIcon name="layers" /><div><strong>{{ rootItem.id }} 的持续上下文 · 当前 v{{ rootItem.context.revision }}</strong><br />人和 Agent 共同消费这些记录；各自会话只取本次需要的部分。</div></div>
  <article v-if="rootItem.context.established" class="gz-panel gz-article">
    <div class="gz-between"><h2>当前确认的理解</h2><button class="gz-btn" type="button" @click="openModal('proposal-create', { item: rootItem })"><GongzuoIcon name="edit" />提出修订</button></div>
    <div class="gz-fact-card"><div class="gz-fact-top"><h3>要解决的问题与目标</h3><StatusBadge value="当前共识" tone="green" /></div><p>{{ rootItem.context.goal }}</p><div class="gz-source-line">来源：本事项当前目标 · 版本历史保留形成依据</div></div>
    <div class="gz-fact-card"><div class="gz-fact-top"><h3>当前范围</h3><StatusBadge value="当前共识" tone="green" /></div><p>{{ rootItem.context.scope || '范围尚未说明。' }}</p></div>
    <div v-for="decision in rootItem.context.decisions" :key="decision.id ?? decision.title" class="gz-fact-card"><div class="gz-fact-top"><h3>{{ decision.title }}</h3><StatusBadge value="已确认" tone="green" /></div><p>{{ decision.body }}</p><div class="gz-between"><div class="gz-source-line">依据：{{ decision.source }}</div><button class="gz-text-btn" type="button" @click="openModal('feedback', { item: rootItem, anchor: decision.title })">就此讨论</button></div></div>
    <div class="gz-fact-card"><div class="gz-fact-top"><h3>仍然未知 / 尚未决定</h3><StatusBadge value="不伪装成事实" tone="amber" /></div><p v-for="unknown in rootItem.context.unknowns" :key="unknown" class="gz-small">{{ unknown }}</p><p v-if="!rootItem.context.unknowns.length" class="gz-small gz-muted">当前没有登记的未知项。</p></div>
  </article>
  <template v-if="rootItem.context.established">
    <div class="gz-section-title"><h2>待采纳的上下文变化</h2><StatusBadge :value="`${rootItem.context.proposals.length} 项`" tone="amber" /></div>
    <section v-for="proposal in rootItem.context.proposals" :key="proposal.id" class="gz-panel pad gz-mb-14">
      <div class="gz-between"><h3>{{ proposal.title }}</h3><StatusBadge value="候选" tone="amber" /></div>
      <div class="gz-diff-block"><div class="gz-diff-minus">− {{ proposal.old }}</div><div class="gz-diff-plus">+ {{ proposal.text }}</div></div>
      <div class="gz-source-line">{{ proposal.by }} · 根据 {{ proposal.source }}</div>
      <div class="gz-between gz-mt-14"><span class="gz-tiny gz-sub">采纳后形成 v{{ rootItem.context.revision + 1 }}，旧运行依据不会被改写。</span><div class="gz-inline"><button class="gz-btn sm" type="button" @click="decideProposal(rootItem, proposal.id, 'reject')">暂不采纳</button><button class="gz-btn primary sm" type="button" @click="decideProposal(rootItem, proposal.id, 'accept')">采纳此修改</button></div></div>
    </section>
    <div v-if="!rootItem.context.proposals.length" class="gz-panel gz-empty">没有待采纳修改。新的意见仍可继续进入讨论。</div>
  </template>
  <div class="gz-section-title"><h2>本次可引用的背景</h2></div>
  <div class="gz-panel pad">
    <div v-for="asset in rootItem.assets" :key="asset" class="gz-resource"><GongzuoIcon name="link" /><div class="gz-grow"><h3>{{ asset }}</h3><p>关联用于定位；读取和操作能力以连接状态为准。</p></div><StatusBadge value="关联" /></div>
    <div class="gz-resource"><GongzuoIcon name="history" /><div class="gz-grow"><h3>上下文版本与形成依据</h3><p>工作完成后仍保留，后续任务只引用相关部分。</p></div><button class="gz-btn sm" type="button" :disabled="!rootItem.context.established" @click="openModal('context-history', { item: rootItem })">版本历史</button></div>
  </div>
  <div class="gz-section-title"><h2>这个上下文如何被使用</h2></div>
  <div class="gz-context-map"><span>工作区 / 领域知识</span><b>→</b><span class="current">{{ rootItem.id }} · {{ rootItem.context.established ? `当前共识 v${rootItem.context.revision}` : '上下文未建立' }}</span><b>→</b><span>子工作关注点</span><b>→</b><span>一次运行的只读依据</span></div>
</template>
