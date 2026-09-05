<script setup lang="ts">
import { computed, reactive, shallowRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import { downloadText } from '../utils/download'
import {
  apiError,
  createCapability,
  createKnowledgeProposal,
  getCapability,
  getContextHistory,
  getEntityDetail,
  getRunArtifactResult,
  publishCapability,
  verifyCapability,
} from '../api/gongzuo'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import type { ContextRevision, Evidence, GongzuoRun, Idea, KnowledgeDocument, MeetingSectionConfig, Topic, WorkItem } from '../types'
import GongzuoIcon from './GongzuoIcon.vue'
import GongzuoModal from './GongzuoModal.vue'
import StatusBadge from './StatusBadge.vue'

const router = useRouter()
const {
  activeWorkspace, state, rootItems, modal, openModal, closeModal, notify, createIdea, discussIdea,
  createItem, createEntity, establishContext, saveRelations, updateEntity, addDiscussion, proposeContext, acceptResult,
  createImprovement, saveMeetingConfig, addMeetingNote, createRun, refreshRun, actOnRun, reviewEvidence,
} = useGongzuoWorkspace()
const busy = shallowRef(false)
const detailRun = shallowRef<GongzuoRun | null>(null)
const history = shallowRef<ContextRevision[]>([])
const capability = shallowRef<Record<string, any> | null>(null)
const ideaDetail = shallowRef<Idea | null>(null)
const runArtifact = shallowRef<{ content: string; version: string } | null>(null)
const modalError = shallowRef('')
const form = reactive({
  body: '', scope: '个人', title: '', itemType: 'requirement', goal: '', domain: '', owner: '我', due: '',
  topics: [] as string[], domains: [] as string[], resources: [] as string[], source: '', anchor: '',
  instruction: '', engine: 'opencode' as 'codex' | 'opencode', runtime: 'native' as 'native' | 'docker', image: '', directory: '', branch: '', model: '', permission: 'read-only' as 'read-only' | 'workspace-write', capabilityCandidateId: '',
  targetKind: 'skill', targetRef: '', desiredBehavior: '', validationPlan: '', content: '',
  runId: '', evidenceId: '', assessment: '', result: 'accepted' as 'accepted' | 'rejected', reason: '',
  contextField: 'goal' as 'goal' | 'scope' | 'decision' | 'unknown', entityType: 'topic' as 'topic' | 'domain' | 'resource',
  entityState: '进行中', endCondition: '', uri: '', childKind: 'other',
})
type AgendaEdit = MeetingSectionConfig & { itemIdsText: string }
const agenda = reactive<AgendaEdit[]>([])

const type = computed(() => modal.type)
const item = computed(() => modal.payload.item as WorkItem | undefined)
const idea = computed(() => modal.payload.idea as Idea | undefined)
const relatedItem = computed(() => modal.payload.item as WorkItem | undefined)
const topic = computed(() => modal.payload.topic as Topic | undefined)
const evidence = computed(() => modal.payload.evidence as Evidence | undefined)
const artifact = computed(() => modal.payload.artifact as Record<string, any> | undefined)
const improvement = computed(() => modal.payload.improvement as Record<string, any> | undefined)
const knowledgeDocument = computed(() => modal.payload.document as KnowledgeDocument | undefined)
const payloadTitle = computed(() => ({
  'idea-create': '先记录，再决定怎样推进', 'idea-discuss': '继续讨论这条线索', 'item-create': idea.value ? '从原始线索形成工作' : '新建工作事项', 'entity-create': '建立可复用的工作关系', 'contribution-create': '拆出一项具体贡献', 'context-establish': '建立初始共享上下文',
  'topic-edit': '编辑专题', relations: '编辑工作关系', 'proposal-create': '提出共享上下文修订', feedback: '对当前内容留下反馈',
  discussion: '围绕这件事讨论', delegate: '委托一次工作', 'run-detail': `${detailRun.value?.id ?? ''} · 运行与环境`,
  'context-history': '共享上下文版本', artifact: '成果与产物', evidence: '验证证据', 'accept-result': '接受本轮结果',
  'improvement-create': '形成能力改进建议', 'improvement-detail': '能力改进说明', 'capability-create': '准备可试验能力候选', 'agenda-config': '配置会议呈现', 'meeting-note': '把会中决定关联回事项',
  'knowledge-proposal': '提出知识修订候选', 'capability-detail': '能力改进候选', search: '查找事项、灵感与资源', peek: item.value ? `${item.value.id} · 事项速览` : '事项速览',
}[type.value ?? ''] ?? '共作'))
const searchResults = computed(() => {
  const q = form.body.trim().toLocaleLowerCase()
  const items = rootItems.value.filter((entry) => `${entry.id} ${entry.title} ${entry.update}`.toLocaleLowerCase().includes(q)).map((entry) => ({ id: entry.id, label: entry.title, kind: 'item' }))
  const ideas = (state.value?.ideas ?? []).filter((entry) => `${entry.id} ${entry.title} ${entry.body}`.toLocaleLowerCase().includes(q)).map((entry) => ({ id: entry.id, label: entry.title, kind: 'idea' }))
  const resources = (state.value?.resources ?? []).filter((entry) => `${entry.id} ${entry.name}`.toLocaleLowerCase().includes(q)).map((entry) => ({ id: entry.id, label: entry.name, kind: 'resource' }))
  return [...items, ...ideas, ...resources]
})

watch(type, async (next) => {
  Object.assign(form, { body: '', scope: activeWorkspace.value === 'team' ? '团队' : '个人', title: '', itemType: activeWorkspace.value === 'team' ? 'requirement' : 'research', goal: '', domain: state.value?.domains[0] ?? '', owner: '我', due: '', topics: [], domains: [], resources: [], source: '', anchor: '', instruction: '', engine: activeWorkspace.value === 'team' ? 'opencode' : 'codex', runtime: 'native', image: '', directory: '', branch: '', model: '', permission: 'read-only', capabilityCandidateId: '', targetKind: 'skill', targetRef: '', desiredBehavior: '', validationPlan: '', content: '', runId: '', evidenceId: '', assessment: '', result: 'accepted', reason: '', contextField: 'goal', entityType: 'topic', entityState: '进行中', endCondition: '', uri: '', childKind: 'other' })
  detailRun.value = null; history.value = []; capability.value = null; ideaDetail.value = null; runArtifact.value = null; modalError.value = ''
  if (next === 'item-create' && idea.value) { form.title = idea.value.title; form.goal = idea.value.body }
  if (next === 'topic-edit' && topic.value) { form.title = topic.value.name; form.goal = topic.value.goal; form.due = topic.value.due ?? ''; form.owner = topic.value.owner; form.entityState = topic.value.state ?? '进行中'; form.endCondition = topic.value.endCondition ?? '' }
  if (next === 'relations' && item.value) { form.owner = item.value.owner; form.due = item.value.due ?? ''; form.topics = [...item.value.topics]; form.domains = [...item.value.domains]; form.resources = [...item.value.assets] }
  if (next === 'delegate' && item.value) form.instruction = activeWorkspace.value === 'team' ? '基于当前共识，完成尚未证明的工作并回传实际结果与不足。' : '根据当前问题与材料完成下一段工作，不扩大范围。'
  if (next === 'idea-discuss' && idea.value) { try { const detail = await getEntityDetail(activeWorkspace.value, idea.value.id) as any; ideaDetail.value = { ...idea.value, ...detail, discussions: (detail.discussions ?? []).map((entry: any) => ({ id: entry.id, by: entry.createdBy ?? '协作者', text: entry.body, anchor: entry.anchor, createdAt: entry.createdAt })) } } catch (caught) { modalError.value = apiError(caught).message } }
  if (next === 'context-history' && item.value) { try { const rows: any = await getContextHistory(activeWorkspace.value, item.value.id); history.value = (rows.items ?? rows ?? []).map((entry: any) => ({ revision: entry.revision ?? entry.revisionNo, text: entry.text ?? entry.content?.summary ?? entry.content?.goal ?? '上下文修订', by: entry.by ?? entry.createdBy ?? '协作者', time: entry.time ?? entry.createdAt, body: entry.content })) } catch (caught) { modalError.value = apiError(caught).message } }
  if (next === 'run-detail') { try { detailRun.value = await refreshRun(String(modal.payload.runId)) } catch (caught) { notify(apiError(caught).message) } }
  if (next === 'knowledge-proposal' && knowledgeDocument.value) { form.title = `修订：${knowledgeDocument.value.title}`; form.content = knowledgeDocument.value.body ?? (knowledgeDocument.value as any).content ?? '' }
  if (next === 'agenda-config') {
    const saved = new Map((state.value?.meeting.sections ?? []).map((section) => [section.key, section]))
    agenda.splice(0, agenda.length, ...(state.value?.meeting.order ?? []).map((key) => { const section = saved.get(key); return { key, title: section?.title ?? ({ decisions: '需要决定的事', topics: '专题目标与缺口', deliveries: '近期交付与变化' } as const)[key], enabled: section?.enabled !== false, filters: { itemIds: [], statuses: [], topicIds: [], ...section?.filters }, fields: [...(section?.fields ?? (key === 'topics' ? ['title'] : ['title', 'status', 'payload']))], payloadFields: [...(section?.payloadFields ?? ['goal', 'update', 'owner', 'due'])], groupBy: section?.groupBy ?? null, itemIdsText: section?.filters?.itemIds?.join(', ') ?? '' } }))
  }
  if (next === 'entity-create') form.entityType = (modal.payload.entityType as typeof form.entityType) ?? 'topic'
  if (next === 'contribution-create' && item.value) { form.owner = activeWorkspace.value === 'team' ? '' : '我'; form.goal = `为“${item.value.title}”交付一个可独立验收的贡献。` }
  if (next === 'context-establish' && item.value) { form.goal = item.value.goal; form.scope = item.value.scope }
  if (next === 'capability-detail') { try { capability.value = await getCapability(activeWorkspace.value, String(modal.payload.capabilityId)) as Record<string, any> } catch (caught) { notify(apiError(caught).message) } }
  if (next === 'capability-create') {
    const improvement = modal.payload.improvement as any
    form.title = improvement?.title ?? ''
    form.targetKind = ['skill', 'agent', 'harness'].includes(improvement?.kind) ? improvement.kind : 'skill'
    form.desiredBehavior = improvement?.desiredBehavior ?? ''
    form.validationPlan = improvement?.validationPlan ?? ''
    const description = String(form.desiredBehavior || improvement?.body || '在明确边界内改善下一次工作。').replace(/\n/g, ' ')
    form.content = form.targetKind === 'skill' ? `---\nname: candidate-skill\ndescription: ${description}\n---\n\n# ${form.title || '候选 Skill'}\n\n${improvement?.body ?? ''}` : String(improvement?.body ?? '')
  }
})

async function submit(action: () => Promise<unknown>) {
  busy.value = true; modalError.value = ''
  try { await action() } catch (caught) { modalError.value = apiError(caught).message } finally { busy.value = false }
}

async function loadArtifactResult() {
  if (!detailRun.value) return
  try { runArtifact.value = await getRunArtifactResult(activeWorkspace.value, detailRun.value.id) }
  catch (caught) { modalError.value = apiError(caught).message }
}

function downloadArtifactResult() {
  if (!detailRun.value || !runArtifact.value) return
  downloadText(runArtifact.value.content, `${detailRun.value.id}-result.txt`)
}

function openItem(id: string) { closeModal(); router.push(`/gongzuo/${activeWorkspace.value}/items/${encodeURIComponent(id)}/overview`) }

async function saveItem() {
  if (!form.title.trim() || !form.goal.trim()) return notify('请填写标题和这次希望得到的结果。')
  const created = await createItem({ title: form.title.trim(), itemType: form.itemType, goal: form.goal.trim(), owner: form.owner, domains: form.domain ? [form.domain] : [], scope: '范围待继续澄清。', update: '已形成目标，尚未承诺排期', participants: ['我'] }, idea.value?.id) as WorkItem
  if (created?.id) openItem(created.id)
}

async function saveRelationsForm() {
  if (!item.value) return
  const desired = [
    ...(state.value?.topics ?? []).filter((entry) => entry.id && form.topics.includes(entry.name)).map((entry) => ({ entityId: String(entry.id), relationType: 'serves' })),
    ...(state.value?.domainEntities ?? []).filter((entry) => form.domains.includes(entry.name)).map((entry) => ({ entityId: entry.id, relationType: 'references' })),
    ...(state.value?.resources ?? []).filter((entry) => form.resources.includes(entry.name)).map((entry) => ({ entityId: entry.id, relationType: 'impacts' })),
  ]
  await saveRelations(item.value, { ...item.value.payload, owner: form.owner, due: form.due || null, topics: form.topics, domains: form.domains, assets: form.resources }, desired)
}

async function saveEntity() {
  if (!form.title.trim()) return notify('请填写名称。')
  await createEntity(form.entityType, form.title.trim(), form.entityType === 'topic' ? { goal: form.goal, owner: form.owner, due: form.due || null, state: form.entityState, endCondition: form.endCondition } : form.entityType === 'resource' ? { kind: 'link', uri: form.uri, description: form.body } : { description: form.body }, relatedItem.value)
}

async function saveContribution() {
  if (!item.value || !form.title.trim() || !form.owner.trim()) return notify('请填写贡献名称与负责人。')
  const created = await createItem({ title: form.title, itemType: form.childKind, goal: form.goal, scope: `继承 ${item.value.id} 共享上下文 v${item.value.context.revision}`, owner: form.owner, parentId: item.value.id, contextRef: { itemId: item.value.id, version: item.value.context.revision }, update: '已分派，尚未回传结果', participants: [form.owner] }) as WorkItem
  if (created?.id) openItem(created.id)
}

function prepareImprovement() {
  if (!improvement.value) return
  if (improvement.value.kind === 'knowledge' || improvement.value.targetKind === 'knowledge') {
    closeModal(); void router.push(`/gongzuo/${activeWorkspace.value}/knowledge`); notify('请先选择真实知识来源，再从该文档提出修订。')
    return
  }
  openModal('capability-create', { improvement: improvement.value, item: item.value })
}

async function saveCapability() {
  if (!improvement.value) return
  const candidate: any = await createCapability(activeWorkspace.value, {
    title: form.title, target: form.targetKind, content: form.content,
    desiredBehavior: form.desiredBehavior, validationPlan: form.validationPlan,
    sourceEntityId: improvement.value.id,
    sourceItemId: improvement.value.itemId ?? item.value?.id,
  })
  window.dispatchEvent(new CustomEvent('gongzuo-capabilities-changed'))
  notify('可试验候选已建立，尚未验证或发布。')
  openModal('capability-detail', { capabilityId: candidate.id })
}

function moveAgenda(index: number, direction: number) { const target = index + direction; if (target < 0 || target >= agenda.length) return; const [entry] = agenda.splice(index, 1); if (entry) agenda.splice(target, 0, entry) }

function meetingSections(): MeetingSectionConfig[] {
  return agenda.map(({ itemIdsText, ...entry }) => ({ ...entry, filters: { ...entry.filters, itemIds: itemIdsText.split(/[,，\s]+/).map((id) => id.trim()).filter(Boolean) } }))
}
</script>

<template>
  <GongzuoModal v-if="type" :title="payloadTitle" :wide="['run-detail', 'artifact', 'capability-detail'].includes(type)" @close="closeModal">
    <template v-if="type === 'idea-create'"><label class="gz-label">想法或问题<textarea v-model="form.body" class="gz-field" autofocus placeholder="保留你的原话即可……"></textarea></label><label class="gz-label">可见范围<select v-model="form.scope" class="gz-field"><option>个人</option><option v-if="activeWorkspace === 'team'">团队</option></select></label><div class="gz-notice neutral"><GongzuoIcon name="idea" /><span>保存后进入灵感池，不启动 AI、不创建运行。</span></div></template>
    <template v-else-if="type === 'idea-discuss' && idea"><h3>{{ idea.title }}</h3><p class="gz-small gz-sub gz-preline">{{ idea.body }}</p><h3>已保留的讨论</h3><div v-for="message in ideaDetail?.discussions" :key="message.id ?? message.createdAt" class="gz-chat-message"><small>{{ message.by }} · {{ message.createdAt ? new Date(message.createdAt).toLocaleString('zh-CN') : '时间未记录' }}</small>{{ message.text }}</div><div v-if="!ideaDetail?.discussions?.length" class="gz-empty">尚无补充观点。</div><label class="gz-label">补充一条观点<textarea v-model="form.body" class="gz-field" placeholder="哪些问题还没想清楚？"></textarea></label></template>
    <template v-else-if="type === 'item-create'"><label class="gz-label">标题<input v-model="form.title" class="gz-field" placeholder="希望解决什么问题？" /></label><div class="gz-form-grid"><label class="gz-label">工作类型<select v-model="form.itemType" class="gz-field"><option value="requirement">需求</option><option value="research">研究</option><option value="fix">修复</option><option value="learning">学习</option><option value="review">复盘</option><option value="hobby">爱好</option><option value="game">游戏</option><option value="other">其他</option></select></label><label class="gz-label">责任人<input v-model="form.owner" class="gz-field" /></label></div><label class="gz-label">这次希望拿到什么结果<textarea v-model="form.goal" class="gz-field"></textarea></label><label class="gz-label">领域<select v-model="form.domain" class="gz-field"><option value="">暂不关联</option><option v-for="domain in state?.domains" :key="domain">{{ domain }}</option></select></label><p class="gz-dialog-note">专题、时间、仓库和执行环境可以稍后关联，不作为登记门槛。</p></template>
    <template v-else-if="type === 'topic-edit' && topic"><label class="gz-label">专题名称<input v-model="form.title" class="gz-field" /></label><label class="gz-label">阶段目标<textarea v-model="form.goal" class="gz-field"></textarea></label><label class="gz-label">怎样算结束<textarea v-model="form.endCondition" class="gz-field"></textarea></label><div class="gz-form-grid"><label class="gz-label">目标日期<input v-model="form.due" type="date" class="gz-field" /></label><label class="gz-label">负责人<input v-model="form.owner" class="gz-field" /></label><label class="gz-label">状态<select v-model="form.entityState" class="gz-field"><option>进行中</option><option>已结束</option></select></label></div></template>
    <template v-else-if="type === 'entity-create'"><label class="gz-label">对象类型<select v-model="form.entityType" class="gz-field"><option value="topic">专题</option><option value="domain">领域</option><option value="resource">资源</option></select></label><label class="gz-label">名称<input v-model="form.title" class="gz-field" autofocus /></label><template v-if="form.entityType === 'topic'"><label class="gz-label">阶段目标<textarea v-model="form.goal" class="gz-field"></textarea></label><label class="gz-label">怎样算结束<textarea v-model="form.endCondition" class="gz-field"></textarea></label><div class="gz-form-grid"><label class="gz-label">负责人<input v-model="form.owner" class="gz-field" /></label><label class="gz-label">目标日期<input v-model="form.due" type="date" class="gz-field" /></label></div></template><template v-else-if="form.entityType === 'resource'"><label class="gz-label">地址或定位<input v-model="form.uri" class="gz-field" placeholder="https://… 或仓库路径" /></label><label class="gz-label">用途<textarea v-model="form.body" class="gz-field"></textarea></label></template><label v-else class="gz-label">说明<textarea v-model="form.body" class="gz-field"></textarea></label><p v-if="relatedItem" class="gz-dialog-note">保存后会直接关联 {{ relatedItem.id }}，不用重新打开关系编辑。</p></template>
    <template v-else-if="type === 'contribution-create' && item"><div class="gz-notice neutral">这项贡献会引用 {{ item.id }} 的共享上下文 v{{ item.context.revision }}，并拥有独立负责人和结果。</div><label class="gz-label">具体贡献<input v-model="form.title" class="gz-field" autofocus /></label><div class="gz-form-grid"><label class="gz-label">工作类型<select v-model="form.childKind" class="gz-field"><option value="research">研究</option><option value="fix">修复</option><option value="review">复盘</option><option value="other">其他</option></select></label><label class="gz-label">负责人<input v-model="form.owner" class="gz-field" /></label></div><label class="gz-label">交付结果<textarea v-model="form.goal" class="gz-field"></textarea></label></template>
    <template v-else-if="type === 'relations' && item"><div class="gz-notice neutral gz-mb-16"><GongzuoIcon name="link" /><span>这些关系指向同一事项；增加专题不会复制任务。</span></div><div class="gz-form-grid"><label class="gz-label">责任人<input v-model="form.owner" class="gz-field" /></label><label class="gz-label">目标日期<input v-model="form.due" type="date" class="gz-field" /></label></div><div class="gz-between"><h3>关联专题</h3><button class="gz-text-btn" type="button" @click="openModal('entity-create', { entityType: 'topic', item })">新建并关联</button></div><label v-for="entry in state?.topics" :key="entry.id ?? entry.name" class="gz-checkline"><input v-model="form.topics" type="checkbox" :value="entry.name" />{{ entry.name }}</label><div class="gz-between"><h3>所属领域</h3><button class="gz-text-btn" type="button" @click="openModal('entity-create', { entityType: 'domain', item })">新建并关联</button></div><label v-for="entry in state?.domains" :key="entry" class="gz-checkline"><input v-model="form.domains" type="checkbox" :value="entry" />{{ entry }}</label><div class="gz-between"><h3>影响资产 / 资源</h3><button class="gz-text-btn" type="button" @click="openModal('entity-create', { entityType: 'resource', item })">登记并关联</button></div><label v-for="entry in state?.resources" :key="entry.id" class="gz-checkline"><input v-model="form.resources" type="checkbox" :value="entry.name" />{{ entry.name }}</label></template>
    <template v-else-if="type === 'context-establish' && item"><div class="gz-notice warning">这个历史事项尚未建立版本化上下文。确认后将形成可追溯的 v1。</div><label class="gz-label">目标<textarea v-model="form.goal" class="gz-field"></textarea></label><label class="gz-label">范围<textarea v-model="form.scope" class="gz-field"></textarea></label></template>
    <template v-else-if="type === 'proposal-create' && item"><div class="gz-notice neutral gz-mb-16"><GongzuoIcon name="history" /><span>当前 v{{ item.context.revision }}。新意见先形成候选，原记录保留。</span></div><label class="gz-label">修改哪部分<select v-model="form.contextField" class="gz-field"><option value="goal">目标</option><option value="scope">范围</option><option value="decision">新增决定</option><option value="unknown">新增未知项</option></select></label><label class="gz-label">修改主题<input v-model="form.title" class="gz-field" /></label><label class="gz-label">建议的新表述<textarea v-model="form.body" class="gz-field"></textarea></label><label class="gz-label">依据或原因<input v-model="form.source" class="gz-field" /></label></template>
    <template v-else-if="(type === 'feedback' || type === 'discussion') && item"><div class="gz-notice neutral gz-mb-15">{{ item.id }} / {{ String(modal.payload.anchor || '当前事项') }} / 上下文 v{{ item.context.revision }}</div><div v-for="message in item.discussions" :key="message.id ?? message.createdAt" class="gz-chat-message" :class="{ user: message.by === '我' }"><small>{{ message.by }} · {{ message.anchor }}</small>{{ message.text }}</div><label class="gz-label">意见<textarea v-model="form.body" class="gz-field" placeholder="指出具体问题，保留依据……"></textarea></label></template>
    <template v-else-if="type === 'delegate' && item"><div class="gz-notice gz-mb-18"><GongzuoIcon name="layers" /><div><strong>使用 {{ item.id }} · 共享上下文 v{{ item.context.revision }}</strong><br />目标、范围、依据和未决问题自动关联。</div></div><label class="gz-label">这次具体做什么<textarea v-model="form.instruction" class="gz-field"></textarea></label><div class="gz-form-grid"><label class="gz-label">执行器<select v-model="form.engine" class="gz-field"><option value="codex">Codex</option><option value="opencode">OpenCode</option></select></label><label class="gz-label">运行方式<select v-model="form.runtime" class="gz-field"><option value="native">原生</option><option value="docker">容器</option></select></label><label class="gz-label">目录权限<select v-model="form.permission" class="gz-field"><option value="read-only">只读分析 / 验证</option><option value="workspace-write">允许修改工作目录</option></select></label></div><label v-if="form.runtime === 'docker'" class="gz-label">镜像<input v-model="form.image" class="gz-field" placeholder="已登记镜像名称" /></label><div class="gz-form-grid"><label class="gz-label">工作目录<input v-model="form.directory" class="gz-field" /></label><label class="gz-label">分支<input v-model="form.branch" class="gz-field" /></label></div><label class="gz-label">模型（可选）<input v-model="form.model" class="gz-field" placeholder="留空使用执行环境默认；例如 gpt-5.6-luna" /></label><label class="gz-label">试验能力候选（可选）<input v-model="form.capabilityCandidateId" class="gz-field" placeholder="cap-…" /></label><p class="gz-dialog-note">责任人不变。创建后状态来自真实执行器，失败会原样显示。</p></template>
    <template v-else-if="type === 'run-detail'"><div v-if="!detailRun" class="gz-empty">正在读取真实运行…</div><template v-else><div class="gz-inline"><StatusBadge :value="detailRun.state" /><StatusBadge v-if="detailRun.staleContext" value="当前上下文已有更新" tone="amber" /></div><h3 class="gz-mt-16">{{ detailRun.instruction || '本次委托' }}</h3><div class="gz-prop"><span>工作事项</span><div>{{ detailRun.itemId }}</div></div><div class="gz-prop"><span>执行器 / 会话</span><div>{{ detailRun.engine }} / <span class="gz-mono">{{ detailRun.session || '尚未建立' }}</span></div></div><div class="gz-prop"><span>依据版本</span><div>上下文 v{{ detailRun.rev }}</div></div><div class="gz-prop"><span>机器 / 环境</span><div>{{ detailRun.machine || '等待分配' }}<br />{{ detailRun.image || '原生环境' }}</div></div><div class="gz-prop"><span>工作目录</span><div class="gz-mono">{{ detailRun.directory || '尚未分配' }}</div></div><div class="gz-prop"><span>分支</span><div class="gz-mono">{{ detailRun.branch || '无' }}</div></div><div v-if="detailRun.result" class="gz-notice neutral">{{ detailRun.result }}</div><div v-if="detailRun.error" class="gz-notice warning">{{ detailRun.error }}</div><h3>运行事件</h3><div class="gz-source-code"><div v-for="event in detailRun.events" :key="event.id ?? event.sequence">{{ event.sequence }}. {{ event.summary || event.type }} <span class="gz-muted">{{ event.occurredAt }}</span></div><span v-if="!detailRun.events?.length">尚无事件。</span></div><div v-if="detailRun.staleContext" class="gz-notice warning gz-mt-14">此运行仍以旧上下文执行。请决定继续旧范围、取消后按新共识重试，或等待当前运行完成；系统不会静默替换输入。</div><h3>固定结果正文</h3><button v-if="!runArtifact" class="gz-btn" type="button" @click="loadArtifactResult">读取真实结果</button><template v-else><div class="gz-tiny gz-muted">固定版本 {{ runArtifact.version || '后端未提供版本头' }}</div><pre class="gz-source-code">{{ runArtifact.content }}</pre><button class="gz-btn" type="button" @click="downloadArtifactResult">下载结果</button></template></template></template>
    <template v-else-if="type === 'context-history'"><div class="gz-timeline"><div v-for="entry in history" :key="entry.revision" class="gz-timeline-event"><time>{{ entry.time }} · {{ entry.by }}</time><h3>v{{ entry.revision }} · {{ entry.text }}</h3><pre v-if="entry.body" class="gz-source-code">{{ JSON.stringify(entry.body, null, 2) }}</pre></div><div v-if="!history.length" class="gz-empty">尚无可读取的版本历史。</div></div></template>
    <template v-else-if="type === 'artifact' && artifact"><StatusBadge :value="artifact.kind || '成果'" /><h2 class="gz-mt-16">{{ artifact.name || artifact.title }}</h2><p>{{ artifact.summary || artifact.description }}</p><div class="gz-prop"><span>固定版本</span><div class="gz-mono">{{ artifact.version || '未提供' }}</div></div><div class="gz-prop"><span>产物地址</span><div class="gz-mono">{{ artifact.uri || '未提供' }}</div></div><a v-if="String(artifact.uri || '').startsWith('http')" class="gz-btn" :href="artifact.uri" target="_blank" rel="noreferrer">打开实际产物</a></template>
    <template v-else-if="type === 'evidence' && evidence"><h3>{{ evidence.name }}</h3><p>{{ evidence.purpose }}</p><div class="gz-prop"><span>当前状态</span><StatusBadge :value="evidence.result" /></div><div class="gz-prop"><span>证据引用</span><div>{{ evidence.source }}</div></div><label class="gz-label">审阅原因<textarea v-model="form.reason" class="gz-field"></textarea></label><div class="gz-notice neutral"><GongzuoIcon name="shield" /><span>接受证据只确认这份固定产物、环境和范围；不会自动完成事项。</span></div></template>
    <template v-else-if="type === 'accept-result' && item"><h3>{{ item.title }}</h3><p>接受前，服务端会确认至少有一条已人工接受且固定产物版本与环境的证据。</p></template>
    <template v-else-if="type === 'improvement-create' && item"><label class="gz-label">候选名称<input v-model="form.title" class="gz-field" /></label><label class="gz-label">改进哪一层<select v-model="form.targetKind" class="gz-field"><option value="knowledge">知识</option><option value="skill">Skill</option><option value="agent">Agent 配置</option><option value="harness">Harness / 流程</option></select></label><label class="gz-label">问题与修改方向<textarea v-model="form.body" class="gz-field"></textarea></label><label class="gz-label">希望改善的行为<textarea v-model="form.desiredBehavior" class="gz-field"></textarea></label><label class="gz-label">验证方法<textarea v-model="form.validationPlan" class="gz-field"></textarea></label><label class="gz-label">修改对象<input v-model="form.targetRef" class="gz-field" /></label><p class="gz-dialog-note">来源事项 {{ item.id }} 自动关联。保存的是建议，验证与发布另有真实门槛。</p></template>
    <template v-else-if="type === 'improvement-detail' && improvement"><StatusBadge value="原始改进建议" tone="amber" /><h3 class="gz-mt-15">{{ improvement.title }}</h3><p>{{ improvement.body }}</p><div class="gz-prop"><span>目标层</span><div>{{ improvement.kind }}</div></div><div class="gz-prop"><span>希望改善</span><div>{{ improvement.desiredBehavior || '未填写' }}</div></div><div class="gz-prop"><span>验证计划</span><div>{{ improvement.validationPlan || '未填写' }}</div></div><div class="gz-notice neutral">这条记录尚不是已安装或已发布能力。进入能力候选后仍需实际 Run 与人工接受证据。</div></template><template v-else-if="type === 'capability-create' && improvement"><div class="gz-notice neutral">来源建议 {{ improvement.id }} 会保留。候选创建后还必须实际委托、人工接受证据与验证，才可发布。</div><label class="gz-label">候选名称<input v-model="form.title" class="gz-field" /></label><label class="gz-label">能力类型<select v-model="form.targetKind" class="gz-field"><option value="skill">Skill</option><option value="agent">Agent 配置</option><option value="harness">Harness / 流程</option></select></label><label class="gz-label">真实候选内容<textarea v-model="form.content" class="gz-field gz-large-textarea"></textarea></label><p v-if="form.targetKind === 'skill'" class="gz-dialog-note">请提交完整 SKILL.md，必须含 name 与 description frontmatter。</p><label class="gz-label">希望改善的行为<textarea v-model="form.desiredBehavior" class="gz-field"></textarea></label><label class="gz-label">验证计划<textarea v-model="form.validationPlan" class="gz-field"></textarea></label></template>
    <template v-else-if="type === 'agenda-config'"><p class="gz-small gz-sub">只配置读取与讲述方式，不复制一份周报事实。</p><details v-for="(entry, index) in agenda" :key="entry.key" class="gz-agenda-edit-row"><summary class="gz-between"><label class="gz-checkline" @click.stop><input v-model="entry.enabled" type="checkbox" />{{ entry.title }}</label><span class="gz-inline"><button class="gz-btn sm" type="button" @click.prevent="moveAgenda(index, -1)">↑</button><button class="gz-btn sm" type="button" @click.prevent="moveAgenda(index, 1)">↓</button></span></summary><div class="gz-form-grid gz-mt-14"><label class="gz-label">只看这些事项 ID<input v-model="entry.itemIdsText" class="gz-field" placeholder="留空使用板块默认规则" /></label><label class="gz-label">按事项字段分组<select v-model="entry.groupBy" class="gz-field"><option :value="null">不分组</option><option value="owner">责任人</option><option value="due">目标时间</option><option value="domains">领域</option></select></label></div><div v-if="entry.key !== 'topics'"><span class="gz-label">事项状态（留空使用板块默认规则）</span><label v-for="status in [{ key: 'open', label: '待确认' }, { key: 'in_progress', label: '进行中' }, { key: 'blocked', label: '已阻塞' }, { key: 'awaiting_acceptance', label: '待验收' }, { key: 'completed', label: '已完成' }]" :key="status.key" class="gz-checkline"><input v-model="entry.filters!.statuses" type="checkbox" :value="status.key" />{{ status.label }}</label><span class="gz-label">显示事项字段</span><label v-for="field in [{ key: 'title', label: '标题' }, { key: 'status', label: '状态' }, { key: 'payload', label: '工作内容' }]" :key="field.key" class="gz-checkline"><input v-model="entry.fields" type="checkbox" :value="field.key" />{{ field.label }}</label><span class="gz-label gz-mt-8">工作内容明细</span><label v-for="field in [{ key: 'goal', label: '目标' }, { key: 'update', label: '最新变化' }, { key: 'owner', label: '责任人' }, { key: 'due', label: '目标时间' }, { key: 'decisions', label: '决定' }]" :key="field.key" class="gz-checkline"><input v-model="entry.payloadFields" type="checkbox" :value="field.key" />{{ field.label }}</label></div><div v-else><span class="gz-label">只看这些专题</span><label v-for="topicRow in state?.topics" :key="topicRow.id" class="gz-checkline"><input v-model="entry.filters!.topicIds" type="checkbox" :value="topicRow.id" />{{ topicRow.name }}</label><span v-if="!state?.topics.length" class="gz-tiny gz-muted">尚无专题；默认会显示全部专题摘要。</span></div></details><div class="gz-notice neutral gz-mt-16"><GongzuoIcon name="layers" /><span>完整展开、摘要和语境决定由后端投影统一去重。</span></div></template>
    <template v-else-if="type === 'meeting-note' && item"><p class="gz-small gz-sub">{{ item.id }} · {{ item.title }}</p><label class="gz-label">决定或行动项<textarea v-model="form.body" class="gz-field"></textarea></label><p class="gz-dialog-note">记录会加入原事项活动；共识变化仍需提出上下文修订。</p></template>
    <template v-else-if="type === 'knowledge-proposal' && knowledgeDocument"><div class="gz-notice neutral gz-mb-16">{{ knowledgeDocument.path }} · 当前读取版本 {{ knowledgeDocument.version }}</div><label class="gz-label">候选名称<input v-model="form.title" class="gz-field" /></label><label class="gz-label">建议正文<textarea v-model="form.content" class="gz-field gz-large-textarea"></textarea></label><label class="gz-label">希望改善的行为<textarea v-model="form.desiredBehavior" class="gz-field"></textarea></label><label class="gz-label">验证计划<textarea v-model="form.validationPlan" class="gz-field"></textarea></label></template>
    <template v-else-if="type === 'capability-detail'"><div v-if="!capability" class="gz-empty">正在读取候选…</div><template v-else><div class="gz-inline"><StatusBadge :value="capability.target" /><StatusBadge :value="capability.status" /></div><h3 class="gz-mt-15">{{ capability.title }}</h3><p>{{ capability.desiredBehavior }}</p><div class="gz-prop"><span>候选版本</span><div class="gz-mono">{{ capability.version }}</div></div><div class="gz-prop"><span>验证计划</span><div>{{ capability.validationPlan }}</div></div><h3>已有验证</h3><div v-for="check in capability.verifications" :key="check.id" class="gz-note-card"><StatusBadge :value="check.result" /><p>{{ check.assessment }}</p><span class="gz-mono gz-tiny">{{ check.runId }} / {{ check.evidenceId }}</span></div><div v-if="capability.status !== 'published'"><hr class="gz-rule" /><div class="gz-form-grid"><label class="gz-label">真实 Run ID<input v-model="form.runId" class="gz-field" /></label><label class="gz-label">已接受证据 ID<input v-model="form.evidenceId" class="gz-field" /></label></div><label class="gz-label">评估结论<textarea v-model="form.assessment" class="gz-field"></textarea></label><label class="gz-label">验证判断<select v-model="form.result" class="gz-field"><option value="accepted">接受</option><option value="rejected">拒绝</option></select></label></div></template></template>
    <template v-else-if="type === 'search'"><input v-model="form.body" class="gz-field" aria-label="搜索" autofocus placeholder="输入标题、ID 或进展……" /><div class="gz-search-results"><button v-for="result in searchResults" :key="`${result.kind}-${result.id}`" type="button" @click="result.kind === 'item' ? openItem(result.id) : notify(`${result.kind === 'idea' ? '灵感' : '资源'}：${result.label}`)"><span class="gz-mono gz-muted">{{ result.id }}</span> {{ result.label }}<StatusBadge :value="result.kind" /></button><div v-if="!searchResults.length" class="gz-empty">没有找到匹配内容。</div></div><p class="gz-dialog-note">只搜索当前空间已读取的真实数据。</p></template>
    <template v-else-if="type === 'peek' && item"><h2>{{ item.title }}</h2><div class="gz-inline"><StatusBadge :value="item.state" /><span>{{ item.owner }}</span><StatusBadge :value="item.kind" /></div><h3 class="gz-mt-20">目标</h3><p>{{ item.goal }}</p><h3>最近变化</h3><p>{{ item.update }}</p><div class="gz-notice neutral">共享上下文 v{{ item.context.revision }} · {{ item.context.proposals.length }} 个候选修改。关闭后保留当前阅读位置。</div></template>

    <div v-if="modalError" class="gz-notice warning gz-mt-14" role="alert">{{ modalError }}</div>
    <template #footer>
      <button class="gz-btn" type="button" @click="closeModal">关闭</button>
      <button v-if="type === 'idea-create'" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => createIdea({ body: form.body, scope: form.scope }))">保存记录</button>
      <button v-else-if="type === 'idea-discuss' && idea" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => discussIdea(idea!, form.body))">保存讨论</button>
      <button v-else-if="type === 'item-create'" class="gz-btn primary" type="button" :disabled="busy" @click="submit(saveItem)">建立事项</button>
      <button v-else-if="type === 'entity-create'" class="gz-btn primary" type="button" :disabled="busy" @click="submit(saveEntity)">建立并关联</button>
      <button v-else-if="type === 'contribution-create'" class="gz-btn primary" type="button" :disabled="busy" @click="submit(saveContribution)">创建贡献</button>
      <button v-else-if="type === 'topic-edit' && topic" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => updateEntity(String(topic!.id), topic!.version ?? 1, form.title, { ...(topic!.payload ?? {}), goal: form.goal, due: form.due || null, owner: form.owner, state: form.entityState, endCondition: form.endCondition }))">保存专题</button>
      <button v-else-if="type === 'relations'" class="gz-btn primary" type="button" :disabled="busy" @click="submit(saveRelationsForm)">保存关系</button>
      <button v-else-if="type === 'context-establish' && item" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => establishContext(item!, form.goal, form.scope))">确认建立 v1</button>
      <button v-else-if="type === 'proposal-create' && item" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => proposeContext(item!, { title: form.title, field: form.contextField, text: form.body, source: form.source }))">保存为候选</button>
      <button v-else-if="(type === 'feedback' || type === 'discussion') && item" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => addDiscussion(item!, form.body, String(modal.payload.anchor || '当前事项')))">保存反馈</button>
      <button v-else-if="type === 'delegate' && item" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => createRun({ itemId: item!.id, instruction: form.instruction, engine: form.engine, runtime: form.runtime, image: form.image || undefined, directory: form.directory || undefined, branch: form.branch || undefined, model: form.model || undefined, permission: form.permission, ...(form.capabilityCandidateId ? { capabilityCandidateId: form.capabilityCandidateId } : {}) } as any))">开始委托</button>
      <template v-else-if="type === 'run-detail' && detailRun"><button v-if="['claimed', 'running'].includes(detailRun.state)" class="gz-btn" type="button" :disabled="busy" @click="submit(() => actOnRun(detailRun!.id, 'pause'))">暂停</button><button v-if="['queued', 'claimed', 'running', 'pause_requested', 'paused'].includes(detailRun.state)" class="gz-btn" type="button" :disabled="busy" @click="submit(() => actOnRun(detailRun!.id, 'cancel'))">取消运行</button><button v-if="['failed', 'cancelled', 'succeeded', 'unavailable'].includes(detailRun.state)" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => actOnRun(detailRun!.id, 'retry', { syncContext: true }))">按当前共识重试</button></template>
      <template v-else-if="type === 'evidence' && evidence && item"><button class="gz-btn" type="button" :disabled="busy || !evidence.id" @click="submit(() => reviewEvidence(item!, String(evidence!.id), 'rejected', form.reason))">拒绝证据</button><button class="gz-btn primary" type="button" :disabled="busy || !evidence.id" @click="submit(() => reviewEvidence(item!, String(evidence!.id), 'accepted', form.reason))">接受证据</button></template>
      <button v-else-if="type === 'accept-result' && item" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => acceptResult(item!))">确认接受</button>
      <button v-else-if="type === 'improvement-create' && item" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => createImprovement(item!, { title: form.title, body: form.body, problem: form.body, targetKind: form.targetKind, targetRef: form.targetRef, desiredBehavior: form.desiredBehavior, validationPlan: form.validationPlan }))">保存建议</button>
      <button v-else-if="type === 'improvement-detail' && improvement" class="gz-btn primary" type="button" @click="prepareImprovement">{{ improvement.kind === 'knowledge' ? '选择知识来源' : '准备试验候选' }}</button><button v-else-if="type === 'capability-create' && improvement" class="gz-btn primary" type="button" :disabled="busy" @click="submit(saveCapability)">建立可试验候选</button><button v-else-if="type === 'agenda-config'" class="gz-btn primary" type="button" :disabled="busy || !agenda.some((entry) => entry.enabled)" @click="submit(() => saveMeetingConfig(meetingSections()))">保存议程</button>
      <button v-else-if="type === 'meeting-note' && item" class="gz-btn primary" type="button" :disabled="busy" @click="submit(() => addMeetingNote(item!.id, form.body, String(modal.payload.snapshotId || '') || undefined))">保存会中记录</button>
      <button v-else-if="type === 'knowledge-proposal' && knowledgeDocument" class="gz-btn primary" type="button" :disabled="busy" @click="submit(async () => { await createKnowledgeProposal(activeWorkspace, { title: form.title, target: 'knowledge', content: form.content, desiredBehavior: form.desiredBehavior, validationPlan: form.validationPlan, sourcePath: knowledgeDocument!.path, baseVersion: knowledgeDocument!.version }); closeModal(); notify('知识修订候选已保存，正式知识尚未改变。') })">保存候选</button>
      <template v-else-if="type === 'capability-detail' && capability"><button v-if="capability.status !== 'published'" class="gz-btn" type="button" :disabled="busy" @click="submit(async () => { await verifyCapability(activeWorkspace, capability!.id, { runId: form.runId, evidenceId: form.evidenceId, result: form.result, assessment: form.assessment }); capability = await getCapability(activeWorkspace, capability!.id) as any; notify('真实验证结果已记录。') })">记录验证</button><button v-if="capability.status === 'verified'" class="gz-btn primary" type="button" :disabled="busy" @click="submit(async () => { await publishCapability(activeWorkspace, capability!.id, capability!.version); capability = await getCapability(activeWorkspace, capability!.id) as any; notify('当前候选版本已发布。') })">发布此版本</button></template>
      <button v-else-if="type === 'peek' && item" class="gz-btn primary" type="button" @click="openItem(item.id)">打开完整协作空间</button>
    </template>
  </GongzuoModal>
</template>
