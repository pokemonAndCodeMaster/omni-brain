export type WorkspaceKind = 'team' | 'personal'
export type ItemTab = 'overview' | 'context' | 'outputs' | 'activity' | 'retro'
export type AgendaKey = 'decisions' | 'topics' | 'deliveries'

export interface ContextDecision {
  id?: string
  title: string
  body: string
  source: string
}

export interface ContextProposal {
  id: string
  title: string
  old: string
  text: string
  by: string
  source: string
  state?: string
  createdAt?: string
}

export interface ContextRevision {
  revision: number
  text: string
  by: string
  time: string
  body?: string
}

export interface ItemContext {
  established: boolean
  revision: number
  goal: string
  scope: string
  decisions: ContextDecision[]
  unknowns: string[]
  proposals: ContextProposal[]
  history: ContextRevision[]
}

export interface Evidence {
  id?: string
  name: string
  purpose: string
  result: string
  source: string
  sourceUrl?: string | null
  version?: string | null
  accepted?: boolean
}

export interface Artifact {
  id: string
  name: string
  kind?: string
  summary?: string
  uri?: string | null
  version?: string | null
  createdAt?: string
  accepted?: boolean
}

export interface Activity {
  id?: string
  time: string
  title: string
  text: string
  actor?: string
}

export interface DiscussionMessage {
  id?: string
  by: string
  text: string
  createdAt?: string
  anchor?: string
}

export interface Improvement {
  id: string
  kind: string
  title: string
  state: string
  body: string
  target: string
  version: string
  checks?: number
  itemId?: string
  validationSummary?: string | null
}

export interface WorkItem {
  id: string
  version: number
  payload: Record<string, unknown>
  title: string
  kind: string
  domains: string[]
  domainEntities?: Array<{ id: string; title: string; name: string; version: number }>
  topics: string[]
  owner: string
  state: string
  due: string | null
  update: string
  goal: string
  scope: string
  participants: string[]
  assets: string[]
  attention: boolean
  context: ItemContext
  evidence: Evidence[]
  artifacts: Artifact[]
  activities: Activity[]
  discussions: DiscussionMessage[]
  improvements: Improvement[]
  parentId: string | null
  createdAt?: string
  updatedAt?: string
  relations?: Array<{ id: string; fromKind: string; fromId: string; toKind: string; toId: string; relationType: string }>
}

export interface Idea {
  id: string
  version?: number
  title: string
  body: string
  state: string
  scope: string
  related: string | null
  origin: string
  reason: string
  discussions?: DiscussionMessage[]
  createdAt?: string
  payload?: Record<string, unknown>
}

export interface Topic {
  id?: string
  name: string
  goal: string
  due: string | null
  owner: string
  version?: number
  state?: string
  endCondition?: string
  payload?: Record<string, unknown>
}

export interface KnowledgeDocument {
  id: string
  title: string
  state: string
  summary?: string
  body: string
  path: string
  version: string | number
  source?: string
  sourcePath?: string
  revision?: string | number
  updatedAt?: string
  links?: Array<{ label: string; uri: string; kind?: string }>
  revisions?: Array<{ revision: string | number; summary: string; at?: string; by?: string }>
}

export interface Resource {
  id: string
  name: string
  kind: string
  uri?: string | null
  capability?: 'link' | 'read' | 'write' | string
  state?: string
  updatedAt?: string | null
  description?: string
}

export interface SkillRegistration {
  id?: string
  name: string
  state: string
  desc: string
  version: string
  limits?: string[]
}

export interface MeetingNote {
  id?: string
  itemId: string
  text: string
  time: string
}

export interface MeetingSnapshot {
  id?: string
  time: string
  items: WorkItem[]
  topics: Topic[]
  snapshotId?: string
  projection?: MeetingProjection
}

export interface MeetingPreviewEntry {
  itemId?: string
  topicId?: string
  presentation: 'full' | 'summary' | 'decision' | 'topic_summary'
  group?: string | null
  values: Record<string, unknown>
  decisions?: Array<Record<string, unknown>>
}

export interface MeetingPreviewSection {
  key: AgendaKey
  title: string
  entries: MeetingPreviewEntry[]
}

export interface MeetingProjection {
  meetingId: string
  meetingVersion: number
  sections: MeetingPreviewSection[]
}

export interface MeetingState {
  version?: number
  order: AgendaKey[]
  enabled: AgendaKey[]
  seen: string[]
  notes: MeetingNote[]
  snapshot: MeetingSnapshot | null
  sections: MeetingSectionConfig[]
}

export interface MeetingSectionConfig {
  key: AgendaKey
  title: string
  enabled: boolean
  filters?: { itemIds?: string[]; statuses?: string[]; topicIds?: string[] }
  fields?: string[]
  payloadFields?: string[]
  groupBy?: string | null
}

export interface WorkspacePreferences {
  group?: 'none' | 'topic' | 'domain'
  filter?: string
  kind?: 'all' | 'mine'
}

export interface WorkspaceState {
  workspace: WorkspaceKind
  version?: number
  items: WorkItem[]
  ideas: Idea[]
  topics: Topic[]
  domains: string[]
  domainEntities?: Array<{ id: string; title: string; name: string; version: number }>
  resources: Resource[]
  knowledge: KnowledgeDocument[]
  skills: SkillRegistration[]
  improvements: Improvement[]
  meeting: MeetingState
  preferences: WorkspacePreferences
  preferenceVersions?: Record<string, number>
  actor?: { id: string; name: string; role?: string }
}

export type RunState = 'queued' | 'claimed' | 'running' | 'pause_requested' | 'paused' | 'cancelling' | 'cancelled' | 'succeeded' | 'failed' | 'unavailable'

export interface RunEvent {
  id?: string | number
  sequence?: number
  occurredAt?: string
  type?: string
  summary?: string
  payload?: Record<string, unknown>
}

export interface GongzuoRun {
  id: string
  itemId: string
  state: RunState
  attempt: number
  machine: string | null
  engine: 'codex' | 'opencode' | string
  session: string | null
  rev: number
  image: string | null
  directory: string | null
  branch: string | null
  createdAt: string
  startedAt: string | null
  finishedAt: string | null
  exitCode: number | null
  error: string | null
  result: string | null
  instruction?: string
  artifactCandidates: Artifact[]
  evidenceCandidates: Evidence[]
  staleContext: boolean
  events?: RunEvent[]
}

export interface Machine {
  id: string
  name: string
  status: string
  capacity: number
  used: number
  image?: string | null
  currentRunId?: string | null
  lastSeenAt?: string | null
  enabled?: boolean
}

export interface ApiErrorShape {
  status: number
  message: string
  detail?: unknown
}
