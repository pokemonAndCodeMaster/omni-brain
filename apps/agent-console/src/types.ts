export type Capability = {
  id: string
  adoption: string
  adoption_label: string
  entrypoints: string[]
  limits: string[]
}

export type Agent = {
  id: string
  name: string
  category: string
  description: string
  default_executor: 'codex' | 'opencode'
  revision: string
  revision_short: string
  release_channel: string
  state: string
  capabilities: Capability[]
  run_count: number
  examples: string[]
}

export type EvalCase = {
  id: string
  dataset_id: string
  name: string
  title: string
  category: string
  kind: string
  prompt?: string
  expected?: unknown
  path: string
  launchable: boolean
}

export type Evaluation = {
  success: boolean
  completion_score: number
  process_score: number
  summary: string
  strengths: string[]
  problems: string[]
  evidence_refs: string[]
  improvement_suggestion: string
  evaluated_at?: string
  judge?: string
}

export type Run = {
  id: string
  agent_id: string
  agent_name: string
  agent_revision: string
  executor: string
  model?: string
  prompt: string
  eval_case_id?: string
  evolution_id?: string
  run_role?: string
  status: string
  evaluation_status: string
  evaluation?: Evaluation
  evaluation_error?: string
  created_at: string
  updated_at: string
  session_id?: string
  worktree?: string
  workspace_available?: boolean
  workspace_released_at?: string
  branch?: string
  base_revision?: string
  head_revision?: string
  commit?: string
  workspace_status?: string
  final_preview?: string
  final_output?: string
  workspace_patch?: string
  event_count: number
  error?: string
}

export type TraceEvent = {
  seq: number
  timestamp: string
  source: string
  channel: string
  type: string
  summary: string
  payload: unknown
}

export type Trial = {
  id: string
  task_id?: string
  record_kind?: string
  started_at?: string
  ended_at?: string
  outcome?: Record<string, unknown>
  path: string
}

export type EvolutionCandidate = {
  iteration: number
  optimizer_run_id: string
  evaluation_run_id: string
  parent_revision: string
  revision: string
  has_changes: boolean
  change_summary: string
  workspace_patch: string
  evaluation: Evaluation
  score: number
  delta: number
  accepted: boolean
}

export type Evolution = {
  id: string
  agent_id: string
  agent_name: string
  prompt: string
  eval_case_id?: string
  executor: string
  model?: string
  max_iterations: number
  status: string
  stage: string
  created_at: string
  updated_at: string
  seed_revision: string
  best_revision: string
  baseline?: {
    run_id: string
    evaluation?: Evaluation
    score?: number
  }
  candidates: EvolutionCandidate[]
  error?: string
}
