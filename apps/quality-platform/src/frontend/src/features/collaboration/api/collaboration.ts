import { http } from '@/shared/api/http'
import type {
  AgentActionInput,
  AgentActionResult,
  Commitment,
  Idea,
  IdeaList,
  IdeaStatus,
  Requirement,
  RequirementContent,
  RequirementDecisionInput,
  RequirementList,
  RequirementRevision,
  RequirementStatus,
  TimelinePage,
} from '../types'

export async function getIdeas(filters: { statuses?: IdeaStatus[]; limit?: number; offset?: number } = {}) {
  const response = await http.get<IdeaList>('/ideas', {
    params: {
      status: filters.statuses?.length ? filters.statuses : undefined,
      limit: filters.limit ?? 30,
      offset: filters.offset ?? 0,
    },
  })
  return response.data
}

export async function createIdea(input: { title: string; raw_content: string; domain_key?: string }) {
  const response = await http.post<Idea>('/ideas', input)
  return response.data
}

export async function getIdea(ideaId: string) {
  const response = await http.get<Idea>(`/ideas/${ideaId}`)
  return response.data
}

export async function addIdeaMessage(ideaId: string, body: string) {
  await http.post(`/ideas/${ideaId}/messages`, { body })
}

export async function getIdeaTimeline(ideaId: string, cursor = 0) {
  const response = await http.get<TimelinePage>(`/ideas/${ideaId}/timeline`, {
    params: { cursor, limit: 30 },
  })
  return response.data
}

export async function startIdeaAction(ideaId: string, input: AgentActionInput) {
  const response = await http.post<AgentActionResult>(`/ideas/${ideaId}/agent-actions`, input)
  return response.data
}

export async function convertIdeaToRequirement(
  ideaId: string,
  input: { title: string; content: RequirementContent; source_run_id?: string },
) {
  const response = await http.post<Requirement>(`/ideas/${ideaId}/convert-to-requirement`, input)
  return response.data
}

export async function archiveIdea(ideaId: string) {
  const response = await http.post<Idea>(`/ideas/${ideaId}/archive`)
  return response.data
}

export async function getRequirements(filters: {
  statuses?: RequirementStatus[]
  commitments?: Commitment[]
  query?: string
  limit?: number
  offset?: number
} = {}) {
  const response = await http.get<RequirementList>('/requirements', {
    params: {
      status: filters.statuses?.length ? filters.statuses : undefined,
      commitment: filters.commitments?.length ? filters.commitments : undefined,
      query: filters.query || undefined,
      limit: filters.limit ?? 30,
      offset: filters.offset ?? 0,
    },
  })
  return response.data
}

export async function createRequirement(input: { title: string; content: RequirementContent }) {
  const response = await http.post<Requirement>('/requirements', input)
  return response.data
}

export async function getRequirement(requirementId: string) {
  const response = await http.get<Requirement>(`/requirements/${requirementId}`)
  return response.data
}

export async function getRequirementRevisions(requirementId: string, includeContent = false) {
  const response = await http.get<RequirementRevision[]>(`/requirements/${requirementId}/revisions`, {
    params: { include_content: includeContent },
  })
  return response.data
}

export async function createRequirementRevision(
  requirementId: string,
  input: { content: RequirementContent; source_run_id?: string },
) {
  const response = await http.post<RequirementRevision>(`/requirements/${requirementId}/revisions`, input)
  return response.data
}

export async function addRequirementMessage(requirementId: string, body: string) {
  await http.post(`/requirements/${requirementId}/messages`, { body })
}

export async function getRequirementTimeline(requirementId: string, cursor = 0) {
  const response = await http.get<TimelinePage>(`/requirements/${requirementId}/timeline`, {
    params: { cursor, limit: 30 },
  })
  return response.data
}

export async function startRequirementAction(requirementId: string, input: AgentActionInput) {
  const response = await http.post<AgentActionResult>(
    `/requirements/${requirementId}/agent-actions`,
    input,
  )
  return response.data
}

export async function decideRequirement(requirementId: string, input: RequirementDecisionInput) {
  await http.post(`/requirements/${requirementId}/decisions`, input)
}
