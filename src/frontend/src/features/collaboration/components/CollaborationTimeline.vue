<script setup lang="ts">
import type { TimelineItem } from '../types'

defineProps<{ items: readonly TimelineItem[] }>()
const emit = defineEmits<{ useRun: [runId: string] }>()

function text(value: unknown) {
  return typeof value === 'string' ? value : ''
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
  }).format(new Date(value))
}

function title(item: TimelineItem) {
  if (item.item_type === 'entry') return text(item.payload.entry_type) === 'human_message' ? '人的补充' : '系统活动'
  if (item.item_type === 'run') return `${text(item.payload.agent_name)} · ${text(item.payload.executor)}`
  if (item.item_type === 'revision') return `Requirement Revision ${String(item.payload.revision_no ?? '')}`
  return `评审决定 · ${text(item.payload.decision_type)}`
}

function summary(item: TimelineItem) {
  if (item.item_type === 'entry') return text(item.payload.body)
  if (item.item_type === 'run') return text(item.payload.result_summary) || text(item.payload.title) || text(item.payload.status)
  if (item.item_type === 'revision') return `由 ${text(item.payload.created_by)} 保存`
  return text(item.payload.reason) || text(item.payload.commitment) || '决定已记录'
}
</script>

<template>
  <ol v-if="items.length" class="collab-timeline">
    <li v-for="item in items" :key="`${item.item_type}-${item.item_id}`">
      <span class="timeline-marker" :class="`type-${item.item_type}`"></span>
      <article>
        <header>
          <strong>{{ title(item) }}</strong>
          <time>{{ formatTime(item.occurred_at) }}</time>
        </header>
        <p>{{ summary(item) }}</p>
        <footer v-if="item.item_type === 'run'">
          <span class="run-state">{{ item.payload.status }}</span>
          <RouterLink :to="`/ai/runs/${item.item_id}`">查看 Run</RouterLink>
          <button
            v-if="item.payload.status === 'succeeded' && item.payload.trigger_action === 'shape_requirement'"
            type="button"
            @click="emit('useRun', item.item_id)"
          >
            使用结构化结果
          </button>
        </footer>
      </article>
    </li>
  </ol>
  <p v-else class="timeline-empty">还没有协作活动</p>
</template>

<style scoped>
.collab-timeline {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}

.collab-timeline li {
  position: relative;
  display: grid;
  grid-template-columns: 20px 1fr;
  gap: 9px;
  padding-bottom: 18px;
}

.collab-timeline li:not(:last-child)::before {
  position: absolute;
  top: 13px;
  bottom: 0;
  left: 6px;
  width: 1px;
  background: var(--color-line);
  content: '';
}

.timeline-marker {
  z-index: 1;
  width: 13px;
  height: 13px;
  margin-top: 3px;
  border: 3px solid white;
  border-radius: 50%;
  background: var(--color-muted);
  box-shadow: 0 0 0 1px var(--color-line);
}

.type-run { background: var(--color-primary); }
.type-decision { background: var(--color-success); }
.type-revision { background: var(--color-warning); }

.collab-timeline article {
  min-width: 0;
  padding: 11px 12px;
  border: 1px solid var(--color-line-subtle);
  border-radius: var(--radius-sm);
  background: var(--color-surface-subtle);
}

.collab-timeline header,
.collab-timeline footer {
  display: flex;
  gap: 9px;
  align-items: center;
  justify-content: space-between;
}

.collab-timeline strong { font-size: 12px; }
.collab-timeline time { color: var(--color-muted); font: 9px var(--font-mono); }
.collab-timeline p { margin: 6px 0 0; color: var(--color-ink-secondary); white-space: pre-wrap; word-break: break-word; }
.collab-timeline footer { justify-content: flex-start; margin-top: 8px; }
.collab-timeline footer a,
.collab-timeline footer button { padding: 0; border: 0; background: transparent; color: var(--color-primary); font-size: 10px; text-decoration: none; }
.run-state { color: var(--color-muted); font: 10px var(--font-mono); }
.timeline-empty { padding: 40px 12px; color: var(--color-muted); text-align: center; }
</style>
