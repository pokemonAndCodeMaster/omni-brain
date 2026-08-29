<script setup lang="ts">
import { shallowRef, watch } from 'vue'
import type { AgentDetail, CreateAgentRunInput } from '../types'

const props = defineProps<{
  agent: AgentDetail
  submitting: boolean
  error: string
}>()

const emit = defineEmits<{
  close: []
  submit: [payload: CreateAgentRunInput]
}>()

const title = shallowRef('')
const prompt = shallowRef('')
const model = shallowRef('')

watch(
  () => props.agent.id,
  () => {
    title.value = ''
    prompt.value = ''
    model.value = ''
  },
  { immediate: true },
)

function submit() {
  const value = prompt.value.trim()
  if (!value) return
  emit('submit', {
    agent_id: props.agent.id,
    prompt: value,
    title: title.value.trim() || undefined,
    model: model.value.trim() || undefined,
  })
}
</script>

<template>
  <div class="dialog-backdrop" @mousedown.self="emit('close')">
    <section
      class="launch-dialog panel"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="`launch-${agent.id}`"
    >
      <header class="dialog-header">
        <div>
          <p class="eyebrow">OpenCode · {{ agent.category }}</p>
          <h2 :id="`launch-${agent.id}`">启动 {{ agent.name }}</h2>
        </div>
        <button class="icon-button" type="button" aria-label="关闭" @click="emit('close')">
          ×
        </button>
      </header>

      <div class="agent-context">
        <span class="state-chip">{{ agent.state }}</span>
        <span>{{ agent.revision_short }}</span>
        <span>{{ agent.capabilities.length }} 项能力</span>
      </div>

      <div v-if="agent.examples.length" class="example-list">
        <p>从示例开始</p>
        <button
          v-for="example in agent.examples"
          :key="example"
          type="button"
          @click="prompt = example"
        >
          {{ example }}
        </button>
      </div>

      <form class="launch-form" @submit.prevent="submit">
        <label>
          <span>任务标题 <small>可选</small></span>
          <input v-model="title" class="field" maxlength="256" placeholder="便于团队识别这次 Run" />
        </label>
        <label>
          <span>任务说明</span>
          <textarea
            v-model="prompt"
            class="field prompt-field"
            required
            rows="8"
            placeholder="说明目标、范围、约束和期望产物"
          ></textarea>
        </label>
        <label>
          <span>OpenCode 模型 <small>可选，留空使用本机默认配置</small></span>
          <input v-model="model" class="field" placeholder="provider/model" />
        </label>

        <p v-if="error" class="form-error" role="alert">{{ error }}</p>

        <footer class="dialog-actions">
          <button class="button" type="button" @click="emit('close')">取消</button>
          <button class="button primary" type="submit" :disabled="submitting || !prompt.trim()">
            {{ submitting ? '正在创建…' : '建立 worktree 并启动' }}
          </button>
        </footer>
      </form>
    </section>
  </div>
</template>

<style scoped>
.dialog-backdrop {
  position: fixed;
  z-index: 80;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgb(23 32 43 / 52%);
}

.launch-dialog {
  width: min(680px, 100%);
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  padding: 22px;
  box-shadow: var(--shadow-md);
}

.dialog-header,
.dialog-actions,
.agent-context {
  display: flex;
  align-items: center;
}

.dialog-header {
  justify-content: space-between;
  gap: 18px;
}

.dialog-header h2,
.eyebrow,
.example-list p {
  margin: 0;
}

.dialog-header h2 {
  margin-top: 4px;
  font-size: 20px;
}

.eyebrow {
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.icon-button {
  width: 34px;
  height: 34px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  background: white;
  color: var(--color-muted);
  font-size: 22px;
}

.agent-context {
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 14px;
  color: var(--color-muted);
  font-family: var(--font-mono);
  font-size: 11px;
}

.state-chip {
  padding: 3px 7px;
  border-radius: 3px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.example-list {
  display: grid;
  gap: 7px;
  margin-top: 22px;
  padding: 14px;
  border: 1px solid var(--color-line-subtle);
  background: var(--color-surface-subtle);
}

.example-list p {
  color: var(--color-muted);
  font-size: 11px;
  font-weight: 700;
}

.example-list button {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-ink-secondary);
  text-align: left;
}

.example-list button:hover {
  color: var(--color-primary);
}

.launch-form {
  display: grid;
  gap: 15px;
  margin-top: 18px;
}

.launch-form label {
  display: grid;
  gap: 6px;
  color: var(--color-ink-secondary);
  font-size: 12px;
  font-weight: 700;
}

.launch-form small {
  color: var(--color-muted);
  font-weight: 400;
}

.prompt-field {
  min-height: 150px;
  resize: vertical;
}

.form-error {
  margin: 0;
  padding: 9px 11px;
  border-left: 3px solid var(--color-danger);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.dialog-actions {
  justify-content: flex-end;
  gap: 8px;
  padding-top: 3px;
}
</style>
