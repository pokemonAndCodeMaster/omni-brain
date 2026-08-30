import type { AgentRun, ExecutorName } from '@/features/agent-runtime/types'

export type IdeaStatus = 'captured' | 'discussing' | 'converted' | 'archived'
export type RequirementStatus =
  | 'candidate'
  | 'accepted'
  | 'rejected'
  | 'deferred'
  | 'merged'
  | 'superseded'
  | 'closed'
export type Commitment = 'NOW' | 'NEXT' | 'LATER'

export interface RequirementContent {
  background: string
  target_users: string[]
  current_problem: string
  value: string
  expected_outcome: string
  in_scope: string[]
  out_of_scope: string[]
  key_actions: string[]
  inputs: string[]
  outputs: string[]
  acceptance_criteria: string[]
  constraints: string[]
  dependencies: string[]
  open_questions: string[]
}

export function emptyRequirementContent(): RequirementContent {
  return {
    background: '',
    target_users: [],
    current_problem: '',
    value: '',
    expected_outcome: '',
    in_scope: [],
    out_of_scope: [],
    key_actions: [],
    inputs: [],
    outputs: [],
    acceptance_criteria: [],
    constraints: [],
    dependencies: [],
    open_questions: [],
  }
}

export interface IdeaSummary {
  id: string
  title: string
  domain_key: string | null
  status: IdeaStatus
  owner_id: string
  requirement_id: string | null
  run_count: number
  created_at: string
  updated_at: string
}

export interface Idea extends IdeaSummary {
  raw_content: string
  created_by: string
  thread_id: string
}

export interface IdeaList {
  items: IdeaSummary[]
  total: number
  limit: number
  offset: number
}

export interface RequirementRevision {
  id: string
  requirement_id: string
  revision_no: number
  content: RequirementContent | null
  source_run_id: string | null
  created_by: string
  created_at: string
}

export interface RequirementSummary {
  id: string
  title: string
  source_type: 'direct' | 'idea'
  source_idea_id: string | null
  status: RequirementStatus
  commitment: Commitment | null
  owner_id: string
  current_revision_no: number
  run_count: number
  work_id: string | null
  created_at: string
  updated_at: string
}

export interface Requirement extends RequirementSummary {
  current_revision_id: string
  accepted_revision_id: string | null
  target_window: string | null
  entry_condition: string | null
  review_at: string | null
  merged_into_id: string | null
  created_by: string
  thread_id: string
  current_revision: RequirementRevision
}

export interface RequirementList {
  items: RequirementSummary[]
  total: number
  limit: number
  offset: number
}

export type TimelineItemType = 'entry' | 'run' | 'revision' | 'decision'

export interface TimelineItem {
  item_type: TimelineItemType
  item_id: string
  occurred_at: string
  payload: Record<string, unknown>
}

export interface TimelinePage {
  items: TimelineItem[]
  next_cursor: number | null
}

export interface AgentActionInput {
  action: 'knowledge_context' | 'shape_requirement'
  executor?: ExecutorName
  model?: string
  instruction?: string
}

export interface RequirementDecisionInput {
  decision_type: 'accept' | 'reject' | 'defer' | 'merge' | 'reopen'
  revision_id?: string
  reason?: string
  commitment?: Commitment
  target_window?: string
  entry_condition?: string
  review_at?: string
  merged_into_id?: string
  revision_content?: RequirementContent
}

export type AgentActionResult = AgentRun
