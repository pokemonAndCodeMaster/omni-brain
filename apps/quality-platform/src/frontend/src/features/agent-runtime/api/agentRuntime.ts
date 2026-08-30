import { http } from '@/shared/api/http'
import type {
  AgentDetail,
  AgentRun,
  AgentRunEventList,
  AgentRunList,
  AgentSummary,
  CreateAgentRunInput,
  AgentRuntimeHealth,
  ExecutorName,
  RunStatus,
} from '../types'

export async function getAgents(): Promise<AgentSummary[]> {
  const response = await http.get<AgentSummary[]>('/agents')
  return response.data
}

export async function refreshAgents(): Promise<AgentSummary[]> {
  const response = await http.post<AgentSummary[]>('/agents/refresh')
  return response.data
}

export async function getAgent(agentId: string): Promise<AgentDetail> {
  const response = await http.get<AgentDetail>(`/agents/${agentId}`)
  return response.data
}

export async function getAgentRuntimeHealth(): Promise<AgentRuntimeHealth> {
  const response = await http.get<AgentRuntimeHealth>('/agent-runtime/health')
  return response.data
}

export async function getAgentRuns(filters: {
  agentId?: string
  executor?: ExecutorName
  subjectType?: 'idea' | 'requirement' | 'work'
  subjectId?: string
  statuses?: RunStatus[]
  limit?: number
  offset?: number
} = {}): Promise<AgentRunList> {
  const response = await http.get<AgentRunList>('/agent-runs', {
    params: {
      agent_id: filters.agentId || undefined,
      executor: filters.executor || undefined,
      subject_type: filters.subjectType || undefined,
      subject_id: filters.subjectId || undefined,
      status: filters.statuses?.length ? filters.statuses : undefined,
      limit: filters.limit ?? 30,
      offset: filters.offset ?? 0,
    },
  })
  return response.data
}

export async function getAgentRun(runId: string): Promise<AgentRun> {
  const response = await http.get<AgentRun>(`/agent-runs/${runId}`)
  return response.data
}

export async function getAgentRunEvents(
  runId: string,
  afterSequence = 0,
): Promise<AgentRunEventList> {
  const response = await http.get<AgentRunEventList>(`/agent-runs/${runId}/events`, {
    params: { after_sequence: afterSequence, limit: 200 },
  })
  return response.data
}

export async function createAgentRun(input: CreateAgentRunInput): Promise<AgentRun> {
  const response = await http.post<AgentRun>('/agent-runs', input)
  return response.data
}

export async function cancelAgentRun(runId: string): Promise<AgentRun> {
  const response = await http.post<AgentRun>(`/agent-runs/${runId}/cancel`)
  return response.data
}
