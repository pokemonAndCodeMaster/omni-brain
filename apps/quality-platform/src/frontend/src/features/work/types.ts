import type { AgentRun, AgentRunSummary, ExecutorName } from '@/features/agent-runtime/types'

export type WorkStatus =
  | 'planned'
  | 'in_progress'
  | 'in_review'
  | 'revision_requested'
  | 'accepted'
  | 'cancelled'

export type StepDisplayStatus =
  | 'blocked'
  | 'ready'
  | 'running'
  | 'awaiting_gate'
  | 'failed'
  | 'completed'

export interface WorkCreateInput {
  title?: string
  owner_id?: string
  reviewer_id?: string
  timebox_start?: string
  timebox_end?: string
  repository_path?: string
  base_revision?: string
}

export interface WorkUpdateInput {
  owner_id?: string
  reviewer_id?: string
  timebox_start?: string | null
  timebox_end?: string | null
}

export interface WorkSummary {
  id: string
  requirement_id: string
  requirement_revision_id: string
  requirement_title: string
  title: string
  status: WorkStatus
  owner_id: string
  reviewer_id: string
  repository_path: string
  base_commit: string
  branch_name: string
  run_count: number
  completed_step_count: number
  step_count: number
  created_at: string
  updated_at: string
}

export interface PlanStep {
  id: string
  work_plan_id: string
  position: number
  step_key: string
  title: string
  description: string
  actor_kind: 'agent' | 'human'
  agent_id: string | null
  default_executor: ExecutorName | null
  status: 'pending' | 'ready' | 'completed'
  display_status: StepDisplayStatus
  completion_note: string | null
  completed_by: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
  runs: AgentRunSummary[]
}

export interface WorkPlan {
  id: string
  work_id: string
  recipe_key: 'standard_development_v1'
  revision_no: number
  status: 'active' | 'completed'
  created_by: string
  created_at: string
  completed_at: string | null
  steps: PlanStep[]
}

export interface WorkEvidence {
  id: string
  work_id: string
  payload: Record<string, unknown>
  created_by: string
  created_at: string
}

export interface WorkDecision {
  id: string
  work_id: string
  decision_type: 'accept' | 'request_changes'
  reason: string
  evidence_id: string | null
  commit_sha: string | null
  actor_id: string
  created_at: string
}

export interface Work extends WorkSummary {
  requirement_status: string
  timebox_start: string | null
  timebox_end: string | null
  worktree_path: string
  created_by: string
  accepted_at: string | null
  plan: WorkPlan
  latest_evidence: WorkEvidence | null
  decisions: WorkDecision[]
}

export interface WorkList {
  items: WorkSummary[]
  total: number
  limit: number
  offset: number
}

export interface WorkStepRunInput {
  executor?: ExecutorName
  model?: string
  instruction?: string
}

export interface WorkEvidenceInput {
  verification_summary?: string
  review_summary?: string
  pull_request_url?: string
  knowledge_proposal?: string
  candidate_eval_case?: string
}

export type WorkRun = AgentRun
