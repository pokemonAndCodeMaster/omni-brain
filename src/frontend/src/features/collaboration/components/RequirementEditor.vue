<script setup lang="ts">
import type { RequirementContent } from '../types'

const model = defineModel<RequirementContent>({ required: true })

function updateText(key: keyof RequirementContent, event: Event) {
  const value = (event.target as HTMLTextAreaElement).value
  model.value = { ...model.value, [key]: value }
}

function updateList(key: keyof RequirementContent, event: Event) {
  const value = (event.target as HTMLTextAreaElement).value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
  model.value = { ...model.value, [key]: value }
}

function lines(value: string[]) {
  return value.join('\n')
}
</script>

<template>
  <div class="requirement-editor">
    <div class="editor-grid">
      <label>
        <span>当前问题</span>
        <textarea :value="model.current_problem" rows="4" @input="updateText('current_problem', $event)"></textarea>
      </label>
      <label>
        <span>期望用户结果</span>
        <textarea :value="model.expected_outcome" rows="4" @input="updateText('expected_outcome', $event)"></textarea>
      </label>
      <label>
        <span>范围内 <small>每行一项</small></span>
        <textarea :value="lines(model.in_scope)" rows="4" @input="updateList('in_scope', $event)"></textarea>
      </label>
      <label>
        <span>验收标准 <small>每行一项</small></span>
        <textarea :value="lines(model.acceptance_criteria)" rows="4" @input="updateList('acceptance_criteria', $event)"></textarea>
      </label>
    </div>
    <details>
      <summary>补充完整 R1</summary>
      <div class="editor-grid detail-grid">
        <label><span>背景与来源</span><textarea :value="model.background" rows="3" @input="updateText('background', $event)"></textarea></label>
        <label><span>为什么值得做</span><textarea :value="model.value" rows="3" @input="updateText('value', $event)"></textarea></label>
        <label><span>目标用户 <small>每行一项</small></span><textarea :value="lines(model.target_users)" rows="3" @input="updateList('target_users', $event)"></textarea></label>
        <label><span>范围外 <small>每行一项</small></span><textarea :value="lines(model.out_of_scope)" rows="3" @input="updateList('out_of_scope', $event)"></textarea></label>
        <label><span>关键动作 <small>每行一项</small></span><textarea :value="lines(model.key_actions)" rows="3" @input="updateList('key_actions', $event)"></textarea></label>
        <label><span>输入 <small>每行一项</small></span><textarea :value="lines(model.inputs)" rows="3" @input="updateList('inputs', $event)"></textarea></label>
        <label><span>输出 <small>每行一项</small></span><textarea :value="lines(model.outputs)" rows="3" @input="updateList('outputs', $event)"></textarea></label>
        <label><span>约束 <small>每行一项</small></span><textarea :value="lines(model.constraints)" rows="3" @input="updateList('constraints', $event)"></textarea></label>
        <label><span>依赖 <small>每行一项</small></span><textarea :value="lines(model.dependencies)" rows="3" @input="updateList('dependencies', $event)"></textarea></label>
        <label><span>未决问题 <small>每行一项</small></span><textarea :value="lines(model.open_questions)" rows="3" @input="updateList('open_questions', $event)"></textarea></label>
      </div>
    </details>
  </div>
</template>

<style scoped>
.requirement-editor,
.editor-grid {
  display: grid;
  gap: 12px;
}

.editor-grid {
  grid-template-columns: 1fr 1fr;
}

.requirement-editor label {
  display: grid;
  gap: 5px;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 650;
}

.requirement-editor small { color: var(--color-muted); font-weight: 400; }
.requirement-editor textarea { width: 100%; padding: 8px 9px; resize: vertical; border: 1px solid var(--color-line); border-radius: var(--radius-sm); font: inherit; }
.requirement-editor details { border-top: 1px solid var(--color-line-subtle); padding-top: 10px; }
.requirement-editor summary { color: var(--color-primary); font-size: 11px; font-weight: 700; }
.detail-grid { margin-top: 12px; }

@media (max-width: 760px) {
  .editor-grid { grid-template-columns: 1fr; }
}
</style>
