<script setup lang="ts">
import { shallowRef } from 'vue'

const props = defineProps<{ submitting?: boolean }>()
const emit = defineEmits<{
  submit: [input: { title: string; raw_content: string; domain_key?: string }]
}>()

const title = shallowRef('')
const rawContent = shallowRef('')
const domainKey = shallowRef('')

function submit() {
  if (!title.value.trim() || !rawContent.value.trim()) return
  emit('submit', {
    title: title.value.trim(),
    raw_content: rawContent.value.trim(),
    domain_key: domainKey.value.trim() || undefined,
  })
}
</script>

<template>
  <form class="idea-capture" @submit.prevent="submit">
    <header>
      <span>快速记录</span>
      <small>admin</small>
    </header>
    <label>
      <span>一句话标题</span>
      <input v-model="title" class="field" maxlength="256" required placeholder="先把想法留下" />
    </label>
    <label>
      <span>原始想法</span>
      <textarea
        v-model="rawContent"
        class="field"
        rows="5"
        required
        placeholder="可以不完整，Agent 不会覆盖这段原文"
      ></textarea>
    </label>
    <label>
      <span>领域 <small>可选</small></span>
      <input v-model="domainKey" class="field" maxlength="128" placeholder="例如 platform / knowledge" />
    </label>
    <button class="button primary" type="submit" :disabled="props.submitting || !title.trim() || !rawContent.trim()">
      {{ props.submitting ? '记录中…' : '记录 Idea' }}
    </button>
  </form>
</template>

<style scoped>
.idea-capture {
  display: grid;
  gap: 13px;
}

.idea-capture header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.idea-capture header span {
  font-weight: 750;
}

.idea-capture header small,
.idea-capture label small {
  color: var(--color-muted);
  font-weight: 400;
}

.idea-capture label {
  display: grid;
  gap: 6px;
  color: var(--color-ink-secondary);
  font-size: 12px;
  font-weight: 650;
}

.idea-capture textarea {
  min-height: 116px;
  resize: vertical;
}
</style>
