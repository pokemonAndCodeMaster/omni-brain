<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiError, getMeetingMarkdown, getMeetingPreview, getMeetingSnapshot } from '../api/gongzuo'
import GongzuoIcon from '../components/GongzuoIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import type { MeetingPreviewEntry, MeetingProjection } from '../types'
import { downloadText } from '../utils/download'

const descriptions: Record<string, string> = {
  decisions: '把需要人的判断放到最前面。进展从事实带入，决定写回原事项。',
  topics: '这里只回答目标和整体缺口，不重复展开已经讲过的事项。',
  deliveries: '跳过前序板块已完整展开的工作，只呈现剩余近期交付。',
}
const labels: Record<string, string> = { title: '事项', status: '状态', owner: '责任人', due: '目标时间', goal: '目标', scope: '范围', update: '最新变化', gap: '当前缺口', relatedItems: '关联事项', participants: '参与者', decisions: '决定' }
const route = useRoute()
const router = useRouter()
const { activeWorkspace, state, itemById, openModal, toggleMeetingSnapshot, resumeMeetingSnapshot, toggleMeetingSeen, notify } = useGongzuoWorkspace()
const index = shallowRef(0)
const presenting = shallowRef(false)
const livePreview = shallowRef<MeetingProjection | null>(null)
const previewError = shallowRef('')
const isTeam = computed(() => activeWorkspace.value === 'team')
const meeting = computed(() => state.value?.meeting)
const preview = computed(() => meeting.value?.snapshot?.projection ?? livePreview.value)
const sections = computed(() => preview.value?.sections ?? [])
const keys = computed(() => sections.value.map((section) => section.key))
const currentSection = computed(() => sections.value[index.value])
const currentEntryGroups = computed(() => {
  const entries = currentSection.value?.entries ?? []
  const grouped = new Map<string, MeetingPreviewEntry[]>()
  for (const entry of entries) {
    const label = entry.group?.trim() || '未分组'
    grouped.set(label, [...(grouped.get(label) ?? []), entry])
  }
  const showHeadings = entries.some((entry) => Boolean(entry.group?.trim()))
  return [...grouped].map(([label, groupEntries]) => ({ label, entries: groupEntries, showHeading: showHeadings }))
})
const factsKey = computed(() => JSON.stringify({ workspace: activeWorkspace.value, meeting: meeting.value?.version, snapshot: meeting.value?.snapshot?.snapshotId, items: state.value?.items.map((item) => [item.id, item.version, item.updatedAt]), topics: state.value?.topics.map((topic) => [topic.id, topic.version]) }))

function next() { index.value = Math.min(keys.value.length - 1, index.value + 1) }
function previous() { index.value = Math.max(0, index.value - 1) }
function onKeydown(event: KeyboardEvent) {
  if (!presenting.value || ['INPUT', 'TEXTAREA', 'SELECT'].includes((event.target as HTMLElement).tagName)) return
  if (event.key === 'ArrowRight') next()
  if (event.key === 'ArrowLeft') previous()
  if (event.key === 'Escape') presenting.value = false
}
function fieldLabel(key: string) { return labels[key] ?? key }
function displayValue(value: unknown): string {
  if (Array.isArray(value)) return value.map((entry) => typeof entry === 'object' ? JSON.stringify(entry) : String(entry)).join('、') || '无'
  if (value && typeof value === 'object') return Object.entries(value as Record<string, unknown>).map(([key, entry]) => `${fieldLabel(key)}：${displayValue(entry)}`).join('；')
  if (value === null || value === undefined || value === '') return '未登记'
  return String(value)
}
function displayFields(entry: MeetingPreviewEntry) {
  return Object.entries(entry.values ?? {}).filter(([key]) => key !== 'title').map(([key, value]) => ({ key, label: fieldLabel(key), value: displayValue(value) }))
}
function entryId(entry: MeetingPreviewEntry) { return entry.itemId ?? entry.topicId ?? '' }

async function loadPreview() {
  if (!meeting.value?.version) { livePreview.value = null; previewError.value = ''; return }
  if (meeting.value?.snapshot?.projection) { previewError.value = ''; return }
  try { livePreview.value = await getMeetingPreview(activeWorkspace.value) as MeetingProjection; previewError.value = '' }
  catch (caught) { livePreview.value = null; previewError.value = apiError(caught).message }
}
async function exportMarkdown() {
  try {
    const markdown = await getMeetingMarkdown(activeWorkspace.value, meeting.value?.snapshot?.snapshotId)
    downloadText(markdown, `${isTeam.value ? '团队周度组会' : '个人周回顾'}.md`, 'text/markdown;charset=utf-8')
    notify('已导出服务器生成的 Markdown 纪要。')
  } catch (caught) { notify(apiError(caught).message) }
}

async function toggleSnapshot() {
  try {
    const result: any = await toggleMeetingSnapshot()
    const query = { ...route.query }
    if (result?.id) query.snapshot = result.id
    else delete query.snapshot
    await router.replace({ query })
  } catch { /* composable reports the server error */ }
}

async function resumeSnapshot(snapshotId: string) {
  if (!snapshotId || meeting.value?.snapshot?.snapshotId === snapshotId) return
  try { resumeMeetingSnapshot(await getMeetingSnapshot(activeWorkspace.value, snapshotId)) }
  catch (caught) {
    notify(apiError(caught).message)
    const query = { ...route.query }; delete query.snapshot; await router.replace({ query })
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
watch(factsKey, () => { index.value = 0; void loadPreview() }, { immediate: true })
watch(() => [activeWorkspace.value, String(route.query.snapshot ?? '')] as const, ([, snapshotId]) => { if (snapshotId) void resumeSnapshot(snapshotId) }, { immediate: true })
</script>

<template>
  <div :class="{ 'gz-presenting': presenting }">
    <PageHeader :title="isTeam ? '质检团队 · 周度组会' : '我的周回顾'" subtitle="把议程保存成呈现方式，不再手工搬运一遍进展。">
      <button class="gz-btn" type="button" @click="openModal('agenda-config')">配置议程</button><button class="gz-btn primary" type="button" :disabled="!sections.length" @click="presenting = true"><GongzuoIcon name="play" />开始演示</button>
    </PageHeader>
    <div class="gz-meeting-controls"><StatusBadge :value="meeting?.snapshot ? '已冻结本次内容' : '读取当前工作事实'" :tone="meeting?.snapshot ? 'green' : 'blue'" /><span class="gz-tiny gz-muted">{{ meeting?.snapshot ? `快照时间 ${meeting.snapshot.time}` : '当前实时视图' }}</span><span class="gz-spacer"></span><button class="gz-btn sm" type="button" :disabled="!meeting?.version" @click="toggleSnapshot">{{ meeting?.snapshot ? '回到实时内容' : '冻结本次内容' }}</button><button class="gz-btn sm" type="button" :disabled="!meeting?.version" @click="exportMarkdown"><GongzuoIcon name="download" />导出纪要</button></div>
    <div class="gz-meeting-config">
      <aside class="gz-panel pad gz-agenda-sidebar"><div class="gz-eyebrow">本次议程</div><button v-for="(section, position) in sections" :key="section.key" class="gz-agenda-button" :class="{ active: index === position }" type="button" @click="index = position"><span class="num">{{ String(position + 1).padStart(2, '0') }}</span>{{ section.title }}</button><hr class="gz-rule" /><p class="gz-small gz-sub">同一事项只在一个板块完整展开。专题保留目标、缺口与关联决定。</p><div class="gz-tiny gz-muted">已讨论 {{ meeting?.seen.length ?? 0 }} 项 · {{ meeting?.notes.length ?? 0 }} 条会中记录</div></aside>
      <section>
        <article v-if="currentSection" class="gz-slide-page"><div class="gz-slide-eyebrow">{{ isTeam ? 'QC TEAM / WEEKLY ALIGNMENT' : 'PERSONAL / WEEKLY REVIEW' }} · 工作事实</div><h2>{{ currentSection.title }}</h2><p class="gz-slide-desc">{{ descriptions[currentSection.key] ?? '按照已保存的会议配置读取当前事实。' }}</p>
          <template v-for="group in currentEntryGroups" :key="group.label">
            <div v-if="group.showHeading" class="gz-meeting-group-head"><span>{{ group.label }}</span><small>{{ group.entries.length }} 项</small></div>
            <div v-for="entry in group.entries" :key="`${entry.presentation}-${entryId(entry)}`" class="gz-meeting-item" :class="{ seen: entry.itemId && meeting?.seen.includes(entry.itemId) }"><div class="gz-between"><h3><span class="gz-mono gz-muted">{{ entryId(entry) }}</span> {{ String(entry.values.title || itemById(entry.itemId || '')?.title || '') }}</h3><StatusBadge :value="entry.itemId && meeting?.seen.includes(entry.itemId) ? '本次已讨论' : entry.presentation === 'full' ? '完整展开' : entry.presentation === 'decision' ? '语境决定' : entry.presentation === 'topic_summary' ? '专题摘要' : '摘要'" :tone="entry.itemId && meeting?.seen.includes(entry.itemId) ? 'green' : entry.presentation === 'decision' ? 'amber' : undefined" /></div><p v-for="field in displayFields(entry)" :key="field.key"><strong>{{ field.label }}：</strong>{{ field.value }}</p><div v-for="(decision, decisionIndex) in entry.decisions" :key="decisionIndex" class="gz-notice neutral"><strong>语境决定：</strong>{{ displayValue(decision.body ?? decision.title) }}</div><div v-if="entry.itemId" class="gz-between"><span class="gz-tiny gz-sub">由会议投影按去重规则生成</span><div class="gz-inline"><button v-if="itemById(entry.itemId)" class="gz-btn sm" type="button" @click="openModal('peek', { item: itemById(entry.itemId) })">查看依据</button><button v-if="itemById(entry.itemId)" class="gz-btn sm" type="button" @click="openModal('meeting-note', { item: itemById(entry.itemId), snapshotId: meeting?.snapshot?.snapshotId })">记录决定</button><button class="gz-btn sm" type="button" @click="toggleMeetingSeen(entry.itemId)">{{ meeting?.seen.includes(entry.itemId) ? '撤销已讨论' : '标记已讨论' }}</button></div></div></div>
          </template>
          <div v-if="!currentSection.entries.length" class="gz-empty">本板块没有剩余事项。前面已经展开的内容不再重复。</div>
          <div class="gz-slide-footer"><span>共作 · 同一事实，按议程呈现</span><span>{{ index + 1 }} / {{ keys.length }} {{ meeting?.snapshot ? '· 已冻结' : '· 实时视图' }}</span></div>
        </article>
        <div v-else class="gz-panel gz-empty">尚未配置会议议程。请先保存至少一个板块。</div>
        <div v-if="previewError" class="gz-notice warning gz-mt-14">{{ previewError }}</div>
        <div class="gz-between gz-meeting-standard-nav"><button class="gz-btn" type="button" :disabled="index === 0" @click="previous">← 上一页</button><span class="gz-tiny gz-muted">专题引用不会增加新的交付。</span><button class="gz-btn" type="button" :disabled="index >= keys.length - 1" @click="next">下一页 →</button></div>
        <div class="gz-presentation-nav"><button class="gz-btn" type="button" @click="previous">←</button><span class="gz-small gz-sub">← → 切页 · Esc 退出</span><button class="gz-btn" type="button" @click="next">→</button><button class="gz-btn" type="button" @click="presenting = false">退出演示</button></div>
      </section>
    </div>
    <div class="gz-meeting-bottom-note gz-notice neutral"><GongzuoIcon name="meeting" /><div>呈现配置决定看哪些对象、按什么顺序、展开到哪一层。冻结保存当时事实；会中记录关联原事项。</div></div>
  </div>
</template>
