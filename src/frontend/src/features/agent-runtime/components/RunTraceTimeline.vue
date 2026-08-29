<script setup lang="ts">
import type { AgentRunEvent } from '../types'

defineProps<{ events: AgentRunEvent[] }>()

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <ol v-if="events.length" class="trace-list">
    <li v-for="event in events" :key="event.id">
      <span class="trace-marker" :class="`source-${event.source}`"></span>
      <div class="trace-content">
        <header>
          <strong>{{ event.event_type }}</strong>
          <span>{{ event.source }} · {{ formatTime(event.occurred_at) }}</span>
        </header>
        <p>{{ event.summary }}</p>
        <details v-if="Object.keys(event.payload).length">
          <summary>原始事件</summary>
          <pre>{{ JSON.stringify(event.payload, null, 2) }}</pre>
        </details>
      </div>
    </li>
  </ol>
  <div v-else class="empty-trace">尚无事件</div>
</template>

<style scoped>
.trace-list {
  display: grid;
  gap: 0;
  margin: 0;
  padding: 0;
  list-style: none;
}

.trace-list li {
  position: relative;
  display: grid;
  grid-template-columns: 17px 1fr;
  gap: 10px;
  padding-bottom: 18px;
}

.trace-list li:not(:last-child)::before {
  position: absolute;
  top: 12px;
  bottom: -2px;
  left: 5px;
  width: 1px;
  background: var(--color-line);
  content: "";
}

.trace-marker {
  z-index: 1;
  width: 11px;
  height: 11px;
  margin-top: 4px;
  border: 2px solid white;
  border-radius: 50%;
  background: var(--color-muted);
  box-shadow: 0 0 0 1px var(--color-line);
}

.source-opencode {
  background: var(--color-primary);
}

.trace-content header {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: baseline;
  justify-content: space-between;
}

.trace-content strong {
  font-family: var(--font-mono);
  font-size: 11px;
}

.trace-content header span {
  color: var(--color-muted);
  font-family: var(--font-mono);
  font-size: 10px;
}

.trace-content p {
  margin: 4px 0 0;
  color: var(--color-ink-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.trace-content details {
  margin-top: 7px;
  color: var(--color-muted);
  font-size: 11px;
}

.trace-content pre {
  max-height: 260px;
  overflow: auto;
  padding: 10px;
  border: 1px solid var(--color-line-subtle);
  background: var(--color-surface-subtle);
  color: var(--color-ink-secondary);
  font: 10px/1.5 var(--font-mono);
  white-space: pre-wrap;
}

.empty-trace {
  padding: 32px;
  color: var(--color-muted);
  text-align: center;
}
</style>
