<script setup lang="ts">
import { computed, onMounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { createAgentRun, getAgent } from '../api/agentRuntime'
import AgentLaunchDialog from '../components/AgentLaunchDialog.vue'
import { useAgentCatalog } from '../composables/useAgentCatalog'
import type { AgentDetail, AgentSummary, CreateAgentRunInput } from '../types'

const router = useRouter()
const { agents, health, loading, error, load } = useAgentCatalog()
const selectedAgent = shallowRef<AgentDetail | null>(null)
const detailLoadingId = shallowRef('')
const launchSubmitting = shallowRef(false)
const launchError = shallowRef('')

const executorHealth = computed(() => health.value?.executors ?? [])
const healthByName = computed(() => new Map(executorHealth.value.map((item) => [item.name, item])))

function canLaunch(agent: AgentSummary) {
  return agent.supported_executors.some((name) => healthByName.value.get(name)?.available)
}

const categories = computed(() => {
  const groups = new Map<string, AgentSummary[]>()
  for (const agent of agents.value) {
    const rows = groups.get(agent.category) ?? []
    rows.push(agent)
    groups.set(agent.category, rows)
  }
  return [...groups.entries()].map(([name, rows]) => ({ name, rows }))
})

onMounted(() => void load())

async function openLaunch(agent: AgentSummary) {
  detailLoadingId.value = agent.id
  launchError.value = ''
  try {
    selectedAgent.value = await getAgent(agent.id)
  } catch (reason) {
    launchError.value = reason instanceof Error ? reason.message : 'Agent 详情加载失败'
  } finally {
    detailLoadingId.value = ''
  }
}

async function launch(payload: CreateAgentRunInput) {
  launchSubmitting.value = true
  launchError.value = ''
  try {
    const run = await createAgentRun(payload)
    selectedAgent.value = null
    await router.push({ name: 'agent-runs', params: { runId: run.id } })
  } catch (reason) {
    launchError.value = reason instanceof Error ? reason.message : 'Run 创建失败'
  } finally {
    launchSubmitting.value = false
  }
}
</script>

<template>
  <section class="catalog-page">
    <header class="page-heading">
      <div>
        <p class="eyebrow">TEAM CAPABILITY CATALOG</p>
        <h2>Agent 能力目录</h2>
        <p>这里展示已发布的团队能力和轻量运行统计；配置与详细轨迹只在需要时读取。</p>
      </div>
      <button class="button" type="button" :disabled="loading" @click="load(true)">
        {{ loading ? '正在刷新…' : '刷新注册表' }}
      </button>
    </header>

    <div class="runtime-strip panel">
      <div
        v-for="item in executorHealth"
        :key="item.name"
        class="runtime-item"
        :class="{ unavailable: !item.available }"
      >
        <span class="runtime-dot"></span>
        <strong>{{ item.name }}</strong>
        <span>{{ item.available ? item.version : item.reason }}</span>
      </div>
      <RouterLink to="/ai/runs">查看 Run 记录</RouterLink>
    </div>

    <p v-if="error || launchError" class="page-error" role="alert">{{ error || launchError }}</p>

    <div v-if="!loading || agents.length" class="category-list">
      <section v-for="category in categories" :key="category.name" class="category-section">
        <header>
          <h3>{{ category.name }}</h3>
          <span>{{ category.rows.length }} 项能力</span>
        </header>
        <div class="agent-grid">
          <article v-for="agent in category.rows" :key="agent.id" class="agent-card panel">
            <div class="agent-card-topline">
              <span class="agent-state" :class="`state-${agent.state}`">{{ agent.state }}</span>
              <span class="revision">{{ agent.revision_short }}</span>
            </div>
            <h4>{{ agent.name }}</h4>
            <p>{{ agent.description }}</p>
            <dl class="run-metrics">
              <div><dt>历史 Run</dt><dd>{{ agent.run_counts.total }}</dd></div>
              <div><dt>运行中</dt><dd>{{ agent.run_counts.active }}</dd></div>
              <div><dt>成功</dt><dd>{{ agent.run_counts.succeeded }}</dd></div>
            </dl>
            <footer>
              <span>{{ agent.default_executor }} 默认 · {{ agent.supported_executors.join(' / ') }}</span>
              <button
                class="button primary"
                type="button"
                :disabled="detailLoadingId === agent.id || !canLaunch(agent)"
                @click="openLaunch(agent)"
              >
                {{ detailLoadingId === agent.id ? '读取配置…' : '启动任务' }}
              </button>
            </footer>
          </article>
        </div>
      </section>
    </div>

    <div v-else class="catalog-loading panel">正在读取 Agent 注册表…</div>

    <AgentLaunchDialog
      v-if="selectedAgent"
      :agent="selectedAgent"
      :submitting="launchSubmitting"
      :error="launchError"
      :executor-health="executorHealth"
      @close="selectedAgent = null"
      @submit="launch"
    />
  </section>
</template>

<style scoped>
.catalog-page,
.category-list {
  display: grid;
  gap: 22px;
}

.page-heading,
.runtime-strip,
.category-section > header,
.agent-card-topline,
.agent-card footer {
  display: flex;
  align-items: center;
}

.page-heading {
  justify-content: space-between;
  gap: 24px;
}

.page-heading h2,
.page-heading p,
.category-section h3,
.agent-card h4,
.agent-card p {
  margin: 0;
}

.page-heading h2 {
  margin-top: 3px;
  font-size: 24px;
}

.page-heading > div > p:last-child {
  margin-top: 7px;
  color: var(--color-muted);
}

.eyebrow {
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.runtime-strip {
  gap: 9px;
  min-height: 44px;
  padding: 0 14px;
  color: var(--color-muted);
  font-size: 12px;
}

.runtime-item {
  display: flex;
  gap: 8px;
  align-items: center;
  padding-right: 14px;
  border-right: 1px solid var(--color-line-subtle);
}

.runtime-strip strong {
  color: var(--color-ink);
}

.runtime-strip a {
  margin-left: auto;
  color: var(--color-primary);
  text-decoration: none;
}

.runtime-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow: 0 0 0 3px var(--color-success-soft);
}

.runtime-item.unavailable .runtime-dot {
  background: var(--color-danger);
  box-shadow: 0 0 0 3px var(--color-danger-soft);
}

.page-error {
  margin: 0;
  padding: 10px 12px;
  border-left: 3px solid var(--color-danger);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.category-section {
  display: grid;
  gap: 11px;
}

.category-section > header {
  justify-content: space-between;
}

.category-section h3 {
  font-size: 15px;
}

.category-section > header span {
  color: var(--color-muted);
  font-size: 11px;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.agent-card {
  display: grid;
  gap: 13px;
  min-height: 245px;
  padding: 16px;
}

.agent-card-topline,
.agent-card footer {
  justify-content: space-between;
}

.agent-state,
.revision {
  font-family: var(--font-mono);
  font-size: 10px;
}

.agent-state {
  padding: 3px 6px;
  border-radius: 3px;
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.state-verified {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.state-implemented {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.revision,
.agent-card footer > span {
  color: var(--color-muted);
}

.agent-card h4 {
  font-size: 17px;
}

.agent-card > p {
  min-height: 42px;
  color: var(--color-ink-secondary);
}

.run-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 0;
  border-block: 1px solid var(--color-line-subtle);
}

.run-metrics div {
  padding: 10px 4px;
}

.run-metrics dt {
  color: var(--color-muted);
  font-size: 10px;
}

.run-metrics dd {
  margin: 3px 0 0;
  font-family: var(--font-mono);
  font-size: 16px;
  font-weight: 700;
}

.agent-card footer {
  margin-top: auto;
}

.agent-card footer > span {
  font-family: var(--font-mono);
  font-size: 10px;
}

.catalog-loading {
  padding: 48px;
  color: var(--color-muted);
  text-align: center;
}

@media (max-width: 680px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
