export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'

export interface AgentRunCounts {
  total: number
  active: number
  succeeded: number
  failed: number
}

export interface AgentSummary {
  id: string
  name: string
  category: string
  description: string
  state: string
  executor: 'opencode'
  revision_short: string
  run_counts: AgentRunCounts
}

export interface AgentCapability {
  id: string
  adoption: string
  adoption_label: string
  entrypoints: string[]
  limits: string[]
}

export interface AgentDetail extends AgentSummary {
  examples: string[]
  capabilities: AgentCapability[]
  repository: string
  revision: string
  release_channel: string | null
  release_date: string | null
}

export interface OpenCodeHealth {
  available: boolean
  command: string
  version: string | null
  endpoint: string | null
  reason: string | null
}

export interface CreateAgentRunInput {
  agent_id: string
  prompt: string
  title?: string
  model?: string
  actor_id?: string
}

export interface AgentRunSummary {
  id: string
  agent_id: string
  agent_name: string
  title: string
  actor_id: string
  status: RunStatus
  model: string | null
  branch_name: string | null
  opencode_session_id: string | null
  exit_code: number | null
  failure_code: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
  updated_at: string
}

export interface AgentRun extends AgentRunSummary {
  prompt: string
  repository_path: string
  base_revision: string
  worktree_path: string | null
  result_summary: string | null
  failure_reason: string | null
  artifact_path: string | null
}

export interface AgentRunList {
  items: AgentRunSummary[]
  total: number
  limit: number
  offset: number
}

export interface AgentRunEvent {
  id: number
  run_id: string
  sequence: number
  occurred_at: string
  event_type: string
  source: string
  channel: string | null
  summary: string
  payload: Record<string, unknown>
}

export interface AgentRunEventList {
  items: AgentRunEvent[]
  next_sequence: number
}
