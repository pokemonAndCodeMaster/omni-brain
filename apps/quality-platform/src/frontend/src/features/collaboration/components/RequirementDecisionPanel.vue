<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import type { RequirementContent, RequirementDecisionInput, RequirementStatus } from '../types'

const props = defineProps<{
  status: RequirementStatus
  currentRevisionId: string
  revisionContent: RequirementContent
  submitting?: boolean
}>()
const emit = defineEmits<{ submit: [input: RequirementDecisionInput] }>()

const decisionType = shallowRef<RequirementDecisionInput['decision_type']>('accept')
const commitment = shallowRef<'NEXT' | 'LATER'>('NEXT')
const reason = shallowRef('')
const targetWindow = shallowRef('')
const entryCondition = shallowRef('')
const reviewAt = shallowRef('')
const mergedIntoId = shallowRef('')

const available = computed(() => {
  if (props.status === 'candidate') return ['accept', 'reject', 'defer', 'merge'] as const
  if (props.status === 'rejected' || props.status === 'deferred') return ['reopen'] as const
  return [] as const
})

function submit() {
  const payload: RequirementDecisionInput = {
    decision_type: decisionType.value,
    revision_id: props.currentRevisionId,
    reason: reason.value.trim() || undefined,
  }
  if (decisionType.value === 'accept') {
    payload.commitment = commitment.value
    payload.target_window = targetWindow.value.trim() || undefined
    payload.entry_condition = entryCondition.value.trim() || undefined
    payload.review_at = reviewAt.value ? new Date(reviewAt.value).toISOString() : undefined
  }
  if (decisionType.value === 'defer') {
    payload.entry_condition = entryCondition.value.trim() || undefined
    payload.review_at = reviewAt.value ? new Date(reviewAt.value).toISOString() : undefined
  }
  if (decisionType.value === 'merge') payload.merged_into_id = mergedIntoId.value.trim()
  if (decisionType.value === 'reopen') payload.revision_content = props.revisionContent
  emit('submit', payload)
}
</script>

<template>
  <form v-if="available.length" class="decision-panel" @submit.prevent="submit">
    <header><strong>需求评审</strong><small>决定由 admin 作出</small></header>
    <label>
      <span>决定</span>
      <select v-model="decisionType" class="select-field">
        <option v-for="item in available" :key="item" :value="item">{{ item }}</option>
      </select>
    </label>
    <label v-if="decisionType === 'accept'">
      <span>承诺</span>
      <select v-model="commitment" class="select-field">
        <option value="NEXT">NEXT · 下一明确窗口</option>
        <option value="LATER">LATER · 后续复审</option>
      </select>
    </label>
    <label v-if="decisionType === 'accept' && commitment === 'NEXT'">
      <span>预计窗口</span>
      <input v-model="targetWindow" class="field" placeholder="例如 S1 / 下周" />
    </label>
    <label v-if="decisionType === 'accept' || decisionType === 'defer'">
      <span>进入条件 / 触发条件</span>
      <textarea v-model="entryCondition" class="field" rows="2"></textarea>
    </label>
    <label v-if="(decisionType === 'accept' && commitment === 'LATER') || decisionType === 'defer'">
      <span>复审时间</span>
      <input v-model="reviewAt" class="field" type="datetime-local" />
    </label>
    <label v-if="decisionType === 'merge'">
      <span>承接 Requirement ID</span>
      <input v-model="mergedIntoId" class="field" required />
    </label>
    <label v-if="['reject', 'defer', 'merge', 'reopen'].includes(decisionType)">
      <span>原因</span>
      <textarea v-model="reason" class="field" rows="3" :required="decisionType !== 'reopen'"></textarea>
    </label>
    <button class="button primary" type="submit" :disabled="submitting">提交决定</button>
  </form>
  <p v-else class="decision-closed">当前状态没有可用的 S0 评审动作。</p>
</template>

<style scoped>
.decision-panel { display: grid; gap: 11px; }
.decision-panel header { display: flex; align-items: center; justify-content: space-between; }
.decision-panel header small { color: var(--color-muted); }
.decision-panel label { display: grid; gap: 5px; color: var(--color-ink-secondary); font-size: 11px; font-weight: 650; }
.decision-panel textarea { resize: vertical; }
.decision-closed { margin: 0; color: var(--color-muted); font-size: 11px; }
</style>
