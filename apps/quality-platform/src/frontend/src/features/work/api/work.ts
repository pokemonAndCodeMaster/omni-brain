import { http } from '@/shared/api/http'
import type {
  Work,
  WorkCreateInput,
  WorkDecision,
  WorkEvidence,
  WorkEvidenceInput,
  WorkList,
  WorkRun,
  WorkStatus,
  WorkStepRunInput,
  WorkUpdateInput,
} from '../types'

export async function createWork(requirementId: string, input: WorkCreateInput = {}) {
  const response = await http.post<Work>(`/requirements/${requirementId}/work`, input)
  return response.data
}

export async function getWorks(filters: { statuses?: WorkStatus[]; limit?: number; offset?: number } = {}) {
  const response = await http.get<WorkList>('/works', {
    params: {
      status: filters.statuses?.length ? filters.statuses : undefined,
      limit: filters.limit ?? 30,
      offset: filters.offset ?? 0,
    },
  })
  return response.data
}

export async function getWork(workId: string) {
  const response = await http.get<Work>(`/works/${workId}`)
  return response.data
}

export async function updateWork(workId: string, input: WorkUpdateInput) {
  const response = await http.patch<Work>(`/works/${workId}`, input)
  return response.data
}

export async function startWorkStep(workId: string, stepId: string, input: WorkStepRunInput) {
  const response = await http.post<WorkRun>(`/works/${workId}/steps/${stepId}/runs`, input)
  return response.data
}

export async function completeWorkStep(workId: string, stepId: string, note: string) {
  const response = await http.post<Work>(`/works/${workId}/steps/${stepId}/complete`, { note })
  return response.data
}

export async function recordWorkEvidence(workId: string, input: WorkEvidenceInput) {
  const response = await http.post<WorkEvidence>(`/works/${workId}/evidence`, input)
  return response.data
}

export async function decideWork(
  workId: string,
  input: { decision_type: 'accept' | 'request_changes'; reason: string },
) {
  const response = await http.post<WorkDecision>(`/works/${workId}/decisions`, input)
  return response.data
}
