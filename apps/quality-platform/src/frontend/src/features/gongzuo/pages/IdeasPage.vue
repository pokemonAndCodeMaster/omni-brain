<script setup lang="ts">
import { computed } from 'vue'
import GongzuoIcon from '../components/GongzuoIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'

const stages = ['待整理', '讨论中', '已有后续']
const { activeWorkspace, state, openModal } = useGongzuoWorkspace()
const ideas = computed(() => state.value?.ideas ?? [])
</script>

<template>
  <PageHeader title="灵感与讨论" subtitle="记录原话，保留分歧。成熟的线索可以关联到已有事项，也可以形成新的工作。">
    <button class="gz-btn primary" type="button" @click="openModal('idea-create')"><GongzuoIcon name="plus" />记录灵感</button>
  </PageHeader>
  <div class="gz-board">
    <section v-for="stage in stages" :key="stage" class="gz-board-col">
      <div class="gz-between"><h2>{{ stage }}</h2><StatusBadge :value="String(ideas.filter((idea) => idea.state === stage).length)" /></div>
      <article v-for="idea in ideas.filter((candidate) => candidate.state === stage)" :key="idea.id" class="gz-idea-card">
        <div class="gz-inline gz-mb-10"><StatusBadge :value="idea.scope" /><span class="gz-mono gz-tiny gz-muted">{{ idea.id }}</span></div>
        <h3>{{ idea.title }}</h3><p class="gz-preline">{{ idea.body }}</p>
        <div class="gz-idea-match"><GongzuoIcon name="link" /> {{ idea.reason }}</div>
        <div class="gz-origin">{{ idea.origin }} · 原始记录保留</div>
        <div class="gz-inline">
          <RouterLink v-if="idea.related" class="gz-btn sm" :to="`/gongzuo/${activeWorkspace}/items/${encodeURIComponent(idea.related)}/overview`">查看 {{ idea.related }}</RouterLink>
          <button v-else class="gz-btn sm" type="button" @click="openModal('item-create', { idea })">形成工作事项</button>
          <button class="gz-btn ghost sm" type="button" @click="openModal('idea-discuss', { idea })">继续讨论</button>
        </div>
      </article>
      <div v-if="!ideas.some((idea) => idea.state === stage)" class="gz-empty">这里还没有灵感</div>
    </section>
  </div>
</template>
