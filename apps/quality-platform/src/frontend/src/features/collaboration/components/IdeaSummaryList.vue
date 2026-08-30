<script setup lang="ts">
import type { IdeaSummary } from '../types'

defineProps<{ items: readonly IdeaSummary[]; loading: boolean }>()
const emit = defineEmits<{ select: [ideaId: string] }>()

const statusLabels = {
  captured: '待展开',
  discussing: '讨论中',
  converted: '已转需求',
  archived: '已归档',
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}
</script>

<template>
  <div class="idea-list">
    <button v-for="item in items" :key="item.id" type="button" @click="emit('select', item.id)">
      <span class="idea-main">
        <strong>{{ item.title }}</strong>
        <span class="status-chip" :class="`status-${item.status}`">{{ statusLabels[item.status] }}</span>
      </span>
      <span class="idea-preview">
        <span>{{ item.domain_key || '未分类' }}</span>
        <span>{{ item.run_count }} Run</span>
        <span>{{ formatTime(item.updated_at) }}</span>
      </span>
    </button>
    <p v-if="!items.length && !loading" class="empty-state">还没有 Idea。先记录一条不完整的想法。</p>
  </div>
</template>

<style scoped>
.idea-list {
  display: grid;
}

.idea-list > button {
  display: grid;
  gap: 9px;
  width: 100%;
  padding: 15px 17px;
  border: 0;
  border-bottom: 1px solid var(--color-line-subtle);
  background: white;
  color: var(--color-ink);
  text-align: left;
}

.idea-list > button:hover {
  background: var(--color-primary-soft);
}

.idea-main,
.idea-preview {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
}

.idea-main strong {
  font-size: 14px;
}

.idea-preview {
  justify-content: flex-start;
  color: var(--color-muted);
  font-family: var(--font-mono);
  font-size: 10px;
}

.status-chip {
  flex: none;
  padding: 3px 7px;
  border-radius: 3px;
  background: var(--color-surface-subtle);
  color: var(--color-muted);
  font-size: 10px;
}

.status-discussing {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.status-converted {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.empty-state {
  padding: 56px 20px;
  color: var(--color-muted);
  text-align: center;
}
</style>
