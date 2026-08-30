<script setup lang="ts">
import { onMounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { getWorks } from '../api/work'
import type { WorkStatus, WorkSummary } from '../types'

const router = useRouter()
const works = shallowRef<WorkSummary[]>([])
const total = shallowRef(0)
const loading = shallowRef(false)
const error = shallowRef('')
const statusFilter = shallowRef<WorkStatus | ''>('')

const statusLabels: Record<WorkStatus, string> = {
  planned: '已计划',
  in_progress: '进行中',
  in_review: '待接受',
  revision_requested: '需修订',
  accepted: '已接受',
  cancelled: '已取消',
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await getWorks({ statuses: statusFilter.value ? [statusFilter.value] : undefined })
    works.value = result.items
    total.value = result.total
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Work 列表加载失败'
  } finally {
    loading.value = false
  }
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

onMounted(() => void load())
</script>

<template>
  <section class="work-page">
    <header class="work-heading">
      <div>
        <p class="work-eyebrow">DELIVERY CONTROL</p>
        <h2>Work</h2>
        <p>从已接纳需求进入真实执行；列表只展示进度摘要，计划和 Run 在详情按需读取。</p>
      </div>
      <span class="work-count">{{ total }} 个 Work</span>
    </header>

    <section class="panel work-list-panel">
      <header class="work-toolbar">
        <div>
          <strong>交付队列</strong>
          <small>{{ loading ? '正在刷新' : 'PostgreSQL' }}</small>
        </div>
        <select v-model="statusFilter" class="select-field" aria-label="按 Work 状态筛选" @change="load">
          <option value="">全部状态</option>
          <option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option>
        </select>
        <button class="button" type="button" :disabled="loading" @click="load">刷新</button>
      </header>

      <p v-if="error" class="collab-error" role="alert">{{ error }}</p>
      <div v-if="!works.length && !loading" class="work-empty">
        <strong>还没有 Work</strong>
        <p>先在一条 accepted Requirement 中创建首个执行闭环。</p>
        <RouterLink class="button primary" to="/ai/requirements">前往需求</RouterLink>
      </div>

      <button
        v-for="work in works"
        :key="work.id"
        class="work-list-item"
        type="button"
        @click="router.push(`/ai/works/${work.id}`)"
      >
        <span class="work-list-main">
          <span>
            <strong>{{ work.title }}</strong>
            <small>{{ work.requirement_title }}</small>
          </span>
          <span class="work-status" :class="`status-${work.status}`">{{ statusLabels[work.status] }}</span>
        </span>
        <span class="progress-track" aria-hidden="true">
          <span :style="{ width: `${(work.completed_step_count / work.step_count) * 100}%` }"></span>
        </span>
        <span class="work-list-meta">
          <span>{{ work.completed_step_count }}/{{ work.step_count }} 步</span>
          <span>{{ work.run_count }} Runs</span>
          <span>{{ work.branch_name }}</span>
          <span>{{ formatTime(work.updated_at) }}</span>
        </span>
      </button>
    </section>
  </section>
</template>

<style scoped>
.work-page {
  display: grid;
  gap: 18px;
}

.work-heading,
.work-toolbar,
.work-list-main,
.work-list-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.work-heading,
.work-list-main {
  justify-content: space-between;
}

.work-heading h2,
.work-heading p,
.work-empty p {
  margin: 0;
}

.work-heading h2 {
  margin-top: 3px;
  font-size: 24px;
}

.work-heading > div > p:last-child {
  margin-top: 7px;
  color: var(--color-muted);
}

.work-eyebrow {
  color: var(--color-primary);
  font: 800 10px var(--font-mono);
  letter-spacing: .12em;
}

.work-count {
  padding: 6px 9px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  background: white;
  color: var(--color-muted);
  font: 10px var(--font-mono);
}

.work-list-panel {
  overflow: hidden;
}

.work-toolbar {
  min-height: 54px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-line);
}

.work-toolbar > div {
  display: grid;
  margin-right: auto;
}

.work-toolbar small {
  color: var(--color-muted);
  font-size: 9px;
}

.work-list-item {
  display: grid;
  gap: 11px;
  width: 100%;
  padding: 16px;
  border: 0;
  border-bottom: 1px solid var(--color-line-subtle);
  background: white;
  color: var(--color-ink);
  text-align: left;
}

.work-list-item:hover {
  background: var(--color-primary-soft);
}

.work-list-main > span:first-child {
  display: grid;
  gap: 4px;
}

.work-list-main small {
  color: var(--color-muted);
}

.work-status {
  padding: 4px 7px;
  border-radius: 3px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font: 700 10px var(--font-mono);
}

.status-accepted {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.status-revision_requested,
.status-cancelled {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.progress-track {
  height: 3px;
  overflow: hidden;
  background: var(--color-line-subtle);
}

.progress-track span {
  display: block;
  height: 100%;
  background: var(--color-primary);
}

.work-list-meta {
  color: var(--color-muted);
  font: 10px var(--font-mono);
}

.work-list-meta span:nth-child(3) {
  overflow: hidden;
  flex: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.work-empty {
  display: grid;
  gap: 10px;
  justify-items: center;
  padding: 64px 20px;
  color: var(--color-muted);
  text-align: center;
}

.work-empty a {
  text-decoration: none;
}

@media (max-width: 720px) {
  .work-heading,
  .work-toolbar,
  .work-list-meta {
    align-items: stretch;
    flex-direction: column;
  }

  .work-toolbar .select-field {
    width: 100%;
  }
}
</style>
