<script setup lang="ts">
import type { RequirementRevision } from '../types'

defineProps<{ revisions: readonly RequirementRevision[]; currentId: string; acceptedId: string | null }>()

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}
</script>

<template>
  <ol class="revision-list">
    <li v-for="revision in revisions" :key="revision.id">
      <span>R{{ revision.revision_no }}</span>
      <div>
        <strong>
          {{ revision.id === currentId ? '当前' : '历史' }}
          <em v-if="revision.id === acceptedId">已接纳</em>
        </strong>
        <small>{{ revision.created_by }} · {{ formatTime(revision.created_at) }}</small>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.revision-list { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
.revision-list li { display: grid; grid-template-columns: 36px 1fr; gap: 8px; align-items: center; padding: 8px; border: 1px solid var(--color-line-subtle); border-radius: var(--radius-sm); }
.revision-list li > span { display: grid; width: 32px; height: 32px; place-items: center; border-radius: 50%; background: var(--color-primary-soft); color: var(--color-primary); font: 700 10px var(--font-mono); }
.revision-list div { display: grid; }
.revision-list strong { font-size: 11px; }
.revision-list em { margin-left: 5px; color: var(--color-success); font-style: normal; }
.revision-list small { color: var(--color-muted); font: 9px var(--font-mono); }
</style>
