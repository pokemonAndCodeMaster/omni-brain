<script setup lang="ts">
import { computed, onMounted, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAgentRuns } from '../api/agentRuntime'
import RunTraceTimeline from '../components/RunTraceTimeline.vue'
import { useAgentRunDetail } from '../composables/useAgentRunDetail'
import type { AgentRunSummary, RunStatus } from '../types'

const route = useRoute()
const router = useRouter()
const selectedRunId = computed(() => String(route.params.runId ?? ''))
const runs = shallowRef<AgentRunSummary[]>([])
const total = shallowRef(0)
const listLoading = shallowRef(false)
const listError = shallowRef('')
const statusFilter = shallowRef<RunStatus | ''>('')
const { run, events, loading, cancelling, error, refresh, cancel } = useAgentRunDetail(selectedRunId)

const active = computed(() => run.value && ['queued', 'running'].includes(run.value.status))

onMounted(() => void loadRuns())

watch(
  () => run.value?.status,
  (status, previous) => {
    if (previous && status && previous !== status) void loadRuns()
  },
)

async function loadRuns() {
  listLoading.value = true
  listError.value = ''
  try {
    const response = await getAgentRuns({
      statuses: statusFilter.value ? [statusFilter.value] : undefined,
    })
    runs.value = response.items
    total.value = response.total
  } catch (reason) {
    listError.value = reason instanceof Error ? reason.message : 'Run 列表加载失败'
  } finally {
    listLoading.value = false
  }
}

function selectRun(runId: string) {
  void router.push({ name: 'agent-runs', params: { runId } })
}

function formatTime(value: string | null) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

const statusLabels: Record<RunStatus, string> = {
  queued: '排队中',
  running: '运行中',
  succeeded: '已完成',
  failed: '失败',
  cancelled: '已取消',
}
</script>

<template>
  <section class="runs-page">
    <header class="page-heading">
      <div>
        <p class="eyebrow">EXECUTION RECORDS</p>
        <h2>Run 记录</h2>
        <p>列表只取轻量元数据；选择一条 Run 后才加载任务内容与增量事件。</p>
      </div>
      <RouterLink class="button primary" to="/ai/agents">启动新任务</RouterLink>
    </header>

    <div class="run-workspace">
      <aside class="run-list panel">
        <header class="run-list-toolbar">
          <div>
            <strong>{{ total }} 条 Run</strong>
            <small>{{ listLoading ? '正在刷新' : 'PostgreSQL' }}</small>
          </div>
          <select v-model="statusFilter" class="select-field" aria-label="按状态筛选" @change="loadRuns">
            <option value="">全部状态</option>
            <option v-for="(label, value) in statusLabels" :key="value" :value="value">
              {{ label }}
            </option>
          </select>
          <button class="button" type="button" :disabled="listLoading" @click="loadRuns">刷新</button>
        </header>

        <p v-if="listError" class="inline-error" role="alert">{{ listError }}</p>

        <div class="run-items">
          <button
            v-for="item in runs"
            :key="item.id"
            class="run-item"
            :class="{ selected: item.id === selectedRunId }"
            type="button"
            @click="selectRun(item.id)"
          >
            <span class="run-item-heading">
              <strong>{{ item.title }}</strong>
              <span class="status-chip" :class="`status-${item.status}`">
                {{ statusLabels[item.status] }}
              </span>
            </span>
            <span class="run-agent">{{ item.agent_name }}</span>
            <span class="run-meta">
              <span>{{ formatTime(item.created_at) }}</span>
              <span>{{ item.model || 'OpenCode 默认模型' }}</span>
            </span>
          </button>

          <p v-if="!runs.length && !listLoading" class="empty-list">尚无 Run 记录</p>
        </div>
      </aside>

      <main class="run-detail panel">
        <div v-if="!selectedRunId" class="empty-detail">
          <span>RUN</span>
          <h3>选择一条记录查看详情</h3>
          <p>只有此时才会查询完整任务、结果和 trace。</p>
        </div>

        <div v-else-if="loading && !run" class="empty-detail">正在读取 Run 详情…</div>

        <template v-else-if="run">
          <header class="detail-header">
            <div>
              <span class="status-chip" :class="`status-${run.status}`">{{ statusLabels[run.status] }}</span>
              <h3>{{ run.title }}</h3>
              <p>{{ run.id }}</p>
            </div>
            <div class="detail-actions">
              <button class="button" type="button" :disabled="loading" @click="refresh(false)">刷新增量</button>
              <button
                v-if="active"
                class="button danger"
                type="button"
                :disabled="cancelling"
                @click="cancel"
              >
                {{ cancelling ? '正在取消…' : '取消任务' }}
              </button>
            </div>
          </header>

          <p v-if="error" class="inline-error" role="alert">{{ error }}</p>

          <dl class="detail-facts">
            <div><dt>Agent</dt><dd>{{ run.agent_name }}</dd></div>
            <div><dt>模型</dt><dd>{{ run.model || 'OpenCode 默认配置' }}</dd></div>
            <div><dt>分支</dt><dd>{{ run.branch_name || '尚未建立' }}</dd></div>
            <div><dt>会话</dt><dd>{{ run.opencode_session_id || '尚未回填' }}</dd></div>
            <div><dt>开始</dt><dd>{{ formatTime(run.started_at) }}</dd></div>
            <div><dt>结束</dt><dd>{{ formatTime(run.finished_at) }}</dd></div>
          </dl>

          <section class="detail-section">
            <h4>任务输入</h4>
            <pre>{{ run.prompt }}</pre>
          </section>

          <section v-if="run.failure_reason" class="failure-section">
            <header><strong>{{ run.failure_code || 'opencode_error' }}</strong></header>
            <p>{{ run.failure_reason }}</p>
          </section>

          <section v-if="run.result_summary" class="detail-section">
            <h4>最终输出</h4>
            <pre>{{ run.result_summary }}</pre>
          </section>

          <section class="trace-section">
            <header>
              <h4>执行轨迹</h4>
              <span>{{ events.length }} 个已加载事件</span>
            </header>
            <RunTraceTimeline :events="events" />
          </section>
        </template>
      </main>
    </div>
  </section>
</template>

<style scoped>
.runs-page {
  display: grid;
  gap: 20px;
}

.page-heading,
.run-list-toolbar,
.detail-header,
.detail-actions,
.run-item-heading,
.run-meta,
.trace-section > header {
  display: flex;
  align-items: center;
}

.page-heading {
  justify-content: space-between;
  gap: 20px;
}

.page-heading h2,
.page-heading p,
.detail-header h3,
.detail-header p,
.detail-section h4,
.trace-section h4,
.failure-section p {
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

.page-heading a {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
}

.run-workspace {
  display: grid;
  grid-template-columns: minmax(300px, 0.34fr) minmax(0, 0.66fr);
  gap: 14px;
  min-height: calc(100vh - 190px);
}

.run-list,
.run-detail {
  min-width: 0;
  overflow: hidden;
}

.run-list-toolbar {
  gap: 8px;
  min-height: 58px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-line);
}

.run-list-toolbar > div {
  display: grid;
  min-width: 85px;
}

.run-list-toolbar small {
  color: var(--color-muted);
  font-size: 9px;
}

.run-list-toolbar .select-field {
  min-width: 110px;
  min-height: 34px;
  margin-left: auto;
}

.run-items {
  max-height: calc(100vh - 250px);
  overflow-y: auto;
}

.run-item {
  display: grid;
  gap: 7px;
  width: 100%;
  padding: 13px 14px;
  border: 0;
  border-bottom: 1px solid var(--color-line-subtle);
  background: white;
  color: var(--color-ink);
  text-align: left;
}

.run-item:hover,
.run-item.selected {
  background: var(--color-primary-soft);
}

.run-item.selected {
  box-shadow: inset 3px 0 var(--color-primary);
}

.run-item-heading,
.run-meta {
  justify-content: space-between;
  gap: 10px;
}

.run-item-heading strong {
  overflow: hidden;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.run-agent {
  color: var(--color-ink-secondary);
  font-size: 11px;
}

.run-meta {
  color: var(--color-muted);
  font-family: var(--font-mono);
  font-size: 9px;
}

.status-chip {
  display: inline-flex;
  flex: none;
  align-items: center;
  min-height: 23px;
  padding: 2px 6px;
  border-radius: 3px;
  background: var(--color-surface-subtle);
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 700;
}

.status-running,
.status-queued {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.status-succeeded {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.status-failed {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.detail-header {
  justify-content: space-between;
  gap: 20px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--color-line);
}

.detail-header h3 {
  margin-top: 7px;
  font-size: 20px;
}

.detail-header p {
  margin-top: 4px;
  color: var(--color-muted);
  font-family: var(--font-mono);
  font-size: 10px;
}

.detail-actions {
  gap: 7px;
}

.button.danger {
  border-color: #e2a9ad;
  color: var(--color-danger);
}

.detail-facts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 0;
  border-bottom: 1px solid var(--color-line);
  background: var(--color-surface-subtle);
}

.detail-facts div {
  min-width: 0;
  padding: 10px 14px;
  border-right: 1px solid var(--color-line-subtle);
}

.detail-facts dt {
  color: var(--color-muted);
  font-size: 9px;
}

.detail-facts dd {
  overflow: hidden;
  margin: 3px 0 0;
  font-family: var(--font-mono);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-section,
.trace-section,
.failure-section {
  margin: 18px 20px;
}

.detail-section h4,
.trace-section h4 {
  margin-bottom: 8px;
  font-size: 12px;
}

.detail-section pre {
  max-height: 340px;
  overflow: auto;
  margin: 0;
  padding: 13px;
  border: 1px solid var(--color-line-subtle);
  background: var(--color-surface-subtle);
  font: 11px/1.6 var(--font-mono);
  white-space: pre-wrap;
  word-break: break-word;
}

.failure-section {
  border: 1px solid #ebc3c6;
  background: var(--color-danger-soft);
}

.failure-section header,
.failure-section p {
  padding: 10px 12px;
}

.failure-section header {
  border-bottom: 1px solid #ebc3c6;
  color: var(--color-danger);
  font-family: var(--font-mono);
  font-size: 10px;
}

.failure-section p {
  color: #8e2a32;
  white-space: pre-wrap;
}

.trace-section > header {
  justify-content: space-between;
  margin-bottom: 11px;
}

.trace-section > header span {
  color: var(--color-muted);
  font-size: 10px;
}

.empty-detail,
.empty-list {
  color: var(--color-muted);
  text-align: center;
}

.empty-detail {
  display: grid;
  min-height: 460px;
  place-content: center;
}

.empty-detail span {
  color: #bec8d3;
  font: 700 46px/1 var(--font-mono);
}

.empty-detail h3 {
  margin: 14px 0 0;
  color: var(--color-ink-secondary);
}

.empty-detail p {
  margin: 6px 0 0;
}

.empty-list {
  padding: 36px 12px;
}

.inline-error {
  margin: 10px;
  padding: 9px 11px;
  border-left: 3px solid var(--color-danger);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

@media (max-width: 1000px) {
  .run-workspace {
    grid-template-columns: 1fr;
  }

  .run-items {
    max-height: 360px;
  }
}

@media (max-width: 680px) {
  .page-heading,
  .detail-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .detail-facts {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
