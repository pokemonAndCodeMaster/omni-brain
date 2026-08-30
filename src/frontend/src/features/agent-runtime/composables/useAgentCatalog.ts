import { shallowRef } from 'vue'
import {
  getAgents,
  getAgentRuntimeHealth,
  refreshAgents,
} from '../api/agentRuntime'
import type { AgentRuntimeHealth, AgentSummary } from '../types'

export function useAgentCatalog() {
  const agents = shallowRef<AgentSummary[]>([])
  const health = shallowRef<AgentRuntimeHealth | null>(null)
  const loading = shallowRef(false)
  const error = shallowRef('')

  async function load(refresh = false) {
    loading.value = true
    error.value = ''
    try {
      const [agentRows, runtimeHealth] = await Promise.all([
        refresh ? refreshAgents() : getAgents(),
        getAgentRuntimeHealth(),
      ])
      agents.value = agentRows
      health.value = runtimeHealth
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : 'Agent 目录加载失败'
    } finally {
      loading.value = false
    }
  }

  return { agents, health, loading, error, load }
}
