<script setup lang="ts">
import { shallowRef, watch } from 'vue'
import type { Work, WorkUpdateInput } from '../types'

const props = defineProps<{ work: Work; disabled?: boolean }>()
const emit = defineEmits<{ save: [input: WorkUpdateInput] }>()

const owner = shallowRef('admin')
const reviewer = shallowRef('admin')
const start = shallowRef('')
const end = shallowRef('')

function localValue(value: string | null) {
  if (!value) return ''
  const date = new Date(value)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 16)
}

watch(
  () => props.work,
  (work) => {
    owner.value = work.owner_id
    reviewer.value = work.reviewer_id
    start.value = localValue(work.timebox_start)
    end.value = localValue(work.timebox_end)
  },
  { immediate: true },
)

function save() {
  emit('save', {
    owner_id: owner.value.trim(),
    reviewer_id: reviewer.value.trim(),
    timebox_start: start.value ? new Date(start.value).toISOString() : null,
    timebox_end: end.value ? new Date(end.value).toISOString() : null,
  })
}
</script>

<template>
  <div class="metadata-form">
    <label><span>Owner</span><input v-model="owner" class="field" /></label>
    <label><span>Reviewer</span><input v-model="reviewer" class="field" /></label>
    <label><span>开始</span><input v-model="start" class="field" type="datetime-local" /></label>
    <label><span>结束</span><input v-model="end" class="field" type="datetime-local" /></label>
    <button
      class="button"
      type="button"
      :disabled="disabled || !owner.trim() || !reviewer.trim() || work.status === 'accepted'"
      @click="save"
    >
      保存责任与时间盒
    </button>
  </div>
</template>

<style scoped>
.metadata-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.metadata-form label {
  display: grid;
  min-width: 0;
  gap: 5px;
}

.metadata-form .field {
  min-width: 0;
}

.metadata-form label span {
  color: var(--color-muted);
  font-size: 9px;
  font-weight: 700;
}

.metadata-form button {
  grid-column: 1 / -1;
}

@media (max-width: 420px) {
  .metadata-form {
    grid-template-columns: 1fr;
  }

  .metadata-form button {
    grid-column: auto;
  }
}
</style>
