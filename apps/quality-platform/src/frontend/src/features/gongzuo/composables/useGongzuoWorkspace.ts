import { computed, reactive, shallowRef } from 'vue'
import {
  apiError,
  createRun as createRunRequest,
  getRunEvents,
  getRun,
  getItemDetail,
  getWorkspaceState,
  listMachines,
  listRuns,
  machineAction,
  mutateWorkspace,
  runAction,
} from '../api/gongzuo'
import type {
  ApiErrorShape,
  GongzuoRun,
  Idea,
  Machine,
  MeetingSectionConfig,
  MeetingState,
  WorkItem,
  WorkspaceKind,
  WorkspaceState,
} from '../types'

const activeWorkspace = shallowRef<WorkspaceKind>('team')
const state = shallowRef<WorkspaceState | null>(null)
const runs = shallowRef<GongzuoRun[]>([])
const machines = shallowRef<Machine[]>([])
const itemDetails = shallowRef<Record<string, WorkItem>>({})
const loading = shallowRef(false)
const runtimeLoading = shallowRef(false)
const error = shallowRef<ApiErrorShape | null>(null)
const toast = shallowRef('')
let toastTimer: ReturnType<typeof setTimeout> | undefined
const scrollPositions = new Map<string, number>()
let meetingSessionWorkspace: WorkspaceKind | null = null
let meetingSessionSnapshot: MeetingState['snapshot'] = null
let meetingSessionSeen: string[] = []

const modal = reactive<{
  type: string | null
  payload: Record<string, unknown>
}>({ type: null, payload: {} })

function emptyMeeting(): MeetingState {
  return { order: ['decisions', 'topics', 'deliveries'], enabled: ['decisions', 'topics', 'deliveries'], seen: [], notes: [], snapshot: null, sections: [] }
}

function normalizeWorkspace(raw: WorkspaceState, workspace: WorkspaceKind): WorkspaceState {
  const source = raw as unknown as Record<string, any>
  const entities = [...(source.ideas ?? []), ...(source.topics ?? []), ...(source.domains ?? []), ...(source.resources ?? []), ...(source.artifacts ?? []), ...(source.improvements ?? [])]
  const entityMap = new Map<string, any>(entities.map((entity: any) => [entity.id, entity]))
  const relations = source.relations ?? []
  const displayStatus: Record<string, string> = { open: '待确认', planned: '待确认', in_progress: '进行中', blocked: '已阻塞', awaiting_acceptance: '待验收', completed: '已完成', cancelled: '已取消' }
  const displayKind: Record<string, string> = { requirement: '需求', research: '研究', fix: '修复', learning: '学习', review: '复盘', personal: '个人', hobby: '爱好', game: '游戏', other: '工作项' }
  const normalizeEntity = (entity: any) => ({ ...entity.payload, ...entity, ...(entity.payload ?? {}), title: entity.title, id: entity.id, version: entity.version })
  const normalizeImprovement = (entry: any) => { const entity = normalizeEntity(entry); return { ...entity, kind: entity.targetKind ?? '改进建议', state: entity.state ?? '草案', body: entity.problem ?? entity.body ?? '', target: entity.targetRef ?? entity.targetKind ?? '', version: String(entity.version ?? 1), itemId: entity.sourceItemId } }
  const topicRows = (source.topics ?? []).map(normalizeEntity)
  const domainRows = (source.domains ?? []).map(normalizeEntity)
  const improvementRows = (source.improvements ?? []).map(normalizeImprovement)
  const itemRows = source.items ?? []
  return {
    ...source,
    workspace,
    items: itemRows.map((rawItem: any) => {
      const detailIncluded = Object.prototype.hasOwnProperty.call(rawItem, 'context')
      const payload = rawItem.payload ?? {}
      const itemRelations = [...relations, ...(rawItem.relations ?? [])].filter((relation: any, index: number, rows: any[]) => (relation.fromId === rawItem.id || relation.toId === rawItem.id) && rows.findIndex((candidate) => candidate.id === relation.id) === index)
      const relatedEntities = (type: string) => itemRelations.map((relation: any) => entityMap.get(relation.fromId === rawItem.id ? relation.toId : relation.fromId)).filter((entity: any) => entity?.entityType === type)
      const rawContext = rawItem.context ?? {}
      const content = rawContext.content ?? payload.context ?? {}
      const proposals = (rawItem.contextProposals ?? content.proposals ?? []).filter((proposal: any) => !proposal.status || proposal.status === 'open').map((proposal: any) => ({
        id: proposal.id, title: proposal.title,
        old: proposal.old ?? (proposal.proposedContent?.goal !== content.goal ? content.goal : proposal.proposedContent?.scope !== content.scope ? content.scope : '当前确认内容'),
        text: typeof proposal.proposedContent === 'string' ? proposal.proposedContent : proposal.proposedContent?.goal !== content.goal ? proposal.proposedContent?.goal : proposal.proposedContent?.scope !== content.scope ? proposal.proposedContent?.scope : proposal.proposedContent?.decisions?.at(-1)?.body ?? proposal.proposedContent?.unknowns?.at(-1) ?? JSON.stringify(proposal.proposedContent ?? {}),
        by: proposal.createdBy ?? '协作者', source: proposal.provenance?.[0]?.source ?? '本次讨论', state: proposal.status, createdAt: proposal.createdAt,
      }))
      const evidence = (rawItem.evidence ?? payload.evidence ?? []).map((entry: any) => ({
        ...entry, id: entry.id, name: entry.name ?? entry.artifactRef ?? '验证证据', purpose: entry.purpose ?? entry.summary ?? '证明本轮结果',
        result: entry.result ?? (entry.status === 'accepted' ? '已证明' : entry.status === 'rejected' ? '未通过' : '未验证'),
        source: entry.source ?? `${entry.artifactRef ?? '产物'} · ${entry.artifactVersion ?? '版本未提供'}`,
        version: entry.artifactVersion, accepted: entry.status === 'accepted',
      }))
      const artifacts = [...(payload.artifacts ?? []), ...relatedEntities('artifact').map(normalizeEntity)].map((entry: any) => ({ ...entry, name: entry.name ?? entry.title ?? entry.ref ?? '运行产物' }))
      return {
      ...payload,
      ...rawItem,
      payload,
      version: rawItem.version ?? 1,
      kind: payload.kind ?? displayKind[rawItem.itemType] ?? rawItem.itemType ?? '工作项',
      state: displayStatus[rawItem.status] ?? rawItem.status ?? '待确认',
      domains: [...new Set([...(payload.domains ?? []), ...relatedEntities('domain').map((entity: any) => entity.title)])],
      topics: [...new Set([...(payload.topics ?? []), ...relatedEntities('topic').map((entity: any) => entity.title)])],
      owner: payload.owner ?? rawItem.createdBy ?? '我',
      due: payload.due ?? null,
      update: payload.update ?? '尚无进展说明',
      goal: (rawItem.context ? content.goal : undefined) ?? payload.goal ?? rawItem.title,
      scope: (rawItem.context ? content.scope : undefined) ?? payload.scope ?? '范围待继续澄清。',
      participants: payload.participants ?? [],
      assets: [...new Set([...(payload.assets ?? []), ...relatedEntities('resource').map((entity: any) => entity.title)])],
      attention: payload.attention ?? ((detailIncluded && !rawItem.context) || ['blocked', 'awaiting_acceptance'].includes(rawItem.status) || proposals.length > 0),
      artifacts,
      evidence,
      activities: (rawItem.activity ?? payload.activities ?? []).map((entry: any) => ({ id: entry.id, time: entry.createdAt ?? entry.time, title: entry.title ?? entry.kind ?? '事项更新', text: entry.text ?? entry.body ?? '', actor: entry.actorId })),
      discussions: (rawItem.discussions ?? []).map((entry: any) => ({ id: entry.id, by: entry.createdBy ?? '协作者', text: entry.body, anchor: entry.anchor, createdAt: entry.createdAt })),
      improvements: [...new Map([...(payload.improvements ?? []).map(normalizeImprovement), ...relatedEntities('improvement').map(normalizeImprovement), ...improvementRows.filter((entry: any) => entry.sourceItemId === rawItem.id)].map((entry: any) => [entry.id ?? entry.title, entry])).values()],
      parentId: payload.parentId ?? null,
      relations: itemRelations,
      context: {
        established: detailIncluded ? Boolean(rawItem.context) : false,
        revision: rawContext.version ?? rawContext.revisionNo ?? content.revision ?? 0,
        goal: content.goal ?? payload.goal ?? rawItem.title,
        scope: content.scope ?? payload.scope ?? '范围待继续澄清。',
        decisions: content.decisions ?? [], unknowns: content.unknowns ?? [], proposals,
        history: (rawItem.contextHistory ?? content.history ?? []).map((entry: any) => ({ revision: entry.revision ?? entry.revisionNo, text: entry.text ?? entry.content?.summary ?? '上下文修订', by: entry.by ?? entry.createdBy ?? '协作者', time: entry.time ?? entry.createdAt, body: entry.content })),
      },
    }}),
    ideas: (source.ideas ?? []).map((entry: any) => { const entity = normalizeEntity(entry); const formed = relations.find((relation: any) => relation.relationType === 'formed_from' && relation.toId === entry.id); return { ...entity, body: entity.body ?? entity.content ?? '', state: formed ? '已有后续' : entity.state ?? '待整理', scope: entity.scope ?? (workspace === 'team' ? '团队' : '个人'), related: entity.related ?? formed?.fromId ?? null, origin: entity.origin ?? entry.createdBy ?? '我', reason: entity.reason ?? (formed ? '已形成后续事项，原始讨论继续保留。' : '尚未分析关联。') } }),
    topics: topicRows.map((entry: any) => ({ ...entry, name: entry.name ?? entry.title, goal: entry.goal ?? '阶段目标待补充', due: entry.due ?? null, owner: entry.owner ?? '我' })),
    domains: domainRows.map((entry: any) => entry.name ?? entry.title),
    domainEntities: domainRows.map((entry: any) => ({ ...entry, name: entry.name ?? entry.title })),
    resources: (source.resources ?? []).map((entry: any) => { const entity = normalizeEntity(entry); return { ...entity, name: entity.name ?? entity.title, kind: entity.kind ?? entity.entityType ?? '资源' } }),
    knowledge: source.knowledge ?? [],
    skills: source.skills ?? [],
    improvements: improvementRows,
    meeting: (() => { const meeting = source.meeting ?? {}; const sections = meeting.config?.sections ?? []; return { ...emptyMeeting(), version: meeting.version, sections, order: sections.length ? sections.map((section: any) => section.key) : emptyMeeting().order, enabled: sections.length ? sections.filter((section: any) => section.enabled !== false).map((section: any) => section.key) : emptyMeeting().enabled, seen: meeting.config?.seen ?? [], notes: (source.meetingNotes ?? []).map((note: any) => ({ id: note.id, itemId: note.itemId, text: note.body, time: note.createdAt })), snapshot: meeting.snapshot ?? null } })(),
    preferences: (Array.isArray(source.preferences) ? source.preferences : []).find((entry: any) => entry.preferenceKey === 'items-view')?.payload ?? (source.preferences && !Array.isArray(source.preferences) ? source.preferences : {}),
    preferenceVersions: Object.fromEntries((Array.isArray(source.preferences) ? source.preferences : []).map((entry: any) => [entry.preferenceKey, entry.version])),
  }
}

function notify(message: string) {
  toast.value = message
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 4300)
}

function openModal(type: string, payload: Record<string, unknown> = {}) {
  modal.type = type
  modal.payload = payload
}

function closeModal() {
  modal.type = null
  modal.payload = {}
}

async function load(workspace: WorkspaceKind, quiet = false) {
  if (activeWorkspace.value !== workspace) {
    itemDetails.value = {}
    runs.value = []
    machines.value = []
    meetingSessionWorkspace = null
    meetingSessionSnapshot = null
    meetingSessionSeen = []
  }
  activeWorkspace.value = workspace
  if (!quiet) loading.value = true
  error.value = null
  try {
    const result = await getWorkspaceState(workspace)
    const normalized = normalizeWorkspace(result, workspace)
    if (meetingSessionWorkspace === workspace) normalized.meeting = { ...normalized.meeting, snapshot: meetingSessionSnapshot, seen: [...meetingSessionSeen] }
    state.value = normalized
  } catch (caught) {
    error.value = apiError(caught)
    state.value = null
  } finally {
    loading.value = false
  }
}

async function loadRuntime(quiet = false) {
  if (!quiet) runtimeLoading.value = true
  try {
    const [nextRuns, nextMachines] = await Promise.all([
      listRuns(activeWorkspace.value),
      listMachines(activeWorkspace.value),
    ])
    runs.value = nextRuns
    machines.value = nextMachines.map((machine: any) => ({ ...machine, used: machine.used ?? machine.activeRuns ?? 0, enabled: machine.enabled ?? !['paused', 'draining', 'disabled'].includes(machine.status), image: machine.image ?? machine.capabilities?.images?.join('、') ?? null }))
  } catch (caught) {
    const problem = apiError(caught)
    error.value = problem
    notify(problem.message)
  } finally {
    runtimeLoading.value = false
  }
}

async function mutate<T>(path: string, method: 'post' | 'put' | 'patch' | 'delete', payload: unknown, success: string) {
  error.value = null
  try {
    const result = await mutateWorkspace<T>(activeWorkspace.value, path, method, payload)
    await load(activeWorkspace.value, true)
    const itemMatch = path.match(/^\/items\/([^/]+)/)
    if (itemMatch?.[1]) await loadItem(decodeURIComponent(itemMatch[1]), true)
    notify(success)
    closeModal()
    return result
  } catch (caught) {
    const problem = apiError(caught)
    error.value = problem
    notify(problem.message)
    throw problem
  }
}

const rootItems = computed(() => (state.value?.items ?? []).filter((item) => !item.parentId))
const actorName = computed(() => state.value?.actor?.name ?? '我')

function itemById(id: string) {
  return itemDetails.value[id] ?? state.value?.items.find((item) => item.id === id)
}

async function loadItem(id: string, quiet = false) {
  if (!quiet) loading.value = true
  try {
    const detail = await getItemDetail(activeWorkspace.value, id)
    const normalized = normalizeWorkspace({
      workspace: activeWorkspace.value,
      items: [detail], ideas: state.value?.ideas ?? [], topics: state.value?.topics ?? [], domains: state.value?.domainEntities ?? [], resources: state.value?.resources ?? [], knowledge: [], skills: [], improvements: state.value?.improvements ?? [], meeting: emptyMeeting(), preferences: {},
    } as any, activeWorkspace.value).items[0]
    if (normalized) itemDetails.value = { ...itemDetails.value, [id]: normalized }
    return normalized
  } catch (caught) {
    console.error('Failed to load Gongzuo item detail', caught)
    const problem = apiError(caught)
    error.value = problem
    notify(problem.message)
    return undefined
  } finally {
    loading.value = false
  }
}

function rootOf(item: WorkItem) {
  return item.parentId ? itemById(item.parentId) ?? item : item
}

function rememberScroll(key: string) {
  scrollPositions.set(key, window.scrollY)
}

function restoreScroll(key: string) {
  requestAnimationFrame(() => window.scrollTo({ top: scrollPositions.get(key) ?? 0 }))
}

async function createIdea(payload: { body: string; scope: string }) {
  const title = payload.body.split('\n')[0]?.slice(0, 120) || '未命名灵感'
  return mutate<Idea>('/entities', 'post', { entityType: 'idea', title, payload: { body: payload.body, scope: payload.scope, state: '待整理' } }, '已保存原话；没有启动 AI。')
}

async function discussIdea(idea: Idea, text: string) {
  try {
    const result = await mutateWorkspace(activeWorkspace.value, `/entities/${encodeURIComponent(idea.id)}/discussions`, 'post', { body: text, anchor: '灵感讨论' })
    if (!idea.related && idea.state === '待整理') await mutateWorkspace(activeWorkspace.value, `/entities/${encodeURIComponent(idea.id)}`, 'patch', { version: idea.version ?? 1, title: idea.title, payload: { ...(idea.payload ?? {}), body: idea.body, scope: idea.scope, state: '讨论中' } })
    await load(activeWorkspace.value, true); closeModal(); notify('观点已留在原始线索下。')
    return result
  } catch (caught) { const problem = apiError(caught); notify(problem.message); throw problem }
}

async function createItem(payload: Record<string, unknown>, ideaId?: string) {
  const { title, itemType, ...details } = payload
  try {
    const item = await mutateWorkspace<WorkItem>(activeWorkspace.value, '/items', 'post', {
      itemType, title, payload: details,
      initialContext: { goal: details.goal || title, scope: details.scope || '' },
      provenance: ideaId ? [{ sourceEntityId: ideaId, relation: 'formed_from' }] : [{ source: '用户创建事项' }],
    })
    if (ideaId && item?.id) {
      await mutateWorkspace(activeWorkspace.value, '/relations', 'post', { fromKind: 'item', fromId: item.id, toKind: 'entity', toId: ideaId, relationType: 'formed_from' })
      const idea = state.value?.ideas.find((entry) => entry.id === ideaId)
      if (idea) await mutateWorkspace(activeWorkspace.value, `/entities/${encodeURIComponent(ideaId)}`, 'patch', { version: idea.version ?? 1, title: idea.title, payload: { ...(idea.payload ?? {}), body: idea.body, scope: idea.scope, state: '已有后续', related: item.id } })
    }
    if (details.parentId && item?.id) await mutateWorkspace(activeWorkspace.value, '/relations', 'post', { fromKind: 'item', fromId: item.id, toKind: 'item', toId: details.parentId, relationType: 'contributes_to' })
    await load(activeWorkspace.value, true)
    closeModal(); notify('事项与初始上下文已建立，尚未自动排期或运行。')
    return item
  } catch (caught) { const problem = apiError(caught); notify(problem.message); throw problem }
}

async function createEntity(entityType: 'topic' | 'domain' | 'resource', title: string, payload: Record<string, unknown>, relatedItem?: WorkItem) {
  try {
    const entity = await mutateWorkspace<{ id: string }>(activeWorkspace.value, '/entities', 'post', { entityType, title, payload })
    if (relatedItem) {
      const relationType = entityType === 'topic' ? 'serves' : entityType === 'domain' ? 'references' : 'impacts'
      await mutateWorkspace(activeWorkspace.value, '/relations', 'post', { fromKind: 'item', fromId: relatedItem.id, toKind: 'entity', toId: entity.id, relationType })
    }
    await load(activeWorkspace.value, true)
    if (relatedItem) await loadItem(relatedItem.id, true)
    closeModal(); notify(entityType === 'topic' ? '专题已建立并关联。' : entityType === 'domain' ? '领域已建立并关联。' : '资源已登记并关联。')
    return entity
  } catch (caught) { const problem = apiError(caught); notify(problem.message); throw problem }
}

async function establishContext(item: WorkItem, goal: string, scope: string) {
  const result = await mutate(`/items/${encodeURIComponent(item.id)}/context`, 'post', { content: { goal, scope, decisions: [], unknowns: [] }, provenance: [{ source: '人工确认建立初始上下文' }] }, '初始上下文已建立为 v1。')
  await loadItem(item.id, true)
  return result
}

async function updateRelations(item: WorkItem, payload: Record<string, unknown>) {
  return mutate(`/items/${encodeURIComponent(item.id)}`, 'patch', { version: item.version, payload }, '事项属性已更新。关系的增删将通过关系接口保存。')
}

async function saveRelations(item: WorkItem, payload: Record<string, unknown>, desired: Array<{ entityId: string; relationType: string }>) {
  const relevant = (item.relations ?? []).filter((relation) => relation.fromId === item.id && relation.toKind === 'entity' && ['serves', 'references', 'impacts'].includes(relation.relationType))
  const wanted = new Set(desired.map((relation) => `${relation.relationType}:${relation.entityId}`))
  const existing = new Set(relevant.map((relation) => `${relation.relationType}:${relation.toId}`))
  try {
    await mutateWorkspace(activeWorkspace.value, `/items/${encodeURIComponent(item.id)}`, 'patch', { version: item.version, payload })
    for (const relation of desired) if (!existing.has(`${relation.relationType}:${relation.entityId}`)) {
      await mutateWorkspace(activeWorkspace.value, '/relations', 'post', { fromKind: 'item', fromId: item.id, toKind: 'entity', toId: relation.entityId, relationType: relation.relationType })
    }
    for (const relation of relevant) if (!wanted.has(`${relation.relationType}:${relation.toId}`)) {
      await mutateWorkspace(activeWorkspace.value, `/relations/${encodeURIComponent(relation.id)}`, 'delete')
    }
    await load(activeWorkspace.value, true)
    await loadItem(item.id, true)
    closeModal(); notify('工作关系已更新，同一事项 ID 保持不变。')
  } catch (caught) { const problem = apiError(caught); notify(problem.message); throw problem }
}

async function updateEntity(entityId: string, version: number, title: string, payload: Record<string, unknown>) {
  return mutate(`/entities/${encodeURIComponent(entityId)}`, 'patch', { version, title, payload }, '内容已更新。')
}

async function reviewEvidence(item: WorkItem, evidenceId: string, status: 'accepted' | 'rejected', reason: string) {
  const result = await mutate(`/evidence/${encodeURIComponent(evidenceId)}/review`, 'post', { status, reason: reason || undefined }, status === 'accepted' ? '证据已人工接受。' : '证据已拒绝并保留原因。')
  await loadItem(item.id, true)
  return result
}

async function addDiscussion(item: WorkItem, text: string, anchor: string) {
  return mutate(`/items/${encodeURIComponent(item.id)}/discussions`, 'post', { body: text, anchor }, '反馈已关联当前内容。')
}

async function proposeContext(item: WorkItem, payload: Record<string, unknown>) {
  const content = { goal: item.context.goal, scope: item.context.scope, decisions: [...item.context.decisions], unknowns: [...item.context.unknowns] }
  if (payload.field === 'goal') content.goal = String(payload.text ?? '')
  else if (payload.field === 'scope') content.scope = String(payload.text ?? '')
  else if (payload.field === 'unknown') content.unknowns.push(String(payload.text ?? ''))
  else content.decisions.push({ title: String(payload.title || '新增决定'), body: String(payload.text ?? ''), source: String(payload.source || '本次修订') })
  return mutate(`/items/${encodeURIComponent(item.id)}/context/proposals`, 'post', { baseVersion: item.context.revision, title: payload.title, proposedContent: content, provenance: payload.source ? [{ source: payload.source }] : [] }, '候选已保存，当前共识没有改变。')
}

async function decideProposal(item: WorkItem, proposalId: string, decision: 'accept' | 'reject') {
  const message = decision === 'accept' ? '已形成新的共识版本，旧 Run 的依据仍保留。' : '本次未采纳；提案处理历史已保留。'
  const result = await mutate(`/context-proposals/${encodeURIComponent(proposalId)}/${decision}`, 'post', { version: item.context.revision }, message)
  await loadItem(item.id, true)
  return result
}

async function acceptResult(item: WorkItem) {
  return mutate(`/items/${encodeURIComponent(item.id)}/accept`, 'post', { version: item.version }, '本轮结果已接受，证据与过程仍然保留。')
}

async function createImprovement(item: WorkItem, payload: Record<string, unknown>) {
  const result = await mutate('/entities', 'post', { entityType: 'improvement', title: payload.title, payload: { ...payload, sourceItemId: item.id } }, '候选已进入维护中心，尚未发布。')
  await loadItem(item.id, true)
  return result
}

async function saveMeetingConfig(sections: MeetingSectionConfig[]) {
  return mutate('/meeting', 'put', { version: state.value?.meeting.version, config: { sections } }, '议程已保存。')
}

async function toggleMeetingSnapshot() {
  if (state.value?.meeting.snapshot) {
    state.value = { ...state.value, meeting: { ...state.value.meeting, snapshot: null } }
    meetingSessionSnapshot = null
    notify('已恢复读取当前事项。冻结快照仍保留在服务器。')
    return null
  }
  try {
    const snapshot: any = await mutateWorkspace(activeWorkspace.value, '/meeting/freeze', 'post')
    meetingSessionWorkspace = activeWorkspace.value
    meetingSessionSnapshot = { snapshotId: snapshot.id, time: snapshot.createdAt, items: [], topics: [], projection: snapshot.snapshot?.projection }
    meetingSessionSeen = [...(state.value?.meeting.seen ?? [])]
    if (state.value) state.value = { ...state.value, meeting: { ...state.value.meeting, snapshot: meetingSessionSnapshot } }
    notify('已冻结本次会议投影。')
    return snapshot
  } catch (caught) { const problem = apiError(caught); notify(problem.message); throw problem }
}

async function toggleMeetingSeen(itemId: string) {
  const seen = state.value?.meeting.seen.includes(itemId) ?? false
  if (state.value) state.value = { ...state.value, meeting: { ...state.value.meeting, seen: seen ? state.value.meeting.seen.filter((id) => id !== itemId) : [...state.value.meeting.seen, itemId] } }
  meetingSessionWorkspace = activeWorkspace.value
  meetingSessionSeen = [...(state.value?.meeting.seen ?? [])]
  notify(seen ? '已撤销本次阅读标记。' : '已标记为本次已讨论；会中决定请另行保存。')
}

function resumeMeetingSnapshot(snapshot: any) {
  meetingSessionWorkspace = activeWorkspace.value
  meetingSessionSnapshot = { snapshotId: snapshot.id, time: snapshot.createdAt ?? snapshot.snapshot?.frozenAt, items: [], topics: [], projection: snapshot.snapshot?.projection }
  meetingSessionSeen = [...(state.value?.meeting.seen ?? [])]
  if (state.value) state.value = { ...state.value, meeting: { ...state.value.meeting, snapshot: meetingSessionSnapshot, seen: [...meetingSessionSeen] } }
}

async function addMeetingNote(itemId: string, text: string, snapshotId?: string) {
  return mutate('/meeting/notes', 'post', { itemId, body: text, snapshotId }, '记录已写回原事项。')
}

async function savePreferences(payload: Record<string, unknown>) {
  return mutate('/preferences/items-view', 'put', { version: state.value?.preferenceVersions?.['items-view'], payload }, '已保存本空间的事项呈现。')
}

async function createRun(payload: Parameters<typeof createRunRequest>[1]) {
  try {
    const result = await createRunRequest(activeWorkspace.value, payload)
    await loadRuntime(true)
    await load(activeWorkspace.value, true)
    notify('委托已创建；状态来自真实执行器。')
    closeModal()
    return result
  } catch (caught) {
    const problem = apiError(caught)
    notify(problem.message)
    throw problem
  }
}

async function refreshRun(runId: string) {
  const detail = await getRun(activeWorkspace.value, runId)
  const events = await getRunEvents(activeWorkspace.value, runId)
  const complete = { ...detail, events }
  runs.value = [complete, ...runs.value.filter((run) => run.id !== runId)]
  return complete
}

async function actOnRun(runId: string, action: 'pause' | 'cancel' | 'retry', payload: Record<string, unknown> = {}) {
  try {
    const result = await runAction(activeWorkspace.value, runId, action, payload)
    await loadRuntime(true)
    notify(action === 'cancel' ? '已提交取消请求，状态以执行器回查为准。' : action === 'pause' ? '已提交暂停请求。' : '已创建重试运行。')
    return result
  } catch (caught) {
    const problem = apiError(caught)
    notify(problem.message)
    throw problem
  }
}

async function setMachineEnabled(machineId: string, enabled: boolean) {
  try {
    await machineAction(activeWorkspace.value, machineId, enabled ? 'enable' : 'pause')
    await loadRuntime(true)
    notify(enabled ? '执行机已恢复接单。' : '执行机已停止接收新任务。')
  } catch (caught) {
    const problem = apiError(caught)
    notify(problem.message)
    throw problem
  }
}

export function useGongzuoWorkspace() {
  return {
    activeWorkspace,
    state,
    runs,
    machines,
    itemDetails,
    loading,
    runtimeLoading,
    error,
    toast,
    modal,
    rootItems,
    actorName,
    load,
    loadRuntime,
    loadItem,
    itemById,
    rootOf,
    notify,
    openModal,
    closeModal,
    rememberScroll,
    restoreScroll,
    createIdea,
    discussIdea,
    createItem,
    createEntity,
    establishContext,
    updateRelations,
    saveRelations,
    updateEntity,
    reviewEvidence,
    addDiscussion,
    proposeContext,
    decideProposal,
    acceptResult,
    createImprovement,
    saveMeetingConfig,
    toggleMeetingSnapshot,
    resumeMeetingSnapshot,
    toggleMeetingSeen,
    addMeetingNote,
    savePreferences,
    createRun,
    refreshRun,
    actOnRun,
    setMachineEnabled,
  }
}
