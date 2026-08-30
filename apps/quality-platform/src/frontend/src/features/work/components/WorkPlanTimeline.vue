<script setup lang="ts">
import { reactive } from 'vue'
import type { ExecutorName } from '@/features/agent-runtime/types'
import type { PlanStep, WorkStatus, WorkStepRunInput } from '../types'

const props = defineProps<{
  steps: PlanStep[]
  workStatus: WorkStatus
  disabled?: boolean
}>()

const emit = defineEmits<{
  launch: [stepId: string, input: WorkStepRunInput]
  complete: [stepId: string, note: string]
}>()

const instructions = reactive<Record<string, string>>({})
const completionNotes = reactive<Record<string, string>>({})
const executors = reactive<Record<string, ExecutorName>>({})

const statusLabels: Record<PlanStep['display_status'], string> = {
  blocked: '等待前序',
  ready: '可启动',
  running: '执行中',
  awaiting_gate: '等待确认',
  failed: '需重试',
  completed: '已完成',
}

function canLaunch(step: PlanStep) {
  if (step.actor_kind !== 'agent') return false
  return ['ready', 'failed', 'awaiting_gate'].includes(step.display_status)
}

function launch(step: PlanStep) {
  emit('launch', step.id, {
    executor: executors[step.id] || step.default_executor || undefined,
    instruction: instructions[step.id]?.trim() || undefined,
  })
}

function complete(step: PlanStep) {
  const note = completionNotes[step.id]?.trim()
  if (note) emit('complete', step.id, note)
}

function short(value: string | null) {
  return value ? value.slice(0, 8) : '—'
}
</script>

<template>
  <ol class="work-plan" aria-label="标准开发计划">
    <li v-for="step in steps" :key="step.id" class="work-step" :class="`is-${step.display_status}`">
      <div class="step-rail" aria-hidden="true">
        <span>{{ String(step.position).padStart(2, '0') }}</span>
      </div>

      <div class="step-body">
        <header class="step-heading">
          <div>
            <h3>{{ step.title }}</h3>
            <p>{{ step.description }}</p>
          </div>
          <span class="step-status" :class="`status-${step.display_status}`">
            {{ statusLabels[step.display_status] }}
          </span>
        </header>

        <dl class="step-meta">
          <div><dt>主体</dt><dd>{{ step.agent_id || 'admin' }}</dd></div>
          <div><dt>默认执行</dt><dd>{{ step.default_executor || '人工 Gate' }}</dd></div>
          <div><dt>历史 Run</dt><dd>{{ step.runs.length }}</dd></div>
          <div><dt>最近 Run</dt><dd>{{ short(step.runs[0]?.id || null) }}</dd></div>
        </dl>

        <div v-if="step.runs.length" class="step-runs">
          <RouterLink
            v-for="run in step.runs.slice(0, 3)"
            :key="run.id"
            :to="`/ai/runs/${run.id}`"
          >
            <span>{{ run.status }}</span>
            <strong>{{ run.id }}</strong>
            <small>{{ run.executor }}{{ run.failure_code ? ` · ${run.failure_code}` : '' }}</small>
          </RouterLink>
          <p v-if="step.runs.length > 3">另有 {{ step.runs.length - 3 }} 次历史 Run</p>
        </div>

        <p v-if="step.completion_note" class="completion-note">
          <strong>人工确认：</strong>{{ step.completion_note }}
        </p>

        <div v-if="canLaunch(step)" class="step-action-form">
          <label>
            <span>执行器</span>
            <select v-model="executors[step.id]" class="select-field">
              <option :value="step.default_executor || 'codex'">{{ step.default_executor || 'codex' }}（默认）</option>
              <option :value="step.default_executor === 'codex' ? 'opencode' : 'codex'">
                {{ step.default_executor === 'codex' ? 'opencode' : 'codex' }}（切换）
              </option>
            </select>
          </label>
          <label class="step-instruction">
            <span>人的补充（可选）</span>
            <input v-model="instructions[step.id]" class="field" placeholder="限定本次任务范围或补充上下文" />
          </label>
          <button class="button primary" type="button" :disabled="disabled" @click="launch(step)">
            {{ step.runs.length ? '新增一次 Run' : '启动步骤' }}
          </button>
        </div>

        <div v-if="step.display_status === 'awaiting_gate'" class="step-gate">
          <label>
            <span>完成依据</span>
            <input v-model="completionNotes[step.id]" class="field" placeholder="说明为什么这一步可以通过" />
          </label>
          <button
            class="button"
            type="button"
            :disabled="disabled || !completionNotes[step.id]?.trim()"
            @click="complete(step)"
          >
            人工确认并解锁下一步
          </button>
        </div>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.work-plan {
  display: grid;
  gap: 0;
  margin: 0;
  padding: 0;
  list-style: none;
}

.work-step {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
}

.step-rail {
  position: relative;
  display: flex;
  justify-content: center;
}

.step-rail::after {
  position: absolute;
  top: 36px;
  bottom: -1px;
  width: 1px;
  background: var(--color-line);
  content: '';
}

.work-step:last-child .step-rail::after {
  display: none;
}

.step-rail span {
  z-index: 1;
  display: grid;
  width: 29px;
  height: 29px;
  place-items: center;
  border: 1px solid var(--color-line);
  border-radius: 50%;
  background: white;
  color: var(--color-muted);
  font: 700 10px var(--font-mono);
}

.is-completed .step-rail span {
  border-color: var(--color-success);
  background: var(--color-success-soft);
  color: var(--color-success);
}

.is-running .step-rail span,
.is-awaiting_gate .step-rail span {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.step-body {
  min-width: 0;
  padding: 0 0 24px 4px;
}

.step-heading,
.step-action-form,
.step-gate {
  display: flex;
  gap: 10px;
  align-items: center;
}

.step-heading {
  justify-content: space-between;
}

.step-heading h3,
.step-heading p {
  margin: 0;
}

.step-heading h3 {
  font-size: 14px;
}

.step-heading p {
  margin-top: 4px;
  color: var(--color-muted);
  font-size: 11px;
}

.step-status {
  flex: none;
  padding: 4px 7px;
  border-radius: 3px;
  background: var(--color-surface-subtle);
  color: var(--color-muted);
  font: 700 10px var(--font-mono);
}

.status-running,
.status-awaiting_gate,
.status-ready {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.status-completed {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.status-failed {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.step-meta {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin: 12px 0 0;
}

.step-meta div {
  display: grid;
  gap: 3px;
}

.step-meta dt {
  color: var(--color-muted);
  font-size: 9px;
}

.step-meta dd {
  overflow: hidden;
  margin: 0;
  font: 10px var(--font-mono);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-runs {
  display: grid;
  gap: 5px;
  margin-top: 12px;
}

.step-runs a {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  gap: 8px;
  padding: 7px 9px;
  border: 1px solid var(--color-line-subtle);
  border-radius: 3px;
  color: var(--color-ink-secondary);
  font: 10px var(--font-mono);
  text-decoration: none;
}

.step-runs strong {
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-runs p {
  margin: 0;
  color: var(--color-muted);
  font-size: 10px;
}

.completion-note {
  margin: 12px 0 0;
  padding: 9px 10px;
  border-left: 2px solid var(--color-success);
  background: var(--color-success-soft);
  color: var(--color-ink-secondary);
  font-size: 11px;
}

.step-action-form,
.step-gate {
  margin-top: 12px;
  padding: 10px;
  border: 1px solid var(--color-line-subtle);
  background: var(--color-surface-subtle);
}

.step-action-form label,
.step-gate label {
  display: grid;
  gap: 4px;
  color: var(--color-muted);
  font-size: 9px;
}

.step-instruction,
.step-gate label {
  flex: 1;
}

@media (max-width: 720px) {
  .work-step {
    grid-template-columns: 38px minmax(0, 1fr);
  }

  .step-meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .step-action-form,
  .step-gate {
    align-items: stretch;
    flex-direction: column;
  }

  .step-runs a {
    grid-template-columns: 60px minmax(0, 1fr);
  }

  .step-runs small {
    grid-column: 2;
  }
}
</style>
