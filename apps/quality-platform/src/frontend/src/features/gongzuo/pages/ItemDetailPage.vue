<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GongzuoIcon from '../components/GongzuoIcon.vue'
import ItemActivityTab from '../components/ItemActivityTab.vue'
import ItemContextTab from '../components/ItemContextTab.vue'
import ItemOutputsTab from '../components/ItemOutputsTab.vue'
import ItemOverviewTab from '../components/ItemOverviewTab.vue'
import ItemRetroTab from '../components/ItemRetroTab.vue'
import LoadingState from '../components/LoadingState.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import type { ItemTab } from '../types'

const route = useRoute()
const router = useRouter()
const { activeWorkspace, loading, error, itemDetails, rootOf, loadItem, runs, openModal } = useGongzuoWorkspace()
const itemId = computed(() => String(route.params.itemId ?? ''))
const item = computed(() => itemDetails.value[itemId.value])
const rootItem = computed(() => item.value ? rootOf(item.value) : undefined)
const tab = computed(() => (['overview', 'context', 'outputs', 'activity', 'retro'].includes(String(route.params.tab)) ? route.params.tab : 'overview') as ItemTab)
const tabs: Array<{ key: ItemTab; label: string }> = [
  { key: 'overview', label: '概览' }, { key: 'context', label: '共享上下文' }, { key: 'outputs', label: '成果与验证' }, { key: 'activity', label: '推进记录' }, { key: 'retro', label: '复盘与成长' },
]
const itemRuns = computed(() => runs.value.filter((run) => run.itemId === item.value?.id || run.itemId === rootItem.value?.id))

async function loadDetail(id: string) {
  const detail = await loadItem(id)
  if (detail?.parentId && !itemDetails.value[detail.parentId]) await loadItem(detail.parentId, true)
}

function setTab(value: string) {
  router.push(`/gongzuo/${activeWorkspace.value}/items/${encodeURIComponent(itemId.value)}/${value}`)
}

function delegateCurrentItem() {
  if (!item.value || !rootItem.value) return
  if (rootItem.value.context.established) openModal('delegate', { item: item.value })
  else openModal('context-establish', { item: rootItem.value })
}

watch(itemId, (id) => { if (id) void loadDetail(id) }, { immediate: true })
</script>

<template>
  <LoadingState v-if="!item" :loading="loading" :error="error?.message" empty="找不到这个事项。" @retry="loadDetail(itemId)" />
  <template v-else-if="rootItem">
    <PageHeader :title="item.title" :subtitle="item.goal" :eyebrow="`${item.id} / ${item.kind}`">
      <button class="gz-btn primary" type="button" @click="delegateCurrentItem"><GongzuoIcon :name="rootItem.context.established ? 'spark' : 'layers'" />{{ rootItem.context.established ? '委托 AI' : '先建立上下文' }}</button>
      <button class="gz-btn" type="button" @click="openModal('discussion', { item: rootItem })"><GongzuoIcon name="message" />就地讨论</button>
    </PageHeader>
    <div class="gz-detail-meta"><StatusBadge :value="item.state" /><span class="gz-owner"><span class="gz-avatar" :class="{ me: item.owner === '我' }">{{ item.owner.slice(-1) }}</span>{{ item.owner }}</span><span>责任人</span><span>·</span><span>目标 {{ item.due || '未安排' }}</span><StatusBadge v-for="domain in item.domains" :key="domain" :value="domain" /><StatusBadge :value="`上下文 v${rootItem.context.revision}`" tone="blue" /><StatusBadge v-if="item.parentId" :value="`继承 ${rootItem.id} 的共同背景`" tone="purple" /><span class="gz-spacer"></span><button class="gz-btn ghost sm" type="button" @click="openModal('relations', { item })">编辑关系</button></div>
    <div class="gz-tabs">
      <button v-for="entry in tabs" :key="entry.key" class="gz-tab" :class="{ active: tab === entry.key }" type="button" @click="setTab(entry.key)">{{ entry.label }}<StatusBadge v-if="entry.key === 'context' && rootItem.context.proposals.length" :value="String(rootItem.context.proposals.length)" tone="amber" /></button>
    </div>
    <div class="gz-detail-layout">
      <section class="gz-detail-main" aria-label="事项内容">
        <ItemOverviewTab v-if="tab === 'overview'" :item="item" :root-item="rootItem" @tab="setTab" @feedback="openModal('feedback', { item, anchor: $event })" />
        <ItemContextTab v-else-if="tab === 'context'" :item="item" :root-item="rootItem" />
        <ItemOutputsTab v-else-if="tab === 'outputs'" :item="item" />
        <ItemActivityTab v-else-if="tab === 'activity'" :item="item" :root-item="rootItem" />
        <ItemRetroTab v-else :item="item" :root-item="rootItem" />
      </section>
      <aside class="gz-detail-aside">
        <section class="gz-panel pad">
          <div class="gz-between"><h2>工作关系</h2><button class="gz-btn ghost icon-only" type="button" aria-label="编辑工作关系" @click="openModal('relations', { item })"><GongzuoIcon name="edit" /></button></div>
          <div class="gz-prop"><span>协调责任</span><div>{{ item.owner }}</div></div><div class="gz-prop"><span>参与者</span><div>{{ item.participants.join('、') || '未登记' }}</div></div><div class="gz-prop"><span>关联专题</span><div class="gz-chips"><StatusBadge v-for="topic in item.topics" :key="topic" :value="topic" /><span v-if="!item.topics.length" class="gz-muted">不要求关联</span></div></div><div class="gz-prop"><span>所属领域</span><div>{{ item.domains.join('、') || '未登记' }}</div></div><div class="gz-prop"><span>影响资产</span><div>{{ item.assets.join('、') || '未登记' }}</div></div>
          <div class="gz-link-capability">关系用于定位与汇总；同步与外部操作以连接能力为准。</div>
        </section>
        <section class="gz-panel pad"><h2>本事项的运行</h2><div v-for="run in itemRuns" :key="run.id" class="gz-note-card"><div class="gz-between"><span class="gz-mono">{{ run.id }}</span><StatusBadge :value="run.state" /></div><p>{{ run.instruction || run.result || '本次委托' }}</p><div class="gz-tiny gz-muted">{{ run.engine }} · {{ run.machine || '等待分配' }}<br />使用上下文 v{{ run.rev }}<span v-if="run.staleContext"> · 有新共识待决定</span></div><button class="gz-text-btn gz-mt-8" type="button" @click="openModal('run-detail', { runId: run.id })">查看运行与环境</button></div><p v-if="!itemRuns.length" class="gz-small gz-muted">尚未启动运行。记录与讨论不要求创建容器。</p></section>
        <section class="gz-panel pad"><h2>这不是一个共享聊天窗口</h2><p class="gz-small gz-sub">不同人和 Agent 使用自己的会话，共享当前确认的工作事实。候选经过采纳后才成为新共识。</p><button class="gz-btn ghost sm" type="button" @click="setTab('context')">查看上下文结构</button></section>
      </aside>
    </div>
  </template>
</template>
