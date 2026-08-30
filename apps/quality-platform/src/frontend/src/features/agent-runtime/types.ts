export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'
export type ExecutorName = 'codex' | 'opencode'

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
  default_executor: ExecutorName
  supported_executors: ExecutorName[]
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

export interface ExecutorHealth {
  name: ExecutorName
  available: boolean
  command: string
  version: string | null
  reason: string | null
  details: Record<string, unknown>
}

export interface AgentRuntimeHealth {
  executors: ExecutorHealth[]
}

export interface CreateAgentRunInput {
  agent_id: string
  prompt: string
  title?: string
  model?: string
  executor?: ExecutorName
  subject_type?: 'idea' | 'requirement' | 'work'
  subject_id?: string
  thread_id?: string
  trigger_action?: string
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
  executor: ExecutorName
  executor_session_id: string | null
  subject_type: 'idea' | 'requirement' | 'work' | null
  subject_id: string | null
  thread_id: string | null
  trigger_action: string | null
  work_id: string | null
  plan_step_id: string | null
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
  result_payload: Record<string, unknown> | null
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
