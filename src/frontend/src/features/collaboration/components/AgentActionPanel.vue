<script setup lang="ts">
import { shallowRef } from 'vue'
import type { AgentActionInput, ExecutorName } from '../types'

defineProps<{ submitting?: boolean }>()
const emit = defineEmits<{ submit: [input: AgentActionInput] }>()

const action = shallowRef<AgentActionInput['action']>('knowledge_context')
const executor = shallowRef<ExecutorName>('codex')
const model = shallowRef('')
const instruction = shallowRef('')

function submit() {
  emit('submit', {
    action: action.value,
    executor: executor.value,
    model: model.value.trim() || undefined,
    instruction: instruction.value.trim() || undefined,
  })
}
</script>

<template>
  <form class="agent-action" @submit.prevent="submit">
    <header>
      <div>
        <strong>调用团队能力</strong>
        <small>结果先作为候选进入时间线</small>
      </div>
      <span>默认 Codex</span>
    </header>
    <div class="action-grid">
      <label>
        <span>动作</span>
        <select v-model="action" class="select-field">
          <option value="knowledge_context">查背景</option>
          <option value="shape_requirement">梳理候选需求</option>
        </select>
      </label>
      <label>
        <span>执行器</span>
        <select v-model="executor" class="select-field">
          <option value="codex">Codex</option>
          <option value="opencode">OpenCode</option>
        </select>
      </label>
    </div>
    <label>
      <span>补充说明 <small>可选</small></span>
      <textarea v-model="instruction" class="field" rows="3" placeholder="只写这次动作需要特别关注的内容"></textarea>
    </label>
    <label>
      <span>模型 <small>可选</small></span>
      <input v-model="model" class="field" placeholder="留空使用执行器默认模型" />
    </label>
    <button class="button primary" type="submit" :disabled="submitting">
      {{ submitting ? '正在启动…' : `启动 ${executor}` }}
    </button>
  </form>
</template>

<style scoped>
.agent-action {
  display: grid;
  gap: 12px;
}

.agent-action header,
.action-grid {
  display: flex;
  gap: 10px;
  align-items: center;
}

.agent-action header {
  justify-content: space-between;
}

.agent-action header div {
  display: grid;
}

.agent-action small,
.agent-action header > span {
  color: var(--color-muted);
  font-size: 10px;
}

.agent-action label {
  display: grid;
  flex: 1;
  gap: 5px;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 650;
}

.agent-action textarea {
  resize: vertical;
}
</style>
