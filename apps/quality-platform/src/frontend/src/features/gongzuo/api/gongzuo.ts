import type { AxiosError } from 'axios'
import { http } from '@/shared/api/http'
import type {
  ApiErrorShape,
  GongzuoRun,
  Machine,
  WorkspaceKind,
  WorkspaceState,
  WorkItem,
} from '../types'

const root = (workspace: WorkspaceKind) => `/gongzuo/${workspace}`

export async function getGongzuoConfig() {
  const { data } = await http.get<{ workspaces: WorkspaceKind[]; defaultWorkspace: WorkspaceKind; identityMode: string }>('/gongzuo/config')
  return data
}

export function apiError(error: unknown): ApiErrorShape {
  if (error && typeof error === 'object' && 'message' in error && 'status' in error) return error as ApiErrorShape
  const candidate = error as AxiosError<{ detail?: unknown; message?: string }>
  const status = candidate.response?.status ?? 0
  const detail = candidate.response?.data?.detail
  const fallback = status === 409
    ? '内容已经被其他更新修改，请刷新后再试。'
    : status === 0
      ? '无法连接共作服务，请确认后端已经启动。'
      : '这次操作没有完成，请稍后重试。'
  return {
    status,
    detail,
    message: candidate.response?.data?.message
      ?? (typeof detail === 'string' ? detail : error instanceof Error ? error.message : fallback),
  }
}

export async function getWorkspaceState(workspace: WorkspaceKind) {
  const { data } = await http.get<WorkspaceState>(`${root(workspace)}/state`)
  return data
}

export async function getItemDetail(workspace: WorkspaceKind, itemId: string) {
  const { data } = await http.get<WorkItem>(`${root(workspace)}/items/${encodeURIComponent(itemId)}`)
  return data
}

export async function getEntityDetail(workspace: WorkspaceKind, entityId: string) {
  const { data } = await http.get(`${root(workspace)}/entities/${encodeURIComponent(entityId)}`)
  return data
}

export async function getKnowledgeList(workspace: WorkspaceKind, query = '') {
  const { data } = await http.get(`${root(workspace)}/knowledge`, { params: { q: query || undefined } })
  return data
}

export async function getKnowledgeDocument(workspace: WorkspaceKind, path: string) {
  const { data } = await http.get(`${root(workspace)}/knowledge/document`, { params: { path } })
  return data
}

export async function createKnowledgeProposal(workspace: WorkspaceKind, payload: Record<string, unknown>) {
  const { data } = await http.post(`${root(workspace)}/knowledge/proposals`, payload)
  return data
}

export async function createCapability(workspace: WorkspaceKind, payload: Record<string, unknown>) {
  const { data } = await http.post(`${root(workspace)}/capabilities`, payload)
  return data
}

export async function listCapabilities(workspace: WorkspaceKind) {
  const { data } = await http.get(`${root(workspace)}/capabilities`)
  return data
}

export async function getCapability(workspace: WorkspaceKind, id: string) {
  const { data } = await http.get(`${root(workspace)}/capabilities/${encodeURIComponent(id)}`)
  return data
}

export async function getMeetingMarkdown(workspace: WorkspaceKind, snapshotId?: string) {
  const response = await http.get(`${root(workspace)}/meeting/markdown`, { responseType: 'text', params: { snapshotId } })
  return String(response.data)
}

export async function getMeetingPreview(workspace: WorkspaceKind) {
  const { data } = await http.get(`${root(workspace)}/meeting/preview`)
  return data
}

export async function getMeetingSnapshot(workspace: WorkspaceKind, snapshotId: string) {
  const { data } = await http.get(`${root(workspace)}/meeting/snapshots/${encodeURIComponent(snapshotId)}`)
  return data
}

export async function getContextHistory(workspace: WorkspaceKind, itemId: string) {
  const { data } = await http.get(`${root(workspace)}/items/${encodeURIComponent(itemId)}/context/history`)
  return data
}

export async function verifyCapability(workspace: WorkspaceKind, id: string, payload: Record<string, unknown>) {
  const { data } = await http.post(`${root(workspace)}/capabilities/${encodeURIComponent(id)}/verify`, payload)
  return data
}

export async function publishCapability(workspace: WorkspaceKind, id: string, version: string) {
  const { data } = await http.post(`${root(workspace)}/capabilities/${encodeURIComponent(id)}/publish`, { version })
  return data
}

export async function mutateWorkspace<T>(
  workspace: WorkspaceKind,
  path: string,
  method: 'post' | 'put' | 'patch' | 'delete',
  payload?: unknown,
) {
  const { data } = await http.request<T>({
    url: `${root(workspace)}${path}`,
    method,
    data: payload,
  })
  return data
}

export async function listRuns(workspace: WorkspaceKind) {
  const { data } = await http.get<GongzuoRun[] | { items: GongzuoRun[] }>(`${root(workspace)}/runs`)
  return Array.isArray(data) ? data : data.items
}

export async function getRun(workspace: WorkspaceKind, runId: string) {
  const { data } = await http.get<GongzuoRun>(`${root(workspace)}/runs/${encodeURIComponent(runId)}`)
  return data
}

export async function getRunEvents(workspace: WorkspaceKind, runId: string) {
  const { data } = await http.get<{ items?: GongzuoRun['events']; nextSequence: number }>(`${root(workspace)}/runs/${encodeURIComponent(runId)}/events`, { params: { afterSequence: 0, limit: 200 } })
  return data.items ?? []
}

export async function getRunArtifactResult(workspace: WorkspaceKind, runId: string) {
  const response = await http.get<string>(`${root(workspace)}/runs/${encodeURIComponent(runId)}/artifacts/result`, { responseType: 'text' })
  return { content: String(response.data), version: String(response.headers['x-artifact-version'] ?? response.headers.etag ?? '') }
}

export async function createRun(
  workspace: WorkspaceKind,
  payload: {
    itemId: string
    instruction: string
    engine: 'codex' | 'opencode'
    runtime: 'native' | 'docker'
    image?: string
    directory?: string
    branch?: string
    model?: string
    permission?: 'read-only' | 'workspace-write'
    capabilityCandidateId?: string
  },
) {
  const { data } = await http.post<GongzuoRun>(`${root(workspace)}/runs`, payload)
  return data
}

export async function runAction(workspace: WorkspaceKind, runId: string, action: 'pause' | 'cancel' | 'retry', payload: Record<string, unknown> = {}) {
  const { data } = await http.post<GongzuoRun>(`${root(workspace)}/runs/${encodeURIComponent(runId)}/${action}`, action === 'retry' ? { syncContext: true, ...payload } : payload)
  return data
}

export async function listMachines(workspace: WorkspaceKind) {
  const { data } = await http.get<Machine[] | { items: Machine[] }>(`${root(workspace)}/machines`)
  return Array.isArray(data) ? data : data.items
}

export async function machineAction(workspace: WorkspaceKind, machineId: string, action: 'enable' | 'pause' | 'drain') {
  const { data } = await http.post<Machine>(`${root(workspace)}/machines/${encodeURIComponent(machineId)}/state`, { action })
  return data
}
